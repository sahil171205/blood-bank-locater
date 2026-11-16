
import streamlit as st
import pandas as pd
import re
from supabase import create_client

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Blood Bank Locator",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

BLOOD_GROUPS = [
    "A+", "A-", "B+", "B-",
    "O+", "O-", "AB+", "AB-"
]

# Red blood cell donor -> compatible recipients
BLOOD_COMPATIBILITY = {
    "O+": ["O+", "A+", "B+", "AB+"],
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "AB+": ["AB+"],
    "AB-": ["AB-", "AB+"]
}

# ---------------- SUPABASE CONNECTION ----------------
@st.cache_resource
def get_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase()
except Exception as e:
    st.error("Database connection failed. Check Streamlit Secrets.")
    st.stop()


# ---------------- DATABASE FUNCTIONS ----------------
def get_data(table):
    try:
        result = supabase.table(table).select("*").execute()
        return pd.DataFrame(result.data or [])
    except Exception as e:
        st.error(f"Unable to load {table}: {e}")
        return pd.DataFrame()


def insert_data(table, data):
    try:
        supabase.table(table).insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False


# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.stApp {
    background: #08090d;
    color: #f5f5f5;
}
[data-testid="stSidebar"] {
    background: #111218;
    border-right: 1px solid #55202e;
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

    donors = get_data("donors")
    requests = get_data("blood_requests")
    banks = get_data("banks")
    stock = get_data("stock")

    total_units = (
        int(pd.to_numeric(stock["units"], errors="coerce").fillna(0).sum())
        if not stock.empty and "units" in stock.columns else 0
    )

    st.markdown("""
    <div class="blood-hero">
        <h1>🩸 BLOOD BANK LOCATOR</h1>
        <p>Connecting Blood Donors, Blood Banks and People in Need.</p>
        <p>Every Drop Counts. Every Life Matters.</p>
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
        st.info("🔍 Find blood donors by city and blood group.")
        st.info("📍 View registered blood bank locations.")

    with b:
        st.info("👤 Register as a blood donor.")
        st.info("🚨 Submit an emergency blood request.")

    st.warning(
        "Demonstration project. Stock availability is not "
        "real-time verified. Always contact the blood bank."
    )


# ---------------- FIND BLOOD ----------------
elif page == "Find Blood":

    st.title("🔍 Find Blood Donors")
    st.caption(
        "Search compatible red blood cell donors "
        "by patient blood group and city"
    )

    group = st.selectbox(
        "Select Patient Blood Group",
        BLOOD_GROUPS
    )

    city = st.text_input(
        "Enter City",
        placeholder="Example: Kagal"
    )

    if st.button("SEARCH DONORS", use_container_width=True):

        if not city.strip():
            st.warning("Please enter your city.")

        else:
            try:
                response = (
                    supabase.table("donors")
                    .select("*")
                    .execute()
                )

                donors = pd.DataFrame(response.data or [])

                if donors.empty:
                    st.warning("No donors registered yet.")

                else:
                    donors["blood_group_clean"] = (
                        donors["blood_group"]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                    )

                    donors["city_clean"] = (
                        donors["city"]
                        .astype(str)
                        .str.strip()
                        .str.casefold()
                    )

                    # Find compatible donor blood groups
                    compatible_groups = [
                        donor_group
                        for donor_group, recipients
                        in BLOOD_COMPATIBILITY.items()
                        if group.upper() in recipients
                    ]

                    result = donors[
                        (
                            donors["blood_group_clean"]
                            .isin(compatible_groups)
                        )
                        &
                        (
                            donors["city_clean"]
                            == city.strip().casefold()
                        )
                    ]

                    st.info(
                        "Compatible donor groups: "
                        + ", ".join(compatible_groups)
                    )

                    if not result.empty:

                        st.success(
                            f"❤️ {len(result)} Donor(s) Found!"
                        )

                        for _, donor in result.iterrows():

                            with st.container(border=True):

                                st.subheader(
                                    "👤 " + str(donor["name"])
                                )

                                col1, col2 = st.columns(2)

                                with col1:
                                    st.write(
                                        "🩸 Blood Group:",
                                        donor["blood_group"]
                                    )
                                    st.write(
                                        "📍 City:",
                                        donor["city"]
                                    )

                                with col2:
                                    st.write(
                                        "🎂 Age:",
                                        donor["age"]
                                    )
                                    st.write(
                                        "📞 Contact:",
                                        donor["phone"]
                                    )

                    else:
                        st.error("No matching donors found.")
                        st.info(
                            "No registered compatible donors "
                            "found in this city."
                        )

            except Exception as e:
                st.error(f"Donor search failed: {e}")

    st.caption(
        "Compatibility applies to red blood cells only. "
        "Hospital crossmatching is required."
    )


# ---------------- BLOOD BANK LOCATOR ----------------
elif page == "Blood Bank Locator":

    st.title("📍 Blood Bank Locator")
    st.caption("Find registered blood bank locations")

    banks = get_data("banks")

    if banks.empty:
        st.info("No blood banks registered yet.")

    else:
        for _, bank in banks.iterrows():

            with st.container(border=True):

                st.subheader("🏥 " + str(bank["name"]))
                st.write("📍", bank["address"])
                st.write("City:", bank["city"])
                st.write("Phone:", bank["phone"])

                latitude = bank.get("latitude", 0)
                longitude = bank.get("longitude", 0)

                if pd.notna(latitude) and pd.notna(longitude):
                    if float(latitude) != 0 and float(longitude) != 0:
                        st.link_button(
                            "Open in Google Maps",
                            f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
                        )

        map_data = banks.copy()

        map_data["latitude"] = pd.to_numeric(
            map_data["latitude"], errors="coerce"
        )
        map_data["longitude"] = pd.to_numeric(
            map_data["longitude"], errors="coerce"
        )

        map_data = map_data.dropna(
            subset=["latitude", "longitude"]
        )

        map_data = map_data[
            (map_data["latitude"] != 0) &
            (map_data["longitude"] != 0)
        ]

        if not map_data.empty:
            st.subheader("Blood Bank Map")

            st.map(
                map_data.rename(
                    columns={
                        "latitude": "lat",
                        "longitude": "lon"
                    }
                )
            )


# ---------------- DONOR REGISTRATION ----------------
elif page == "Donor Registration":

    st.title("❤️ Blood Donor Registration")
    st.write("Register yourself as a blood donor.")

    with st.form("donor_form"):

        name = st.text_input("Full Name")

        age = st.number_input(
            "Age",
            min_value=18,
            max_value=65,
            value=18
        )

        phone = st.text_input(
            "Mobile Number",
            max_chars=10
        )

        group = st.selectbox(
            "Blood Group",
            BLOOD_GROUPS
        )

        city = st.text_input("City")

        agree = st.checkbox(
            "I agree to be contacted about blood donation."
        )

        submit = st.form_submit_button(
            "REGISTER DONOR",
            use_container_width=True
        )

    if submit:

        if not name.strip() or not city.strip():
            st.error("Please enter your name and city.")

        elif not re.fullmatch(r"[6-9][0-9]{9}", phone.strip()):
            st.error("Enter a valid 10-digit Indian mobile number.")

        elif not agree:
            st.warning("Please provide your consent.")

        else:

            data = {
                "name": name.strip(),
                "age": int(age),
                "phone": phone.strip(),
                "blood_group": group,
                "city": city.strip()
            }

            if insert_data("donors", data):
                st.success("Donor Registered Successfully! ❤️")
                st.balloons()


# ---------------- BLOOD REQUEST ----------------
elif page == "Blood Request":

    st.title("🚨 Emergency Blood Request")
    st.write("Submit a request for required blood.")

    with st.form("request_form"):

        patient = st.text_input("Patient Name")

        phone = st.text_input(
            "Contact Number",
            max_chars=10
        )

        group = st.selectbox(
            "Required Blood Group",
            BLOOD_GROUPS
        )

        city = st.text_input("City")
        hospital = st.text_input("Hospital Name")

        units = st.number_input(
            "Required Units",
            min_value=1,
            max_value=20,
            value=1
        )

        agree = st.checkbox(
            "I confirm that these details are correct."
        )

        submit = st.form_submit_button(
            "SUBMIT BLOOD REQUEST",
            use_container_width=True
        )

    if submit:

        if not patient.strip() or not city.strip() or not hospital.strip():
            st.error("Please complete all required fields.")

        elif not re.fullmatch(r"[6-9][0-9]{9}", phone.strip()):
            st.error("Enter a valid 10-digit Indian mobile number.")

        elif not agree:
            st.warning("Please confirm the information.")

        else:

            data = {
                "patient_name": patient.strip(),
                "phone": phone.strip(),
                "blood_group": group,
                "city": city.strip(),
                "hospital_name": hospital.strip(),
                "units": int(units),
                "status": "Pending"
            }

            if insert_data("blood_requests", data):
                st.success("Blood Request Submitted Successfully! ❤️")


# ---------------- ADMIN DASHBOARD ----------------
elif page == "Admin Dashboard":

    st.title("🔐 Admin Dashboard")

    admin_password = st.secrets.get("ADMIN_PASSWORD", "")

    if not admin_password:
        st.error(
            "ADMIN_PASSWORD is missing in Streamlit Secrets."
        )
        st.stop()

    password = st.text_input(
        "Admin Password",
        type="password"
    )

    if password == admin_password:

        st.success("Admin Login Successful!")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Donors",
            "Blood Requests",
            "Blood Banks",
            "Manage Stock"
        ])

        # DONORS
        with tab1:

            st.subheader("Registered Blood Donors")

            donors = get_data("donors")

            if donors.empty:
                st.info("No donors registered.")

            else:
                st.dataframe(
                    donors,
                    use_container_width=True
                )

                st.download_button(
                    "Download Donors CSV",
                    donors.to_csv(index=False).encode("utf-8"),
                    "donors.csv",
                    "text/csv"
                )

        # BLOOD REQUESTS
        with tab2:

            st.subheader("Blood Requests")

            requests = get_data("blood_requests")

            if requests.empty:
                st.info("No blood requests.")

            else:

                st.dataframe(
                    requests,
                    use_container_width=True
                )

                selected_id = st.selectbox(
                    "Select Request ID to Update Status",
                    requests["id"].tolist()
                )

                new_status = st.selectbox(
                    "Request Status",
                    [
                        "Pending",
                        "Contacted",
                        "Completed",
                        "Cancelled"
                    ]
                )

                if st.button("UPDATE REQUEST STATUS"):

                    try:
                        supabase.table("blood_requests").update(
                            {"status": new_status}
                        ).eq("id", selected_id).execute()

                        st.success("Request status updated.")
                        st.rerun()

                    except Exception as e:
                        st.error(str(e))

        # BLOOD BANKS
        with tab3:

            st.subheader("Register Blood Bank")

            with st.form("bank_form"):

                bank_name = st.text_input("Blood Bank Name")
                bank_city = st.text_input("City")
                address = st.text_input("Full Address")
                bank_phone = st.text_input("Phone Number")

                latitude = st.number_input(
                    "Latitude",
                    value=0.0,
                    format="%.6f"
                )

                longitude = st.number_input(
                    "Longitude",
                    value=0.0,
                    format="%.6f"
                )

                add_bank = st.form_submit_button(
                    "ADD BLOOD BANK"
                )

            if add_bank:

                if not all([
                    bank_name.strip(),
                    bank_city.strip(),
                    address.strip(),
                    bank_phone.strip()
                ]):
                    st.error("Complete all bank details.")

                else:

                    bank_data = {
                        "name": bank_name.strip(),
                        "city": bank_city.strip(),
                        "address": address.strip(),
                        "phone": bank_phone.strip(),
                        "latitude": latitude,
                        "longitude": longitude
                    }

                    if insert_data("banks", bank_data):
                        st.success("Blood Bank Added!")
                        st.rerun()

            st.divider()

            st.subheader("Registered Blood Banks")

            banks = get_data("banks")

            if not banks.empty:
                st.dataframe(
                    banks,
                    use_container_width=True
                )

        # MANAGE STOCK
        with tab4:

            st.subheader("Manage Blood Stock")

            banks = get_data("banks")

            if banks.empty:
                st.warning("First register a blood bank.")

            else:

                bank_options = {
                    f"{row['name']} - {row['city']}": int(row["id"])
                    for _, row in banks.iterrows()
                }

                with st.form("stock_form"):

                    selected_bank = st.selectbox(
                        "Select Blood Bank",
                        list(bank_options.keys())
                    )

                    blood_group = st.selectbox(
                        "Blood Group",
                        BLOOD_GROUPS
                    )

                    stock_units = st.number_input(
                        "Available Units",
                        min_value=0,
                        max_value=10000,
                        value=0
                    )

                    save_stock = st.form_submit_button(
                        "SAVE STOCK"
                    )

                if save_stock:

                    bank_id = bank_options[selected_bank]

                    try:

                        supabase.table("stock").upsert(
                            {
                                "bank_id": bank_id,
                                "blood_group": blood_group,
                                "units": int(stock_units)
                            },
                            on_conflict="bank_id,blood_group"
                        ).execute()

                        st.success("Blood Stock Saved!")
                        st.rerun()

                    except Exception as e:
                        st.error(str(e))

            st.divider()

            st.subheader("Current Blood Stock")

            stock = get_data("stock")

            if not stock.empty:
                st.dataframe(
                    stock,
                    use_container_width=True
                )


    elif password:
        st.error("Incorrect Admin Password.")


# ---------------- FOOTER ----------------
st.markdown("---")

st.markdown(
    "<center>🩸 BLOOD CARE | SAVE BLOOD • SAVE LIVES</center>",
    unsafe_allow_html=True
)
