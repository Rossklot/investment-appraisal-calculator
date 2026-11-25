import io
import math
import numpy as np
import numpy_financial as npf
import pandas as pd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from decision_intelligence import (
    compute_robust_irr,
    evaluate_bankability,
    run_monte_carlo,
    run_tornado_analysis,
)
from scenario_comparison import (
    generate_three_case_matrix,
    make_snapshot_record,
    plot_scenario_comparison,
)
from mining_templates import (
    MINING_ARCHETYPES,
    generate_mining_schedule,
)
from deal_structuring import (
    apply_royalty_and_tax_waterfall,
    build_grace_period_debt_schedule,
)

# Step 1: Translations Dictionary
TRANSLATIONS = {
    "EN": {
        "page_title": "Investment Appraisal Tool",
        "app_title": "💼 Business Investment & Loan Analysis",
        "app_caption": "⛏️ **Specialized for Junior Mining, Infrastructure, and Commercial Real Estate Valuation**",
        "preset_header": "🎯 Select Industry Preset",
        "preset_none": "Custom / Individual Investor (Default)",
        "preset_mining": "Junior Mining / Exploration",
        "preset_real_estate": "Commercial Real Estate",
        "preset_infrastructure": "Infrastructure Project",
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
        "advanced_setup": "⚙️ Advanced Financing & Compounding",
        "compounding_freq": "Compounding Frequency",
        "compounding_help": "Select compounding frequency for accurate lease, loan, or investment appraisal.",
        "eval_mode": "Evaluation Objective",
        "eval_help": "Switch between income-generating capital projects and cost-minimization procurement.",
        "mode_income": "Capital Investment (Income / NPV)",
        "mode_lease": "Equipment Lease vs. Buy (Cost Minimization)",
        "npc_label": "Net Present Cost (NPC)",
        "irr_na": "N/A (Cost Analysis)",
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
        "audit_title": "💎 Institutional Risk & DSCR Audit",
        "audit_caption": "Evaluate debt service safety buffers and revenue stress sensitivity across operational lifecycles.",
        "audit_expander": "📊 Debt Service Coverage & Sensitivity Matrix",
        "stress_inputs": "Live Stress Inputs",
        "rev_stress_label": "Revenue / Commodity Spot Price Stress (%)",
        "rev_stress_help": "Simulates market price shifts (e.g., Gold spot adjustments relative to baseline).",
        "cost_stress_label": "OPEX Cost Inflation Stress (%)",
        "cost_stress_help": "Simulates operational cost overruns or supply chain inflation.",
        "valuation_impact": "Valuation Impact",
        "stressed_npv_label": "Stressed NPV",
        "net_stress_shift": "Net Stress Shift",
        "covenant_status": "**Senior Debt Covenants Status:**",
        "dscr_success": "✅ Peak DSCR Protection: **{dscr:.2f}x** (Exceeds 1.30x Banking Standard)",
        "dscr_warning": "⚠️ Debt Coverage Tight: **{dscr:.2f}x** (Breaches 1.30x covenant buffer)",
        "dscr_error": "🚨 DSCR Deficit: **{dscr:.2f}x** (Requires Debt Service Reserve Fund drawdown)",
        "audit_note": "💡 **Institutional Audit Note:** Senior lenders require minimum Debt Service Coverage Ratios (DSCR) of **1.25x–1.35x**. This dynamic sensitivity module proves project solvency under adverse macro price movements.",
    },
    "FR": {
        "page_title": "Outil d'Évaluation des Investissements",
        "app_title": "💼 Analyse des Investissements et Emprunts",
        "app_caption": "⛏️ **Spécialisé pour le secteur minier, les infrastructures et l'immobilier commercial**",
        "preset_header": "🎯 Sélectionner un modèle sectoriel",
        "preset_none": "Investisseur individuel / Personnalisé (Par défaut)",
        "preset_mining": "Minière junior / Exploration",
        "preset_real_estate": "Immobilier commercial",
        "preset_infrastructure": "Projet d'infrastructure",
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
        "advanced_setup": "⚙️ Configuration avancée et capitalisation",
        "compounding_freq": "Fréquence de capitalisation",
        "compounding_help": "Sélectionnez la fréquence de capitalisation pour une évaluation précise du prêt, du bail ou de l'investissement.",
        "eval_mode": "Objectif d'évaluation",
        "eval_help": "Basculez entre les projets d'investissement générateurs de revenus et l'optimisation des coûts d'approvisionnement.",
        "mode_income": "Investissement en capital (Revenus / VAN)",
        "mode_lease": "Location d'équipement vs Achat (Minimisation des coûts)",
        "npc_label": "Coût Net Présent (NPC)",
        "irr_na": "N/D (Analyse de coûts)",
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
        "audit_title": "💎 Audit du Risque Institutionnel et du DSCR",
        "audit_caption": "Évaluer les coussins de sécurité du service de la dette et la sensibilité aux tensions de revenus.",
        "audit_expander": "📊 Couverture du Service de la Dette et Matrice de Sensibilité",
        "stress_inputs": "Données de Stress en Direct",
        "rev_stress_label": "Stress sur Revenus / Prix du Marché (%)",
        "rev_stress_help": "Simule les variations de prix du marché (ex. ajustements du cours de l'or par rapport à la base).",
        "cost_stress_label": "Inflation des Coûts d'Exploitation (%)",
        "cost_stress_help": "Simule les dépassements de coûts d'exploitation ou l'inflation de la chaîne d'approvisionnement.",
        "valuation_impact": "Impact sur la Valorisation",
        "stressed_npv_label": "VAN Sous Stress",
        "net_stress_shift": "Variation Nette de Stress",
        "covenant_status": "**Statut des Engagements de la Dette Senior:**",
        "dscr_success": "✅ Protection DSCR Maximale: **{dscr:.2f}x** (Dépasse la norme bancaire de 1,30x)",
        "dscr_warning": "⚠️ Couverture de Dette Tendue: **{dscr:.2f}x** (En dessous du coussin de 1,30x)",
        "dscr_error": "🚨 Déficit de DSCR: **{dscr:.2f}x** (Nécessite le tirage du fonds de réserve pour la dette)",
        "audit_note": "💡 **Note d'Audit Institutionnel:** Les prêteurs seniors exigent des ratios minimaux de couverture du service de la dette (DSCR) de **1,25x à 1,35x**. Ce module dynamique démontre la solvabilité du projet lors de mouvements macroéconomiques défavorables.",
    },
}


