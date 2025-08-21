import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# ----------------------
# Streamlit Page Config
# ----------------------
st.set_page_config(
    page_title="📋 Veracore Fee Entry",
    page_icon="📋",
    layout="wide"
)

# ----------------------
# Session State
# ----------------------
if 'fees' not in st.session_state:
    st.session_state.fees = []

if 'current_fee' not in st.session_state:
    st.session_state.current_fee = {
        'fee_type': '',
        'system': '',
        'quantity': '',
        'reference_number': ''
    }

# ----------------------
# Selenium Functions
# ----------------------
def setup_selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_to_3plwhs(driver, url, username, password):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    st.success("Logged into global 3PLWHS system. Ready to process fees.")
    time.sleep(5)

def add_fee_to_system(driver, fee):
    try:
        # Fee Type dropdown
        fee_type_dropdown = Select(driver.find_element(By.NAME, "feeType"))
        fee_type_dropdown.select_by_visible_text(fee['fee_type'])

        # System dropdown (per fee)
        system_dropdown = Select(driver.find_element(By.NAME, "system"))
        system_dropdown.select_by_visible_text(fee['system'])

        # Quantity
        qty_field = driver.find_element(By.NAME, "quantity")
        qty_field.clear()
        qty_field.send_keys(fee['quantity'])

        # Reference Number
        ref_field = driver.find_element(By.NAME, "referenceNumber")
        ref_field.clear()
        ref_field.send_keys(fee['reference_number'])

        # Click Save
        driver.find_element(By.XPATH, "//button[contains(text(),'Save')]").click()
        st.success(f"Fee '{fee['fee_type']}' submitted to system '{fee['system']}'")
        time.sleep(2)
    except Exception as e:
        st.error(f"Failed to submit fee '{fee['fee_type']}': {e}")

# ----------------------
# Streamlit Interface
# ----------------------
st.title("📋 Veracore Fee Entry (Global 3PLWHS)")

with st.sidebar:
    st.header("🔐 Login")
    veracore_url = st.text_input("3PLWHS URL", value="https://wms.3plwinner.com/VeraCore/Home")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

st.subheader("📝 Enter Fee Details (System per fee)")
st.session_state.current_fee['fee_type'] = st.text_input("Fee Type", st.session_state.current_fee['fee_type'])
st.session_state.current_fee['system'] = st.selectbox("System", ["System A", "System B", "System C"], index=0)
st.session_state.current_fee['quantity'] = st.text_input("Quantity", st.session_state.current_fee['quantity'])
st.session_state.current_fee['reference_number'] = st.text_input("Reference Number", st.session_state.current_fee['reference_number'])

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Add Fee to List"):
        if all(st.session_state.current_fee.values()):
            st.session_state.fees.append(st.session_state.current_fee.copy())
            st.session_state.current_fee = {'fee_type': '', 'system': '', 'quantity': '', 'reference_number': ''}
            st.success("Fee added to list!")
        else:
            st.warning("Please fill all fields before adding.")

with col2:
    if st.button("🗑️ Clear Current Fee"):
        st.session_state.current_fee = {'fee_type': '', 'system': '', 'quantity': '', 'reference_number': ''}

# Fee List
if st.session_state.fees:
    st.subheader("📝 Fee List")
    for i, fee in enumerate(st.session_state.fees):
        st.write(f"Fee {i+1}: {fee['fee_type']} | System: {fee['system']} | Qty: {fee['quantity']} | Ref: {fee['reference_number']}")
        if st.button(f"Remove Fee {i+1}", key=f"remove_{i}"):
            st.session_state.fees.pop(i)
            st.experimental_rerun()

# Submit Fees
st.subheader("🚀 Submit Fees to 3PLWHS")
if st.button("Login & Process All Fees"):
    if username and password and veracore_url:
        driver = setup_selenium_driver()
        login_to_3plwhs(driver, veracore_url, username, password)
        for fee in st.session_state.fees:
            add_fee_to_system(driver, fee)
        st.success("All fees processed. Review browser for results.")
    else:
        st.error("Please enter login URL, username, and password.")


