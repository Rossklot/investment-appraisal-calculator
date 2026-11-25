import numpy as np
import pandas as pd


def build_grace_period_debt_schedule(
    loan_amount,
    annual_interest_rate,
    loan_term_years,
    grace_period_years=0,
    discount_fee_pct=0.0,
):
    """
    Generates an annual debt service schedule supporting an interest-only
    construction/ramp-up grace period before principal amortization begins.
    """
    loan_amount = float(loan_amount)
    annual_interest_rate = float(annual_interest_rate)
    loan_term_years = int(loan_term_years)
    grace_period_years = min(int(grace_period_years), max(0, loan_term_years - 1))

    if loan_amount <= 0 or loan_term_years <= 0:
        return pd.DataFrame(
            columns=[
                "Year",
                "Beginning Balance",
                "Annual Payment",
                "Interest Paid",
                "Principal Paid",
                "Ending Balance",
                "Phase",
            ]
        )

    amort_years = max(1, loan_term_years - grace_period_years)
    r = annual_interest_rate

    if r > 0:
        amort_payment = loan_amount * (r * (1.0 + r) ** amort_years) / ((1.0 + r) ** amort_years - 1.0)
    else:
        amort_payment = loan_amount / amort_years

    rows = []
    balance = loan_amount

    for yr in range(1, loan_term_years + 1):
        beg_bal = balance
        interest_paid = beg_bal * r

        if yr <= grace_period_years:
            principal_paid = 0.0
            payment = interest_paid
            phase = "Interest-Only Grace"
        else:
            payment = amort_payment
            principal_paid = min(beg_bal, max(0.0, payment - interest_paid))
            payment = interest_paid + principal_paid
            phase = "Amortizing"

        end_bal = max(0.0, beg_bal - principal_paid)
        rows.append(
            {
                "Year": yr,
                "Beginning Balance": beg_bal,
                "Annual Payment": payment,
                "Interest Paid": interest_paid,
                "Principal Paid": principal_paid,
                "Ending Balance": end_bal,
                "Phase": phase,
            }
        )
        balance = end_bal

    return pd.DataFrame(rows)


def apply_royalty_and_tax_waterfall(
    pre_tax_cash_flows,
    total_initial_outlay,
    nsr_royalty_pct=0.0,
    corporate_tax_rate_pct=0.0,
    use_mining_template=False,
    mining_df=None,
    debt_schedule=None,
    tax_shield_interest=True,
):
    """
    Applies Net Smelter Return (NSR) royalty and Corporate Income Tax (with straight-line
    CapEx depreciation shield and optional interest deductibility) to produce After-Tax Cash Flows.
    Returns (after_tax_cash_flows, waterfall_df).
    """
    n_years = len(pre_tax_cash_flows)
    if n_years == 0:
        return [], pd.DataFrame()

    nsr_rate = float(nsr_royalty_pct) / 100.0
    tax_rate = float(corporate_tax_rate_pct) / 100.0
    annual_depreciation = float(total_initial_outlay) / float(n_years) if total_initial_outlay > 0 else 0.0

    # Extract gross revenue if mining template is active so NSR applies strictly to revenue
    gross_revenues = []
    if use_mining_template and mining_df is not None and not mining_df.empty:
        payable_col = next((c for c in mining_df.columns if "payable" in str(c).lower()), None)
        price_col = next((c for c in mining_df.columns if "price" in str(c).lower()), None)
        if payable_col and price_col:
            gross_revenues = (mining_df[payable_col] * mining_df[price_col]).tolist()

    rows = []
    after_tax_cfs = []

    for i, pre_cf in enumerate(pre_tax_cash_flows):
        yr = i + 1
        pre_cf = float(pre_cf)

        # 1. NSR Royalty (on Gross Revenue in mining mode, or positive operating inflows in general mode)
        if gross_revenues and i < len(gross_revenues):
            rev_base = max(0.0, float(gross_revenues[i]))
        else:
            rev_base = max(0.0, pre_cf)

        royalty_paid = rev_base * nsr_rate
        post_royalty_cf = pre_cf - royalty_paid

        # 2. Interest expense lookup for tax shield
        interest_exp = 0.0
        if tax_shield_interest and debt_schedule is not None and not debt_schedule.empty:
            if "Year" in debt_schedule.columns and "Interest Paid" in debt_schedule.columns:
                yr_match = debt_schedule[debt_schedule["Year"] == yr]
                if not yr_match.empty:
                    interest_exp = float(yr_match["Interest Paid"].iloc[0])

        # 3. Taxable Income & Corporate Tax (only taxed when EBT > 0)
        depreciation = annual_depreciation if pre_cf > 0 else 0.0
        taxable_income = post_royalty_cf - depreciation - interest_exp
        taxes_paid = max(0.0, taxable_income) * tax_rate

        after_tax_cf = post_royalty_cf - taxes_paid
        after_tax_cfs.append(after_tax_cf)

        rows.append(
            {
                "Year": yr,
                "Pre-Tax / Pre-Royalty CF": pre_cf,
                "NSR Royalty": -royalty_paid,
                "Depreciation Shield": depreciation,
                "Taxable Income": max(0.0, taxable_income),
                "Corporate Tax": -taxes_paid,
                "After-Tax Net CF": after_tax_cf,
            }
        )

    return after_tax_cfs, pd.DataFrame(rows)