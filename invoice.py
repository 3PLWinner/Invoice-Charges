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


# -------------------------------
# Selenium setup
# -------------------------------
def setup_selenium_driver():
    chrome_options = Options()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


# -------------------------------
# Open accessorial fee window
# -------------------------------
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
            st.info("🎯 Accessorial fee window opened (regular click)")
        except:
            try:
                driver.execute_script("arguments[0].click();", accfee_btn)
                clicked = True
                st.info("🎯 Accessorial fee window opened (JS click)")
            except:
                ActionChains(driver).move_to_element(accfee_btn).click().perform()
                clicked = True
                st.info("🎯 Accessorial fee window opened (action chains)")
        
        if clicked:
            time.sleep(3)  # Wait for window to fully load
            return True
    except Exception as e:
        st.error(f"❌ Failed to open accessorial fee window: {str(e)}")
        return False
    

# -------------------------------
# Login and select system
# -------------------------------
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



def wait_for_no_overlay(driver, timeout=30):
    """Wait until any ExtJS loading mask/overlay disappears."""
    WebDriverWait(driver, timeout).until_not(
        EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'x-mask') and not(contains(@style,'display: none'))]")
        )
    )




# -------------------------------
# Add a fee with improved workflow and debugging
# -------------------------------
def add_fee(driver, wait, fee_type, quantity, reference):
    st.info("➡️ Starting add_fee process...")

    try:

        try:
            fee_window = driver.find_element(By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]")
            if not fee_window.is_displayed():
                st.info("🔄 Accessorial fee window not visible, opening...")
                open_accessorial_fee_window(driver, wait)
        except:
            st.info("🔄 Accessorial fee window not found, opening...")
            open_accessorial_fee_window(driver, wait)


        # Wait for Accessorial Fee window
        fee_window = wait.until(EC.presence_of_element_located((
            By.XPATH, "//div[contains(@class,'x-window') and contains(.,'Accessorial Fee')]"
        )))
        st.info("✅ Accessorial Fee window detected")

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
        st.info(f"Searching with: '{search_text}' (first 15 chars)")
        
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
            st.info(f"Found exact match for: {fee_type}")
        except:
            # If exact match fails, try to find a row that contains the search text
            try:
                fee_row = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    f"//tr[contains(@class,'x-grid-row') and td[2]/div[contains(normalize-space(text()), '{search_text}')]]"
                )))
                # Get the actual text from the found row
                actual_fee_text = fee_row.find_element(By.XPATH, "./td[2]/div").text.strip()
                st.info(f"Found partial match: '{actual_fee_text}' for search '{search_text}'")
            except:
                # Last resort: click the first available row
                fee_row = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//tr[contains(@class,'x-grid-row')][1]"
                )))
                actual_fee_text = fee_row.find_element(By.XPATH, "./td[2]/div").text.strip()
                st.warning(f"Used first available option: '{actual_fee_text}'")
        
        fee_row.click()

        st.info(f"Selected fee type: {fee_type}")
        time.sleep(3)  # let the grid refresh
        try:
            # Strategy 1: Use the active element (since cursor should already be there)
            qty_input = driver.switch_to.active_element
            st.info("Using active element for quantity input")
        except:
            try:
                # Strategy 2: Find by the correct ID pattern
                qty_input = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//input[contains(@id, 'numberfield-') and contains(@id, '-inputEl')]"
                )))
                st.info("Found quantity input by ID pattern")
                qty_input.click()
            except:
                # Strategy 3: Find by role and class attributes
                qty_input = wait.until(EC.element_to_be_clickable((
                    By.XPATH, "//input[@role='spinbutton' and contains(@class, 'x-form-field')]"
                )))
                st.info("Found quantity input by role and class")
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

        st.success("💾 Saved fee successfully!")

        time.sleep(2)

        st.info("Reopening Accessorial Fee Window for next entry...")
        success = open_accessorial_fee_window(driver, wait)

        if success:
            st.success("Ready for next fee entry")
        else:
            st.warning("Could not automatically reopen accessorial fee window. Use the 'Test Accessorial Button' to open it manually.")

        st.success(f"✅ Fee added successfully!\n\nFee Type: {fee_type}\nQuantity: {quantity}\nReference: {reference}")

    except Exception as e:
        st.error(f"❌ Error in add_fee: {e}")
        
        # Enhanced debugging information
        try:
            # Look for all number fields in the current window
            number_fields = driver.find_elements(By.XPATH, "//input[contains(@id, 'numberfield-')]")
            st.info(f"Found {len(number_fields)} number field elements:")
            for i, field in enumerate(number_fields):
                field_id = field.get_attribute('id')
                field_value = field.get_attribute('value')
                is_displayed = field.is_displayed()
                st.info(f"  Field {i}: id='{field_id}', value='{field_value}', displayed={is_displayed}")
                
            # Also check for any input with spinbutton role
            spinbutton_fields = driver.find_elements(By.XPATH, "//input[@role='spinbutton']")
            st.info(f"Found {len(spinbutton_fields)} spinbutton elements:")
            for i, field in enumerate(spinbutton_fields):
                field_id = field.get_attribute('id')
                field_class = field.get_attribute('class')
                field_value = field.get_attribute('value')
                st.info(f"  Spinbutton {i}: id='{field_id}', class='{field_class}', value='{field_value}'")
                
        except Exception as debug_e:
            st.error(f"Debug info failed: {debug_e}")
        
        screenshot_name = f"error_add_fee_{int(time.time())}.png"
        driver.save_screenshot(screenshot_name)
        st.warning(f"📷 Screenshot saved: {screenshot_name}")




