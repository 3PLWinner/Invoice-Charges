import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Selenium setup
def setup_selenium_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# Login function (works correctly)
def login_to_3plwhs(driver, url, username, password):
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    
    # Type credentials
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
    
    # Click login button (handles <span> inside button)
    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Login']/..")))
    login_btn.click()
    
    # Wait for system selection boxes to appear
    try:
        system_boxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "SystemSelectClassic")))
        return system_boxes
    except:
        return None

# Streamlit app
st.title("Invoice Charges Automation")

# Step 1: Credentials
veracore_url = st.text_input("3PLWHS URL", value="https://wms.3plwinner.com/VeraCore/Home/#systems")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    driver = setup_selenium_driver()
    system_boxes = login_to_3plwhs(driver, veracore_url, username, password)
    
    if system_boxes:
        st.success("✅ Login successful!")
        st.session_state["driver"] = driver
        st.session_state["logged_in"] = True
        # Extract system names dynamically
        systems = [elem.text for elem in system_boxes]
        st.session_state["systems"] = systems
    else:
        st.error("❌ Login failed or system boxes not found.")

# Step 2: Only show fee form if logged in
if st.session_state.get("logged_in"):
    st.header("Fee Entries")
    
    # Select the system dynamically
    selected_system = st.selectbox("Select OMS System", st.session_state["systems"])
    
    fees = []
    with st.form("fee_form"):
        fee_type = st.text_input("Fee Type")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        reference_number = st.text_input("Reference Number")
        submit = st.form_submit_button("Add Fee")
        
        if submit:
            fees.append({
                "fee_type": fee_type,
                "quantity": quantity,
                "reference_number": reference_number,
                "system": selected_system
            })
            st.success(f"Added fee: {fee_type}, Qty: {quantity}, Ref: {reference_number}")

    if st.button("Run Automation"):
        driver = st.session_state["driver"]
        wait = WebDriverWait(driver, 10)
        for fee in fees:
            driver.get(f"{veracore_url}/accessorial_activities")
            
            # Click the selected system box dynamically
            system_boxes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".system-box")))
            for box in system_boxes:
                if box.text == fee["system"]:
                    box.click()
                    break
            
            # Input fee info
            wait.until(EC.presence_of_element_located((By.NAME, "fee_type"))).send_keys(fee["fee_type"])
            wait.until(EC.presence_of_element_located((By.NAME, "quantity"))).send_keys(str(fee["quantity"]))
            wait.until(EC.presence_of_element_located((By.NAME, "reference_number"))).send_keys(fee["reference_number"])
            
            # Click submit
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit']")))
            submit_btn.click()
        
        st.success("All fees processed!")







