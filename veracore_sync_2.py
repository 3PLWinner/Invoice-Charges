# veracore_sync.py - Modified to use 3plwhs system with customer ID input
import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os

VERACORE_URL = "https://wms.3plwinner.com/VeraCore"
VERACORE_USER = "ljannatipour"
VERACORE_PASS = "Inkypinky343!"
SYSTEM_ID = "3plwhs"  # Fixed system ID for all logins

st.set_page_config(
    page_title="Veracore Sync", 
    layout="wide"
)

# Your existing Selenium setup code
binary_path = os.path.join(os.getcwd(), "chrlauncher-win64-stable-codecs-sync", "chrlauncher 2.6 (64-bit).exe")

def setup_selenium_driver():
    chrome_options = Options()
    
    # Comment out custom binary for now - use system Chrome
    # chrome_options.binary_location = binary_path
    if st.checkbox("Show Browser (disable headless)", value=True):
        pass  # don't add --headless
    else:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Try multiple approaches to get working driver
    try:
        # Method 1: Try ChromeDriverManager with newer version
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e1:
        try:
            # Method 2: Use system chromedriver (if installed)
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e2:
            # Method 3: Manual driver path (user needs to download)
            st.error(f"Chrome driver issues. Please install chromedriver manually or use Method 2 below.")
            st.error(f"Error 1: {e1}")
            st.error(f"Error 2: {e2}")
            raise Exception("Could not initialize Chrome driver")
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def open_accessorial_fee_window(driver, wait):
    """Your existing function to open accessorial fee window"""
    wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-mask')]")))

    try:
        try:
            wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x-mask')]")))
        except:
            pass
            
        accfee_btn = wait.until(EC.element_to_be_clickable((By.ID, "ui-accfee-btn")))
        
        clicked = False
        try:
            accfee_btn.click()
            clicked = True
        except:
            try:
                driver.execute_script("arguments[0].click();", accfee_btn)
                clicked = True
            except:
                ActionChains(driver).move_to_element(accfee_btn).click().perform()
                clicked = True
        
        if clicked:
            time.sleep(3)
            return True
        
    except Exception as e:
        st.error(f"Failed to open fee window: {str(e)}")
        return False

def login_and_select_system(driver, url, username, password, system_id="3plwhs"):
    """Logs in and selects the fixed system (3plwhs)."""
    wait = WebDriverWait(driver, 30)
    driver.get(url)

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

    # Select the fixed system (3plwhs)
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

    return system_id

def input_system_id_in_fee_window(driver, wait, customer_name):
    """Input the customer_name into the system ID field in the fee window"""
    try:
        # Look for the system search combobox with specific placeholder
        system_id_input = wait.until(EC.presence_of_element_located((
            By.ID, "combo-1043-inputEl"
        )))

        # Click to focus and clear any existing content
        system_id_input.send_keys(Keys.CONTROL + "a")
        system_id_input.send_keys(Keys.DELETE)
        time.sleep(0.2)

        # Input the customer_name character by character (like the fee type search)
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
            st.info(f"✅ Successfully set system ID to: {customer_name}")
            return True
        else:
            st.warning(f"⚠️ System ID may not have been set correctly. Expected: {customer_name}, Got: {entered_value}")
            return False
        
    except Exception as e:
        st.error(f"Error setting system ID: {e}")
        # Fallback: try to find by more general combobox pattern
        try:
            screenshot_name = f"system_id_error_{int(time.time())}.png"
            driver.save_screenshot(screenshot_name)
            st.error(f"Screenshot saved: {screenshot_name}")
        except:
            pass
        return False

# Add this function to create fee_date column if missing
def update_database_schema():
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(work_orders)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'fee_date' not in columns:
        cursor.execute("ALTER TABLE work_orders ADD COLUMN fee_date TEXT")
        conn.commit()
    conn.close()

def add_fee(driver, wait, fee_type, quantity, reference, fee_date=None, customer_name=None):
    """Modified add_fee function with correct sequence: fee type → customer name → date → quantity → reference"""
    try:
        try:
            fee_window = driver.find_element(By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]")
            if not fee_window.is_displayed():
                open_accessorial_fee_window(driver, wait)
        except:
            open_accessorial_fee_window(driver, wait)

        fee_window = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
        )))

        # STEP 1: Find and type in fee type search box (exclude the system search combobox)
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

        # STEP 2: Click on fee type in dropdown
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

        # STEP 3: Fill in system ID (customer ID) - AFTER selecting fee type
        if customer_name:
            input_system_id_in_fee_window(driver, wait, customer_name)

        # STEP 4: Input Date
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
                st.warning(f"Could not set fee date: {e}")

        # STEP 5: Input Quantity
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

        # STEP 6: Input Reference
        ref_input = driver.switch_to.active_element
        ref_input.send_keys(reference)
        time.sleep(0.1)

        # STEP 7: Submit the form
        ref_input.send_keys(Keys.TAB)
        time.sleep(0.1)
        active = driver.switch_to.active_element
        active.send_keys(Keys.ENTER)
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]")))
        time.sleep(1)
        st.info(f"Added fee: {fee_type} (Qty: {quantity}, Ref: {reference}, Date: {fee_date}, System ID: {customer_name})")
        return True

    except Exception as e:
        st.error(f"Error adding fee: {e}")
        screenshot_name = f"error_add_fee_{int(time.time())}.png"
        driver.save_screenshot(screenshot_name)
        return False
    
