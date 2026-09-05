import io
import math
import numpy_financial as npf
import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Step 1: Translations Dictionary
TRANSLATIONS = {
    "EN": {
        "page_title": "Investment Appraisal Tool",
        "app_title": "💼 Business Investment & Loan Analysis",
        "app_caption": "⛏️ **Specialized for Junior Mining, Infrastructure, and Commercial Real Estate Valuation**",
        "preset_header": "🎯 Select Industry Preset",
        "select_preset": "Choose a scenario preset:",
        "select_currency": "Select Currency:",
        "loan_header": "1. Loan Setup",
        "loan_amount": "Loan Amount ($)",
        "loan_amount_help": "Total principal amount borrowed from the financial institution or lender.",
        "interest_rate": "Loan Interest Rate (%)",
        "interest_rate_help": "Annual nominal interest rate charged on the loan balance.",
        "loan_term": "Loan Term (Years)",
        "loan_term_help": "Duration of the loan repayment period in full years.",
        "discount_fee": "Loan Discount Fee (%)",
        "discount_fee_help": "Upfront fee or origination charge deducted by the bank at closing.",
        "metrics_header": "2. Investment Metrics",
        "initial_equity": "Initial Equity Outlay ($)",
        "initial_equity_help": "Direct cash out of pocket required upfront to sponsor or initiate the project.",
        "hurdle_rate": "Target Discount Rate / Hurdle Rate (%)",
        "hurdle_rate_help": "Minimum required rate of return desired by equity investors/board.",
        "support_title": "☕ Support My Work",
        "share_title": "🔗 Share This Model",
        "share_caption": "Copy this permalink to share your exact model configuration with clients or partners.",
        "feedback_text": "💬 Have feedback or feature ideas? Leave a comment on [GitHub](https://github.com/Rossklot/investment-appraisal-calculator/issues) or reach out directly!",
        "expected_cf": "Expected Cash Flows",
        "year_noi": "Year {} NOI ($)",
        "results_header": "Results & Performance",
        "annual_ds": "Annual Debt Service",
        "net_outlay": "Net Initial Outlay",
        "npv_label": "Net Present Value (NPV)",
        "irr_label": "Internal Rate of Return (IRR)",
        "profitable": "Profitable",
        "unprofitable": "Unprofitable",
        "npv_desc": "- *Net Present Value (NPV):* Project creates *{}{:,.2f}* in value above your return target.",
        "ds_desc": "- *Debt Coverage:* Annual net cash flows are positive after covering the *{}{:,.2f}* annual loan repayment.",
        "risk_header": "📋 Investment Risk Assessment",
        "verdict_worth": "**Verdict: WORTH TAKING INVESTMENT**",
        "verdict_marginal": "**Verdict: MARGINAL / BREAK-EVEN**",
        "verdict_not_worth": "**Verdict: NOT WORTH TAKING INVESTMENT**",
        "chart_title": "Annual Cash Flow vs. Loan Repayment",
        "org_name_label": "🏢 Organization Name for PDF Header:",
        "dl_pdf": "📄 Download Executive PDF Report",
        "dl_csv": "📥 Download Summary as CSV",
        "sensitivity_header": "NPV Sensitivity Analysis",
        "sensitivity_title": "NPV Sensitivity Across Discount Rates",
    },
    "FR": {
        "page_title": "Outil d'Évaluation des Investissements",
        "app_title": "💼 Analyse des Investissements et Emprunts",
        "app_caption": "⛏️ **Spécialisé pour le secteur minier, les infrastructures et l'immobilier commercial**",
        "preset_header": "🎯 Sélectionner un modèle sectoriel",
        "select_preset": "Choisir un scénario prédéfini :",
        "select_currency": "Sélectionner la devise :",
        "loan_header": "1. Configuration de l'Emprunt",
        "loan_amount": "Montant du prêt ($)",
        "loan_amount_help": "Montant total du capital emprunté auprès de l'institution financière.",
        "interest_rate": "Taux d'intérêt du prêt (%)",
        "interest_rate_help": "Taux d'intérêt nominal annuel appliqué au solde du prêt.",
        "loan_term": "Durée du prêt (Années)",
        "loan_term_help": "Durée de remboursement du prêt en années complètes.",
        "discount_fee": "Frais de dossier / d'émission (%)",
        "discount_fee_help": "Frais initiaux déduits par la banque lors de la clôture.",
        "metrics_header": "2. Indicateurs d'Investissement",
        "initial_equity": "Apport initial en fonds propres ($)",
        "initial_equity_help": "Capital initial nécessaire investi directement pour lancer le projet.",
        "hurdle_rate": "Taux d'actualisation / Taux de rentabilité exigé (%)",
        "hurdle_rate_help": "Taux de rendement minimal exigé par les investisseurs ou le conseil.",
        "support_title": "☕ Soutenir mon travail",
        "share_title": "🔗 Partager ce modèle",
        "share_caption": "Copiez ce lien permanent pour partager cette configuration exacte avec vos clients.",
        "feedback_text": "💬 Des commentaires ou idées ? Laissez un message sur [GitHub](https://github.com/Rossklot/investment-appraisal-calculator/issues) !",
        "expected_cf": "Flux de trésorerie prévus",
        "year_noi": "Année {} RNO ($)",
        "results_header": "Résultats & Performance",
        "annual_ds": "Service annuel de la dette",
        "net_outlay": "Investissement initial net",
        "npv_label": "Valeur Actuelle Nette (VAN)",
        "irr_label": "Taux de Rentabilité Interne (TRI)",
        "profitable": "Rentable",
        "unprofitable": "Non rentable",
        "npv_desc": "- *Valeur Actuelle Nette (VAN) :* Le projet crée *{}{:,.2f}* de valeur au-delà de votre objectif.",
        "ds_desc": "- *Couverture de la dette :* Les flux nets sont positifs après le paiement de *{}{:,.2f}* pour la dette.",
        "risk_header": "📋 Évaluation des Risques d'Investissement",
        "verdict_worth": "**Décision : INVESTISSEMENT RECOMMANDÉ**",
        "verdict_marginal": "**Décision : MARGINAL / SEUIL DE RENTABILITÉ**",
        "verdict_not_worth": "**Décision : INVESTISSEMENT NON RECOMMANDÉ**",
        "chart_title": "Flux de trésorerie annuels vs Remboursement de la dette",
        "org_name_label": "🏢 Nom de l'organisation pour l'en-tête PDF :",
        "dl_pdf": "📄 Télécharger le rapport PDF",
        "dl_csv": "📥 Télécharger le résumé CSV",
        "sensitivity_header": "Analyse de Sensibilité de la VAN",
        "sensitivity_title": "Sensibilité de la VAN selon le taux d'actualisation",
    },
}

