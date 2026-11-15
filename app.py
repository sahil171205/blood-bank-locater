
import streamlit as st
import sqlite3
import pandas as pd
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Blood Bank Locator",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB = "blood_bank.db"

BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-",
    "O+", "O-", "AB+", "AB-"
]

# ---------------- DATABASE ----------------
def connect_db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    with connect_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bank_id INTEGER NOT NULL,
                blood_group TEXT NOT NULL,
                units INTEGER NOT NULL DEFAULT 0,
                UNIQUE(bank_id, blood_group),
                FOREIGN KEY(bank_id) REFERENCES banks(id)
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                blood_group TEXT NOT NULL,
                city TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                blood_group TEXT NOT NULL,
                city TEXT NOT NULL,
                units INTEGER NOT NULL,
                contact TEXT NOT NULL,
                status TEXT DEFAULT 'Pending'
            )
        """)

init_db()

def read_data(query, params=()):
    with connect_db() as con:
        return pd.read_sql_query(query, con, params=params)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.stApp {
    background: #08090d;
    color: #f5f5f5;
}
[data-testid="stSidebar"] {
    background: #111218;
    border-right: 1px solid #332027;
}
h1, h2, h3 {
    color: #ff334f !important;
}
p, label, span {
    color: #eeeeee;
}
div.stButton > button {
    background: linear-gradient(90deg,#b90028,#ff1744);
    color: white;
    border: none;
    border-radius: 9px;
    font-weight: bold;
    min-height: 42px;
}
div.stButton > button:hover {
    background: #ff3659;
    color: white;
    border: 1px solid #ff8297;
}
div[data-testid="stMetric"] {
    background: #171820;
    border: 1px solid #49202d;
    padding: 18px;
    border-radius: 12px;
}
div[data-testid="stForm"] {
    background: #12131a;
    border: 1px solid #49202d;
    padding: 18px;
    border-radius: 12px;
}
input, textarea {
    background: #20212a !important;
    color: white !important;
}
.blood-hero {
    background: linear-gradient(120deg,#220711,#111218,#330817);
    padding: 30px;
    border: 1px solid #8c1635;
    border-radius: 18px;
    margin-bottom: 22px;
}
.blood-hero h1 {
    font-size: 36px;
    margin-bottom: 5px;
}
.small-text {
    color: #bbbbc5;
    font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("# 🩸 BLOOD CARE")
st.sidebar.caption("BLOOD BANK LOCATOR SYSTEM")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Home",
        "Find Blood",
        "Blood Bank Locator",
        "Donor Registration",
        "Blood Request",
        "Admin Dashboard"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("SAVE BLOOD • SAVE LIVES")

# ---------------- HOME ----------------
if page == "Home":

    banks = read_data("SELECT * FROM banks")
    donors = read_data("SELECT * FROM donors")
    requests = read_data("SELECT * FROM requests")

    stock = read_data("SELECT * FROM stock")

    total_units = int(stock["units"].sum()) if not stock.empty else 0

    st.markdown("""
    <div class="blood-hero">
        <h1>🩸 BLOOD BANK LOCATOR</h1>
        <p>Connecting Blood Donors, Blood Banks and People in Need.</p>
        <p class="small-text">A platform designed to make blood search easier.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Blood Banks", len(banks))
    c2.metric("Registered Donors", len(donors))
    c3.metric("Blood Units Listed", total_units)
    c4.metric("Blood Requests", len(requests))

    st.markdown("## ❤️ Welcome to Blood Care")

    a, b = st.columns(2)

    with a:
        st.info("🔍 Find blood banks by city and blood group.")
        st.info("📍 View registered blood bank locations.")

    with b:
        st.info("👤 Register as a blood donor.")
        st.info("🚨 Submit an emergency blood request.")

    st.warning(
        "This is a demonstration project. "
        "Listed stock is not real-time verified. "
        "Always contact the blood bank before visiting."
    )

# ---------------- FIND BLOOD ----------------
elif page == "Find Blood":

    st.title("🔍 Find Available Blood")

    banks = read_data("""
        SELECT banks.name, banks.city, banks.address,
               banks.phone, stock.blood_group, stock.units
        FROM banks
        JOIN stock ON banks.id = stock.bank_id
        WHERE stock.units > 0
    """)

    col1, col2 = st.columns(2)

    with col1:
        group = st.selectbox("Select Blood Group", BLOOD_GROUPS)

    with col2:
        city = st.text_input("Enter City")

    if st.button("SEARCH BLOOD", use_container_width=True):

        if city.strip():
            result = banks[
                (banks["blood_group"] == group) &
                (banks["city"].str.lower() == city.strip().lower())
            ]

            if not result.empty:
                st.success(f"{len(result)} matching listing(s) found.")

                for _, item in result.iterrows():
                    with st.container(border=True):
                        st.subheader("🏥 " + item["name"])
                        st.write("📍", item["address"])
                        st.write("City:", item["city"])
                        st.write("Blood Group:", item["blood_group"])
                        st.write("Listed Units:", int(item["units"]))
                        st.write("📞", item["phone"])
            else:
                st.error("No matching listing found.")
        else:
            st.warning("Please enter your city.")

# ---------------- BLOOD BANK LOCATOR ----------------
elif page == "Blood Bank Locator":

    st.title("📍 Blood Bank Locator")
    st.caption("Find registered blood banks by
