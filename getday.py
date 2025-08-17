#!/usr/bin/python3
import os
import sys
import json
from calendar import monthrange
import hashlib
from hashlib import sha1
import hmac
import base64
from datetime import datetime, timezone, timedelta
import time
import pytz
import requests
import jmespath
from pathlib import Path

from includes import Spreadsheet

# I think this is python-telegram-bot
import telegram
import logging

# Create a logger
logger = logging.getLogger("")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

current_path=os.path.dirname(os.path.abspath(__file__))

# Local time doings
def localtime(inputTime):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inputTime))

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
# export octopusInTable="YOUR_OCTOPUSIN_TABLE" # normally octopusIn


# Push message doings
def send_telegram_message(bot, chat_id, date_query, overnight):
    logger.debug(f"running sendmessage function - chat_id is {chat_id}")
    logger.debug("Building telegram message with overnight data")
    total_consumed = 0
    total_cost = 0
    message_str = f"Overnight usage for {date_query}:\n"
    for hh in overnight:
        message_str += (
            hh["hour"]
            + ":"
            + hh["minute"]
            + " - "
            + "{0:.3f}".format(hh["consumed"])
            + "kWh @ £"
            + "{0:.2f}".format(hh["price"] / 100)
            + "\n"
        )
        total_consumed += hh["consumed"]
        total_cost += hh["consumed"] * hh["price"] / 100
    message_str += f"Consumed: {'{0:.3f}'.format(total_consumed)}kWh\nCost: £{'{0:.2f}'.format(total_cost)}"
    logger.debug(f"Sending the telegram message: {message_str}")

    bot.send_message(chat_id=chat_id, text=message_str)


def localtime(inputTime):
    logger.debug(f"running localtime function - localtime is {localtime}")
    return time.strftime("%Y-%m-%d %H:%M:%S %Z", time.localtime(inputTime))


# Local time doings
def utc_calc(time_string, day_diff=0):
    logger.debug(
        f"running utc_calc function - time_string is {time_string} - day_diff is {day_diff}"
    )
    local = pytz.timezone("Europe/London")
    naive = datetime.strptime(time_string, "%Y-%m-%d")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc) + timedelta(days=day_diff)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_price_data(octopusInfo, date_query):
    logger.info(f"running get_price_data function for {date_query}")
    # print(f"Getting agile price data for {date_query}...")
    results = {}
    auth = "Basic " + base64.b64encode(octopusInfo["APIKey"].encode("UTF-8")).decode(
        "UTF-8"
    )
    url = f"{octopusInfo['URL']}/v1/products/{octopusInfo['Tariff']}/electricity-tariffs/E-1R-{octopusInfo['Tariff']}-A/standard-unit-rates/?period_from={utc_calc(date_query)}&period_to={utc_calc(date_query,1)}"
    # print(f"URL is {url}")
    Session = requests.Session()
    header = {"Authorization": auth}
    logger.debug(f"web service call to {url}")
    try:
        resp = Session.get(url, headers=header, timeout=60)
        status_code = resp.status_code
        logger.debug(f"Response status code: {str(status_code)}")
        logger.debug("\nHere is the resultant:")
        logger.debug(json.dumps(resp.json()))
        logger.debug("#####################\n")
        results = resp.json()
    except Exception as e:
        logger.error("Agile data request failed because " + str(e))
    logger.info("end of get_price_data function")
    return results


def get_consumed_data(octopusInfo, date_query):
    logger.info(f"running get_consumed_data function for {date_query}")
    results = {}
    auth = "Basic " + base64.b64encode(octopusInfo["APIKey"].encode("UTF-8")).decode(
        "UTF-8"
    )
    url = f"{octopusInfo['URL']}/v1/electricity-meter-points/{octopusInfo['MPAN']}/meters/{octopusInfo['SN']}/consumption/?period_from={utc_calc(date_query)}&period_to={utc_calc(date_query,1)}"
    # print(f"URL is {url}")
    Session = requests.Session()
    header = {"Authorization": auth}
    logger.debug(f"web service call to {url}")
    try:
        resp = Session.get(url, headers=header, timeout=60)
        status_code = resp.status_code
        logger.debug(f"Response status code: {str(status_code)}")
        logger.debug("\nHere is the resultant:")
        logger.debug(json.dumps(resp.json()))
        logger.debug("#####################\n")
        results = resp.json()
    except Exception as e:
        logger.error(f"Consumption data request failed because {str(e)}")
    return results


