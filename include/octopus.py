import requests
import base64
import json
from include.logger import log
from include.time_functions import utc_calc, utc_to_localtime

class Octopus():
    def __init__(self,octopus_info):
        self.octopus_info = octopus_info
        self.url = octopus_info['url']
        self.api_key = octopus_info['api_key']
        self.tariff = octopus_info['tariff']
        self.mpan = octopus_info['mpan']
        self.sn = octopus_info['sn']

    def get_price_data(self, date_query):
        log.info(f"running get_price_data function for {date_query}")
        # print(f"Getting agile price data for {date_query}...")
        results = {}
        auth = "Basic " + base64.b64encode(self.api_key.encode("UTF-8")).decode(
            "UTF-8"
        )
        url = f"{self.url}/v1/products/{self.tariff}/electricity-tariffs/E-1R-{self.tariff}-A/standard-unit-rates/?period_from={utc_calc(date_query)}&period_to={utc_calc(date_query,1)}"
        # print(f"URL is {url}")
        Session = requests.Session()
        header = {"Authorization": auth}
        log.debug(f"web service call to {url}")
        try:
            resp = Session.get(url, headers=header, timeout=60)
            status_code = resp.status_code
            log.debug(f"Response status code: {str(status_code)}")
            log.debug("\nHere is the resultant:")
            log.debug(json.dumps(resp.json(),indent=2))
            log.debug("#####################\n")
            results = resp.json()
        except Exception as e:
            log.error("Agile data request failed because " + str(e))
        log.info("end of get_price_data function")
        return results

    # This returns results in local time - we'll leave it as it is
    def get_consumed_data(self, date_query):
        log.info(f"running get_consumed_data function for {date_query}")
        results = {}
        auth = "Basic " + base64.b64encode(self.api_key.encode("UTF-8")).decode(
            "UTF-8"
        )
        url = f"{self.url}/v1/electricity-meter-points/{self.mpan}/meters/{self.sn}/consumption/?period_from={utc_calc(date_query)}&period_to={utc_calc(date_query,1)}"
        # print(f"URL is {url}")
        Session = requests.Session()
        header = {"Authorization": auth}
        log.debug(f"web service call to {url}")
        try:
            resp = Session.get(url, headers=header, timeout=60)
            status_code = resp.status_code
            log.debug(f"Response status code: {str(status_code)}")
            log.debug("\nHere is the resultant:")
            log.debug(json.dumps(resp.json(),indent=2))
            log.debug("#####################\n")
            results = resp.json()
        except Exception as e:
            log.error(f"Consumption data request failed because {str(e)}")
        return results

    def get_usage(self,date_query):
        log.info(f"get_octopus_usage function for {date_query}")
        price_data = self.get_price_data(date_query)
        consumed_data = self.get_consumed_data(date_query)
        results = True
        overnight = {}
        new_data = False

        # Check validity of results
        if "results" not in price_data:
            log.warning("No JSON results in price_data - please try again later")
            results = False
        else:
            if len(price_data["results"]) == 0:
                log.warning("Empty results set in price_data - please try again later")
                results = False

        if "results" not in consumed_data:
            log.warning("No JSON results consumed_data - please try again later")
            results = False
        else:
            if len(consumed_data["results"]) == 0:
                log.warning(
                    "Empty results set in consumed_data - please try again later"
                )
                results = False

        if results:
            log.debug("We have consumed and price results, so carry on")
            overnight = []
            usage = []

            log.debug(f"Checking to see if there's already data for {date_query}")
            # TODO: check the spreadsheet for data

            log.debug("Looping through the results of consumed_data")
            for consumed in consumed_data["results"]:
                # consumed is in local time - trim after the +
                consumed["interval_start_local"] = consumed["interval_start"].split("+")[0].replace('T',' ')
                for price in price_data["results"]:
                    # price is in UTC - convert it to local
                    price["valid_from_local"]=utc_to_localtime(price["valid_from"])
                    id = {}
                    if price["valid_from_local"] == consumed["interval_start_local"]:
                        # this is where the database stuff comes in
                        id["year"] = consumed["interval_start"][:4]
                        id["month"] = consumed["interval_start"][5:7]
                        id["day"] = consumed["interval_start"][8:10]
                        id["hour"] = consumed["interval_start"][11:13]
                        id["minute"] = consumed["interval_start"][14:16]
                        id["consumed"] = consumed["consumption"]
                        id["price"] = price["value_inc_vat"]
                        usage.append(id)
                        if int(id["hour"]) >= 0 and int(id["hour"]) <= 6:
                            overnight.append(id)
                        log.debug(
                            f"{id['year']}-{id['month']}-{id['day']} {id['hour']}:{id['minute']} - {id['consumed']} kWh @ £{id['price']/100}"
                        )

        return usage, overnight

