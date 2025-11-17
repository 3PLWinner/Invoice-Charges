import streamlit as st
import pandas as pd
from datetime import datetime
import os


excel_file = 'master_work_orders.xlsx'
upload_dir = 'uploads'
os.makedirs(upload_dir, exist_ok=True)

if not os.path.exists(excel_file):
    df_init = pd.DataFrame(columns=[
        "Timestamp", "Work Order ID", "Reference Number", "Department", "Customer", "SPD/LTL", "Fee Type", "Quantity", "Notes", "File Link"
    ])
    df_init.to_excel(excel_file, index=False)

df = pd.read_excel(excel_file)

CUSTOMERS = [
    'CUS530', 'ICL103', 'CUS534','CUS304','CUS539','CUS554','CUS524',
    'CUS516','CUS547','CUS544','CUS514','CUS464','CUS478','CUS490',
    'CUS536','CUS491','CUS205','CUS392','CUS528','CUS540','CUS496',
    'HARPRJ','CUS518','CUS487','CUS545','CUS532','CUS479','CUS429',
    'CUS494','ICL101','CUS541','CUS320','CUS538','CUS410','CUS355',
    'CUS327','SPK101','CUS537','CUS359','CUS548','CUS344','CUS260',
    'CUS529','CUS227','CUS371','CUS297','CUS373','CUS250','CUS237',
    'CUS277','CUS546','CUS370','CUS542','CUS430','CUS456','CUS527',
    'CUS453','TTN101','TTN102','CUS552','CUS533','CUS360','SPK102',
    'CUS535','CUS253'
]

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

RECEIVING_FEES = [
        "RCV - Master Carton Labels",
        "RCV - Removals and Inspections",
        "RCV - Shrink Wrap",
        "RCV - Sorting",
        "RCV - FCL 20G Loose Loaded",
        "RCV - FCL 40G Loose Loaded",
        "RCV - FCL 40HQ Loose Loaded",
        "RCV - Wooden Pallet",
        "RCV - Per Pallet",
        "RCV - Single Package",
        "RCV - Freight Inbound Charges",
        "RCV - UNI Sorting",
        "RCV - FCL 53HQ Loose Loaded",
        "Pallet Out",
    ]

SHIPPING_FEES = [
    "PPF - Insert",
    "GAF - Administrative Fee",
    "FAP - Amazon FBA Shipping Preparation",
    "FAP - Amazon FBA Product Labeling",
    "PP - Box 24x24x24",
    "PP - Box 18x18x12",
    "PP - Box 12x12x12",
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
    "PPF - Quoted Freight Shipment",
    "PP - Box - 18x14x12",
    "PPF - UNI Business to Business Order",
    "FAP - Pallet Labels",
    "Pallet Out",
    "PPF - Quoted Ground Shipment",
    "FAP - Shipping Labels",
    "PP - Straps",
    "PPF - Unshipped Pallet Storage",
    "PPF - Overtime Labor",
    "Master Carton Out",
    "Picked Items",
    "Additional Items",
    "PPF - Truck Seals",
    "PP - Box 16x12x6",
    "PP - Plastic Toppers",
    "PP - Box 12x8x6",
    "PP - Document Holder",
    "PP - Box 12x6x4"
]


CROSSDOCK_FEES = [
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
    "Pallet Out",
    "Master Carton Out"
]


#Helper Functions
def generate_wo_id(df):
    if df.empty:
        return "WO-000001"
    else:
        last_id = df['Work Order ID'].iloc[-1]
        last_num = int(last_id.split('-')[1])
        new_num = last_num + 1
        return f"WO-{new_num:06d}"

def handle_file_upload(uploaded_file):
    if uploaded_file is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(upload_dir, f"{timestamp}_{uploaded_file.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return ""

def save_rows(rows):
    df = pd.read_excel(excel_file)
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    df.to_excel(excel_file, index=False)


# Initialize session state for all fee types
if "receiving_fees" not in st.session_state:
    st.session_state.receiving_fees = []
if "shipping_fees" not in st.session_state:
    st.session_state.shipping_fees = []
if "crossdock_fees" not in st.session_state:
    st.session_state.crossdock_fees = []
if "work_order_notes" not in st.session_state:
    st.session_state.work_order_notes = ""

#UI
st.title("Digital Work Order Form")

speech_event = st.query_params.get("speech_event")

st.markdown("""
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === "st_speech") {
        const key = event.data.key;
        const text = event.data.text;

        // Update Streamlit component value
        window.parent.postMessage(
            { type: "streamlit:componentValue", id: key, data: text },
            "*"
        );
    }
});
</script>
""", unsafe_allow_html=True)


st.subheader("Work Order Details")

customer = st.selectbox("Customer", CUSTOMERS)
reference_number = st.text_input("Reference Number (required)")
uploaded_file = st.file_uploader("Upload Supporting Documents (optional)")
file_path = handle_file_upload(uploaded_file)
carrier_type = st.selectbox("SPD or LTL", ["SPD","LTL"])
work_order_id = generate_wo_id(df)
st.info(f"Work Order ID automatically assigned: **{work_order_id}**")

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["Receiving", "Shipping", "Crossdock"])


