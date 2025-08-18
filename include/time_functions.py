from datetime import datetime, timezone, timedelta
import zoneinfo
import time
import pytz

from include.logger import log

def utc_calc(time_string, day_diff=0):
    log.debug(
        f"running utc_calc function - time_string is {time_string} - day_diff is {day_diff}"
    )
    local = pytz.timezone("Europe/London")
    naive = datetime.strptime(time_string, "%Y-%m-%d")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc) + timedelta(days=day_diff)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_to_localtime(input_time):
    dt_utc = datetime.strptime(input_time, "%Y-%m-%dT%H:%M:%SZ")
    dt_utc = dt_utc.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))

    # Convert to local timezone (London)
    dt_local = dt_utc.astimezone(zoneinfo.ZoneInfo("Europe/London"))

    # Format as YYYY-mm-dd HH:MM:SS
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")

