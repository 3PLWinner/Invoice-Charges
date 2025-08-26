# warehouse_app.py - Main warehouse worker interface
import streamlit as st
import sqlite3
import pandas as pd
import qrcode
from io import BytesIO
import json
from datetime import datetime
import time

# Your existing fee types from the Veracore script
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

# Sample customers - replace with your actual customer data
CUSTOMERS = {
    "CUST001": "ABC Company",
    "CUST002": "XYZ Corporation", 
    "CUST003": "123 Industries",
    "CUST004": "Demo Customer",
    "CUST005": "Test Company",
    "CUST006": "Sample Corp",
    "CUST007": "Example LLC",
    "CUST008": "Demo Industries",
    "CUST009": "Test Logistics",
    "CUST010": "Warehouse Co",
    "VSO335": "Meriden International"
}

st.set_page_config(
    page_title="Warehouse Fee Entry", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Make sure CUSTOMERS is available globally
if 'CUSTOMERS' not in globals():
    CUSTOMERS = {
        "CUST001": "ABC Company",
        "CUST002": "XYZ Corporation", 
        "CUST003": "123 Industries",
        "CUST004": "Demo Customer",
        "CUST005": "Test Company",
        "CUST006": "Sample Corp",
        "CUST007": "Example LLC",
        "CUST008": "Demo Industries",
        "CUST009": "Test Logistics",
        "CUST010": "Warehouse Co",
        "VSO335": "Meriden International"
    }

# Database functions
def init_database():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    
    # Create work orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            reference_numbers TEXT NOT NULL,
            fee_data TEXT NOT NULL,
            date_created DATETIME NOT NULL,
            barcode_data TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            veracore_synced BOOLEAN DEFAULT 0,
            sync_date DATETIME,
            created_by TEXT,
            notes TEXT
        )
    ''')
    
    # Create users table for simple authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'worker'
        )
    ''')
    
    # Insert default users if none exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        default_users = [
            ('admin', 'admin123', 'admin'),
            ('worker1', 'worker123', 'worker'),
            ('worker2', 'worker123', 'worker'),
            ('accounting', 'acc123', 'accounting')
        ]
        cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", default_users)
    
    conn.commit()
    conn.close()

def save_work_order(customer_id, customer_name, reference_numbers, fee_data, created_by):
    """Save a new work order to the database"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    
    # Generate barcode data
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    cursor.execute('''
        INSERT INTO work_orders 
        (customer_id, customer_name, reference_numbers, fee_data, date_created, barcode_data, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        customer_id,
        customer_name,
        json.dumps(reference_numbers),
        json.dumps(fee_data),
        datetime.now().isoformat(),
        f"WO-{timestamp}",
        created_by
    ))
    
    work_order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return work_order_id, f"WO-{work_order_id}-{timestamp}"

def authenticate_user(username, password):
    """Simple user authentication"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