#RECEIVING TAB
with tab1:
    st.header("Receiving Work Order")

    fee_type = st.selectbox("Select Fee", RECEIVING_FEES, key="recv_fee_select")
    quantity = st.number_input("Quantity", min_value=1, key="recv_qty")

    if st.button("Add Receiving Fee"):
        st.session_state.receiving_fees.append(
            {"department": "Receiving", "fee": fee_type, "quantity": quantity}
        )
        st.success("Fee Added!")

    st.markdown("---")
    st.header("Fees added to this work order")

    if len(st.session_state.receiving_fees) > 0:
        st.table(st.session_state.receiving_fees)
    else:
        st.info("No fees added yet.")



#SHIPPING TAB
with tab2:
    st.header("Shipping Work Order")

    fee_type = st.selectbox("Select Fee", SHIPPING_FEES, key="ship_fee_select")
    quantity = st.number_input("Quantity", min_value=1, key="ship_qty")

    if st.button("Add Shipping Fee"):
        st.session_state.shipping_fees.append(
            {"department": "Shipping", "fee": fee_type, "quantity": quantity}
        )
        st.success("Fee Added!")
    
    st.markdown("---")
    st.header("Fees added to this work order")

    if len(st.session_state.shipping_fees) > 0:
        st.table(st.session_state.shipping_fees)
    else:
        st.info("No fees added yet.")


#CROSSDOCK TAB
with tab3:
    st.header("Crossdock Work Order")

    fee_type = st.selectbox("Select Fee", CROSSDOCK_FEES, key="crossdock_fee_select")
    quantity = st.number_input("Quantity", min_value=1, key="crossdock_qty")

    if st.button("Add Crossdock Fee"):
        st.session_state.crossdock_fees.append(
            {"department": "Crossdock", "fee": fee_type, "quantity": quantity}
        )
        st.success("Fee Added!")
    
    
    st.markdown("---")
    st.header("Fees added to this work order")

    if len(st.session_state.crossdock_fees) > 0:
        st.table(st.session_state.crossdock_fees)
    else:
        st.info("No fees added yet.")



st.subheader("Work Order Notes (applies to entire work order)")

if "work_order_notes" not in st.session_state:
    st.session_state["work_order_notes"] = ""

notes_box = st.text_area(
    "Notes:",
    value=st.session_state.work_order_notes,
    key="notes_area",
    height=150
)

st.session_state.work_order_notes = notes_box

st.markdown("""
<button id="micBtn" style="padding: 10px 15px; font-size: 16px;">
🎤 Dictate Notes
</button>
<p id="status"></p>

<script>
var recognizing = false;
var recognition = new (window.SpeechRecognition ||
                       window.webkitSpeechRecognition)();

recognition.continuous = true;
recognition.interimResults = true;

document.getElementById("micBtn").onclick = function() {
    if (recognizing) {
        recognition.stop();
        recognizing = false;
        document.getElementById("status").innerHTML = "Stopped.";
    } else {
        recognition.start();
        recognizing = true;
        document.getElementById("status").innerHTML = "Listening...";
    }
};

recognition.onresult = function(event) {
    let text = "";
    for (var i = 0; i < event.results.length; ++i) {
        text += event.results[i][0].transcript;
    }

    const textarea = document.querySelector("textarea[data-testid='stTextArea']");
    textarea.value = text;

    textarea.dispatchEvent(new Event("input", { bubbles: true }));
};
</script>
""", unsafe_allow_html=True)

# Collect all fees from all tabs
all_fees = st.session_state.receiving_fees + st.session_state.shipping_fees + st.session_state.crossdock_fees

if st.button("Submit Work Order"):
    if reference_number.strip() == "":
        st.error("Reference Number is required.")
    elif len(all_fees) == 0:
        st.error("At least one fee must be added to the work order.")
    else:
        rows = []
        for fee in all_fees:
            rows.append({
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Work Order ID": work_order_id,
                "Reference Number": reference_number,
                "Department": fee["department"],
                "Customer": customer,
                "SPD/LTL": carrier_type,
                "Fee Type": fee["fee"],
                "Quantity": fee["quantity"],
                "Notes": st.session_state.work_order_notes,
                "File Link": file_path
            })
        save_rows(rows)
        st.success(f"Work Order {work_order_id} submitted successfully!")
        # Clear all fees after successful submission
        st.session_state.receiving_fees = []
        st.session_state.shipping_fees = []
        st.session_state.crossdock_fees = []

