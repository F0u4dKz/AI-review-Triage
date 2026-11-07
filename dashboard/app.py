"""Read-only dashboard over the gold views in analytics.duckdb."""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "analytics.duckdb"


def query(sql: str) -> pd.DataFrame:
    connection = duckdb.connect(DB_PATH.as_posix(), read_only=True)
    try:
        return connection.execute(sql).df()
    finally:
        connection.close()


def main() -> None:
    st.set_page_config(page_title="Review triage", layout="wide")
    st.title("Review triage")

    if not DB_PATH.exists():
        st.error("analytics.duckdb is missing. Run `make dbt` first.")
        return

    kpi = query("select * from gold.kpi_overview")
    row = kpi.iloc[0]
    sales, items, satisfaction = st.columns(3)
    sales.metric("Sales value", f"{row['sales_value']:,.2f}")
    items.metric("Items sold", f"{int(row['items_sold']):,}")
    if pd.isna(row["satisfaction_score"]):
        satisfaction.metric("Satisfaction", "No reviews")
    else:
        satisfaction.metric("Satisfaction", f"{row['satisfaction_score']:.0f} / 100")

    st.subheader("Monthly sales")
    monthly = query("select sales_month, sales_value from gold.monthly_sales")
    if monthly.empty:
        st.write("No delivered orders yet.")
    else:
        monthly["sales_month"] = pd.to_datetime(monthly["sales_month"]).dt.strftime("%Y-%m")
        st.bar_chart(monthly, x="sales_month", y="sales_value")

    st.subheader("Satisfaction")
    grain = st.radio("Show by", ["Category", "Product"], horizontal=True)
    if grain == "Category":
        chart = query(
            "select category_name, satisfaction_score from gold.satisfaction_by_category"
        )
        label = "category_name"
    else:
        chart = query(
            "select product_name, satisfaction_score from gold.satisfaction_by_product"
        )
        label = "product_name"
    if chart.empty:
        st.write("No reviews yet.")
    else:
        st.bar_chart(chart, x=label, y="satisfaction_score")


if __name__ == "__main__":
    main()
