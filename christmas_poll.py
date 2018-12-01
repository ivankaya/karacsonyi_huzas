# -*- coding: utf-8 -*-

import sys

import os

import smtplib

import random

import logging

from email.mime.text import MIMEText

from mail_template import message_template

PARTICIPANTS_FILE = os.path.dirname(os.path.realpath(__file__)) + "/participants.csv"


def check_environment():
    for env_key in ["CP_SMTP_SERVER_ADDR", "CP_SMTP_SERVER_PORT",
                    "CP_SMTP_SERVER_UNAME", "CP_SMTP_SERVER_PWD",
                    "CP_SENDER_MAIL_ADDR", "CP_SMTP_SERVER_NICKNAME"]:
        if os.getenv(env_key, "") == "":
            raise KeyError("{} not defined.".format(env_key))


def load_csv_as_dict(filepath, key_col=0, value_col=1, delimiter=";", offset=0):
    return {row.split(delimiter)[key_col].replace("\n", ""): row.split(delimiter)[value_col].replace(
            "\n", "") for row in open(filepath).readlines()[offset:]}


def create_pairings(name_dict):
    names = sorted(name_dict.keys())
    pairings = zip(sorted(name_dict.keys()), names)
    while any([pair[0] == pair[1] for pair in pairings]):
        random.shuffle(names)
        pairings = list(zip(sorted(name_dict.keys()), names))
    return pairings


if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    try:
        check_environment()
    except KeyError as key_error:
        logger.error("Missing environment values.")
        logger.debug(key_error)
        sys.exit()

    try:
        random.seed(int(sys.argv[1]))
        logger.info("Using seed {0}".format(sys.argv[1]))
    except (ValueError, IndexError) as seed_error:
        logger.warning("Invalid or no seed provided, using default.")
        logger.debug(seed_error)
        random.seed(42)

    name_to_mail = load_csv_as_dict(PARTICIPANTS_FILE)

    with smtplib.SMTP(os.getenv("CP_SMTP_SERVER_ADDR"), os.getenv("CP_SMTP_SERVER_PORT")) as smtpObj:
        smtpObj.login(user=os.getenv("CP_SMTP_SERVER_UNAME"), password=os.getenv("CP_SMTP_SERVER_PWD"))
        for drawn_pair in create_pairings(name_to_mail):
            msg = MIMEText(message_template.format(recipient=drawn_pair[0], drawn_person=drawn_pair[
                1], sender_nickname=os.getenv("CP_SMTP_SERVER_NICKNAME", os.getenv("CP_SENDER_MAIL_ADDR"))))
            msg['Subject'] = "Karácsonyi móka 2018"
            msg['From'] = os.getenv("CP_SENDER_MAIL_ADDR")
            msg['To'] = name_to_mail[drawn_pair[0]]

            try:
                smtpObj.sendmail(msg['From'], msg['To'], msg.as_string())
                logger.info("Email sent to {0}: {1}.".format(drawn_pair[0], name_to_mail[drawn_pair[0]]))
            except smtplib.SMTPException as smtp_error:
                logger.error("Sending to {0}: {1} failed.".format(drawn_pair[0], name_to_mail[drawn_pair[0]]))
                logger.debug(smtp_error)
        smtpObj.quit()

