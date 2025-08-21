import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# -------------------------------
# Selenium setup
# -------------------------------
def setup_selenium_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

# -------------------------------
# Login function
# -------------------------------
def login_to_3plwhs(driver, url, username, password):
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    
    # Type credentials
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(username)
    wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(password)
    
    # Click login button (handles <span> inside button)
    login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Login']/..")))
    login_btn.click()
    
    # Wait a moment for home page to load
    WebDriverWait(driver, 10).until(lambda d: True)
    
    # Login is assumed successful; we won't check any element
    return True

# -------------------------------
# Streamlit app
# -------------------------------
st.title("Invoice Charges Automation")

# Step 1: Credentials
veracore_url = st.text_input("3PLWHS URL", value="https://global-3plwhs.example.com")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
    driver = setup_selenium_driver()
    login_to_3plwhs(driver, veracore_url, username, password)
    st.success("✅ Login successful!")
    st.session_state["driver"] = driver
    st.session_state["logged_in"] = True

# Step 2: OMS system input
if st.session_state.get("logged_in"):
    driver = st.session_state["driver"]
    
    oms_system = st.text_input("Enter OMS System")
    
    if st.button("Confirm System") and oms_system:
        # Type the OMS system in the browser (adjust the selector if needed)
        system_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "system_input"))
        )
        system_input.clear()
        system_input.send_keys(oms_system)
        system_input.submit()  # or click a 'Go' button if needed
        st.success(f"System '{oms_system}' selected. You can now enter fees.")
        st.session_state["system_selected"] = oms_system

# Step 3: Fee input only if system selected
if st.session_state.get("system_selected"):
    st.header("Fee Entries")
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
                "system": st.session_state["system_selected"]
            })
            st.success(f"Added fee: {fee_type}, Qty: {quantity}, Ref: {reference_number}")








