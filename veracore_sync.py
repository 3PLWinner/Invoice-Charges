# veracore_sync.py - Integrates your existing Veracore scraping with work orders
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
        pass  # don’t add --headless
    else:
        chrome_options.add_argument("--headless=new")

    #chrome_options.add_argument("--headless=new")
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

def login_and_select_system(driver, url, username, password, system_id):
    """Your existing login function"""
    wait = WebDriverWait(driver, 30)
    driver.get(url)

    username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    username_field.clear()
    username_field.send_keys(username)
    
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_field.clear()
    password_field.send_keys(password)

    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Login']/..")))
    login_btn.click()

    wait.until(lambda d: "auth=" in d.current_url)

    system_box = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@onclick, \"'{system_id}'\")]"))
    )
    system_box.click()

    wait.until(EC.presence_of_element_located((By.ID, "ui-accfee-btn")))
    time.sleep(3)
    time.sleep(5)
    
    try:
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x-mask')]")))
    except:
        pass

    open_accessorial_fee_window(driver, wait)
    return True

def add_fee(driver, wait, fee_type, quantity, reference):
    """Your existing add_fee function"""
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

        search_box = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
            "//input[contains(@class,'x-form-text') and @type='text']"
        )))
        search_box.click()
        search_box.clear()

        search_text = fee_type[:15]
        
        for char in search_text:
            search_box.send_keys(char)
            time.sleep(0.15)
        
        time.sleep(1.5)

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

        try:
            qty_input = driver.switch_to.active_element
        except:
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

        ref_input = driver.switch_to.active_element
        ref_input.send_keys(reference)
        time.sleep(0.1)

        ref_input.send_keys(Keys.TAB)
        time.sleep(0.1)
        active = driver.switch_to.active_element
        active.send_keys(Keys.ENTER)

        time.sleep(2)
        success = open_accessorial_fee_window(driver, wait)
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

