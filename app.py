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

                    save_stock = st.form_submit_button("SAVE STOCK")

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
