import pandas as pd
import json
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import pymssql
import logging
import sys

# Configure logging
log_dir = r"C:\VeracoreSync\logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'veracore_sync_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "server": "3PLWIN-SERVER\\WINNERSQLDEV",
    "user": "sa",
    "password": "$!SQL_d3v!$",
    "database": "WarehouseSystem"
}

# Veracore configuration
VERACORE_URL = "https://wms.3plwinner.com/VeraCore"
VERACORE_USER = "ljannatipour"
VERACORE_PASS = "Inkypinky343!"
SYSTEM_ID = "3plwhs"

def get_connection():
    return pymssql.connect(
        server=DB_CONFIG["server"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )

def setup_selenium_driver():
    chrome_options = Options()
    
    # Keep headless for scheduled tasks
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Add window size for headless mode
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("ChromeDriver intialized using webdriver-manager")
    except Exception as e:
        logger.error(f"Failed to initialize Chrome driver: {e}")
        raise

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def open_accessorial_fee_window(driver, wait):
    """Open accessorial fee window"""
    try:
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-mask')]")))
    except:
        pass
        
    try:
        accfee_btn = wait.until(EC.element_to_be_clickable((By.ID, "ui-accfee-btn")))
        
        try:
            accfee_btn.click()
        except:
            try:
                driver.execute_script("arguments[0].click();", accfee_btn)
            except:
                ActionChains(driver).move_to_element(accfee_btn).click().perform()
        
        time.sleep(3)
        return True
        
    except Exception as e:
        logger.error(f"Failed to open accessorial fee window: {e}")
        return False

def login_and_select_system(driver, url, username, password, system_id="3plwhs"):
    """Logs in and selects the fixed system"""
    wait = WebDriverWait(driver, 30)
    driver.get(url)

    try:
        # Login
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        username_field.clear()
        username_field.send_keys(username)
        
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_field.clear()
        password_field.send_keys(password)
        
        login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Login']/..")))
        password_field.send_keys(Keys.TAB)
        time.sleep(0.3)
        driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
        time.sleep(0.3)
        
        try:
            login_btn.click()
        except:
            driver.execute_script("arguments[0].click();", login_btn)

        # Select the fixed system
        system_el = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//a[contains(@onclick, \"'{system_id}'\")]"))
        )
        
        try:
            system_el.click()
        except:
            driver.execute_script("arguments[0].click();", system_el)

        # Wait until main UI is ready
        wait.until(EC.presence_of_element_located((By.ID, "ui-accfee-btn")))
        time.sleep(2)

        logger.info(f"Successfully logged in and selected system: {system_id}")
        return system_id
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise

def input_system_id_in_fee_window(driver, wait, customer_name):
    """Input the customer_name into the system ID field in the fee window"""
    try:
        system_id_input = wait.until(EC.presence_of_element_located((
            By.ID, "combo-1043-inputEl"
        )))

        system_id_input.send_keys(Keys.CONTROL + "a")
        system_id_input.send_keys(Keys.DELETE)
        time.sleep(0.2)

        for char in customer_name:
            system_id_input.send_keys(char)
            time.sleep(0.1)
        time.sleep(2)

        system_id_input.send_keys(Keys.DOWN)
        time.sleep(0.3)
        system_id_input.send_keys(Keys.ENTER)
        time.sleep(0.5)

        entered_value = system_id_input.get_attribute('value')
        if entered_value and customer_name in entered_value:
            return True
        else:
            return False
            
    except Exception as e:
        logger.error(f"Failed to input system ID {customer_name}: {e}")
        return False

def add_fee(driver, wait, fee_type, quantity, reference, fee_date=None, customer_name=None):
    """Add fee to Veracore"""
    try:
        # Ensure fee window is open
        try:
            fee_window = driver.find_element(By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]")
            if not fee_window.is_displayed():
                open_accessorial_fee_window(driver, wait)
        except:
            open_accessorial_fee_window(driver, wait)

        fee_window = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
        )))

        # Step 1: Find and type in fee type search box
        search_box = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
            "//input[contains(@class,'x-form-text') and @type='text' and not(@placeholder='System Search...')]"
        )))
        search_box.click()
        search_box.clear()

        search_text = fee_type[:15]
        
        for char in search_text:
            search_box.send_keys(char)
            time.sleep(0.15)
        
        time.sleep(1.5)

        # Step 2: Click on fee type in dropdown
        try:
            fee_row = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f"//tr[contains(@class,'x-grid-row') and td[2]/div[normalize-space(text())='{fee_type}']]"
            )))
        except:
            try:
                fee_row = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    f"//tr[contains(@class,'x-grid-row') and td[2]/div[contains(normalize-space(text()), '{search_text}')]]"
                )))
            except:
                fee_row = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//tr[contains(@class,'x-grid-row')][1]"
                )))
        
        fee_row.click()
        time.sleep(3)

        # Step 3: Fill in system ID (customer ID)
        if customer_name:
            if not input_system_id_in_fee_window(driver, wait, customer_name):
                logger.warning(f"Failed to input system ID: {customer_name}")

        # Step 4: Input Date
        if fee_date:
            try:
                if isinstance(fee_date, str):
                    fee_date = datetime.strptime(str(fee_date), "%Y-%m-%d").date()
                elif isinstance(fee_date, datetime):
                    fee_date = fee_date.date()
                fee_date_str = fee_date.strftime("%m/%d/%Y")
                date_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'datefield-') and contains(@id, '-inputEl')]")))
                date_input.click()
                date_input.clear()
                time.sleep(0.2)
                date_input.send_keys(fee_date_str)
                date_input.send_keys(Keys.TAB)
                time.sleep(0.2)
                date_input.send_keys(Keys.TAB)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to input date: {e}")
                return False

        # Step 5: Input Quantity
        try:
            qty_input = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//input[contains(@id, 'numberfield-') and contains(@id, '-inputEl')]"
            )))
            qty_input.click()
        except:
            qty_input = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//input[@role='spinbutton' and contains(@class, 'x-form-field')]"
            )))
            qty_input.click()

        time.sleep(0.2)
        qty_input.clear()
        time.sleep(0.1)
        
        qty_input.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        qty_input.send_keys(str(quantity))
        time.sleep(0.1)
        
        qty_input.send_keys(Keys.TAB)
        time.sleep(0.2)

        # Step 6: Input Reference
        ref_input = driver.switch_to.active_element
        ref_input.send_keys(reference)
        time.sleep(0.1)

        # Step 7: Submit the form
        ref_input.send_keys(Keys.TAB)
        time.sleep(0.1)
        active = driver.switch_to.active_element
        active.send_keys(Keys.ENTER)
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]")))
        time.sleep(1)
        
        logger.info(f"Successfully added fee: {fee_type} (Qty: {quantity}) for customer: {customer_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to add fee {fee_type}: {e}")
        screenshot_name = f"error_add_fee_{int(time.time())}.png"
        try:
            driver.save_screenshot(os.path.join(log_dir, screenshot_name))
            logger.info(f"Screenshot saved: {screenshot_name}")
        except:
            pass
        return False

