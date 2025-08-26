# accounting_app.py - Accounting dashboard
import streamlit as st
import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Accounting Dashboard", 
    layout="wide"
)

def authenticate_user(username, password):
    """Simple user authentication"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    return result

def load_work_orders():
    """Load all work orders from database"""
    conn = sqlite3.connect('warehouse_system.db')
    df = pd.read_sql_query("""
        SELECT * FROM work_orders 
        ORDER BY date_created DESC
    """, conn)
    conn.close()
    return df

def update_work_order_status(order_id, new_status):
    """Update work order status"""
    conn = sqlite3.connect('warehouse_system.db')
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE work_orders 
        SET status = ?, sync_date = ?
        WHERE id = ?
    """, (new_status, datetime.now().isoformat(), order_id))
    conn.commit()
    conn.close()

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login screen
if not st.session_state.logged_in:
    st.title("📊 Accounting Dashboard")
    st.subheader("Login")
    
    with st.form("login_form"):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.info("**Accounting Access**\nUse: accounting / acc123\nOr: admin / admin123")
        
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("🔐 Login"):
                user_data = authenticate_user(username, password)
                if user_data and user_data[1] in ['accounting', 'admin']:
                    st.session_state.logged_in = True
                    st.session_state.username = user_data[0]
                    st.session_state.role = user_data[1]
                    st.rerun()
                else:
                    st.error("Access denied. Accounting role required.")

