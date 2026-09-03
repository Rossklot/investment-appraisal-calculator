import streamlit as st
import numpy_financial as npf
import pandas as pd
import plotly.express as px
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==============================================================================
# 1. PDF REPORT GENERATOR FUNCTION
# ==============================================================================
def generate_pdf_report(selected_scenario, npv, irr, annual_ds, net_outlay, hurdle_rate, currency="$", company_name="Investment Appraisal Corp"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom Company Branding Header
    company_style = ParagraphStyle(
        'CompanyHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=0,
        spaceAfter=10
    )
    story.append(Paragraph(f"<b>ORGANIZATION:</b> {company_name}", company_style))
    story.append(Paragraph("<b>REPORT TYPE:</b> Executive Investment Evaluation", company_style))
    story.append(Spacer(1, 10))
    
    # Title
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12
    )
    story.append(Paragraph(f"Project Appraisal: {selected_scenario}", title_style))
    story.append(Spacer(1, 12))
    
    # Financial Results Table
    data = [
        ["Metric", "Value"],
        ["Net Present Value (NPV)", f"{currency}{npv:,.2f}"],
        ["Internal Rate of Return (IRR)", f"{irr:.2f}%"],
        ["Target Hurdle Rate", f"{hurdle_rate:.2f}%"],
        ["Net Initial Outlay", f"{currency}{net_outlay:,.2f}"],
        ["Annual Debt Service", f"{currency}{annual_ds:,.2f}"]
    ]
    
    table = Table(data, colWidths=[250, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    
    story.append(table)
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()

# ==============================================================================
# 2. STREAMLIT APP LAYOUT & SIDEBAR (CONTINUE YOUR EXISTING CODE)
# ==============================================================================
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

# --- SIDEBAR SCENARIO & CURRENCY SELECTORS ---
query_params = st.query_params

default_scenario = query_params.get("scenario", list(scenarios.keys())[0])
selected_scenario = st.sidebar.selectbox(
    "Choose a scenario preset:", 
    list(scenarios.keys()), 
    index=list(scenarios.keys()).index(default_scenario) if default_scenario in scenarios else 0
)

# ⚠️ DEFINE PRESET HERE BEFORE INPUTS USE IT!
preset = scenarios[selected_scenario]

# Currency selection
currency_symbols = {
    "USD ($)": "$",
    "CAD (C$)": "C$",
    "EUR (€)": "€",
    "GBP (£)": "£",
    "AUD (A$)": "A$"
}
default_curr = query_params.get("currency", "$")
curr_index = list(currency_symbols.values()).index(default_curr) if default_curr in currency_symbols.values() else 0

selected_currency_label = st.sidebar.selectbox("Select Currency:", list(currency_symbols.keys()), index=curr_index)
currency_symbol = currency_symbols[selected_currency_label]

st.query_params["scenario"] = selected_scenario
st.query_params["currency"] = currency_symbol

# --- 1. LOAN SETUP ---
st.sidebar.header("1. Loan Setup")

loan_amount = st.sidebar.number_input(
    "Loan Amount ($)", 
    value=preset["loan_amount"], 
    step=5000.0,
    help="Total principal amount borrowed from the financial institution or lender."
)
interest_rate = st.sidebar.number_input(
    "Loan Interest Rate (%)", 
    value=preset["interest_rate"], 
    step=0.25,
    help="Annual nominal interest rate charged on the loan balance."
) / 100
loan_term = st.sidebar.number_input(
    "Loan Term (Years)", 
    value=preset["loan_term"], 
    step=1,
    help="Duration of the loan repayment period in full years."
)
discount_fee_pct = st.sidebar.number_input(
    "Loan Discount Fee (%)", 
    value=1.0, 
    step=0.1,
    help="Upfront fee or origination charge deducted by the bank at closing."
) / 100

# --- 2. INVESTMENT METRICS ---
st.sidebar.header("2. Investment Metrics")

initial_equity = st.sidebar.number_input(
    "Initial Equity Outlay ($)", 
    value=20000.0, 
    step=1000.0,
    help="Direct cash out of pocket required upfront to sponsor or initiate the project."
)
hurdle_rate = st.sidebar.number_input(
    "Target Discount Rate / Hurdle Rate (%)", 
    value=8.0, 
    step=0.5,
    help="Minimum required rate of return desired by equity investors/board."
) / 100

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

# --- SHARE SCENARIO WIDGET ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Share This Model")

# Encode link dynamically
encoded_scenario = selected_scenario.replace(" ", "%20")
share_url = f"https://kabamba-appraisal-tool.streamlit.app/?scenario={encoded_scenario}&currency={currency_symbol}"

st.sidebar.code(share_url, language="text")
st.sidebar.caption("Copy this permalink to share your exact model configuration with clients or partners.")

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
m1.metric("Annual Debt Service", f"{currency_symbol}{annual_debt_service:,.2f}")
m2.metric("Net Initial Outlay", f"{currency_symbol}{total_initial_outlay:,.2f}")
m3.metric("Net Present Value (NPV)", f"{currency_symbol}{npv:,.2f}", delta="Profitable" if npv > 0 else "Unprofitable")
m4.metric("Internal Rate of Return (IRR)", f"{irr * 100:.2f}%" if not pd.isna(irr) else "N/A")

st.write(f"- *Net Present Value (NPV):* Project creates *{currency_symbol}{npv:,.2f}* in value above your return target.")
st.write(f"- *Debt Coverage:* Annual net cash flows are positive after covering the *{currency_symbol}{annual_debt_service:,.2f}* annual loan repayment.")

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


pdf_data = generate_pdf_report(
    selected_scenario=selected_scenario,
    npv=npv,
    irr=irr * 100,
    annual_ds=annual_debt_service,
    net_outlay=total_initial_outlay,
    hurdle_rate=hurdle_rate
)

# Create summary DataFrame for CSV export
df_summary = pd.DataFrame({
    "Metric": ["Net Present Value (NPV)", "Internal Rate of Return (IRR)", "Annual Debt Service", "Net Initial Outlay"],
    "Value": [f"{currency_symbol}{npv:,.2f}", f"{irr * 100:.2f}%", f"{currency_symbol}{annual_debt_service:,.2f}", f"{currency_symbol}{total_initial_outlay:,.2f}"]
})

col1, col2 = st.columns(2)
with col1:
    st.download_button(
        label="📄 Download Executive PDF Report",
        data=pdf_data,
        file_name="Executive_Investment_Report.pdf",
        mime="application/pdf"
    )
with col2:
    st.download_button(
        label="📥 Download Summary as CSV",
        data=df_summary.to_csv(index=False),  # Make sure df_summary matches your DataFrame variable name
        file_name="investment_summary.csv",
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