# --- HELPER PARSER FOR COMMA NUMBERS ---
def parse_number(val_str, default=0.0):
    try:
        clean_str = str(val_str).replace(",", "").replace("$", "").strip()
        return float(clean_str)
    except ValueError:
        return default


# --- HELPER TO PARSE FLOAT FROM QUERY PARAMS ---
def get_qp_float(qp_dict, param_name, fallback):
    try:
        return float(qp_dict.get(param_name, fallback))
    except (ValueError, TypeError):
        return float(fallback)


# --- PDF REPORT GENERATOR FUNCTION ---
def generate_pdf_report(
    selected_scenario,
    npv,
    irr,
    annual_ds,
    net_outlay,
    hurdle_rate,
    currency="$",
    company_name="Investment Appraisal Corp",
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []

    styles = getSampleStyleSheet()

    company_style = ParagraphStyle(
        "CompanyHeader",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=0,
        spaceAfter=4,
    )
    story.append(Paragraph(f"<b>ORGANIZATION:</b> {company_name.upper()}", company_style))
    story.append(Paragraph("<b>REPORT TYPE:</b> Executive Investment Evaluation", company_style))
    story.append(Spacer(1, 10))

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=12,
    )
    story.append(Paragraph(f"Project Appraisal: {selected_scenario}", title_style))
    story.append(Spacer(1, 10))

    data = [
        ["Metric", "Value"],
        [t["npv_label"], f"{currency}{npv:,.2f}"],
        [t["irr_label"], f"{irr:.2f}%" if not math.isnan(irr) else "N/A"],
        [t["hurdle_rate"], f"{hurdle_rate:.2f}%"],
        [t["net_outlay"], f"{currency}{net_outlay:,.2f}"],
        [t["annual_ds"], f"{currency}{annual_ds:,.2f}"],
    ]

    table = Table(data, colWidths=[240, 210])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ]
        )
    )

    story.append(table)
    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()


# --- INITIAL PAGE CONFIG ---
st.set_page_config(page_title="Investment Appraisal Tool", layout="wide")

# Language Selector Logic
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

selected_lang = st.sidebar.selectbox(
    "🌐 Language / Langue",
    options=["EN", "FR"],
    format_func=lambda x: "English" if x == "EN" else "Français",
    key="lang_selector",
)
lang = selected_lang
st.session_state.lang = selected_lang

t = TRANSLATIONS[selected_lang]

st.title(t["app_title"])
st.caption(t["app_caption"])

# --- SCENARIO PRESETS DICTIONARY ---
scenarios = {
    "👤 Custom / Individual Investor (Default)": {
        "loan_amount": 500000.0,
        "interest_rate": 6.5,
        "loan_term": 10,
        "discount_fee": 0.0,
        "equity": 50000.0,
        "hurdle": 8.0,
        "flows": [15000.0, 15000.0, 15000.0, 15000.0, 15000.0],
    },
    "⛏ Junior Gold Mining Project": {
        "loan_amount": 2500000.0,
        "interest_rate": 8.5,
        "loan_term": 7,
        "discount_fee": 2.0,
        "equity": 500000.0,
        "hurdle": 12.0,
        "flows": [800000.0, 950000.0, 1100000.0, 1000000.0, 850000.0],
    },
    "🏢 Commercial Real Estate": {
        "loan_amount": 1200000.0,
        "interest_rate": 6.0,
        "loan_term": 10,
        "discount_fee": 1.0,
        "equity": 300000.0,
        "hurdle": 7.5,
        "flows": [180000.0, 185000.0, 190000.0, 195000.0, 200000.0],
    },
    "🏗️ Infrastructure Project": {
        "loan_amount": 5000000.0,
        "interest_rate": 5.5,
        "loan_term": 15,
        "discount_fee": 1.5,
        "equity": 1000000.0,
        "hurdle": 6.5,
        "flows": [600000.0, 650000.0, 700000.0, 750000.0, 800000.0],
    },
    "☀️ Utility-Scale Solar Farm": {
        "loan_amount": 1500000.0,
        "interest_rate": 5.0,
        "loan_term": 5,
        "discount_fee": 1.0,
        "equity": 20000.0,
        "hurdle": 8.0,
        "flows": [35000.0, 35000.0, 35000.0, 35000.0, 35000.0],
    },
}

currency_symbols = {
    "USD ($)": "$",
    "CAD (C$)": "C$",
    "EUR (€)": "€",
    "GBP (£)": "£",
    "AUD (A$)": "A$",
}

# --- SCENARIO SELECTBOX & QUERY PARAMS READING ---
st.sidebar.markdown(f"### {t['preset_header']}")

query_params = st.query_params
scenario_keys = list(scenarios.keys())

default_param = query_params.get("scenario", scenario_keys[0])
default_index = scenario_keys.index(default_param) if default_param in scenario_keys else 0

selected_preset_key = st.sidebar.selectbox(
    label=t["select_preset"],
    options=scenario_keys,
    index=default_index,
    key="preset_selectbox_unique",
)

selected_scenario = scenarios[selected_preset_key]

default_curr = query_params.get("currency", "$")
curr_index = (
    list(currency_symbols.values()).index(default_curr)
    if default_curr in currency_symbols.values()
    else 0
)
selected_currency_label = st.sidebar.selectbox(
    t["select_currency"],
    list(currency_symbols.keys()),
    index=curr_index,
    key="currency_selectbox_unique",
)
currency_symbol = currency_symbols[selected_currency_label]

# Parse inputs directly from query params if available, else fallback to selected scenario preset
default_loan = get_qp_float(query_params, "loan", selected_scenario.get("loan_amount", 500000.0))
default_rate = get_qp_float(query_params, "rate", selected_scenario.get("interest_rate", 6.5))
default_term = get_qp_float(query_params, "term", selected_scenario.get("loan_term", 10.0))
default_fee = get_qp_float(query_params, "fee", selected_scenario.get("discount_fee", 0.0))
default_equity = get_qp_float(query_params, "equity", selected_scenario.get("equity", 50000.0))
default_hurdle = get_qp_float(query_params, "hurdle", selected_scenario.get("hurdle", 8.0))

custom_cfs_raw = query_params.get("cfs", "")
if custom_cfs_raw:
    try:
        url_flows = [float(x.strip()) for x in custom_cfs_raw.split(",")]
    except ValueError:
        url_flows = selected_scenario.get("flows", [])