# Step 2: Language Selector Logic (Clean Text Only)
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

selected_lang = st.sidebar.selectbox(
    "🌐 Language / Langue",
    options=["EN", "FR"],
    format_func=lambda x: "English" if x == "EN" else "Français",
    key="lang_selector",
)

t = TRANSLATIONS[selected_lang]

# ==============================================================================
# 1. PDF REPORT GENERATOR FUNCTION
# ==============================================================================
def generate_pdf_report(selected_scenario, npv, irr, annual_ds, net_outlay, hurdle_rate, currency="$", company_name="Investment Appraisal Corp"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    
    company_style = ParagraphStyle(
        'CompanyHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=0,
        spaceAfter=4
    )
    story.append(Paragraph(f"<b>ORGANIZATION:</b> {company_name.upper()}", company_style))
    story.append(Paragraph("<b>REPORT TYPE:</b> Executive Investment Evaluation", company_style))
    story.append(Spacer(1, 10))
    
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12
    )
    story.append(Paragraph(f"Project Appraisal: {selected_scenario}", title_style))
    story.append(Spacer(1, 10))
    
    data = [
        ["Metric", "Value"],
        [t["npv_label"], f"{currency}{npv:,.2f}"],
        [t["irr_label"], f"{irr:.2f}%" if not math.isnan(irr) else "N/A"],
        [t["hurdle_rate"], f"{hurdle_rate:.2f}%"],
        [t["net_outlay"], f"{currency}{net_outlay:,.2f}"],
        [t["annual_ds"], f"{currency}{annual_ds:,.2f}"]
    ]
    
    table = Table(data, colWidths=[240, 210])
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
# 2. STREAMLIT APP LAYOUT & SIDEBAR
# ==============================================================================
st.set_page_config(page_title=t["page_title"], layout="wide")
st.title(t["app_title"])
st.caption(t["app_caption"])