# -------------------------------
# Close driver safely
# -------------------------------
def close_driver():
    if "driver" in st.session_state:
        try:
            st.session_state["driver"].quit()
        except:
            pass
        del st.session_state["driver"]
        st.session_state["logged_in"] = False

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("Veracore OMS Invoice Charges")

# Add a sidebar for better organization
with st.sidebar:
    st.header("Connection Settings")
    veracore_url = st.text_input("3PLWHS URL", value="https://wms.3plwinner.com/VeraCore")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    system_id = st.text_input("System ID")
    
    if st.button("🔌 Login and Connect"):
        if not (username and password and system_id):
            st.warning("Please enter all fields: username, password, and system ID.")
        else:
            with st.spinner("Connecting to Veracore OMS..."):
                try:
                    # Close existing driver if any
                    close_driver()
                    
                    driver = setup_selenium_driver()
                    login_and_select_system(driver, veracore_url, username, password, system_id)
                    
                    st.session_state["driver"] = driver
                    st.session_state["logged_in"] = True
                    st.session_state["system_id"] = system_id
                    st.success(f"✅ Connected to system {system_id}")
                    
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    close_driver()
    
    if st.session_state.get("logged_in"):
        st.success(f"🟢 Connected to system {st.session_state.get('system_id', 'Unknown')}")
        if st.button("🔌 Disconnect"):
            close_driver()
            st.success("Disconnected successfully")
            st.rerun()

