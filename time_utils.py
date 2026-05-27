from datetime import datetime

import pytz


def is_within_sleep_time(sleep_config):
    tz = pytz.timezone(sleep_config.timezone)
    now = datetime.now(tz)
    current_time = now.time()

    start = sleep_config.sleep_start_time
    end = sleep_config.sleep_end_time

    if start <= end:
        return start <= current_time <= end
    else:
        return current_time >= start or current_time <= end