# --- SCENARIO PRESETS ---
st.sidebar.header(t["preset_header"])

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

query_params = st.query_params

default_scenario = query_params.get("scenario", list(scenarios.keys())[0])
selected_scenario = st.sidebar.selectbox(
    t["select_preset"], 
    list(scenarios.keys()), 
    index=list(scenarios.keys()).index(default_scenario) if default_scenario in scenarios else 0
)

preset = scenarios[selected_scenario]

currency_symbols = {
    "USD ($)": "$",
    "CAD (C$)": "C$",
    "EUR (€)": "€",
    "GBP (£)": "£",
    "AUD (A$)": "A$"
}
default_curr = query_params.get("currency", "$")
curr_index = list(currency_symbols.values()).index(default_curr) if default_curr in currency_symbols.values() else 0

selected_currency_label = st.sidebar.selectbox(t["select_currency"], list(currency_symbols.keys()), index=curr_index)
currency_symbol = currency_symbols[selected_currency_label]

st.query_params["scenario"] = selected_scenario
st.query_params["currency"] = currency_symbol

# --- 1. LOAN SETUP ---
st.sidebar.header(t["loan_header"])

loan_amount = st.sidebar.number_input(
    t["loan_amount"], 
    value=preset["loan_amount"], 
    step=5000.0,
    help=t["loan_amount_help"]
)
interest_rate = st.sidebar.number_input(
    t["interest_rate"], 
    value=preset["interest_rate"], 
    step=0.25,
    help=t["interest_rate_help"]
) / 100
loan_term = st.sidebar.number_input(
    t["loan_term"], 
    value=preset["loan_term"], 
    step=1,
    help=t["loan_term_help"]
)
discount_fee_pct = st.sidebar.number_input(
    t["discount_fee"], 
    value=1.0, 
    step=0.1,
    help=t["discount_fee_help"]
) / 100

# --- 2. INVESTMENT METRICS ---
st.sidebar.header(t["metrics_header"])

initial_equity = st.sidebar.number_input(
    t["initial_equity"], 
    value=20000.0, 
    step=1000.0,
    help=t["initial_equity_help"]
)
hurdle_rate = st.sidebar.number_input(
    t["hurdle_rate"], 
    value=8.0, 
    step=0.5,
    help=t["hurdle_rate_help"]
) / 100

