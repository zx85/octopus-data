#!/usr/bin/python3

# This needs the following environment variables to be created:

# Telegram goodness
# export telegramBotToken="YOUR_TELEGRAM_BOT_TOKEN"
# export telegramChatId="YOUR_PERSONAL_CHAT_ID"

# Octopus variables
# export octopusURL="https://api.octopus.energy"
# export octopusTariff="YOUR_OCTOPUS_AGILE_TARIFF"
# export octopusAPIKey="YOUR_OCTOPUS_API_KEY"
# export octopusMPAN="YOUR_SMARTMETER_MPAN"
# export octopusSN="YOUR_SMARTMETER_SERIAL"

import os
import sys
import json
from calendar import monthrange
import requests
import jmespath
from pathlib import Path

from include.google_sheets import Spreadsheet
from include.octopus import Octopus
from include.telegram import TelegramBot

from include.logger import log

current_path=os.path.dirname(os.path.abspath(__file__))

# Octopus goodies
octopus_info = {
    "url": os.environ.get("OCTOPUS_URL"),
    "tariff": os.environ.get("OCTOPUS_TARIFF"),
    "api_key": os.environ.get("OCTOPUS_API_KEY"),
    "mpan": os.environ.get("OCTOPUS_MPAN"),
    "sn": os.environ.get("OCTOPUS_SN")
}

def main():
    # Bot business
    telegram_bot=TelegramBot(
        bot_token=os.environ.get("TELEGRAM_BOT_TOKEN"),
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    )

    # Database credentials for the conkers
    # Initialize spreadsheet
    sheet = Spreadsheet(
        creds_file=f"{current_path}/../google.json",
        spreadsheet_name="Solar Database",
        worksheet_name="octopusIn",
    )


    octopus=Octopus(octopus_info)

    if len(sys.argv) < 2:
        print("Usage: getday.py yyyy-mm-dd")
        print("eg. getday.py 2023-01-15")
        exit(1)
    date_query = sys.argv[1]

    # check the spreadsheet to see if it's the first update for the day

    # do the Octopus stuff - and return the overnight data if it's arrived
    usage, overnight = octopus.get_usage(date_query)

    # add data to the spreadsheet if there's new data

    # Send the message about the overnight data
    log.debug(f'Overnight is {overnight}')
    if overnight:
        telegram_bot.send_telegram_message(date_query, overnight)

if __name__ == "__main__":
    main()
