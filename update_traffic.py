from db import get_all_user_ids, update_traffic_metrics
from outline.api import get_traffic_for_key
from settings import DEFAULT_SERVER_ID
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

def run_traffic_update():
    logging.info("=== Start traffic update ===")

    for user_id, key_id in get_all_user_ids():
        if not key_id:
            continue

        try:
            current_total = get_traffic_for_key(key_id, DEFAULT_SERVER_ID)
            update_traffic_metrics(user_id, current_total)
            logging.info(f"[+] Updated traffic for user {user_id}, key={key_id}: {current_total} bytes")
        except Exception as e:
            logging.error(f"[!] Error updating traffic for user {user_id}: {str(e)}")

    logging.info("=== End traffic update ===")

if __name__ == "__main__":
    run_traffic_update()

from datetime import date

# ...
def run_traffic_update():
    # ... основной цикл
    if date.today().day == 1:
        from db import reset_monthly_usage
        reset_monthly_usage()