# Database functions
def get_pending_work_orders():
    """Get all work orders that haven't been synced to Veracore"""
    conn = sqlite3.connect('warehouse_system.db')
    df = pd.read_sql_query("""
        SELECT * FROM work_orders 
        WHERE veracore_synced = 0 OR veracore_synced IS NULL
        ORDER BY date_created ASC
    """, conn)
    conn.close()
    return df

def mark_work_order_synced(order_id, success=True):
    """Mark a work order as synced to Veracore"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE work_orders 
        SET veracore_synced = ?, sync_date = ?, status = ?
        WHERE id = ?
    """, (1 if success else 0, datetime.now().isoformat(), 'completed' if success else 'pending', order_id))
    conn.commit()
    conn.close()

def sync_single_order(order):
    """Sync a single work order to Veracore - using customer_name as system ID input"""
    reference_numbers = json.loads(order['reference_numbers'])
    fee_data = json.loads(order['fee_data'])
    customer_name = order['customer_name']  # This will be used as system ID input

    fee_date = order.get('fee_date')
    if not fee_date:
        fee_date = datetime.fromisoformat(order['date_created']).date()
    else:
        if isinstance(fee_date, str):
            fee_date = datetime.strptime(fee_date, "%Y-%m-%d").date()
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        driver = st.session_state.driver
        wait = WebDriverWait(driver, 30)
        
        total_fees = len(fee_data)
        successful_fees = 0
        
        for i, fee in enumerate(fee_data):
            # Update progress
            progress = (i + 1) / total_fees
            progress_bar.progress(progress)
            status_text.text(f"Syncing fee {i+1}/{total_fees}: {fee['type']} (System ID: {customer_name})")

            # Use the first reference number for each fee
            reference = reference_numbers[0] if reference_numbers else order['barcode_data']

            # Pass customer_name as system ID to the add_fee function
            success = add_fee(driver, wait, fee['type'], fee['quantity'], reference, fee_date, customer_name)

            if success:
                successful_fees += 1
                st.success(f"Added: {fee['type']} (Qty: {fee['quantity']}, System ID: {customer_name})")
                time.sleep(1)
        
                # Reopen fee window only if there is another fee in the same order
                if i < total_fees - 1:
                    open_accessorial_fee_window(driver, wait)
            else:
                st.error(f"Failed: {fee['type']}")
    
            time.sleep(1)  # Brief pause between fees

        # Mark as synced if all fees were successful
        if successful_fees == total_fees:
            mark_work_order_synced(order['id'], True)
            st.success(f"Work Order #{order['id']} fully synced! ({successful_fees}/{total_fees} fees)")
        else:
            st.warning(f"Partial sync: {successful_fees}/{total_fees} fees synced")
        
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"Sync failed for WO #{order['id']}: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def sync_all_orders(pending_orders):
    """Sync all pending orders"""
    if pending_orders.empty:
        st.info("No orders to sync")
        return
    
    overall_progress = st.progress(0)
    overall_status = st.empty()
    
    total_orders = len(pending_orders)
    synced_orders = 0
    
    for idx, (_, order) in enumerate(pending_orders.iterrows()):
        overall_progress.progress((idx + 1) / total_orders)
        overall_status.text(f"Processing order {idx + 1}/{total_orders}: WO #{order['id']} (System ID: {order['customer_name']})")

        with st.expander(f"Syncing WO #{order['id']} - System ID: {order['customer_name']}", expanded=True):
            sync_single_order(order)
            synced_orders += 1
        
        time.sleep(2)  # Brief pause between orders
    
    overall_progress.empty()
    overall_status.empty()
    
    st.balloons()
    st.success(f"Bulk sync complete! Processed {synced_orders}/{total_orders} orders")

# Initialize session states
if "veracore_connected" not in st.session_state:
    st.session_state.veracore_connected = False

# Main Application - Auto Login to 3plwhs
st.title("Veracore Sync Dashboard")
st.subheader("Fixed System Login (3plwhs) with Dynamic Customer IDs")

