from veracore_sync import setup_selenium_driver, login_and_select_system, sync_single_order, get_pending_work_orders, VERACORE_URL, VERACORE_USER, VERACORE_PASS, SYSTEM_ID
import time
import os


def auto_sync_loop():
    driver = setup_selenium_driver()
    login_and_select_system(driver, VERACORE_URL, VERACORE_USER, VERACORE_PASS, SYSTEM_ID)

    while True:
        pending = get_pending_work_orders()
        for _, order in pending.iterrows():
            sync_single_order(order)
        time.sleep(60)  # check once per minute