def update_octopus_usage(sheet, octopusInfo, date_query):
    logger.info(f"running update_octopus_usage function for {date_query}")
    price_data = get_price_data(octopusInfo, date_query)
    consumed_data = get_consumed_data(octopusInfo, date_query)
    results = True
    overnight = {}
    new_data = False

    # Check validity of results
    if "results" not in price_data:
        logger.warning("No JSON results in price_data - please try again later")
        results = False
    else:
        if len(price_data["results"]) == 0:
            logger.warning("Empty results set in price_data - please try again later")
            results = False

    if "results" not in consumed_data:
        logger.warning("No JSON results consumed_data - please try again later")
        results = False
    else:
        if len(consumed_data["results"]) == 0:
            logger.warning(
                "Empty results set in consumed_data - please try again later"
            )
            results = False

    if results:
        logger.debug("We have consumed and price results, so carry on")
        last_overnight = []

        logger.debug(f"Checking to see if there's already data for {date_query}")
        # TODO: check the spreadsheet for data

        logger.debug("Looping through the results of consumed_data")
        for each_result in consumed_data["results"]:
            for each_price in price_data["results"]:
                id = {}
                if each_price["valid_from"] == each_result["interval_start"]:
                    # this is where the database stuff comes in
                    id["year"] = each_result["interval_start"][:4]
                    id["month"] = each_result["interval_start"][5:7]
                    id["day"] = each_result["interval_start"][8:10]
                    id["hour"] = each_result["interval_start"][11:13]
                    id["minute"] = each_result["interval_start"][14:16]
                    id["consumed"] = each_result["consumption"]
                    id["price"] = each_price["value_inc_vat"]
                    if int(id["hour"]) >= 0 and int(id["hour"]) <= 6:
                        last_overnight.append(id)
                    logger.debug(
                        f"{id['year']}-{id['month']}-{id['day']} {id['hour']}:{id['minute']} - {id['consumed']} kWh @ £{id['price']/100}"
                    )
            # TODO: replace into the spreadsheet
        if new_data:
            logger.debug("last_overnight is new - returning it")
        else:
            logger.debug("last_overnight is not new - returning empty set")
        return last_overnight


def main():
    # Bot business
    bot = telegram.Bot(token=os.environ.get("telegramBotToken"))
    mychatid = os.environ.get("telegramChatId")

    # Database credentials for the conkers
    # Initialize spreadsheet
    sheet = Spreadsheet(
        creds_file=f"{current_path}/google.json",
        spreadsheet_name="Solar Database",
        worksheet_name="octopusIn",
    )

    # Octopus goodies
    octopusInfo = {
        "URL": os.environ.get("octopusURL"),
        "Tariff": os.environ.get("octopusTariff"),
        "APIKey": os.environ.get("octopusAPIKey"),
        "MPAN": os.environ.get("octopusMPAN"),
        "SN": os.environ.get("octopusSN")
    }

    if len(sys.argv) < 2:
        print("Usage: getday.py yyyy-mm-dd")
        print("eg. getday.py 2023-01-15")
        exit(1)
    date_query = sys.argv[1]

    # check to see if it's the first update

    # do the Octopus stuff - and return the overnight data if it's arrived
    overnight = update_octopus_usage(sheet, octopusInfo, date_query)

    # Send the message
    if overnight:
        send_telegram_message(bot, mychatid, date_query, overnight)


if __name__ == "__main__":
    main()