def get_pending_work_orders():
    """Get all work orders that haven't been synced to Veracore"""
    try:
        conn = get_connection()
        query = """
            SELECT * FROM work_orders 
            WHERE veracore_synced = 0 OR veracore_synced IS NULL
            ORDER BY date_created ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Failed to get pending work orders: {e}")
        return pd.DataFrame()

def mark_work_order_synced(order_id, success=True):
    """Mark a work order as synced to Veracore"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE work_orders 
            SET veracore_synced = %s, sync_date = %s, status = %s
            WHERE id = %s
        """, (1 if success else 0, datetime.now(), 'completed' if success else 'pending', order_id))
        conn.commit()
        conn.close()
        logger.info(f"Work order {order_id} marked as {'synced' if success else 'failed'}")
    except Exception as e:
        logger.error(f"Failed to mark work order {order_id} as synced: {e}")

def sync_single_order(driver, wait, order):
    """Sync a single work order to Veracore"""
    try:
        reference_numbers = json.loads(order['reference_numbers'])
        fee_data = json.loads(order['fee_data'])
        customer_name = order['customer_name']

        fee_date = order.get('fee_date')
        if not fee_date:
            fee_date = order['date_created'].date()
        else:
            if isinstance(fee_date, str):
                fee_date = datetime.strptime(fee_date, "%Y-%m-%d").date()

        logger.info(f"Starting sync for Work Order #{order['id']} - Customer: {customer_name}")
        
        total_fees = len(fee_data)
        successful_fees = 0
        
        for i, fee in enumerate(fee_data):
            logger.info(f"Syncing fee {i+1}/{total_fees}: {fee['type']} for {customer_name}")

            reference = reference_numbers[0] if reference_numbers else order['barcode_data']

            success = add_fee(driver, wait, fee['type'], fee['quantity'], reference, fee_date, customer_name)

            if success:
                successful_fees += 1
                time.sleep(1)
                
                # Reopen fee window if there's another fee in the same order
                if i < total_fees - 1:
                    open_accessorial_fee_window(driver, wait)
            else:
                logger.error(f"Failed to add fee: {fee['type']}")
    
            time.sleep(1)

        # Mark as synced if all fees were successful
        if successful_fees == total_fees:
            mark_work_order_synced(order['id'], True)
            logger.info(f"Work Order #{order['id']} fully synced! ({successful_fees}/{total_fees} fees)")
        else:
            logger.warning(f"Partial sync for WO #{order['id']}: {successful_fees}/{total_fees} fees synced")
        
        return successful_fees == total_fees
        
    except Exception as e:
        logger.error(f"Sync failed for WO #{order['id']}: {str(e)}")
        return False

def main():
    """Main execution function"""
    logger.info("Starting Veracore sync process")
    
    driver = None
    try:
        # Get pending work orders
        pending_orders = get_pending_work_orders()
        
        if pending_orders.empty:
            logger.info("No pending work orders to sync")
            return
        
        logger.info(f"Found {len(pending_orders)} pending work orders")
        
        # Setup Selenium driver
        driver = setup_selenium_driver()
        
        # Login to Veracore
        login_and_select_system(driver, VERACORE_URL, VERACORE_USER, VERACORE_PASS, SYSTEM_ID)
        wait = WebDriverWait(driver, 30)
        
        # Process each order
        total_orders = len(pending_orders)
        successful_orders = 0
        
        for idx, (_, order) in enumerate(pending_orders.iterrows()):
            logger.info(f"Processing order {idx + 1}/{total_orders}: WO #{order['id']} (Customer: {order['customer_name']})")
            
            if sync_single_order(driver, wait, order):
                successful_orders += 1
            
            time.sleep(2)  # Brief pause between orders
        
        logger.info(f"Sync complete! Successfully processed {successful_orders}/{total_orders} orders")
        
    except Exception as e:
        logger.error(f"Main process failed: {e}")
        
    finally:
        # Cleanup
        if driver:
            try:
                driver.quit()
                logger.info("Driver closed successfully")
            except:
                logger.warning("Failed to close driver cleanly")

if __name__ == "__main__":
    main()