# Main dashboard
else:
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Accounting Dashboard")
    with col2:
        st.write(f"**User:** {st.session_state.username}")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Load data
    df = load_work_orders()
    
    if df.empty:
        st.warning("No work orders found. Create some work orders first using the warehouse app.")
        st.stop()

    # Parse JSON fields for analysis
    df['date_created'] = pd.to_datetime(df['date_created'])
    df['date_only'] = df['date_created'].dt.date
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    min_date = df['date_only'].min()
    max_date = df['date_only'].max()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Status filter
    all_statuses = df['status'].unique()
    selected_statuses = st.sidebar.multiselect(
        "Status",
        options=all_statuses,
        default=all_statuses
    )
    
    # Customer filter
    all_customers = df['customer_name'].unique()
    selected_customers = st.sidebar.multiselect(
        "Customers",
        options=all_customers,
        default=all_customers
    )
    
    # Apply filters
    if len(date_range) == 2:
        mask = (df['date_only'] >= date_range[0]) & (df['date_only'] <= date_range[1])
        filtered_df = df[mask]
    else:
        filtered_df = df
    
    filtered_df = filtered_df[
        (filtered_df['status'].isin(selected_statuses)) &
        (filtered_df['customer_name'].isin(selected_customers))
    ]

    # Metrics row
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = len(filtered_df)
        st.metric("Total Orders", total_orders)
    
    with col2:
        pending_orders = len(filtered_df[filtered_df['status'] == 'pending'])
        st.metric("Pending", pending_orders)
    
    with col3:
        completed_orders = len(filtered_df[filtered_df['status'] == 'completed'])
        st.metric("Completed", completed_orders)
    
    with col4:
        synced_orders = len(filtered_df[filtered_df['veracore_synced'] == 1])
        st.metric("Synced to Veracore", synced_orders)

    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        # Orders by date
        daily_orders = filtered_df.groupby('date_only').size().reset_index(name='count')
        if not daily_orders.empty:
            fig = px.bar(
                daily_orders, 
                x='date_only', 
                y='count',
                title="Orders by Date",
                labels={'date_only': 'Date', 'count': 'Number of Orders'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Status distribution
        status_counts = filtered_df['status'].value_counts()
        if not status_counts.empty:
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Work orders table
    st.subheader("📋 Work Orders")
    
    # Search and sort options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search orders...", placeholder="Search by customer, reference, or barcode")
    with col2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Customer", "Status"])
    with col3:
        show_details = st.checkbox("Show Details", value=False)
    
    # Apply search
    if search_term:
        search_mask = (
            filtered_df['customer_name'].str.contains(search_term, case=False, na=False) |
            filtered_df['reference_numbers'].str.contains(search_term, case=False, na=False) |
            filtered_df['barcode_data'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    # Apply sorting
    if sort_by == "Date (Newest)":
        filtered_df = filtered_df.sort_values('date_created', ascending=False)
    elif sort_by == "Date (Oldest)":
        filtered_df = filtered_df.sort_values('date_created', ascending=True)
    elif sort_by == "Customer":
        filtered_df = filtered_df.sort_values('customer_name')
    elif sort_by == "Status":
        filtered_df = filtered_df.sort_values('status')

    # Display work orders
    for idx, order in filtered_df.iterrows():
        # Parse JSON data
        reference_numbers = json.loads(order['reference_numbers']) if order['reference_numbers'] else []
        fee_data = json.loads(order['fee_data']) if order['fee_data'] else []
        
        # Status indicator
        status_color = {
            'pending': '🟡',
            'processing': '🔵',
            'completed': '🟢',
            'billed': '✅',
            'cancelled': '🔴'
        }.get(order['status'], '⚪')
        
        sync_indicator = '🔄' if order['veracore_synced'] else '⏳'
        
        with st.expander(
            f"{status_color} WO #{order['id']} - {order['customer_name']} - {order['date_created'].strftime('%Y-%m-%d %H:%M')} {sync_indicator}"
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Customer:** {order['customer_name']} ({order['customer_id']})")
                st.write(f"**References:** {', '.join(reference_numbers)}")
                st.write(f"**Status:** {order['status'].title()}")
                st.write(f"**Created By:** {order['created_by']}")
                st.write(f"**Barcode:** `{order['barcode_data']}`")
                if order['notes']:
                    st.write(f"**Notes:** {order['notes']}")
            
            with col2:
                st.write("**Fees:**")
                for fee in fee_data:
                    st.write(f"• {fee['type']} (Qty: {fee['quantity']})")
                
                st.write(f"**Veracore Synced:** {'Yes' if order['veracore_synced'] else 'No'}")
                if order['sync_date']:
                    sync_date = datetime.fromisoformat(order['sync_date'])
                    st.write(f"**Last Sync:** {sync_date.strftime('%Y-%m-%d %H:%M')}")
            
            if show_details:
                # Status update section
                st.subheader("Update Status")
                new_status = st.selectbox(
                    "Change Status",
                    options=['pending', 'processing', 'completed', 'billed', 'cancelled'],
                    index=['pending', 'processing', 'completed', 'billed', 'cancelled'].index(order['status']),
                    key=f"status_{order['id']}"
                )
                
                if st.button(f"Update Status", key=f"update_{order['id']}"):
                    update_work_order_status(order['id'], new_status)
                    st.success(f"Status updated to {new_status}")
                    st.rerun()

    # Summary stats at bottom
    if not filtered_df.empty:
        st.subheader("📊 Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            # Customer breakdown
            customer_summary = filtered_df['customer_name'].value_counts().head(5)
            st.write("**Top Customers:**")
            for customer, count in customer_summary.items():
                st.write(f"• {customer}: {count} orders")
        
        with col2:
            # Fee analysis (if we wanted to get fancy)
            st.write("**Recent Activity:**")
            recent_orders = filtered_df.head(5)
            for _, order in recent_orders.iterrows():
                st.write(f"• WO #{order['id']} - {order['customer_name']} - {order['status']}")

    # Export functionality
    st.subheader("📤 Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export to CSV"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"work_orders_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📋 Export Summary"):
            summary_data = {
                'Total Orders': len(filtered_df),
                'Pending': len(filtered_df[filtered_df['status'] == 'pending']),
                'Completed': len(filtered_df[filtered_df['status'] == 'completed']),
                'Synced': len(filtered_df[filtered_df['veracore_synced'] == 1])
            }
            st.json(summary_data)
    
    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()