# Initialize database
init_database()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# Login Screen
if not st.session_state.logged_in:
    st.title("🏭 Warehouse Management System")
    st.subheader("Login")
    
    with st.form("login_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("**Default Users:**")
            st.write("• admin / admin123")
            st.write("• worker1 / worker123") 
            st.write("• accounting / acc123")
        
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("🔐 Login", use_container_width=True):
                if username and password:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state.logged_in = True
                        st.session_state.username = user_data[0]
                        st.session_state.role = user_data[1]
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")

# Main Application
else:
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("📦 Warehouse Fee Entry System")
    with col2:
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**Role:** {st.session_state.role.title()}")
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()

    # Main fee entry form
    st.subheader("Create New Work Order")
    
    with st.form("work_order_form", clear_on_submit=True):
        # Customer selection
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Customer Selection**")
            selection_method = st.radio("Method", ["Dropdown", "Scan/Manual Entry"], horizontal=True)
            
            if selection_method == "Dropdown":
                customer_options = [f"{k} - {v}" for k, v in CUSTOMERS.items()]
                selected = st.selectbox("Select Customer", [""] + customer_options)
                if selected:
                    customer_id = selected.split(" - ")[0]
                    customer_name = selected.split(" - ")[1]
                else:
                    customer_id = customer_name = ""
            else:
                scanned_id = st.text_input("Customer ID (scan or type)")
                customer_id = scanned_id
                customer_name = CUSTOMERS.get(scanned_id, scanned_id) if scanned_id else ""
                if customer_name and customer_name != scanned_id:
                    st.success(f"✅ Found: {customer_name}")
                elif scanned_id and customer_name == scanned_id:
                    st.warning("⚠️ Customer not in database - will use ID as name")
        
        with col2:
            st.write("**Reference Numbers**")
            ref_input_method = st.radio("Input Method", ["Individual Entry", "Bulk Entry"], horizontal=True)
            
            reference_numbers = []
            if ref_input_method == "Individual Entry":
                num_refs = st.number_input("Number of References", min_value=1, max_value=10, value=1)
                for i in range(int(num_refs)):
                    ref = st.text_input(f"Reference #{i+1}", key=f"ref_{i}")
                    if ref:
                        reference_numbers.append(ref)
            else:
                bulk_refs = st.text_area("Enter references (one per line)", height=100)
                if bulk_refs:
                    reference_numbers = [ref.strip() for ref in bulk_refs.split('\n') if ref.strip()]

        # Fee selection
        st.write("**Fee Selection**")
        
        # Initialize fee data storage
        if 'fee_entries' not in st.session_state:
            st.session_state.fee_entries = []
        
        # Add fee entry section
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            fee_type = st.selectbox("Fee Type", [""] + FEE_TYPES, key="new_fee_type")
        with col2:
            fee_quantity = st.number_input("Quantity", min_value=1, value=1, key="new_fee_qty")
        with col3:
            if st.form_submit_button("➕ Add Fee") and fee_type:
                st.session_state.fee_entries.append({
                    'type': fee_type,
                    'quantity': fee_quantity
                })
        
        # Display added fees
        if st.session_state.fee_entries:
            st.write("**Selected Fees:**")
            for i, fee in enumerate(st.session_state.fee_entries):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(fee['type'])
                with col2:
                    st.write(f"Qty: {fee['quantity']}")
                with col3:
                    if st.form_submit_button(f"🗑️", key=f"remove_{i}"):
                        st.session_state.fee_entries.pop(i)
                        st.rerun()

        # Date
        fee_date = st.date_input("Fee Date", value=datetime.now().date())
        
        # Notes
        notes = st.text_area("Notes (optional)", height=100)
        
        # Submit work order
        submitted = st.form_submit_button("🚀 Create Work Order", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            if not customer_id:
                st.error("Please select or enter a customer")
            elif not reference_numbers:
                st.error("Please enter at least one reference number")
            elif not st.session_state.fee_entries:
                st.error("Please add at least one fee")
            else:
                # Save work order
                try:
                    work_order_id, barcode_data = save_work_order(
                        customer_id,
                        customer_name,
                        reference_numbers,
                        st.session_state.fee_entries,
                        st.session_state.username
                    )
                    
                    # Generate QR code
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(barcode_data)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color="black", back_color="white")
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    
                    # Success message
                    st.success(f"✅ Work Order #{work_order_id} Created Successfully!")
                    
                    # Display work order details and QR code
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Work Order Details")
                        st.write(f"**ID:** {work_order_id}")
                        st.write(f"**Customer:** {customer_name} ({customer_id})")
                        st.write(f"**References:** {', '.join(reference_numbers)}")
                        st.write(f"**Fees:** {len(st.session_state.fee_entries)} items")
                        st.write(f"**Date:** {fee_date}")
                        if notes:
                            st.write(f"**Notes:** {notes}")
                    
                    with col2:
                        st.subheader("Barcode")
                        st.image(buf.getvalue(), width=300)
                        st.code(barcode_data, language="text")
                    
                    # Clear the form
                    st.session_state.fee_entries = []
                    
                except Exception as e:
                    st.error(f"Error creating work order: {str(e)}")

    # Quick stats
    if st.session_state.role in ['admin', 'accounting']:
        st.subheader("Quick Stats")
        
        conn = sqlite3.connect('warehouse_system.db')
        
        # Get today's stats
        today = datetime.now().date()
        today_orders = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM work_orders WHERE DATE(date_created) = ?", 
            conn, params=[today]
        ).iloc[0]['count']
        
        # Get pending orders
        pending_orders = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM work_orders WHERE status = 'pending'", 
            conn
        ).iloc[0]['count']
        
        # Get total orders
        total_orders = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM work_orders", 
            conn
        ).iloc[0]['count']
        
        conn.close()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Today's Orders", today_orders)
        with col2:
            st.metric("Pending Orders", pending_orders)
        with col3:
            st.metric("Total Orders", total_orders)

    # Navigation to other apps
    st.subheader("Navigation")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Accounting Dashboard", use_container_width=True):
            st.info("Open accounting_app.py on port 8502")
    
    with col2:
        if st.button("🔄 Sync with Veracore", use_container_width=True):
            st.info("Open veracore_sync.py on port 8503")