def authenticate_user(username, password):
    """Simple user authentication"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def sync_single_order(order):
    """Sync a single work order to Veracore"""
    reference_numbers = json.loads(order['reference_numbers'])
    fee_data = json.loads(order['fee_data'])
    
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
            status_text.text(f"Syncing fee {i+1}/{total_fees}: {fee['type']}")
            
            # Use the first reference number for each fee
            reference = reference_numbers[0] if reference_numbers else order['barcode_data']
            
            success = add_fee(driver, wait, fee['type'], fee['quantity'], reference)
            
            if success:
                successful_fees += 1
                st.success(f"✅ Synced: {fee['type']} (Qty: {fee['quantity']})")
            else:
                st.error(f"❌ Failed: {fee['type']}")
            
            time.sleep(1)  # Brief pause between fees
        
        # Mark as synced if all fees were successful
        if successful_fees == total_fees:
            mark_work_order_synced(order['id'], True)
            st.success(f"🎉 Work Order #{order['id']} fully synced! ({successful_fees}/{total_fees} fees)")
        else:
            st.warning(f"⚠️ Partial sync: {successful_fees}/{total_fees} fees synced")
        
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        st.error(f"❌ Sync failed for WO #{order['id']}: {str(e)}")
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
        overall_status.text(f"Processing order {idx + 1}/{total_orders}: WO #{order['id']}")
        
        with st.expander(f"Syncing WO #{order['id']}", expanded=True):
            sync_single_order(order)
            synced_orders += 1
        
        time.sleep(2)  # Brief pause between orders
    
    overall_progress.empty()
    overall_status.empty()
    
    st.balloons()
    st.success(f"🎉 Bulk sync complete! Processed {synced_orders}/{total_orders} orders")

# Initialize session states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "veracore_connected" not in st.session_state:
    st.session_state.veracore_connected = False

# Login to sync app
if not st.session_state.logged_in:
    st.title("🔄 Veracore Sync System")
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("🔐 Login"):
            user_data = authenticate_user(username, password)
            if user_data and user_data[1] in ['admin', 'worker']:
                st.session_state.logged_in = True
                st.session_state.username = user_data[0]
                st.session_state.role = user_data[1]
                st.rerun()
            else:
                st.error("Access denied. Admin or worker role required.")

# Main sync interface
else:
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔄 Veracore Sync System")
    with col2:
        if st.button("🚪 Logout"):
            # Clean up driver on logout
            if "driver" in st.session_state:
                try:
                    st.session_state.driver.quit()
                except:
                    pass
                del st.session_state.driver
            st.session_state.logged_in = False
            st.session_state.veracore_connected = False
            st.rerun()

    # Veracore connection section
    if not st.session_state.veracore_connected:
        st.subheader("🔌 Connect to Veracore")
        
        with st.form("veracore_connection"):
            url = st.text_input("Veracore URL", value="https://wms.3plwinner.com/VeraCore")
            veracore_username = st.text_input("Veracore Username")
            veracore_password = st.text_input("Veracore Password", type="password")
            system_id = st.text_input("System ID")
            
            if st.form_submit_button("🔌 Connect to Veracore"):
                if all([url, veracore_username, veracore_password, system_id]):
                    with st.spinner("Connecting to Veracore..."):
                        try:
                            # Clean up any existing driver
                            if "driver" in st.session_state:
                                try:
                                    st.session_state.driver.quit()
                                except:
                                    pass
                            
                            driver = setup_selenium_driver()
                            login_and_select_system(driver, url, veracore_username, veracore_password, system_id)
                            
                            st.session_state.driver = driver
                            st.session_state.veracore_connected = True
                            st.session_state.veracore_url = url
                            st.session_state.veracore_username = veracore_username
                            st.session_state.system_id = system_id
                            
                            st.success("✅ Connected to Veracore!")
                            time.sleep(2)
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Connection failed: {str(e)}")
                            if "driver" in st.session_state:
                                try:
                                    st.session_state.driver.quit()
                                except:
                                    pass
                else:
                    st.warning("Please fill in all connection details")

    # Sync section (only show when connected)
    else:
        # Connection status
        st.success(f"🟢 Connected to Veracore (System: {st.session_state.get('system_id', 'Unknown')})")
        
        if st.button("🔌 Disconnect from Veracore"):
            if "driver" in st.session_state:
                try:
                    st.session_state.driver.quit()
                except:
                    pass
                del st.session_state.driver
            st.session_state.veracore_connected = False
            st.rerun()

        # Load pending work orders
        pending_orders = get_pending_work_orders()
        
        if pending_orders.empty:
            st.info("🎉 No pending work orders to sync!")
        else:
            st.subheader(f"📋 Pending Work Orders ({len(pending_orders)})")
            
            # Bulk sync section
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Bulk Operations**")
                if st.button("🚀 Sync All Pending Orders", use_container_width=True, type="primary"):
                    sync_all_orders(pending_orders)
            
            with col2:
                auto_sync = st.checkbox("🔄 Auto Sync New Orders")
                if auto_sync:
                    st.info("Auto sync enabled - new orders will sync automatically")

            # Individual work order sync
            st.subheader("📝 Individual Work Orders")
            
            for idx, order in pending_orders.iterrows():
                # Parse order data
                reference_numbers = json.loads(order['reference_numbers'])
                fee_data = json.loads(order['fee_data'])
                
                with st.expander(
                    f"WO #{order['id']} - {order['customer_name']} - {len(fee_data)} fees - {order['date_created'][:10]}"
                ):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Customer:** {order['customer_name']} ({order['customer_id']})")
                        st.write(f"**References:** {', '.join(reference_numbers)}")
                        st.write(f"**Created:** {order['date_created'][:16]}")
                        st.write(f"**By:** {order['created_by']}")
                    
                    with col2:
                        st.write("**Fees to Sync:**")
                        for fee in fee_data:
                            st.write(f"• {fee['type']} (Qty: {fee['quantity']})")
                    
                    with col3:
                        if st.button(f"🔄 Sync", key=f"sync_{order['id']}"):
                            sync_single_order(order)

# Show sync statistics
if st.session_state.logged_in:
    st.subheader("📊 Sync Statistics")
    
    # Get sync stats
    conn = sqlite3.connect('warehouse_system.db')
    stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(CASE WHEN veracore_synced = 1 THEN 1 ELSE 0 END) as synced_orders,
            SUM(CASE WHEN veracore_synced = 0 OR veracore_synced IS NULL THEN 1 ELSE 0 END) as pending_orders
        FROM work_orders
    """, conn)
    
    recent_syncs = pd.read_sql_query("""
        SELECT id, customer_name, sync_date 
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
        
        # Recent sync activity
        if not recent_syncs.empty:
            st.subheader("🕐 Recent Sync Activity")
            for _, sync in recent_syncs.iterrows():
                sync_time = datetime.fromisoformat(sync['sync_date'])
                st.write(f"• WO #{sync['id']} - {sync['customer_name']} - {sync_time.strftime('%Y-%m-%d %H:%M')}")

# Cleanup function
def cleanup_driver():
    if "driver" in st.session_state:
        try:
            st.session_state.driver.quit()
        except:
            pass

# Register cleanup
import atexit
atexit.register(cleanup_driver)