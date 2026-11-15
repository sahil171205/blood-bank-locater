
# ---------------- FIND BLOOD ----------------
elif page == "Find Blood":

    st.title("🔍 Find Blood Donors")
    st.caption("Search registered donors by blood group and city")

    donors = get_data("donors")

    group = st.selectbox(
        "Select Blood Group",
        BLOOD_GROUPS
    )

    city = st.text_input(
        "Enter City",
        placeholder="Example: Kagal"
    )

    if st.button("SEARCH DONORS", use_container_width=True):

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
                .str.lower()
            )

            result = result[
                (result["blood_group"] == group.upper()) &
                (result["city"] == city.strip().lower())
            ]

            if not result.empty:

                st.success(
                    f"❤️ {len(result)} Donor(s) Found!"
                )

                for _, donor in result.iterrows():

                    with st.container(border=True):

                        st.subheader(
                            "👤 " + str(donor["name"])
                        )

                        st.write(
                            "🩸 Blood Group:",
                            donor["blood_group"]
                        )

                        st.write(
                            "📍 City:",
                            donor["city"].title()
                        )

                        st.write("🎂 Age:", donor["age"])

                        st.write(
                            "📞 Contact:",
                            donor["phone"]
                        )

            else:
                st.error("No matching donors found.")
                st.info(
                    "Check Blood Group and City."
                )