# Automatic Veracore connection to 3plwhs system
if not st.session_state.veracore_connected:
    if not VERACORE_USER or not VERACORE_PASS or not VERACORE_URL:
        st.error("Missing Veracore credentials. Please check VERACORE_USER, VERACORE_PASS, and VERACORE_URL.")
        st.stop()
    
    with st.spinner(f"Auto-connecting to Veracore system: {SYSTEM_ID}..."):
        try:
            # Clean up any existing driver
            if "driver" in st.session_state:
                try:
                    st.session_state.driver.quit()
                except:
                    pass

            driver = setup_selenium_driver()
            
            st.info(f"Logging into Veracore with fixed system: {SYSTEM_ID}")
            
            # Login and select fixed system (3plwhs)
            selected_system = login_and_select_system(driver, VERACORE_URL, VERACORE_USER, VERACORE_PASS, SYSTEM_ID)

            st.session_state.driver = driver
            st.session_state.veracore_connected = True
            st.session_state.current_system = selected_system

            st.success(f"Auto-connected to Veracore (Fixed System: {selected_system})")
            st.info("Customer IDs from work orders will be used as System ID inputs in fee forms")
            time.sleep(1)
            st.rerun()

        except Exception as e:
            st.error(f"Auto-connection failed: {e}")
            if "driver" in st.session_state:
                try:
                    st.session_state.driver.quit()
                except:
                    pass
            st.stop()

# Main sync interface (only if connected)
if st.session_state.veracore_connected:
    current_system = st.session_state.get('current_system', 'Unknown')
    st.success(f"Connected to Veracore (Fixed System: {current_system})")

    # Load pending work orders
    pending_orders = get_pending_work_orders()

    if pending_orders.empty:
        st.info("No pending work orders to sync!")
    else:
        st.subheader(f"Pending Work Orders ({len(pending_orders)})")

        # Show which customer IDs will be processed
        unique_customers = pending_orders['customer_name'].unique()
        st.info(f"Will process {len(unique_customers)} different customer IDs as System ID inputs: {', '.join(unique_customers)}")
        
        # Bulk sync section
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("**Bulk Operations**")
            if st.button("Sync All Pending Orders", use_container_width=True, type="primary"):
                sync_all_orders(pending_orders)

        with col2:
            auto_sync = st.checkbox("Auto Sync New Orders")
            if auto_sync:
                st.info("Auto sync enabled - new orders will sync automatically")

        # Individual work order sync
        st.subheader("Individual Work Orders")
        for idx, order in pending_orders.iterrows():
            reference_numbers = json.loads(order['reference_numbers'])
            fee_data = json.loads(order['fee_data'])

            with st.expander(f"WO #{order['id']} - {order['customer_name']} (System ID: {order['customer_name']}) - {len(fee_data)} fees - {order['date_created'][:10]}"):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Customer:** {order['customer_name']}")
                    st.write(f"**System ID Input:** {order['customer_name']}")
                    st.write(f"**References:** {', '.join(reference_numbers)}")
                    st.write(f"**Created:** {order['date_created'][:16]}")
                    st.write(f"**By:** {order['created_by']}")

                with col2:
                    st.write("**Fees to Sync:**")
                    for fee in fee_data:
                        st.write(f"• {fee['type']} (Qty: {fee['quantity']})")

                with col3:
                    if st.button(f"Sync", key=f"sync_{order['id']}"):
                        sync_single_order(order)

# Show sync statistics
st.subheader("Sync Statistics")
conn = sqlite3.connect('warehouse_system.db')
stats = pd.read_sql_query("""
    SELECT 
        COUNT(*) as total_orders,
        SUM(CASE WHEN veracore_synced = 1 THEN 1 ELSE 0 END) as synced_orders,
        SUM(CASE WHEN veracore_synced = 0 OR veracore_synced IS NULL THEN 1 ELSE 0 END) as pending_orders
    FROM work_orders
""", conn)

recent_syncs = pd.read_sql_query("""
    SELECT id, customer_name, customer_id, sync_date 
    FROM work_orders 
    WHERE veracore_synced = 1 AND sync_date IS NOT NULL
    ORDER BY sync_date DESC
    LIMIT 5
""", conn)
conn.close()

if not stats.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", stats.iloc[0]['total_orders'])
    with col2:
        st.metric("Synced Orders", stats.iloc[0]['synced_orders'])
    with col3:
        st.metric("Pending Sync", stats.iloc[0]['pending_orders'])

    if not recent_syncs.empty:
        st.subheader("Recent Sync Activity")
        for _, sync in recent_syncs.iterrows():
            sync_time = datetime.fromisoformat(sync['sync_date'])
            st.write(f"• WO #{sync['id']} - {sync['customer_name']} (System ID: {sync['customer_name']}) - {sync_time.strftime('%Y-%m-%d %H:%M')}")

# Cleanup function
def cleanup_driver():
    if "driver" in st.session_state:
        try:
            st.session_state.driver.quit()
        except:
            pass

import atexit
atexit.register(cleanup_driver)