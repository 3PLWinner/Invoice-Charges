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
    "VSO335": "Meriden International",
    "CUS001": "3PLWINNER"
}

# Configure Streamlit page
st.set_page_config(
    page_title="Warehouse Fee Entry", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Database functions
def init_database():
    """Initialize the SQLite database safely, adding missing columns if needed."""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    
    # Create work_orders table if it doesn't exist (basic schema)
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
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(work_orders)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add missing columns
    if 'fee_date' not in columns:
        cursor.execute("ALTER TABLE work_orders ADD COLUMN fee_date DATE")
    
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


def save_work_order(customer_id, customer_name, reference_numbers, fee_data, fee_date, created_by, notes=""):
    """Save a new work order to the database with customer_id for web scraping access"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    
    # Generate barcode data with work order ID
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    cursor.execute('''
        INSERT INTO work_orders 
        (customer_id, customer_name, reference_numbers, fee_data, fee_date, date_created, barcode_data, created_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        customer_id,
        customer_name,
        json.dumps(reference_numbers),
        json.dumps(fee_data),
        fee_date.isoformat(),
        datetime.now().isoformat(),
        f"WO-{timestamp}",  # Temporary barcode, will update with ID
        created_by,
        notes
    ))
    
    work_order_id = cursor.lastrowid
    
    # Update barcode with actual work order ID
    barcode_data = f"WO-{work_order_id}-{timestamp}"
    cursor.execute("UPDATE work_orders SET barcode_data = ? WHERE id = ?", (barcode_data, work_order_id))
    
    conn.commit()
    conn.close()
    return work_order_id, barcode_data

def authenticate_user(username, password):
    """Simple user authentication"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def get_work_order_stats():
    """Get work order statistics"""
    conn = sqlite3.connect('warehouse_system.db')
    
    # Get today's stats
    today = datetime.now().date()
    today_orders = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM work_orders WHERE DATE(date_created) = ?", 
        conn, params=[today.isoformat()]
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
    return today_orders, pending_orders, total_orders

def get_work_orders_for_sync():
    """Get work orders that need to be synced with Veracore - customer_id available for web scraping"""
    conn = sqlite3.connect('warehouse_system.db')
    
    # Get pending work orders with customer_id for web scraping script
    work_orders = pd.read_sql_query('''
        SELECT id, customer_id, customer_name, reference_numbers, fee_data, fee_date,
               date_created, barcode_data, created_by, notes
        FROM work_orders 
        WHERE status = 'pending' AND veracore_synced = 0
        ORDER BY date_created ASC
    ''', conn)
    
    conn.close()
    
    # Parse JSON fields and return structured data with customer_id for web scraping
    sync_data = []
    for _, row in work_orders.iterrows():
        sync_data.append({
            'work_order_id': row['id'],
            'customer_id': row['customer_id'],  # This will be used by your web scraping script
            'customer_name': row['customer_name'],
            'reference_numbers': json.loads(row['reference_numbers']),
            'fee_data': json.loads(row['fee_data']),
            'fee_date': row['fee_date'],
            'date_created': row['date_created'],
            'barcode_data': row['barcode_data'],
            'created_by': row['created_by'],
            'notes': row['notes']
        })
    
    return sync_data

# Initialize database
init_database()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "fee_entries" not in st.session_state:
    st.session_state.fee_entries = []
if "show_success" not in st.session_state:
    st.session_state.show_success = False

# Login Screen
if not st.session_state.logged_in:
    st.title("🏭 Warehouse Management System")
    st.subheader("Login")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("**Default Users:**")
        st.write("• admin / admin123")
        st.write("• worker1 / worker123") 
        st.write("• accounting / acc123")
    
    with col2:
        with st.form("login_form"):
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
            st.session_state.fee_entries = []
            st.session_state.show_success = False
            st.rerun()

    # Show success message if work order was just created
    if st.session_state.show_success:
        st.success("✅ Work Order created successfully!")
        st.session_state.show_success = False

    # Main fee entry form
    st.subheader("Create New Work Order")
    
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

    # Fee selection section
    st.write("**Fee Selection**")
    
    # Add new fee
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        fee_type = st.selectbox("Fee Type", [""] + FEE_TYPES, key="new_fee_type")
    with col2:
        fee_quantity = st.number_input("Quantity", min_value=1, value=1, key="new_fee_qty")
    with col3:
        if st.button("➕ Add Fee") and fee_type:
            st.session_state.fee_entries.append({
                'type': fee_type,
                'quantity': fee_quantity
            })
            st.rerun()
    
    # Display current fees
    if st.session_state.fee_entries:
        st.write("**Selected Fees:**")
        fees_to_remove = []
        
        for i, fee in enumerate(st.session_state.fee_entries):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"• {fee['type']}")
            with col2:
                st.write(f"Qty: {fee['quantity']}")
            with col3:
                if st.button("🗑️ Remove", key=f"remove_{i}"):
                    fees_to_remove.append(i)
        
        # Remove fees marked for removal
        for idx in reversed(fees_to_remove):
            st.session_state.fee_entries.pop(idx)
        
        if fees_to_remove:
            st.rerun()

    # Additional fields
    st.write("**Fee Details**")
    col1, col2 = st.columns(2)
    with col1:
        fee_date = st.date_input("Fee Date", value=datetime.now().date(), help="This date will be used when entering fees into Veracore")
    with col2:
        st.write("")  # Spacer

    notes = st.text_area("Notes (optional)", height=100)

    # Submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Create Work Order", use_container_width=True, type="primary"):
            # Validation
            errors = []
            if not customer_id:
                errors.append("Please select or enter a customer")
            if not reference_numbers:
                errors.append("Please enter at least one reference number")
            if not st.session_state.fee_entries:
                errors.append("Please add at least one fee")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Save work order with customer_id for web scraping
                try:
                    work_order_id, barcode_data = save_work_order(
                        customer_id,
                        customer_name,
                        reference_numbers,
                        st.session_state.fee_entries,
                        fee_date,
                        st.session_state.username,
                        notes=notes
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
                        st.write(f"**Fee Date:** {fee_date.strftime('%B %d, %Y')}")
                        st.write("**Fees:**")
                        for fee in st.session_state.fee_entries:
                            st.write(f"  • {fee['type']} (Qty: {fee['quantity']})")
                        if notes:
                            st.write(f"**Notes:** {notes}")
                    
                    with col2:
                        st.subheader("Barcode")
                        st.image(buf.getvalue(), width=300)
                        st.code(barcode_data, language="text")
                    
                    # Clear the form for next entry
                    st.session_state.fee_entries = []
                    st.session_state.show_success = True
                    
                except Exception as e:
                    st.error(f"Error creating work order: {str(e)}")

    # Quick stats
    if st.session_state.role in ['admin', 'accounting']:
        st.subheader("Quick Stats")
        
        try:
            today_orders, pending_orders, total_orders = get_work_order_stats()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Today's Orders", today_orders)
            with col2:
                st.metric("Pending Orders", pending_orders)
            with col3:
                st.metric("Total Orders", total_orders)
        except Exception as e:
            st.warning(f"Could not load stats: {e}")

    # Navigation section
    st.subheader("Navigation")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Accounting Dashboard", use_container_width=True):
            st.info("💡 To access accounting dashboard, run: `streamlit run accounting_app.py --server.port 8502`")
    
    with col2:
        if st.button("🔄 Sync with Veracore", use_container_width=True):
            st.info("💡 To access Veracore sync, run: `streamlit run veracore_sync.py --server.port 8503`")

    # Debug section for admins
    if st.session_state.role == 'admin':
        with st.expander("🔧 Debug Information"):
            st.write("**Session State:**")
            st.write(f"- Logged in: {st.session_state.logged_in}")
            st.write(f"- Username: {st.session_state.username}")
            st.write(f"- Role: {st.session_state.role}")
            st.write(f"- Fee entries: {len(st.session_state.fee_entries)}")
            
            if st.button("Clear Fee Entries"):
                st.session_state.fee_entries = []
                st.rerun()
            
            if st.button("View Database Tables"):
                try:
                    conn = sqlite3.connect('warehouse_system.db')
                    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                    st.write("Tables:", tables)
                    
                    # Show recent work orders with customer_id for web scraping reference
                    recent_orders = pd.read_sql_query(
                        "SELECT id, customer_id, customer_name, fee_date, date_created, status FROM work_orders ORDER BY id DESC LIMIT 5", 
                        conn
                    )
                    st.write("Recent Work Orders:")
                    st.dataframe(recent_orders)
                    conn.close()
                except Exception as e:
                    st.error(f"Database error: {e}")
            
            # Show sample sync data
            if st.button("Preview Sync Data"):
                try:
                    sync_data = get_work_orders_for_sync()
                    if sync_data:
                        st.write("**Sample work order data that will be sent to Veracore (includes customer_id for web scraping):**")
                        st.json(sync_data[0] if sync_data else {})
                    else:
                        st.write("No pending work orders to sync")
                except Exception as e:
                    st.error(f"Error getting sync data: {e}")