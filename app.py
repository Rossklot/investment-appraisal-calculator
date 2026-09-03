import streamlit as st
import numpy_financial as npf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Investment Appraisal Tool", layout="wide")

st.title("💼 Business Investment & Loan Analysis")
st.caption("⛏️ **Specialized for Junior Mining, Infrastructure, and Commercial Real Estate Valuation**")

# --- SCENARIO PRESETS ---
st.sidebar.header("🎯 Select Industry Preset")

scenarios = {
    "⛏️ Junior Gold Mining Project (Default)": {
        "loan_amount": 0.0,
        "interest_rate": 0.0,
        "loan_term": 10,
        "discount_fee": 0.0,
        "initial_equity": 2000000.0,
        "hurdle_rate": 11.0,
        "noi": [-2000000.0, 1500000.0, 1500000.0, 1500000.0, 1500000.0, 1500000.0, 1500000.0, 1500000.0, 1500000.0, 0.0]
    },
    "🏢 Commercial Real Estate Development": {
        "loan_amount": 3000000.0,
        "interest_rate": 6.5,
        "loan_term": 10,
        "discount_fee": 1.0,
        "initial_equity": 1000000.0,
        "hurdle_rate": 8.5,
        "noi": [0.0, 450000.0, 460000.0, 475000.0, 490000.0, 500000.0, 510000.0, 525000.0, 540000.0, 550000.0]
    },
    "☀️ Utility-Scale Solar Farm": {
        "loan_amount": 1500000.0,
        "interest_rate": 5.0,
        "loan_term": 10,
        "discount_fee": 0.5,
        "initial_equity": 500000.0,
        "hurdle_rate": 7.0,
        "noi": [250000.0, 245000.0, 240000.0, 235000.0, 230000.0, 225000.0, 220000.0, 215000.0, 210000.0, 100000.0]
    }
}

# Sidebar - Project & Loan Inputs
st.sidebar.header("1. Loan Setup")
loan_amount = st.sidebar.number_input("Loan Amount ($)", value=100000.0, step=5000.0)
annual_interest_rate = st.sidebar.number_input("Loan Interest Rate (%)", value=6.5, step=0.1) / 100
loan_term_years = st.sidebar.number_input("Loan Term (Years)", value=5, min_value=1)
discount_fee_pct = st.sidebar.number_input("Loan Discount Fee (%)", value=1.0, step=0.1) / 100

st.sidebar.header("2. Investment Metrics")
initial_equity = st.sidebar.number_input("Initial Equity Outlay ($)", value=20000.0, step=1000.0)
hurdle_rate = st.sidebar.number_input("Target Discount Rate / Hurdle Rate (%)", value=8.0, step=0.5) / 100

selected_scenario = st.sidebar.selectbox("Choose a scenario preset:", list(scenarios.keys()))
preset = scenarios[selected_scenario]

# Support / Buy Me a Coffee Button in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("☕ Support My Work")
st.sidebar.markdown(
    """
    <a href="https://buymeacoffee.com/Kabamba" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 160px !important;" >
    </a>
    """,
    unsafe_allow_html=True
)

# Feedback Section
st.sidebar.markdown("---")
st.sidebar.markdown(
    "💬 Have feedback or feature ideas? Leave a comment on [GitHub](https://github.com/Rossklot/investment-appraisal-calculator/issues) or reach out directly!"
)

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

# Risk Analysis Summary Box
st.markdown("---")
st.subheader("📋 Investment Risk Assessment")

if npv > 0 and irr > hurdle_rate:
    st.success(f"""
    **Verdict: WORTH TAKING INVESTMENT**
    * **Net Present Value (NPV):** Project creates **${npv:,.2f}** in value above your return target.
    * **Return Rate (IRR):** The expected return of **{irr * 100:.2f}%** comfortably clears your hurdle rate of **{hurdle_rate * 100:.2f}%**.
    * **Debt Coverage:** Annual net cash flows are positive after covering the **${annual_debt_service:,.2f}** annual loan repayment.
    """)
elif npv == 0:
    st.warning(f"""
    **Verdict: MARGINAL / BREAK-EVEN**
    * **Net Present Value (NPV):** Project breaks even at **$0.00**.
    * **Return Rate (IRR):** The project matches your hurdle rate of **{hurdle_rate * 100:.2f}%** exactly without adding additional value.
    """)
else:
    st.error(f"""
    **Verdict: NOT WORTH TAKING INVESTMENT**
    * **Net Present Value (NPV):** Project destroys value by **${npv:,.2f}**.
    * **Return Rate (IRR):** The expected return of **{irr * 100:.2f}%** falls short of your hurdle rate of **{hurdle_rate * 100:.2f}%**.
    * **Risk Warning:** The net operating cash flows are insufficient relative to the initial equity and debt service obligations.
    """)

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

# CSV Export Feature
csv_data = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Summary as CSV",
    data=csv_data,
    file_name="investment_appraisal_summary.csv",
    mime="text/csv"
)

# Discount Rate Sensitivity Line Chart
st.markdown("---")
st.subheader("NPV Sensitivity Analysis")

rates = [r / 100 for r in range(1, 30)]
npvs = [npf.npv(r, full_cash_stream) for r in rates]

sens_df = pd.DataFrame({"Discount Rate (%)": [r * 100 for r in rates], "NPV ($)": npvs})
sens_fig = px.line(sens_df, x="Discount Rate (%)", y="NPV ($)", title="NPV Sensitivity Across Discount Rates")
sens_fig.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(sens_fig, width="stretch")
