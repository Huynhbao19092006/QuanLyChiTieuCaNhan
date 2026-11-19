from utils.page_context import *


def show_export():
    show_page_title(
        "Xuất dữ liệu",
        "Tải xuống dữ liệu giao dịch để lưu trữ và báo cáo.",
    )

    transactions, categories = load_data()

    if not transactions:
        st.info("Chưa có dữ liệu để xuất.")
        return

    df = transaction_dataframe(transactions, categories)

    st.subheader("Xem trước dữ liệu")
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.caption("Nhấn nút để tải dữ liệu CSV về máy.")
        csv_downloaded = st.download_button(
            label="📄 Tải xuống CSV",
            data=csv_data,
            file_name="giao_dich_ca_nhan.csv",
            mime="text/csv",
            width="stretch",
        )
        if csv_downloaded:
            show_notification(
                "success",
                "File CSV đã sẵn sàng để tải xuống.",
            )

    with col2:
        try:
            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl",
            ) as writer:
                df.to_excel(
                    writer,
                    sheet_name="Giao dịch",
                    index=False,
                )

                summary = pd.DataFrame([
                    {
                        "Chỉ tiêu": "Tổng thu nhập",
                        "Số tiền": df.loc[
                            df["Loại"] == "Thu nhập",
                            "Số tiền",
                        ].sum(),
                    },
                    {
                        "Chỉ tiêu": "Tổng chi tiêu",
                        "Số tiền": df.loc[
                            df["Loại"] == "Chi tiêu",
                            "Số tiền",
                        ].sum(),
                    },
                ])

                summary.to_excel(
                    writer,
                    sheet_name="Tổng quan",
                    index=False,
                )

            st.caption("Nhấn nút để tải báo cáo Excel về máy.")
            excel_downloaded = st.download_button(
                label="📊 Tải xuống Excel",
                data=excel_buffer.getvalue(),
                file_name="bao_cao_chi_tieu.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )
            if excel_downloaded:
                show_notification(
                    "success",
                    "File Excel đã sẵn sàng để tải xuống.",
                )

        except Exception as error:
            st.error(f"Không thể tạo file Excel: {error}")