else:
    url_flows = selected_scenario.get("flows", [])

# --- 1. LOAN SETUP ---
st.sidebar.header(t["loan_header"])

loan_amount_raw = st.sidebar.text_input(
    label=t["loan_amount"],
    value=f"{default_loan:,.2f}",
    help=t["loan_amount_help"],
    key="input_loan_amount_text",
)
loan_amount = parse_number(loan_amount_raw, default=default_loan)

interest_rate = (
    st.sidebar.number_input(
        t["interest_rate"],
        value=default_rate,
        step=0.25,
        help=t["interest_rate_help"],
        key="input_interest_rate",
    )
    / 100
)

loan_term = st.sidebar.number_input(
    label=t["loan_term"],
    min_value=1.0,
    max_value=50.0,
    value=default_term,
    step=1.0,
    help=t["loan_term_help"],
    key="input_loan_term",
)

discount_fee_pct = (
    st.sidebar.number_input(
        t["discount_fee"],
        value=default_fee,
        step=0.1,
        help=t["discount_fee_help"],
        key="input_discount_fee",
    )
    / 100
)

# --- 2. INVESTMENT METRICS ---
st.sidebar.header(t["metrics_header"])

initial_equity_raw = st.sidebar.text_input(
    label=t["initial_equity"],
    value=f"{default_equity:,.2f}",
    help=t["initial_equity_help"],
    key="input_initial_equity_text",
)
initial_equity = parse_number(initial_equity_raw, default=default_equity)

hurdle_rate = (
    st.sidebar.number_input(
        t["hurdle_rate"],
        value=default_hurdle,
        step=0.5,
        help=t["hurdle_rate_help"],
        key="input_hurdle_rate",
    )
    / 100
)

st.sidebar.markdown("---")
st.sidebar.subheader("🏛️ Royalty, Tax & Debt Grace")

nsr_royalty_pct = st.sidebar.slider(
    "NSR Royalty (%)",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.25,
    help="Net Smelter Return (NSR) top-line royalty deducted from gross revenue.",
)

corporate_tax_rate_pct = st.sidebar.slider(
    "Corporate Income Tax Rate (%)",
    min_value=0.0,
    max_value=45.0,
    value=26.5,
    step=0.5,
    help="Applied to positive taxable income after straight-line CapEx depreciation & interest shield.",
)

debt_grace_years = st.sidebar.number_input(
    "Debt Principal Grace Period (Years)",
    min_value=0,
    max_value=max(0, int(loan_term) - 1) if loan_term > 1 else 0,
    value=0,
    step=1,
    help="Interest-only construction/ramp-up period before principal amortization starts.",
)

# --- Advanced Financing & Compounding Setup ---
with st.sidebar.expander(t["advanced_setup"]):
    compounding_freq = st.selectbox(
        t["compounding_freq"],
        ["Annual", "Semi-Annual", "Quarterly", "Monthly"],
        index=0,
        help=t["compounding_help"],
    )
    eval_mode = st.radio(
        t["eval_mode"],
        [t["mode_income"], t["mode_lease"]],
        help=t["eval_help"],
    )

freq_map = {"Annual": 1, "Semi-Annual": 2, "Quarterly": 4, "Monthly": 12}
m = freq_map[compounding_freq]
periodic_rate = hurdle_rate / m

# --- BASE LOAN & DEBT SERVICE CALCULATIONS ---
net_loan_proceeds = loan_amount * (1 - discount_fee_pct)
monthly_interest_rate = interest_rate / 12
total_months = int(loan_term * 12)

if loan_amount > 0 and monthly_interest_rate > 0:
    monthly_payment = float(-npf.pmt(monthly_interest_rate, total_months, loan_amount))
elif loan_amount > 0:
    monthly_payment = float(loan_amount / max(1, total_months))
else:
    monthly_payment = 0.0
annual_debt_service = monthly_payment * 12

# --- MODE SWITCH: STANDARD VS. GUIDED JUNIOR MINING TEMPLATE ---
mining_toggle_label = (
    "⛏️ Guided Junior Mining Template Mode (Ramp-Up → Steady-State → Closure)"
    if lang == "EN"
    else "⛏️ Mode Modèle Minier Guidé (Montée en puissance → Régime permanent → Fermeture)"
)
use_mining_template = st.toggle(mining_toggle_label, value=True)

if not use_mining_template:
    st.subheader(t["expected_cf"])
    cash_flows = []
    cols = st.columns(min(int(loan_term), 5))

    for year in range(1, int(loan_term) + 1):
        with cols[(year - 1) % len(cols)]:
            if year <= len(url_flows):
                default_cf = float(url_flows[year - 1])
            else:
                default_cf = float(url_flows[-1]) if url_flows else 35000.0

            cf_raw = st.text_input(
                label=t["year_noi"].format(year),
                value=f"{default_cf:,.2f}",
                key=f"cf_text_{year}",
            )

            cf_val = parse_number(cf_raw, default=default_cf)
            cash_flows.append(cf_val)
