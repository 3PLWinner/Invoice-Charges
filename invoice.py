import streamlit as st
import cv2
from pyzbar import pyzbar
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# ---------------- Page Config ----------------
st.set_page_config(page_title="Veracore Fee Scanner", page_icon="📱", layout="wide")

# ---------------- Session State ----------------
if 'fees' not in st.session_state:
    st.session_state.fees = []

if 'current_fee' not in st.session_state:
    st.session_state.current_fee = {'fee_type': None, 'system': None, 'quantity': None, 'reference_number': None}

if 'scan_mode' not in st.session_state:
    st.session_state.scan_mode = 'fee_type'

# ---------------- Barcode Decode ----------------
def decode_barcode_from_image(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        barcodes = pyzbar.decode(gray)
        if barcodes:
            return barcodes[0].data.decode('utf-8')
        return None
    except:
        return None

# ---------------- Selenium Setup ----------------
def setup_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# ---------------- Veracore Login ----------------
def login_veracore(driver, url, username, password):
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(3)
    st.success("✅ Logged in")

def select_system(driver, system_name):
    system_dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "customerSystem"))
    )
    Select(system_dropdown).select_by_visible_text(system_name)
    st.success(f"✅ Selected system: {system_name}")

def open_accessorial_activity(driver):
    lightning = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.lightning-icon"))
    )
    lightning.click()
    st.success("✅ Accessorial Activity opened")

def fill_fee(driver, fee):
    fee_type_dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.NAME, "feeType"))
    )
    Select(fee_type_dropdown).select_by_visible_text(fee['fee_type'])
    qty_field = driver.find_element(By.NAME, "quantity")
    qty_field.clear()
    qty_field.send_keys(str(fee['quantity']))
    ref_field = driver.find_element(By.NAME, "referenceNumber")
    ref_field.clear()
    ref_field.send_keys(fee['reference_number'])
    driver.find_element(By.XPATH, "//button[contains(text(),'Save')]").click()
    st.success(f"✅ Fee added: {fee['fee_type']} | {fee['quantity']} | {fee['reference_number']}")

def process_fees(driver, fees_list):
    for fee in fees_list:
        fill_fee(driver, fee)
        time.sleep(1)

# ---------------- Main App ----------------
def main():
    st.markdown('<h1 style="text-align:center;">📱 Veracore Fee Scanner</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("🔐 Login & System")
        url = st.text_input("Veracore URL", value="https://wms.3plwinner.com/VeraCore/Home")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        system_options = ["Customer A", "Customer B", "Customer C"]
        selected_system = st.selectbox("Customer System", system_options)
    
    st.header("📋 Scan Fee")
    mode = st.session_state.scan_mode
    st.info(f"Next: {mode.replace('_',' ').title()}")
    
    uploaded_file = st.file_uploader("Upload barcode", type=['png','jpg','jpeg'])
    if uploaded_file:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        st.image(image, width=300)
        barcode = decode_barcode_from_image(image)
        if barcode:
            st.session_state.current_fee[mode] = barcode
            st.success(f"✅ {mode.replace('_',' ').title()}: {barcode}")
            # Move to next mode
            if mode == 'fee_type':
                st.session_state.scan_mode = 'quantity'
            elif mode == 'quantity':
                st.session_state.scan_mode = 'reference_number'
            else:
                # Completed current fee
                st.session_state.scan_mode = 'fee_type'
                st.session_state.current_fee['system'] = selected_system
                st.session_state.fees.append(st.session_state.current_fee.copy())
                st.success(f"Fee added. Total: {len(st.session_state.fees)}")
                st.session_state.current_fee = {'fee_type': None, 'system': None, 'quantity': None, 'reference_number': None}
                st.experimental_rerun()
    
    st.subheader("📝 Fee List")
    for i, fee in enumerate(st.session_state.fees):
        st.write(f"{i+1}. {fee['fee_type']} | {fee['system']} | {fee['quantity']} | {fee['reference_number']}")
    
    if st.button("🚀 Login & Submit Fees"):
        driver = setup_driver()
        login_veracore(driver, url, username, password)
        select_system(driver, selected_system)
        open_accessorial_activity(driver)
        process_fees(driver, st.session_state.fees)
        st.success("🎉 All fees submitted! Review browser to confirm.")
        st.info("Browser will remain open for review.")

if __name__ == "__main__":
    main()
