import streamlit as st
import numpy_financial as npf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Investment Appraisal Tool", layout="wide")

st.title("💼 Business Investment & Loan Analysis")

# Sidebar - Project & Loan Inputs
st.sidebar.header("1. Loan Setup")
loan_amount = st.sidebar.number_input("Loan Amount ($)", value=100000.0, step=5000.0)
annual_interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=6.5, step=0.1) / 100
loan_term_years = st.sidebar.number_input("Loan Term (Years)", value=5, min_value=1)
discount_fee_pct = st.sidebar.number_input("Loan Discount Fee (%)", value=1.0, step=0.1) / 100

st.sidebar.header("2. Investment Metrics")
initial_equity = st.sidebar.number_input("Initial Equity Outlay ($)", value=20000.0, step=1000.0)
hurdle_rate = st.sidebar.number_input("Target Discount Rate / Hurdle Rate (%)", value=8.0, step=0.5) / 100

# Loan Calculations
net_loan_proceeds = loan_amount * (1 - discount_fee_pct)
monthly_interest_rate = annual_interest_rate / 12
total_months = int(loan_term_years * 12)

# Monthly Debt Payment (PMT)
monthly_payment = -npf.pmt(monthly_interest_rate, total_months, loan_amount)
annual_debt_service = monthly_payment * 12

# Cash Flow Input Table
st.subheader("Expected Cash Flows")
cash_flows = []
cols = st.columns(int(loan_term_years))

for year in range(1, int(loan_term_years) + 1):
    with cols[year - 1]:
        cf = st.number_input(f"Year {year} NOI ($)", value=35000.0, step=1000.0, key=f"cf_{year}")
        cash_flows.append(cf)

# Calculate Net Annual Cash Flow after Debt Service
net_cash_flows = [cf - annual_debt_service for cf in cash_flows]

# TVM Calculations
total_initial_outlay = initial_equity + (loan_amount - net_loan_proceeds)
full_cash_stream = [-total_initial_outlay] + net_cash_flows

npv = npf.npv(hurdle_rate, full_cash_stream)
irr = npf.irr(full_cash_stream)

# Display Key Metrics
st.markdown("---")
st.subheader("Results & Performance")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Annual Debt Service", f"${annual_debt_service:,.2f}")
m2.metric("Net Initial Outlay", f"${total_initial_outlay:,.2f}")
m3.metric("Net Present Value (NPV)", f"${npv:,.2f}", delta="Profitable" if npv > 0 else "Unprofitable")
m4.metric("Internal Rate of Return (IRR)", f"{irr * 100:.2f}%" if not pd.isna(irr) else "N/A")

# Data Table & Visualization
df = pd.DataFrame({
    "Year": list(range(1, int(loan_term_years) + 1)),
    "Operating Cash Flow (NOI)": cash_flows,
    "Debt Service": [annual_debt_service] * int(loan_term_years),
    "Net Cash Flow": net_cash_flows
})

fig = px.bar(df, x="Year", y=["Operating Cash Flow (NOI)", "Debt Service"], barmode="group",
             title="Annual Cash Flow vs. Loan Repayment")
st.plotly_chart(fig, width="stretch")

st.dataframe(df, width="stretch")