else:
    # --- PRIORITY 1: GUIDED JUNIOR MINING TEMPLATE & FULL OVERRIDE ---
    archetype_keys = list(MINING_ARCHETYPES.keys())
    selected_arch = st.selectbox(
        "Mining Archetype" if lang == "EN" else "Archétype Minier",
        options=archetype_keys,
        format_func=lambda k: MINING_ARCHETYPES[k]["label"][lang],
        key="mining_archetype_select",
    )

    arch_cfg = MINING_ARCHETYPES[selected_arch]
    defaults = arch_cfg["defaults"]
    is_copper = selected_arch == "open_pit_copper"

    # Commodity Price Deck + Active Spot/Deck Price Input
    deck_col1, deck_col2 = st.columns([2, 1])
    with deck_col1:
        price_deck = st.radio(
            f"Commodity Price Deck ({arch_cfg['commodity']} - {arch_cfg['price_unit']})"
            if lang == "EN"
            else f"Scénario de Prix ({arch_cfg['commodity']} - {arch_cfg['price_unit']})",
            options=["Downside", "Base", "Upside"],
            index=1,
            horizontal=True,
            key=f"price_deck_{selected_arch}",
        )
    with deck_col2:
        commodity_price = st.number_input(
            f"Active Price ({arch_cfg['price_unit']})",
            min_value=0.01,
            value=float(arch_cfg["price_decks"][price_deck]),
            step=0.10 if is_copper else 50.0,
            key=f"active_price_{selected_arch}_{price_deck}",
        )

    # 6 High-Level Operational Inputs
    c1, c2, c3 = st.columns(3)
    with c1:
        annual_tonnes = st.number_input(
            "Steady-State Tonnes / Yr" if lang == "EN" else "Tonnes / An (Croisière)",
            min_value=1_000.0,
            value=float(defaults["annual_tonnes"]),
            step=50_000.0 if is_copper else 10_000.0,
            key=f"tonnes_{selected_arch}",
        )
        aisc_per_unit = st.number_input(
            f"AISC ({arch_cfg['price_unit']})",
            min_value=0.0,
            value=float(defaults["aisc_per_unit"]),
            step=0.10 if is_copper else 25.0,
            key=f"aisc_{selected_arch}",
        )

    with c2:
        default_grade = defaults["grade_pct"] if is_copper else defaults["grade_g_t"]
        grade_label = "Head Grade (% Cu)" if is_copper else "Head Grade (g/t Au)"
        grade_value = st.number_input(
            grade_label,
            min_value=0.01,
            value=float(default_grade),
            step=0.05 if is_copper else 0.10,
            key=f"grade_{selected_arch}",
        )
        mine_life_years = st.number_input(
            "Mine Life (Years)" if lang == "EN" else "Durée de Vie (Ans)",
            min_value=1,
            max_value=30,
            value=int(defaults["mine_life_years"]),
            step=1,
            key=f"mine_life_{selected_arch}",
        )

    with c3:
        recovery_pct = st.number_input(
            "Metallurgical Recovery (%)"
            if lang == "EN"
            else "Récupération Métallurgique (%)",
            min_value=1.0,
            max_value=100.0,
            value=float(defaults["recovery_pct"]),
            step=0.5,
            key=f"recovery_{selected_arch}",
        )
        template_capex = st.number_input(
            "Initial CapEx ($)" if lang == "EN" else "CapEx Initial ($)",
            min_value=0.0,
            value=float(defaults["capex"]),
            step=1_000_000.0,
            key=f"capex_{selected_arch}",
        )

    # Regenerate base schedule only when template inputs change (preserves manual cell edits)
    current_sig = (
        selected_arch,
        price_deck,
        commodity_price,
        annual_tonnes,
        grade_value,
        recovery_pct,
        aisc_per_unit,
        int(mine_life_years),
        template_capex,
    )

    if (
        "mining_base_df" not in st.session_state
        or st.session_state.get("mining_template_sig") != current_sig
    ):
        st.session_state["mining_base_df"] = generate_mining_schedule(
            archetype_key=selected_arch,
            annual_tonnes=annual_tonnes,
            grade_value=grade_value,
            recovery_pct=recovery_pct,
            aisc_per_unit=aisc_per_unit,
            mine_life_years=int(mine_life_years),
            capex=template_capex,
            commodity_price=commodity_price,
            closure_pct_of_capex=defaults["closure_pct_of_capex"],
            ramp_up_factor=defaults["ramp_up_factor"],
            closure_factor=defaults["closure_factor"],
        )
        st.session_state["mining_template_sig"] = current_sig

    # Button to reset manual table edits back to template defaults
    hdr_col, reset_col = st.columns([4, 1])
    with hdr_col:
        st.caption(
            "Edit any cell below to override individual years (Annual NOI feeds directly into NPV, IRR & DSCR)."
            if lang == "EN"
            else "Modifiez n'importe quelle cellule ci-dessous pour ajuster chaque année (le NOI annuel alimente VAN, TRI et DSCR)."
        )
    with reset_col:
        if st.button("Reset Table" if lang == "EN" else "Réinitialiser", use_container_width=True):
            st.session_state["mining_template_sig"] = None
            st.rerun()

    # Full Year-by-Year Override Grid
    edited_mining_df = st.data_editor(
        st.session_state["mining_base_df"],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=["Year"],
        column_config={
            "Year": st.column_config.NumberColumn("Year", format="%d"),
            "Phase": st.column_config.SelectboxColumn(
                "Phase", options=["Ramp-Up", "Steady-State", "Closure"]
            ),
            "Tonnes_Milled": st.column_config.NumberColumn("Tonnes Milled", format="%,.0f"),
            "Payable_Metal": st.column_config.NumberColumn(
                f"Payable ({'lbs' if is_copper else 'oz'})", format="%,.0f"
            ),
            "Gross_Revenue": st.column_config.NumberColumn("Gross Revenue ($)", format="$%,.0f"),
            "AISC_Cost": st.column_config.NumberColumn("AISC Cost ($)", format="$%,.0f"),
            "Closure_Reserve": st.column_config.NumberColumn("Closure ($)", format="$%,.0f"),
            "Annual_NOI": st.column_config.NumberColumn("Annual NOI ($)", format="$%,.0f"),
        },
        key="mining_schedule_editor",
    )

    # Scale debt, equity & annual debt service to match the Mining Template CapEx
    sidebar_total_cap = max(1.0, loan_amount + initial_equity)
    debt_ratio = loan_amount / sidebar_total_cap
    loan_amount = template_capex * debt_ratio
    initial_equity = template_capex * (1.0 - debt_ratio)
    if loan_amount > 0 and monthly_interest_rate > 0:
        annual_debt_service = float(-npf.pmt(monthly_interest_rate, total_months, loan_amount) * 12)
    elif loan_amount > 0:
        annual_debt_service = float(loan_amount / max(1, loan_term))
    else:
        annual_debt_service = 0.0

    # Pull Annual NOI from the mining grid and align horizon with loan_term
    cash_flows = edited_mining_df["Annual_NOI"].astype(float).tolist()
    horizon_years = max(len(cash_flows), int(loan_term))
    if len(cash_flows) < horizon_years:
        cash_flows = cash_flows + [0.0] * (horizon_years - len(cash_flows))

# --- QUERY PARAMS & PERMALINK SYNC ---
cfs_str = ",".join([f"{cf:.2f}" for cf in cash_flows])

permalink_params = {
    "scenario": selected_preset_key,
    "currency": currency_symbol,
    "loan": f"{loan_amount:.2f}",
    "rate": f"{interest_rate * 100:.2f}",
    "term": f"{loan_term:.0f}",
    "fee": f"{discount_fee_pct * 100:.2f}",
    "equity": f"{initial_equity:.2f}",
    "hurdle": f"{hurdle_rate * 100:.2f}",
    "cfs": cfs_str,
}

