import streamlit as st
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

FEE_TYPES = [
    "RCV - Shrink Wrap",
    "RCV - Sorting",
    "RCV - FCL 20G Loose Loaded",
    "RCV - FCL 40G Loose Loaded",
    "RCV - FCL 40HQ Loose Loaded",
    "RCV - Wooden Pallet",
    "PPF - Insert",
    "GAF - Administrative Fee",
    "FAP - Amazon FBA Shipping Preparation",
    "FAP - Amazon FBA Product Labeling",
    "PP - Box 24x24x24",
    "PP - Box 18x18x12",
    "PP - Box 12x12x12",
    "RCV - Per Pallet",
    "RCV - Single Package",
    "PP - Box 24X18X18",
    "PP - Box 10x10x10",
    "PP - Box 8x8x8",
    "PP - White Box 12x12x12 w/ arrows",
    "PP - Product Labels",
    "PPF - Prepaid Labels",
    "PPF - Work Order",
    "PP - Shrink Wrap",
    "PP - Wooden Pallet",
    "PP - Box 19 1/2 x 7 5/8 x 3 1/4",
    "PP - Box 9 5/8 x 7 5/8 x 5 1/4",
    "RCV - Freight Inbound Charges",
    "PPF - Quoted Freight Shipment",
    "PP - Box - 18x14x12",
    "RCV - UNI Sorting",
    "PPF - UNI Business to Business Order",
    "FAP - Pallet Labels",
    "RCV - Master Carton Labels",
    "RCV - Removals and Inspections",
    "Pallet Out",
    "PPF - Quoted Ground Shipment",
    "FAP - Shipping Labels",
    "PP - Straps",
    "RCV - FCL 53HQ Loose Loaded",
    "PPF - Unshipped Pallet Storage",
    "PPF - Overtime Labor",
    "Master Carton Out",
    "CD - Per Pallet",
    "CD - Shrink Wrap",
    "CD - Daily Storage",
    "CD - Wooden Pallets",
    "CD - Admin & Sorting Time",
    "CD - Insert",
    "Picked Items",
    "Additional Items",
    "RCV - Individual Units",
    "CD - Single Package",
    "CD - Per Unit",
    "PPF - Truck Seals",
    "PP - Box 16x12x6",
    "PP - Plastic Toppers",
    "PP - Box 12x8x6",
    "PP - Document Holder",
    "PP - Box 12x6x4"
]
binary_path = os.path.join(os.getcwd(), "chrlauncher-win64-stable-codecs-sync", "chrlauncher 2.6 (64-bit).exe")
def setup_selenium_driver():
    chrome_options = Options()
    chrome_options.binary_location = binary_path
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def open_accessorial_fee_window(driver, wait):
    """Opens the accessorial fee window with multiple strategies"""
    try:
        # Wait for any masks to disappear first
        try:
            wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x-mask')]")))
        except:
            pass
            
        accfee_btn = wait.until(EC.element_to_be_clickable((By.ID, "ui-accfee-btn")))
        
        # Try multiple click strategies
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
            time.sleep(3)  # Wait for window to fully load
            return True
    except Exception as e:
        st.error(f"Failed to open fee window: {str(e)}")
        return False

def login_and_select_system(driver, url, username, password, system_id):
    wait = WebDriverWait(driver, 30)
    driver.get(url)

    # Enter credentials
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    username_field.clear()
    username_field.send_keys(username)
    
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_field.clear()
    password_field.send_keys(password)

    # Click login button
    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Login']/..")))
    login_btn.click()

    # Wait for login success (URL contains auth=)
    wait.until(lambda d: "auth=" in d.current_url)

    # Click system box by system_id
    system_box = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@onclick, \"'{system_id}'\")]"))
    )
    system_box.click()

    # Wait for OMS dashboard to be ready by checking for Accessorial Fee button
    wait.until(EC.presence_of_element_located((By.ID, "ui-accfee-btn")))
    
    # Additional wait to ensure page is fully loaded
    time.sleep(3)

    # Wait for any loading masks/overlays to disappear before trying to click
    time.sleep(5)  # Give extra time for page to fully load
    
    # Wait for any masks to disappear
    try:
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'x-mask')]")))
    except:
        pass  # Mask might not be present or might already be gone

    # Automatically open the accessorial fee window immediately after login
    open_accessorial_fee_window(driver, wait)

    return True