st.sidebar.markdown("---")
st.sidebar.subheader(t["support_title"])
st.sidebar.markdown(
    """
    <a href="https://buymeacoffee.com/Kabamba" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 160px !important;" >
    </a>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.subheader(t["share_title"])

encoded_scenario = selected_scenario.replace(" ", "%20")
share_url = f"https://kabamba-appraisal-tool.streamlit.app/?scenario={encoded_scenario}&currency={currency_symbol}"

st.sidebar.code(share_url, language="text")
st.sidebar.caption(t["share_caption"])

st.sidebar.markdown("---")
st.sidebar.markdown(t["feedback_text"])

net_loan_proceeds = loan_amount * (1 - discount_fee_pct)
monthly_interest_rate = interest_rate / 12
total_months = int(loan_term * 12)

monthly_payment = -npf.pmt(monthly_interest_rate, total_months, loan_amount)
annual_debt_service = monthly_payment * 12

st.subheader(t["expected_cf"])
cash_flows = []
cols = st.columns(int(loan_term))

for year in range(1, int(loan_term) + 1):
    with cols[year - 1]:
        cf = st.number_input(t["year_noi"].format(year), value=35000.0, step=1000.0, key=f"cf_{year}")
        cash_flows.append(cf)

net_cash_flows = [cf - annual_debt_service for cf in cash_flows]

total_initial_outlay = initial_equity + (loan_amount - net_loan_proceeds)
full_cash_stream = [-total_initial_outlay] + net_cash_flows

npv = npf.npv(hurdle_rate, full_cash_stream)
irr = npf.irr(full_cash_stream)

st.markdown("---")
st.subheader(t["results_header"])

m1, m2, m3, m4 = st.columns(4)
m1.metric(t["annual_ds"], f"{currency_symbol}{annual_debt_service:,.2f}")
m2.metric(t["net_outlay"], f"{currency_symbol}{total_initial_outlay:,.2f}")
m3.metric(t["npv_label"], f"{currency_symbol}{npv:,.2f}", delta=t["profitable"] if npv > 0 else t["unprofitable"])
m4.metric(t["irr_label"], f"{irr * 100:.2f}%" if irr is not None and not math.isnan(irr) else "N/A")

st.write(t["npv_desc"].format(currency_symbol, npv))
st.write(t["ds_desc"].format(currency_symbol, annual_debt_service))

st.markdown("---")
st.subheader(t["risk_header"])

if npv > 0 and irr > hurdle_rate:
    st.success(f"{t['verdict_worth']}\n* **{t['npv_label']}:** {currency_symbol}{npv:,.2f}\n* **{t['irr_label']}:** {irr * 100:.2f}%")
elif npv == 0:
    st.warning(f"{t['verdict_marginal']}\n* **{t['npv_label']}:** {currency_symbol}0.00")
else:
    st.error(f"{t['verdict_not_worth']}\n* **{t['npv_label']}:** {currency_symbol}{npv:,.2f}")

df = pd.DataFrame({
    "Year": list(range(1, int(loan_term) + 1)),
    "Operating Cash Flow (NOI)": cash_flows,
    "Debt Service": [annual_debt_service] * int(loan_term),
    "Net Cash Flow": net_cash_flows
})

fig = px.bar(df, x="Year", y=["Operating Cash Flow (NOI)", "Debt Service"], barmode="group", title=t["chart_title"])
st.plotly_chart(fig, width="stretch")

st.dataframe(df, width="stretch")

df_summary = pd.DataFrame({
    "Metric": [t["npv_label"], t["irr_label"], t["annual_ds"], t["net_outlay"]],
    "Value": [f"{currency_symbol}{npv:,.2f}", f"{irr * 100:.2f}%", f"{currency_symbol}{annual_debt_service:,.2f}", f"{currency_symbol}{total_initial_outlay:,.2f}"]
})

company_name = st.text_input(t["org_name_label"], value="Investment Appraisal Corp")

pdf_data = generate_pdf_report(
    selected_scenario=selected_scenario,
    npv=npv,
    irr=irr * 100 if irr is not None else 0.0,
    annual_ds=annual_debt_service,
    net_outlay=total_initial_outlay,
    hurdle_rate=hurdle_rate * 100,
    currency=currency_symbol,
    company_name=company_name
)

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label=t["dl_pdf"],
        data=pdf_data,
        file_name=f"{selected_scenario.replace(' ', '_')}_Report.pdf",
        mime="application/pdf",
        key="pdf_download_btn"
    )

with col2:
    st.download_button(
        label=t["dl_csv"],
        data=df_summary.to_csv(index=False),
        file_name=f"{selected_scenario.replace(' ', '_')}_Summary.csv",
        mime="text/csv",
        key="csv_download_btn"
    )

st.markdown("---")
st.subheader(t["sensitivity_header"])

rates = [r / 100 for r in range(1, 30)]
npvs = [npf.npv(r, full_cash_stream) for r in rates]

sens_df = pd.DataFrame({"Discount Rate (%)": [r * 100 for r in rates], "NPV ($)": npvs})
sens_fig = px.line(sens_df, x="Discount Rate (%)", y="NPV ($)", title=t["sensitivity_title"])
sens_fig.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(sens_fig, width="stretch")