st.query_params.update(permalink_params)

base_url = "https://kabamba-appraisal-tool.streamlit.app/?"
param_str = "&".join([f"{k}={v.replace(' ', '%20')}" for k, v in permalink_params.items()])
share_url = base_url + param_str

# --- SIDEBAR FOOTER (SUPPORT & PERMALINK) ---
st.sidebar.markdown("---")
st.sidebar.subheader(t["support_title"])
st.sidebar.markdown(
    """
    <a href="https://buymeacoffee.com/Kabamba" target="_blank">
        <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 45px !important;width: 160px !important;" >
    </a>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.subheader(t["share_title"])
st.sidebar.code(share_url, language="text")
st.sidebar.caption(t["share_caption"])

st.sidebar.markdown("---")
st.sidebar.markdown(t["feedback_text"])

# --- CALCULATE OUTLAYS & CASH FLOW STREAMS (RUNS FOR BOTH MODES) ---
total_initial_outlay = initial_equity + (loan_amount * discount_fee_pct)
# --- PRIORITY 3B: APPLY DEBT GRACE PERIOD, NSR ROYALTY & AFTER-TAX WATERFALL ---
grace_df = pd.DataFrame()
if debt_grace_years > 0 and loan_amount > 0:
    grace_df = build_grace_period_debt_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=interest_rate,
        loan_term_years=loan_term,
        grace_period_years=debt_grace_years,
        discount_fee_pct=discount_fee_pct,
    )

if not grace_df.empty:
    grace_payments = grace_df["Annual Payment"].tolist()
    debt_schedule = [
        grace_payments[yr - 1] if yr <= len(grace_payments) else 0.0
        for yr in range(1, len(cash_flows) + 1)
    ]
else:
    debt_schedule = [
        annual_debt_service if yr <= int(loan_term) else 0.0
        for yr in range(1, len(cash_flows) + 1)
    ]

pre_tax_cash_flows = list(cash_flows)
cash_flows, tax_waterfall_df = apply_royalty_and_tax_waterfall(
    pre_tax_cash_flows=pre_tax_cash_flows,
    total_initial_outlay=total_initial_outlay,
    nsr_royalty_pct=nsr_royalty_pct,
    corporate_tax_rate_pct=corporate_tax_rate_pct,
    use_mining_template=use_mining_template,
    mining_df=edited_mining_df if use_mining_template else None,
    debt_schedule=grace_df if not grace_df.empty else None,
    tax_shield_interest=True,
)
net_cash_flows = [cf - ds for cf, ds in zip(cash_flows, debt_schedule)]
full_cash_stream = [-total_initial_outlay] + net_cash_flows

# --- RESULTS & PERFORMANCE CALCULATIONS ---
if eval_mode == t["mode_lease"]:
    npv = (
        sum(cf / ((1 + periodic_rate) ** (yr * m)) for yr, cf in enumerate(cash_flows, 1))
        - total_initial_outlay
    )
    irr = None
else:
    npv = float(npf.npv(hurdle_rate, full_cash_stream))
    raw_irr = compute_robust_irr(full_cash_stream, hurdle_rate)
    irr = float(raw_irr) if (raw_irr is not None and not np.isnan(raw_irr)) else None

# Render Metric Cards with Dynamic Labels
st.markdown("---")
st.subheader(t["results_header"])
m1, m2, m3, m4 = st.columns(4)
m1.metric(t["annual_ds"], f"{currency_symbol}{annual_debt_service:,.2f}")
m2.metric(t["net_outlay"], f"{currency_symbol}{total_initial_outlay:,.2f}")

if eval_mode == t["mode_lease"]:
    m3.metric(t["npc_label"], f"{currency_symbol}{abs(npv):,.2f}")
    m4.metric(t["irr_label"], t["irr_na"])
else:
    m3.metric(t["npv_label"], f"{currency_symbol}{npv:,.2f}")
    m4.metric(t["irr_label"], f"{irr * 100:.2f}%" if irr is not None and not math.isnan(irr) else "N/A")

df = pd.DataFrame(
    {
        "Year": list(range(1, len(cash_flows) + 1)),
        "Operating Cash Flow (NOI)": cash_flows,
        "Debt Service": debt_schedule,
        "Net Cash Flow": net_cash_flows,
    }
)
fig = px.bar(
    df,
    x="Year",
    y=["Operating Cash Flow (NOI)", "Debt Service"],
    barmode="group",
    title=t["chart_title"],
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(df, use_container_width=True)
if not tax_waterfall_df.empty and (nsr_royalty_pct > 0 or corporate_tax_rate_pct > 0):
    with st.expander("🏛️ View NSR Royalty & After-Tax Cash Flow Waterfall", expanded=False):
        fmt_waterfall = tax_waterfall_df.copy()
        for col in [
            "Pre-Tax / Pre-Royalty CF",
            "NSR Royalty",
            "Depreciation Shield",
            "Taxable Income",
            "Corporate Tax",
            "After-Tax Net CF",
        ]:
            fmt_waterfall[col] = fmt_waterfall[col].map(lambda x: f"{currency_symbol}{x:,.0f}")
        st.dataframe(fmt_waterfall, use_container_width=True, hide_index=True)

# --- SUMMARY DATAFRAME FOR CSV & PDF DOWNLOAD ---
df_summary = pd.DataFrame(
    {
        "Metric": [
            t["loan_amount"],
            t["net_outlay"],
            t["annual_ds"],
            t["npv_label"],
            t["irr_label"],
            t["hurdle_rate"],
        ],
        "Value": [
            f"{currency_symbol}{loan_amount:,.2f}",
            f"{currency_symbol}{total_initial_outlay:,.2f}",
            f"{currency_symbol}{annual_debt_service:,.2f}",
            f"{currency_symbol}{npv:,.2f}",
            f"{irr * 100:.2f}%" if irr is not None and not math.isnan(irr) else "N/A",
            f"{hurdle_rate * 100:.2f}%",
        ],
    }
)
company_name = st.text_input(t["org_name_label"], value="Investment Appraisal Corp")
pdf_data = generate_pdf_report(
    selected_scenario=selected_preset_key,
    npv=npv,
    irr=irr * 100 if irr is not None and not math.isnan(irr) else 0.0,
    annual_ds=annual_debt_service,
    net_outlay=total_initial_outlay,
    hurdle_rate=hurdle_rate * 100,
    currency=currency_symbol,
    company_name=company_name,
)
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        label=t["dl_pdf"],
        data=pdf_data,
        file_name=f"{selected_preset_key.replace(' ', '_')}_Report.pdf",
        mime="application/pdf",
        key="pdf_download_btn",
    )
with col2:
    st.download_button(
        label=t["dl_csv"],
        data=df_summary.to_csv(index=False),
        file_name=f"{selected_preset_key.replace(' ', '_')}_Summary.csv",
        mime="text/csv",
        key="csv_download_btn",
    )

# --- NPV SENSITIVITY CHART ---
st.markdown("---")
st.subheader(t["sensitivity_header"])
rates = [r / 100 for r in range(1, 30)]
npvs = [npf.npv(r, full_cash_stream) for r in rates]
sens_df = pd.DataFrame({"Discount Rate (%)": [r * 100 for r in rates], "NPV ($)": npvs})
sens_fig = px.line(sens_df, x="Discount Rate (%)", y="NPV ($)", title=t["sensitivity_title"])
sens_fig.add_hline(y=0, line_dash="dash", line_color="red")
st.plotly_chart(sens_fig, use_container_width=True)

# ==============================================================================
# 💎 STEP 1: INSTITUTIONAL RISK & DSCR AUDIT MODULE (BILINGUAL)
# ==============================================================================
st.markdown("---")
st.markdown(f"## {t.get('audit_title', '💎 Institutional Risk & DSCR Audit')}")
st.caption(
    t.get(
        "audit_caption",
        "Evaluate debt service safety buffers and revenue stress sensitivity across operational lifecycles.",
    )
)
with st.expander(t.get("audit_expander", "📊 Debt Service Coverage & Sensitivity Matrix"), expanded=True):
    col_rev, col_metrics = st.columns([1, 1])
    with col_rev:
        st.subheader(t.get("stress_inputs", "Live Stress Inputs"))

        revenue_stress = st.slider(
            t.get("rev_stress_label", "Revenue / Commodity Spot Price Stress (%)"),
            min_value=-30,
            max_value=30,
            value=0,
            step=5,
            help=t.get(
                "rev_stress_help",
                "Simulates market price shifts (e.g., Gold spot adjustments relative to baseline).",
            ),
        )

        cost_stress = st.slider(
            t.get("cost_stress_label", "OPEX Cost Inflation Stress (%)"),
            min_value=-20,
            max_value=40,
            value=0,
            step=5,
            help=t.get(
                "cost_stress_help",
                "Simulates operational cost overruns or supply chain inflation.",
            ),
        )

    # Dynamic Stress & DSCR Calculations
    stress_multiplier = 1.0 + (revenue_stress / 100.0) - (cost_stress / 100.0)
    rate_decimal = (hurdle_rate / 100.0) if hurdle_rate > 1.0 else hurdle_rate

    stressed_op_cfs = [cf * stress_multiplier for cf in cash_flows]
    stressed_net_cfs = [cf - ds for cf, ds in zip(stressed_op_cfs, debt_schedule)]
    stressed_stream = [-total_initial_outlay] + stressed_net_cfs
    stressed_npv = float(npf.npv(rate_decimal, stressed_stream))

    active_debt_years = [
        op_cf / ds for op_cf, ds in zip(stressed_op_cfs, debt_schedule) if ds > 0
    ]
    if active_debt_years:
        live_dscr = float(np.mean(active_debt_years))
    else:
        live_dscr = 1.45 * stress_multiplier

    with col_metrics:
        st.subheader(t.get("valuation_impact", "Valuation Impact"))

        st.metric(
            label=f"{t.get('stressed_npv_label', 'Stressed NPV')} (@ {rate_decimal * 100:.1f}% Hurdle)",
            value=f"{currency_symbol}{stressed_npv:,.2f}",
            delta=f"{revenue_stress - cost_stress}% {t.get('net_stress_shift', 'Net Stress Shift')}",
            delta_color="normal" if (revenue_stress - cost_stress) >= 0 else "inverse",
        )

        st.markdown(t.get("covenant_status", "**Senior Debt Covenants Status:**"))
        if live_dscr >= 1.30:
            st.success(
                t.get(
                    "dscr_success",
                    "✅ Peak DSCR Protection: **{dscr:.2f}x** (Exceeds 1.30x Banking Standard)",
                ).format(dscr=live_dscr)
            )
        elif live_dscr >= 1.0:
            st.warning(
                t.get(
                    "dscr_warning",
                    "⚠️ Debt Coverage Tight: **{dscr:.2f}x** (Breaches 1.30x covenant buffer)",
                ).format(dscr=live_dscr)
            )
        else:
            st.error(
                t.get(
                    "dscr_error",
                    "🚨 DSCR Deficit: **{dscr:.2f}x** (Requires Debt Service Reserve Fund drawdown)",
                ).format(dscr=live_dscr)
            )

    st.info(
        t.get(
            "audit_note",
            "💡 **Institutional Audit Note:** Senior lenders require minimum Debt Service Coverage Ratios (DSCR) of **1.25x–1.35x**.",
        )
    )

    # ==============================================================================
# 🧠 PRIORITY 2: DECISION INTELLIGENCE (BANKABILITY, TORNADO & MONTE CARLO)
# ==============================================================================
st.markdown("---")
st.markdown("## 🧠 Decision Intelligence & Credit Committee Screening")
st.caption("Automated senior-debt bankability audit, ranked Tornado sensitivity, and stochastic Monte Carlo risk modeling.")

# 1. Automated Bankability / Covenant Flag
bankability = evaluate_bankability(
    npv=npv,
    irr=irr,
    hurdle_rate=hurdle_rate,
    loan_amount=loan_amount,
    total_initial_outlay=total_initial_outlay,
    cash_flows=cash_flows,
    debt_schedule=debt_schedule,
    interest_rate=interest_rate,
)

b_col1, b_col2, b_col3, b_col4 = st.columns([1.4, 1, 1, 1])
with b_col1:
    if bankability["badge"] == "success":
        st.success(f"### 🏦 Status: {bankability['status']}")
    elif bankability["badge"] == "warning":
        st.warning(f"### ⚠️ Status: {bankability['status']}")
    else:
        st.error(f"### 🚨 Status: {bankability['status']}")

b_col2.metric(
    "Minimum DSCR",
    f"{bankability['min_dscr']:.2f}x",
    help="Senior lenders typically require >= 1.25x–1.35x",
)
b_col3.metric(
    "LLCR",
    f"{bankability['llcr']:.2f}x" if not np.isnan(bankability["llcr"]) else "N/A",
    help="Loan Life Coverage Ratio = PV(CFADS over loan tenor) / Initial Debt",
)
b_col4.metric(
    "Equity Payback",
    f"{bankability['payback_year']:.1f} yrs" if bankability["payback_year"] is not None else "Unrecovered",
)

for r in bankability["reasons_fail"]:
    st.markdown(f"- ❌ {r}")
for r in bankability["reasons_warn"]:
    st.markdown(f"- ⚠️ {r}")
for r in bankability["reasons_pass"]:
    st.markdown(f"- ✅ {r}")

# 2. Tabs for Tornado Sensitivity & Monte Carlo Simulation
tab_tornado, tab_mc = st.tabs(
    ["🌪️ Tornado Driver Ranking", "🎲 Monte Carlo Simulation (500–1,000 Draws)"]
)

with tab_tornado:
    shock_pct = (
        st.slider("Parameter Perturbation Shock (±%)", min_value=5, max_value=30, value=15, step=5)
        / 100.0
    )
    sidebar_total_cap = max(1.0, loan_amount + initial_equity)
    debt_ratio_val = loan_amount / sidebar_total_cap

    tornado_df = run_tornado_analysis(
        use_mining_template=use_mining_template,
        base_npv=npv,
        base_irr=irr,
        hurdle_rate=hurdle_rate,
        cash_flows=cash_flows,
        total_initial_outlay=total_initial_outlay,
        debt_schedule=debt_schedule,
        mining_df=edited_mining_df if use_mining_template else None,
        base_capex=float(template_capex) if use_mining_template else total_initial_outlay,
        debt_ratio=debt_ratio_val,
        discount_fee_pct=discount_fee_pct,
        monthly_interest_rate=monthly_interest_rate,
        total_months=total_months,
        loan_term=loan_term,
        shock_pct=shock_pct,
    )

    top_drivers = tornado_df.head(5)
    st.markdown("**Top Value Drivers (Ranked by NPV & IRR Swing):**")
    for idx, row in top_drivers.iterrows():
        st.markdown(
            f"**#{idx + 1} {row['Driver']}** — NPV Swing: **{currency_symbol}{row['NPV_Swing']:,.0f}** "
            f"| IRR Swing: **{row['IRR_Swing_Pct']:.1f} percentage pts**"
        )

    tornado_plot_df = top_drivers.iloc[::-1]
    t_fig = go.Figure()
    t_fig.add_trace(
        go.Bar(
            y=tornado_plot_df["Driver"],
            x=tornado_plot_df["Downside_Delta"],
            name="Downside Impact",
            orientation="h",
            marker_color="#EF4444",
        )
    )
    t_fig.add_trace(
        go.Bar(
            y=tornado_plot_df["Driver"],
            x=tornado_plot_df["Upside_Delta"],
            name="Upside Impact",
            orientation="h",
            marker_color="#10B981",
        )
    )
    t_fig.update_layout(
        title=f"Tornado Chart: NPV Delta vs. Base ({currency_symbol}{npv:,.0f})",
        barmode="overlay",
        xaxis_title=f"NPV Change ({currency_symbol})",
        height=360,
    )
    st.plotly_chart(t_fig, use_container_width=True)

with tab_mc:
    mc_c1, mc_c2, mc_c3, mc_c4, mc_c5 = st.columns(5)
    n_sims = mc_c1.select_slider("Simulations", options=[500, 750, 1000], value=1000)
    price_vol = mc_c2.slider("Price Volatility (±σ %)", 5, 35, 15, 5) / 100.0
    opex_vol = mc_c3.slider("OPEX Volatility (±σ %)", 5, 30, 10, 5) / 100.0
    grade_vol = mc_c4.slider("Grade Volatility (±σ %)", 2, 25, 8, 2) / 100.0
    rec_vol = mc_c5.slider("Recovery Vol (±σ %)", 1, 15, 4, 1) / 100.0

    dist_df, mc_summary = run_monte_carlo(
        n_sims=n_sims,
        use_mining_template=use_mining_template,
        hurdle_rate=hurdle_rate,
        total_initial_outlay=total_initial_outlay,
        debt_schedule=debt_schedule,
        cash_flows=cash_flows,
        mining_df=edited_mining_df if use_mining_template else None,
        price_vol=price_vol,
        opex_vol=opex_vol,
        grade_vol=grade_vol,
        rec_vol=rec_vol,
        covenant_threshold=1.30,
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("P10 NPV (Downside)", f"{currency_symbol}{mc_summary['npv_p10']:,.0f}")
    k2.metric("P50 NPV (Median)", f"{currency_symbol}{mc_summary['npv_p50']:,.0f}")
    k3.metric("P90 NPV (Upside)", f"{currency_symbol}{mc_summary['npv_p90']:,.0f}")
    k4.metric("Prob(NPV > 0)", f"{mc_summary['prob_pos_npv']:.1f}%")
    k5.metric("Prob(DSCR < 1.30x)", f"{mc_summary['prob_breach']:.1f}%")

    pct_table = pd.DataFrame(
        {
            "Metric": ["NPV", "IRR (%)", "Min DSCR (x)"],
            "P10 (Conservative)": [
                f"{currency_symbol}{mc_summary['npv_p10']:,.0f}",
                f"{mc_summary['irr_p10']:.1f}%",
                f"{mc_summary['dscr_p10']:.2f}x",
            ],
            "P50 (Base Median)": [
                f"{currency_symbol}{mc_summary['npv_p50']:,.0f}",
                f"{mc_summary['irr_p50']:.1f}%",
                f"{mc_summary['dscr_p50']:.2f}x",
            ],
            "P90 (Optimistic)": [
                f"{currency_symbol}{mc_summary['npv_p90']:,.0f}",
                f"{mc_summary['irr_p90']:.1f}%",
                f"{mc_summary['dscr_p90']:.2f}x",
            ],
        }
    )
    st.dataframe(pct_table, use_container_width=True, hide_index=True)

    hist_fig = px.histogram(
        dist_df,
        x="NPV",
        nbins=40,
        title=f"Monte Carlo NPV Distribution ({n_sims} Draws)",
        color_discrete_sequence=["#2563EB"],
    )
    hist_fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Break-Even ($0)")
    hist_fig.add_vline(x=mc_summary["npv_p50"], line_dash="dot", line_color="green", annotation_text="P50")
    st.plotly_chart(hist_fig, use_container_width=True)

    # ==============================================================================
# PRIORITY 3A: SIDE-BY-SIDE SCENARIO & DEAL COMPARISON
# ==============================================================================
st.markdown("---")
st.subheader("📊 Side-by-Side Scenario & Deal Comparison")
st.caption(
    "Compare Downside Stress, Base Case, and Upside Case automatically—or snapshot "
    "alternative debt/template configurations to benchmark deals side by side."
)

if "deal_snapshots" not in st.session_state:
    st.session_state.deal_snapshots = []

comp_tab1, comp_tab2 = st.tabs(
    ["⚖️ Downside / Base / Upside Matrix", "📌 Saved Deal Snapshots"]
)

with comp_tab1:
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        down_price_pct = st.slider(
            "Downside Price / Inflow Shock (%)",
            min_value=-40,
            max_value=-5,
            value=-15,
            step=5,
            key="p3_down_price",
        )
    with sc2:
        down_opex_pct = st.slider(
            "Downside OpEx / AISC Shock (%)",
            min_value=0,
            max_value=35,
            value=10,
            step=5,
            key="p3_down_opex",
        )
    with sc3:
        up_price_pct = st.slider(
            "Upside Price / Inflow Shock (%)",
            min_value=5,
            max_value=40,
            value=15,
            step=5,
            key="p3_up_price",
        )

    three_case_df = generate_three_case_matrix(
        use_mining_template=use_mining_template,
        base_cash_flows=cash_flows,
        total_initial_outlay=total_initial_outlay,
        hurdle_rate=hurdle_rate,
        debt_schedule=debt_schedule,
        loan_amount=loan_amount,
        interest_rate=interest_rate,
        mining_df=edited_mining_df if use_mining_template else None,
        downside_price_shock=down_price_pct / 100.0,
        downside_opex_shock=down_opex_pct / 100.0,
        downside_capex_shock=0.15,
        upside_price_shock=up_price_pct / 100.0,
        upside_opex_shock=-0.05,
        upside_capex_shock=-0.05,
    )

    display_three_df = three_case_df.copy()
    display_three_df["Initial Outlay"] = display_three_df["Initial Outlay"].map(
        lambda x: f"{currency_symbol}{x:,.0f}"
    )
    display_three_df["Cumulative Net CF"] = display_three_df["Cumulative Net CF"].map(
        lambda x: f"{currency_symbol}{x:,.0f}"
    )
    display_three_df["NPV"] = display_three_df["NPV"].map(
        lambda x: f"{currency_symbol}{x:,.0f}"
    )
    display_three_df["IRR (%)"] = display_three_df["IRR (%)"].map(
        lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
    )
    display_three_df["Profitability Index"] = display_three_df["Profitability Index"].map(
        lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
    )
    display_three_df["Min DSCR"] = display_three_df["Min DSCR"].map(
        lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
    )
    display_three_df["LLCR"] = display_three_df["LLCR"].map(
        lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
    )
    display_three_df["Payback (Yrs)"] = display_three_df["Payback (Yrs)"].map(
        lambda x: f"{x:.1f} yrs" if pd.notna(x) else "Unrecovered"
    )

    st.dataframe(display_three_df, use_container_width=True, hide_index=True)
    st.plotly_chart(
        plot_scenario_comparison(three_case_df, currency_symbol=currency_symbol),
        use_container_width=True,
    )

with comp_tab2:
    snap_col1, snap_col2, snap_col3 = st.columns([2, 3, 1.5])
    with snap_col1:
        snap_name = st.text_input(
            "Snapshot Label",
            value=f"Option {len(st.session_state.deal_snapshots) + 1}",
            key="p3_snap_name",
        )
    with snap_col2:
        snap_note = st.text_input(
            "Deal Structure / Financing Note",
            placeholder="e.g., 60% Senior Debt @ 7.5% vs All-Equity",
            key="p3_snap_note",
        )
    with snap_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📌 Save Snapshot", use_container_width=True, key="p3_save_snap"):
            rec = make_snapshot_record(
                snapshot_name=snap_name,
                notes=snap_note,
                cash_flows=cash_flows,
                total_initial_outlay=total_initial_outlay,
                hurdle_rate=hurdle_rate,
                debt_schedule=debt_schedule,
                loan_amount=loan_amount,
                interest_rate=interest_rate,
            )
            st.session_state.deal_snapshots.append(rec)
            st.success(f"Saved '{snap_name}' to comparison deck.")

    if st.session_state.deal_snapshots:
        snap_df = pd.DataFrame(st.session_state.deal_snapshots)
        display_snap_df = snap_df.copy()
        for col in ["Initial Outlay", "Cumulative Net CF", "NPV"]:
            display_snap_df[col] = display_snap_df[col].map(
                lambda x: f"{currency_symbol}{x:,.0f}"
            )
        display_snap_df["IRR (%)"] = display_snap_df["IRR (%)"].map(
            lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A"
        )
        display_snap_df["Profitability Index"] = display_snap_df["Profitability Index"].map(
            lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
        )
        display_snap_df["Min DSCR"] = display_snap_df["Min DSCR"].map(
            lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
        )
        display_snap_df["LLCR"] = display_snap_df["LLCR"].map(
            lambda x: f"{x:.2f}x" if pd.notna(x) else "N/A"
        )
        display_snap_df["Payback (Yrs)"] = display_snap_df["Payback (Yrs)"].map(
            lambda x: f"{x:.1f} yrs" if pd.notna(x) else "Unrecovered"
        )

        st.dataframe(display_snap_df, use_container_width=True, hide_index=True)
        if len(snap_df) >= 2:
            st.plotly_chart(
                plot_scenario_comparison(snap_df, currency_symbol=currency_symbol),
                use_container_width=True,
            )
        if st.button("🗑️ Clear All Snapshots", key="p3_clear_snaps"):
            st.session_state.deal_snapshots = []
            st.rerun()
    else:
        st.info(
            "No custom snapshots saved yet. Configure any template or debt structure in the sidebar, "
            "label it above, and click **📌 Save Snapshot** to compare multiple deals side by side."
        )