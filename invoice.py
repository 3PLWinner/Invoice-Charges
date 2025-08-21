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
    
    # Wait for system dropdown to appear on the home page
    try:
        system_dropdown = wait.until(EC.presence_of_element_located((By.NAME, "system_select")))
        return True
    except:
        return False

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
    login_success = login_to_3plwhs(driver, veracore_url, username, password)
    
    if login_success:
        st.success("✅ Login successful! Please select your system.")
        st.session_state["driver"] = driver
        st.session_state["logged_in"] = True
    else:
        st.error("❌ Login failed. Check your credentials.")

# Step 2: Only show system selection if logged in
if st.session_state.get("logged_in"):
    driver = st.session_state["driver"]
    wait = WebDriverWait(driver, 10)
    
    # Grab available systems from dropdown on home page
    system_options = [option.text for option in wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "select[name='system_select'] option"))
    )]
    
    selected_system = st.selectbox("Select System", system_options)
    
    if st.button("Confirm System"):
        # Select system in browser
        system_dropdown = driver.find_element(By.NAME, "system_select")
        system_dropdown.send_keys(selected_system)
        st.success(f"System '{selected_system}' selected. You can now enter fees.")
        st.session_state["system_selected"] = selected_system

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







