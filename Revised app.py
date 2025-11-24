# app_interface.py

import streamlit as st
import pandas as pd
from datetime import date
from database import (
    init_db,
    add_transaction,
    get_all_transactions,
    get_summary,
    set_goal,
    get_goal_progress,
    get_goal,
)

# Initialize the database connection and setup tables
init_db()

st.set_page_config(page_title="Expense Tracker Pro", layout="centered")

# --- HEADER ---
st.title("💸 Expense Tracker Pro")

user_name = st.text_input("Your name (no password):", value="User")
if not user_name.strip():
    user_name = "User"
st.caption(f"Hello, **{user_name}**! Manage your finances below.")

# --- NAVIGATION SIDE MENU ---
selected_page = st.sidebar.radio(
    "Select Page",
    ["Dashboard & Targets", "Input Transaction", "Records & Overview"],
)

# --- DASHBOARD & TARGETS PAGE ---
if selected_page == "Dashboard & Targets":

    st.header("📈 Financial Dashboard")

    income_total, expense_total, net_balance = get_summary()

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Income Total", f"₹ {income_total:.2f}")
    col_b.metric("Expense Total", f"₹ {expense_total:.2f}")
    col_c.metric("Net Balance", f"₹ {net_balance:.2f}")

    st.subheader("Define Your Budgets")

    budget_col1, budget_col2 = st.columns(2)

    with budget_col1:
        monthly_budget = st.number_input(
            "Monthly Budget (₹)", min_value=0.0, step=500.0, value=float(get_goal("monthly") or 0.0)
        )
        if st.button("Save Monthly Budget"):
            set_goal("monthly", monthly_budget)
            st.success("Monthly budget saved!")

    with budget_col2:
        weekly_budget = st.number_input(
            "Weekly Budget (₹)", min_value=0.0, step=200.0, value=float(get_goal("weekly") or 0.0)
        )
        if st.button("Save Weekly Budget"):
            set_goal("weekly", weekly_budget)
            st.success("Weekly budget saved!")

    st.markdown("---")
    st.subheader("Budget Progress")

    for period_key, label_name in [("monthly", "Monthly"), ("weekly", "Weekly")]:
        budget_goal, spent_amount, remaining_amount, status_msg = get_goal_progress(period_key)
        st.markdown(f"### {label_name} Budget")
        if budget_goal is None:
            st.info(f"No {label_name.lower()} budget set yet.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Set Budget", f"₹ {budget_goal:.2f}")
            c2.metric("Spent", f"₹ {spent_amount:.2f}")
            c3.metric("Remaining", f"₹ {remaining_amount:.2f}")
            if "exceeded" in status_msg:
                st.error(status_msg)
            elif "close" in status_msg:
                st.warning(status_msg)
            else:
                st.success(status_msg)

# --- INPUT TRANSACTION PAGE ---
elif selected_page == "Input Transaction":
    st.header("➕ New Transaction Entry")

    trans_type = st.radio("Type:", ["Expense", "Income"])
    amt = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    categ = st.text_input("Category (e.g., Food, Travel, Salary)", value="")
    trans_date = st.date_input("Date", value=date.today())
    note_text = st.text_area("Optional Note", height=60)

    if st.button("Submit Transaction"):
        if amt <= 0:
            st.error("Please enter an amount greater than zero.")
        elif not categ.strip():
            st.error("Category cannot be empty.")
        else:
            entry_type = "expense" if trans_type == "Expense" else "income"
            add_transaction(
                t_type=entry_type,
                amount=amt,
                category=categ.strip(),
                t_date=trans_date.isoformat(),
                note=note_text.strip(),
            )
            st.success(f"{trans_type} recorded successfully.")

# --- RECORDS & OVERVIEW PAGE ---
elif selected_page == "Records & Overview":
    st.header("🗃️ Transaction Records")

    all_records = get_all_transactions()

    if not all_records:
        st.info("No transactions found.")
    else:
        df = pd.DataFrame(
            all_records,
            columns=["ID", "Date", "Type", "Category", "Amount", "Note"]
        )
        df["Date"] = pd.to_datetime(df["Date"]).dt.date

        st.subheader("Complete Transactions")
        st.dataframe(df, height=400)

        inc_total, exp_total, net_bal = get_summary()
        st.markdown("---")
        st.subheader("Summary Metrics")
        ca1, ca2, ca3 = st.columns(3)
        ca1.metric("Total Income", f"₹ {inc_total:.2f}")
        ca2.metric("Total Expense", f"₹ {exp_total:.2f}")
        ca3.metric("Net Balance", f"₹ {net_bal:.2f}")