def add_fee(driver, wait, fee_type, quantity, reference):
    try:
        try:
            fee_window = driver.find_element(By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]")
            if not fee_window.is_displayed():
                open_accessorial_fee_window(driver, wait)
        except:
            open_accessorial_fee_window(driver, wait)

        # Wait for Accessorial Fee window
        fee_window = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
        )))

        # Find the search box inside the fee window (ignore dynamic IDs)
        search_box = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
            "//input[contains(@class,'x-form-text') and @type='text']"
        )))
        search_box.click()
        search_box.clear()

        # Only type the first 15 characters to show dropdown options
        search_text = fee_type[:15]
        
        for char in search_text:
            search_box.send_keys(char)
            time.sleep(0.15)
        
        time.sleep(1.5)  # Give a bit more time for dropdown to populate

        # Look for the fee type in the dropdown results (more flexible matching)
        # First try exact match, then try partial match if that fails
        try:
            fee_row = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f"//tr[contains(@class,'x-grid-row') and td[2]/div[normalize-space(text())='{fee_type}']]"
            )))
        except:
            # If exact match fails, try to find a row that contains the search text
            try:
                fee_row = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    f"//tr[contains(@class,'x-grid-row') and td[2]/div[contains(normalize-space(text()), '{search_text}')]]"
                )))
            except:
                # Last resort: click the first available row
                fee_row = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//tr[contains(@class,'x-grid-row')][1]"
                )))
        
        fee_row.click()
        time.sleep(3)  # let the grid refresh
        
        try:
            # Strategy 1: Use the active element (since cursor should already be there)
            qty_input = driver.switch_to.active_element
        except:
            try:
                # Strategy 2: Find by the correct ID pattern
                qty_input = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//input[contains(@id, 'numberfield-') and contains(@id, '-inputEl')]"
                )))
                qty_input.click()
            except:
                # Strategy 3: Find by role and class attributes
                qty_input = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//input[@role='spinbutton' and contains(@class, 'x-form-field')]"
                )))
                qty_input.click()

        # Clear and enter quantity
        time.sleep(0.2)
        qty_input.clear()  # Try clear first
        time.sleep(0.1)
        
        # Alternative: Select all and replace
        qty_input.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        qty_input.send_keys(str(quantity))
        time.sleep(0.1)
        
        # Move to reference field
        qty_input.send_keys(Keys.TAB)
        time.sleep(0.2)

        # Enter reference in the next active element
        ref_input = driver.switch_to.active_element
        ref_input.send_keys(reference)
        time.sleep(0.1)

        # Save the entry
        ref_input.send_keys(Keys.TAB)
        time.sleep(0.1)
        active = driver.switch_to.active_element
        active.send_keys(Keys.ENTER)

        time.sleep(2)

        # Reopen for next entry
        success = open_accessorial_fee_window(driver, wait)

        return True

    except Exception as e:
        st.error(f"Error adding fee: {e}")
        screenshot_name = f"error_add_fee_{int(time.time())}.png"
        driver.save_screenshot(screenshot_name)
        return False

def close_driver():
    if "driver" in st.session_state:
        try:
            st.session_state["driver"].quit()
        except:
            pass
        del st.session_state["driver"]
        st.session_state["logged_in"] = False

# Streamlit UI - Simplified
st.title("🚚 Veracore OMS Fee Entry")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Connection Section
if not st.session_state.get("logged_in"):
    st.subheader("Connect to Veracore")
    
    with st.form("login_form"):
        url = st.text_input("Veracore URL", value="https://wms.3plwinner.com/VeraCore")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        system_id = st.text_input("System ID")
        
        if st.form_submit_button("🔌 Connect", use_container_width=True):
            if all([url, username, password, system_id]):
                with st.spinner("Connecting..."):
                    try:
                        close_driver()
                        driver = setup_selenium_driver()
                        login_and_select_system(driver, url, username, password, system_id)
                        
                        st.session_state["driver"] = driver
                        st.session_state["logged_in"] = True
                        st.session_state["system_id"] = system_id
                        st.success("✅ Connected!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
                        close_driver()
            else:
                st.warning("Please fill in all fields")

# Fee Entry Section
else:
    # Status bar
    col_status, col_disconnect = st.columns([3, 1])
    with col_status:
        st.success(f"🟢 Connected to system {st.session_state.get('system_id', 'Unknown')}")
    with col_disconnect:
        if st.button("🔌 Disconnect"):
            close_driver()
            st.rerun()

    st.subheader("Add Accessorial Fee")
    
    # Main fee entry form
    with st.form("fee_form"):
        fee_type = st.selectbox("Fee Type", FEE_TYPES)
        
        col_qty, col_ref = st.columns(2)
        with col_qty:
            quantity = st.number_input("Quantity", min_value=1, value=1)
        with col_ref:
            reference_number = st.text_input("Reference Number")
        
        if st.form_submit_button("➕ Add Fee", use_container_width=True):
            if not reference_number:
                st.warning("Please enter a reference number")
            else:
                with st.spinner("Adding fee..."):
                    try:
                        wait = WebDriverWait(st.session_state["driver"], 30)
                        success = add_fee(
                            st.session_state["driver"],
                            wait,
                            fee_type,
                            quantity,
                            reference_number
                        )
                        if success:
                            st.success(f"✅ Added: {fee_type} (Qty: {quantity}, Ref: {reference_number})")
                    except Exception as e:
                        st.error(f"❌ Failed to add fee: {str(e)}")

    # Quick actions row
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎯 Open Fee Window", use_container_width=True):
            try:
                wait = WebDriverWait(st.session_state["driver"], 30)
                success = open_accessorial_fee_window(st.session_state["driver"], wait)
                if success:
                    st.success("Window opened!")
                else:
                    st.error("Failed to open window")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("🔄 Refresh Page", use_container_width=True):
            try:
                st.session_state["driver"].refresh()
                time.sleep(5)
                st.success("Page refreshed")
            except Exception as e:
                st.error(f"Failed to refresh: {e}")
    
    with col3:
        if st.button("📷 Screenshot", use_container_width=True):
            try:
                timestamp = int(time.time())
                screenshot_path = f"screenshot_{timestamp}.png"
                st.session_state["driver"].save_screenshot(screenshot_path)
                st.success(f"Saved: {screenshot_path}")
            except Exception as e:
                st.error(f"Screenshot failed: {e}")

# Cleanup on app shutdown
if st.session_state.get("driver"):
    import atexit
    atexit.register(lambda: st.session_state["driver"].quit())














