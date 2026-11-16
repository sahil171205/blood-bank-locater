
import streamlit as st
import sqlite3
import pandas as pd
import re

# ---------- PAGE CONFIG ----------
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

# Donor -> Compatible recipients (Red Blood Cells)
BLOOD_COMPATIBILITY = {
    "O+": ["O+", "A+", "B+", "AB+"],
    "O-": BLOOD_GROUPS,
    "A+": ["A+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "AB+": ["AB+"],
    "AB-": ["AB-", "AB+"]
}

# ---------- DATABASE ----------
def connect_db():
    return sqlite3.connect(
        DB,
        check_same_thread=False
    )


def init_db():
    with connect_db() as con:
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
                units INTEGER NOT NULL,
                FOREIGN KEY(bank_id) REFERENCES banks(id)
            )
        """)


def get_data(table):
    allowed = ["donors", "banks", "stock"]

    if table not in allowed:
        return pd.DataFrame()

    with connect_db() as con:
        return pd.read_sql_query(
            f"SELECT * FROM {table}", con
        )


def add_donor(name, age, group, city, phone):
    with connect_db() as con:
        con.execute("""
            INSERT INTO donors
            (name, age, blood_group, city, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (name, age, group, city, phone))


def add_bank(name, city, address, phone, lat, lon):
    with connect_db() as con:
        con.execute("""
            INSERT INTO banks
            (name, city, address, phone, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, city, address, phone, lat, lon))


def save_stock(bank_id, group, units):
    with connect_db() as con:
        existing = con.execute("""
            SELECT id FROM stock
            WHERE bank_id = ? AND blood_group = ?
        """, (bank_id, group)).fetchone()

        if existing:
            con.execute("""
                UPDATE stock
                SET units = ?
                WHERE id = ?
            """, (units, existing[0]))
        else:
            con.execute("""
                INSERT INTO stock
                (bank_id, blood_group, units)
                VALUES (?, ?, ?)
            """, (bank_id, group, units))


def valid_phone(phone):
    return bool(re.fullmatch(r"[6-9]\d{9}", phone))


def compatible_donors(recipient_group):
    return [
        donor for donor, recipients
        in BLOOD_COMPATIBILITY.items()
        if recipient_group in recipients
    ]


init_db()

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
.stApp {
    background: #080b12;
    color: white;
}

h1, h2, h3 {
    color: #ff354b !important;
}

p, label {
    color: #f2f2f2;
}

[data-testid="stSidebar"] {
    background: #141923;
}

.stButton > button {
    background: linear-gradient(
        90deg, #a50020, #ff304f
    );
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #ff5369;
    color: white;
}

[data-testid="stMetric"] {
    background: #181d29;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #ab2338;
}

div[data-testid="stForm"] {
    border: 1px solid #742539;
    border-radius: 12px;
    padding: 20px;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.title("🩸 BLOOD BANK LOCATOR")
st.sidebar.caption("Find Blood. Save Lives.")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Find Blood",
        "Register Donor",
        "Blood Banks",
        "Register Blood Bank",
        "Blood Stock",
        "Blood Compatibility",
        "About"
    ]
)

st.sidebar.divider()
st.sidebar.info(
    "A college project developed using "
    "Python, Streamlit and SQLite."
)

# ---------- DASHBOARD ----------
if page == "Dashboard":

    st.title("🩸 Blood Bank Locator")
    st.subheader("Every Drop Counts. Every Life Matters.")

    donors = get_data("donors")
    banks = get_data("banks")
    stock = get_data("stock")

    c1, c2, c3 = st.columns(3)

    c1.metric("Registered Donors", len(donors))
    c2.metric("Blood Banks", len(banks))
    c3.metric(
        "Blood Units",
        int(stock["units"].sum())
        if not stock.empty else 0
    )

    st.divider()

    st.subheader("Welcome to Blood Bank Locator")

    st.write("""
    Blood Bank Locator is a web-based application
    designed to help users search for registered
    blood donors and blood banks.

    The system provides blood group compatibility
    information and available blood stock records.
    """)

    st.warning(
        "This is a demonstration project. "
        "Blood availability and donor eligibility "
        "must be confirmed with a hospital."
    )

# ---------- FIND BLOOD ----------
elif page == "Find Blood":

    st.title("🔍 Find Blood Donors")
    st.caption(
        "Search donors using recipient blood group and city"
    )

    donors = get_data("donors")

    recipient_group = st.selectbox(
        "Select Patient Blood Group",
        BLOOD_GROUPS
    )

    city = st.text_input(
        "Enter City",
        placeholder="Example: Kagal"
    )

    include_compatible = st.checkbox(
        "Include Compatible Blood Groups",
        value=True
    )

    if st.button(
        "SEARCH DONORS",
        use_container_width=True
    ):

        if not city.strip():
            st.warning("Please enter your city.")

        elif donors.empty:
            st.warning("No donors registered yet.")

        else:
            result = donors.copy()

            result["blood_group"] = (
                result["blood_group"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            result["city"] = (
                result["city"]
                .astype(str)
                .str.strip()
            )

            if include_compatible:
                groups = compatible_donors(
                    recipient_group
                )
            else:
                groups = [recipient_group]

            result = result[
                result["blood_group"].isin(groups)
                &
                result["city"].str.contains(
                    re.escape(city.strip()),
                    case=False,
                    na=False,
                    regex=True
                )
            ]

            st.info(
                "Compatible donor groups: "
                + ", ".join(groups)
            )

            if result.empty:
                st.warning(
                    "No matching registered donors found."
                )
            else:
                st.success(
                    f"{len(result)} matching donor(s) found!"
                )

                st.dataframe(
                    result[
                        [
                            "name",
                            "age",
                            "blood_group",
                            "city"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )

                st.caption(
                    "Donor contact details are not "
                    "published publicly in this demo."
                )

    st.warning(
        "Compatibility is for red blood cells only. "
        "Hospital testing and crossmatching are required."
    )

# ---------- REGISTER DONOR ----------
elif page == "Register Donor":

    st.title("❤️ Register as Blood Donor")

    with st.form("donor_form"):

        name = st.text_input("Full Name")

        age = st.number_input(
            "Age",
            min_value=18,
            max_value=65,
            value=21
        )

        group = st.selectbox(
            "Blood Group",
            BLOOD_GROUPS
        )

        city = st.text_input("City")

        phone = st.text_input("Mobile Number")

        consent = st.checkbox(
            "I agree to store my details "
            "for this demonstration."
        )

        submitted = st.form_submit_button(
            "REGISTER DONOR",
            use_container_width=True
        )

        if submitted:

            if not name.strip() or not city.strip():
                st.error("Please fill all required fields.")

            elif not valid_phone(phone):
                st.error(
                    "Enter a valid 10-digit mobile number."
                )

            elif not consent:
                st.error(
                    "Please provide consent."
                )

            else:
                add_donor(
                    name.strip(),
                    age,
                    group,
                    city.strip(),
                    phone
                )

                st.success(
                    "Donor registered successfully!"
                )

# ---------- BLOOD BANKS ----------
elif page == "Blood Banks":

    st.title("🏥 Find Blood Banks")

    banks = get_data("banks")

    city = st.text_input(
        "Search Blood Banks by City"
    )

    if banks.empty:
        st.warning("No blood banks registered.")

    else:
        result = banks.copy()

        if city.strip():
            result = result[
                result["city"].str.contains(
                    re.escape(city.strip()),
                    case=False,
                    na=False
                )
            ]

        if result.empty:
            st.warning("No blood banks found.")

        else:
            st.dataframe(
                result[
                    [
                        "name",
                        "city",
                        "address",
                        "phone"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📍 Blood Bank Locations")

            map_data = result[
                ["latitude", "longitude"]
            ].dropna()

            if not map_data.empty:
                st.map(map_data)

# ---------- REGISTER BLOOD BANK ----------
elif page == "Register Blood Bank":

    st.title("🏥 Register Blood Bank")

    st.info(
        "Demo registration only. "
        "Production systems require verified "
        "blood bank administrators."
    )

    with st.form("bank_form"):

        name = st.text_input("Blood Bank Name")
        city = st.text_input("City")
        address = st.text_area("Full Address")
        phone = st.text_input("Contact Number")

        lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=16.7,
            format="%.6f"
        )

        lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=74.2,
            format="%.6f"
        )

        submitted = st.form_submit_button(
            "ADD BLOOD BANK",
            use_container_width=True
        )

        if submitted:

            if not all([
                name.strip(),
                city.strip(),
                address.strip(),
                phone.strip()
            ]):
                st.error("Fill all fields.")

            else:
                add_bank(
                    name.strip(),
                    city.strip(),
                    address.strip(),
                    phone.strip(),
                    lat,
                    lon
                )

                st.success(
                    "Blood bank registered successfully!"
                )

# ---------- BLOOD STOCK ----------
elif page == "Blood Stock":

    st.title("🩸 Blood Stock Management")

    banks = get_data("banks")

    if banks.empty:
        st.warning(
            "Register a blood bank first."
        )

    else:
        bank_options = {
            f"{row['name']} - {row['city']} "
            f"(ID: {row['id']})": int(row["id"])
            for _, row in banks.iterrows()
        }

        with st.form("stock_form"):

            selected_bank = st.selectbox(
                "Select Blood Bank",
                list(bank_options.keys())
            )

            group = st.selectbox(
                "Blood Group",
                BLOOD_GROUPS
            )

            units = st.number_input(
                "Available Units",
                min_value=0,
                step=1
            )

            submitted = st.form_submit_button(
                "SAVE STOCK",
                use_container_width=True
            )

            if submitted:
                save_stock(
                    bank_options[selected_bank],
                    group,
                    units
                )

                st.success(
                    "Blood stock updated!"
                )

        st.divider()

        stock = get_data("stock")

        if not stock.empty:

            merged = stock.merge(
                banks[["id", "name", "city"]],
                left_on="bank_id",
                right_on="id",
                how="left"
            )

            st.subheader("Available Blood Stock")

            st.dataframe(
                merged[
                    [
                        "name",
                        "city",
                        "blood_group",
                        "units"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

# ---------- BLOOD COMPATIBILITY ----------
elif page == "Blood Compatibility":

    st.title("🧬 Blood Group Compatibility")

    st.caption(
        "Red Blood Cell Donation Compatibility"
    )

    donor_group = st.selectbox(
        "Select Donor Blood Group",
        BLOOD_GROUPS
    )

    recipients = BLOOD_COMPATIBILITY[
        donor_group
    ]

    st.success(
        f"{donor_group} can donate red blood cells to: "
        + ", ".join(recipients)
    )

    st.subheader("Compatible Recipient Groups")

    cols = st.columns(4)

    for i, group in enumerate(BLOOD_GROUPS):

        with cols[i % 4]:

            if group in recipients:
                st.success(f"✅ {group}")
            else:
                st.error(f"❌ {group}")

    st.divider()

    recipient = st.selectbox(
        "Select Recipient Blood Group",
        BLOOD_GROUPS,
        key="recipient_check"
    )

    donor_groups = compatible_donors(recipient)

    st.info(
        "Compatible donor groups: "
        + ", ".join(donor_groups)
    )

    st.warning(
        "This chart applies to red blood cells, "
        "not plasma or platelets. A hospital must "
        "verify compatibility before transfusion."
    )

# ---------- ABOUT ----------
elif page == "About":

    st.title("ℹ️ About This Project")

    st.subheader("Blood Bank Locator")

    st.write("""
    Blood Bank Locator is a Python-based
    web application developed as a college project.

    Technologies Used:
    - Python
    - Streamlit
    - SQLite
    - Pandas
    - HTML / CSS

    Main Features:
    - Donor Registration
    - Blood Donor Search
    - Blood Bank Registration
    - Blood Bank Location Map
    - Blood Stock Management
    - Blood Group Compatibility
    - Dashboard
    """)

    st.subheader("Project Team")

    st.write("""
    Ritesh K. Kumbhar - 98

    Sahil P. Gosavi - 97

    Rugved V. Patil - 102

    Omkar P. Shivgand - 95
    """)

    st.caption(
        "Department of Artificial Intelligence "
        "and Machine Learning"
    )