# Main content area
if st.session_state.get("logged_in"):
    st.header(f"Fee Entry for System {st.session_state['system_id']}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("fee_form"):
            st.subheader("Add Accessorial Fee")
            fee_type_selection = st.selectbox("Fee Type", FEE_TYPES, help="Select a fee type - only first 15 characters will be used for searching")
            if fee_type_selection == "Custom Entry":
                fee_type = st.text_input("Custom Fee Type", help="Enter fee type name - only first 15 characters will be used for searching")
            else:
                fee_type = fee_type_selection
            col_qty, col_ref = st.columns(2)
            with col_qty:
                quantity = st.number_input("Quantity", min_value=1, value=1)
            with col_ref:
                reference_number = st.text_input("Reference Number")
            
            submit = st.form_submit_button("➕ Add Fee", use_container_width=True)

            if submit:
                if not fee_type or not reference_number:
                    st.warning("Please enter both Fee Type and Reference Number")
                else:
                    with st.spinner("Adding fee..."):
                        try:
                            wait = WebDriverWait(st.session_state["driver"], 30)
                            add_fee(
                                st.session_state["driver"],
                                wait,
                                fee_type,
                                quantity,
                                reference_number
                            )
                            st.success(f"✅ Fee added successfully!")
                            st.info(f"**Fee Type:** {fee_type}  \n**Quantity:** {quantity}  \n**Reference:** {reference_number}")
                            
                        except Exception as e:
                            st.error(f"❌ Failed to add fee: {str(e)}")
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("🎯 Open Accessorial Window", use_container_width=True):
            try:
                with st.spinner("Testing accessorial fee button..."):
                    wait = WebDriverWait(st.session_state["driver"], 30)
                    success = open_accessorial_fee_window(st.session_state["driver"], wait)
                    if success:
                        st.success("Accessorial fee window opened!")
                    else:
                        st.error("Failed to open accessorial fee window")
            except Exception as e:
                    st.error(f"Error: {str(e)}")

        st.subheader("Debug Tools")

        if st.button("🔍 Check for Overlays"):
            try:
                driver = st.session_state["driver"]
                overlays = driver.find_elements(By.XPATH, "//div[contains(@class, 'x-mask') or contains(@class, 'mask') or contains(@class, 'overlay')]")
                
                if overlays:
                    st.warning(f"Found {len(overlays)} overlay/mask elements:")
                    for i, overlay in enumerate(overlays):
                        try:
                            overlay_class = overlay.get_attribute("class")
                            overlay_style = overlay.get_attribute("style")
                            is_displayed = overlay.is_displayed()
                            st.text(f"Overlay {i}: class='{overlay_class}', displayed={is_displayed}")
                            if "display: none" not in overlay_style and is_displayed:
                                st.error(f"Active overlay blocking clicks: {overlay_class}")
                        except:
                            st.text(f"Overlay {i}: Could not get details")
                else:
                    st.success("No overlays/masks found!")
                    
            except Exception as e:
                st.error(f"Overlay check failed: {e}")

                
        if st.button("🔄 Refresh OMS Page"):
            try:
                st.session_state["driver"].refresh()
                time.sleep(5)  # Wait for page to reload
                st.success("Page refreshed")
            except Exception as e:
                st.error(f"Failed to refresh: {e}")
                
        if st.button("📷 Take Screenshot"):
            try:
                timestamp = int(time.time())
                screenshot_path = f"screenshot_{timestamp}.png"
                st.session_state["driver"].save_screenshot(screenshot_path)
                st.success(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                st.error(f"Screenshot failed: {e}")

else:
    st.info("👈 Please connect to Veracore OMS using the sidebar to start adding fees.")
    
    with st.expander("ℹ️ How to use this tool"):
        st.markdown("""
        1. **Connect**: Enter your Veracore URL, credentials, and system ID in the sidebar
        2. **Login**: Click "Login and Connect" to establish connection
        3. **Auto-Open**: The accessorial fee window will open automatically after login
        4. **Add Fees**: Use the fee entry form to add accessorial fees
        5. **Debug**: Use the debug tools if you encounter issues
        
        **Features**:
        - Automatically opens accessorial fee window upon login
        - Comprehensive field detection with multiple fallback strategies
        - Real-time feedback during fee addition process
        - Debug tools to inspect page elements
        - Automatic screenshot capture on errors
        - **Smart Search**: Only types first 15 characters to show dropdown options
        """)

# Cleanup on app shutdown
if st.session_state.get("driver"):
    import atexit
    atexit.register(lambda: st.session_state["driver"].quit())














