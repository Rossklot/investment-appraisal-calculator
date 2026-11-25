import numpy as np
import numpy_financial as npf
import pandas as pd
import streamlit as st


def compute_robust_irr(cash_stream, hurdle_rate=0.08):
    """Returns economically valid IRR even when closure costs create multiple sign changes."""
    if not cash_stream or cash_stream[0] >= 0:
        return np.nan
    coeffs = list(reversed(cash_stream))
    roots = np.roots(coeffs)
    real_roots = [r.real for r in roots if abs(r.imag) < 1e-6 and r.real > 0]
    valid_irrs = [(1.0 / r) - 1.0 for r in real_roots if ((1.0 / r) - 1.0) > -0.99]
    positive_irrs = [r for r in valid_irrs if r > 0]
    if positive_irrs:
        return float(max(positive_irrs))
    if valid_irrs:
        return float(min(valid_irrs, key=lambda x: abs(x - hurdle_rate)))
    raw = npf.irr(cash_stream)
    return float(raw) if (raw is not None and not np.isnan(raw)) else np.nan


def _eval_mining_metrics(
    base_df,
    price_mult,
    aisc_mult,
    grade_mult,
    rec_mult,
    capex_mult,
    hurdle_rate,
    debt_ratio,
    discount_fee_pct,
    monthly_interest_rate,
    total_months,
    loan_term,
    base_capex,
):
    """Helper to re-evaluate NPV, IRR, and Min DSCR under perturbed mining parameters."""
    df = base_df.copy()
    metal_factor = grade_mult * rec_mult
    rev = df["Gross_Revenue"].astype(float).values * price_mult * metal_factor
    aisc = df["AISC_Cost"].astype(float).values * aisc_mult * metal_factor
    closure = df["Closure_Reserve"].astype(float).values * capex_mult
    op_cfs = (rev - aisc - closure).tolist()

    horizon = max(len(op_cfs), int(loan_term))
    if len(op_cfs) < horizon:
        op_cfs = op_cfs + [0.0] * (horizon - len(op_cfs))

    capex = base_capex * capex_mult
    loan_amt = capex * debt_ratio
    equity_amt = capex * (1.0 - debt_ratio)
    outlay = equity_amt + (loan_amt * discount_fee_pct)

    if loan_amt > 0 and monthly_interest_rate > 0:
        ann_ds = float(-npf.pmt(monthly_interest_rate, total_months, loan_amt) * 12)
    elif loan_amt > 0:
        ann_ds = float(loan_amt / max(1, loan_term))
    else:
        ann_ds = 0.0

    debt_sched = [ann_ds if yr <= int(loan_term) else 0.0 for yr in range(1, len(op_cfs) + 1)]
    net_cfs = [cf - ds for cf, ds in zip(op_cfs, debt_sched)]
    stream = [-outlay] + net_cfs

    npv = float(npf.npv(hurdle_rate, stream))
    irr = compute_robust_irr(stream, hurdle_rate)
    active_dscrs = [cf / ds for cf, ds in zip(op_cfs, debt_sched) if ds > 0]
    min_dscr = float(min(active_dscrs)) if active_dscrs else 99.0
    return npv, irr, min_dscr


def run_tornado_analysis(
    use_mining_template,
    base_npv,
    base_irr,
    hurdle_rate,
    cash_flows=None,
    total_initial_outlay=0.0,
    debt_schedule=None,
    mining_df=None,
    base_capex=0.0,
    debt_ratio=0.0,
    discount_fee_pct=0.0,
    monthly_interest_rate=0.0,
    total_months=120,
    loan_term=10,
    shock_pct=0.15,
):
    """Computes ranked one-at-a-time parameter impacts on NPV and IRR."""
    rows = []

    if use_mining_template and mining_df is not None:
        drivers = [
            ("Commodity Price", "price"),
            ("AISC / Operating Cost", "aisc"),
            ("Head Grade", "grade"),
            ("Metallurgical Recovery", "rec"),
            ("Initial CapEx", "capex"),
            ("Discount / Hurdle Rate", "hurdle"),
        ]
        for label, key in drivers:
            s = min(shock_pct, 0.10) if key == "rec" else shock_pct
            low_params = dict(
                price_mult=1 - s if key == "price" else 1.0,
                aisc_mult=1 - s if key == "aisc" else 1.0,
                grade_mult=1 - s if key == "grade" else 1.0,
                rec_mult=1 - s if key == "rec" else 1.0,
                capex_mult=1 - s if key == "capex" else 1.0,
                hurdle_rate=max(0.005, hurdle_rate * (1 - s)) if key == "hurdle" else hurdle_rate,
            )
            high_params = dict(
                price_mult=1 + s if key == "price" else 1.0,
                aisc_mult=1 + s if key == "aisc" else 1.0,
                grade_mult=1 + s if key == "grade" else 1.0,
                rec_mult=1 + s if key == "rec" else 1.0,
                capex_mult=1 + s if key == "capex" else 1.0,
                hurdle_rate=hurdle_rate * (1 + s) if key == "hurdle" else hurdle_rate,
            )

            low_npv, low_irr, _ = _eval_mining_metrics(
                mining_df,
                **low_params,
                debt_ratio=debt_ratio,
                discount_fee_pct=discount_fee_pct,
                monthly_interest_rate=monthly_interest_rate,
                total_months=total_months,
                loan_term=loan_term,
                base_capex=base_capex,
            )
            high_npv, high_irr, _ = _eval_mining_metrics(
                mining_df,
                **high_params,
                debt_ratio=debt_ratio,
                discount_fee_pct=discount_fee_pct,
                monthly_interest_rate=monthly_interest_rate,
                total_months=total_months,
                loan_term=loan_term,
                base_capex=base_capex,
            )
            rows.append(
                {
                    "Driver": f"{label} (±{int(s*100)}%)",
                    "Low_Input_NPV": low_npv,
                    "High_Input_NPV": high_npv,
                    "Downside_Delta": min(low_npv, high_npv) - base_npv,
                    "Upside_Delta": max(low_npv, high_npv) - base_npv,
                    "NPV_Swing": abs(high_npv - low_npv),
                    "Low_IRR_Pct": (low_irr * 100) if not np.isnan(low_irr) else np.nan,
                    "High_IRR_Pct": (high_irr * 100) if not np.isnan(high_irr) else np.nan,
                    "IRR_Swing_Pct": abs((high_irr - low_irr) * 100)
                    if (not np.isnan(high_irr) and not np.isnan(low_irr))
                    else 0.0,
                }
            )
    else:
        cfs = np.array(cash_flows, dtype=float)
        ds = np.array(debt_schedule, dtype=float)
        drivers = ["Operating NOI", "Initial Outlay", "Discount Rate", "Debt Service"]
        for label in drivers:
            if label == "Operating NOI":
                low_s = [-total_initial_outlay] + (cfs * (1 - shock_pct) - ds).tolist()
                high_s = [-total_initial_outlay] + (cfs * (1 + shock_pct) - ds).tolist()
                low_npv, high_npv = float(npf.npv(hurdle_rate, low_s)), float(npf.npv(hurdle_rate, high_s))
                low_irr, high_irr = compute_robust_irr(low_s, hurdle_rate), compute_robust_irr(high_s, hurdle_rate)
            elif label == "Initial Outlay":
                low_s = [-total_initial_outlay * (1 - shock_pct)] + (cfs - ds).tolist()
                high_s = [-total_initial_outlay * (1 + shock_pct)] + (cfs - ds).tolist()
                low_npv, high_npv = float(npf.npv(hurdle_rate, low_s)), float(npf.npv(hurdle_rate, high_s))
                low_irr, high_irr = compute_robust_irr(low_s, hurdle_rate), compute_robust_irr(high_s, hurdle_rate)
            elif label == "Discount Rate":
                base_s = [-total_initial_outlay] + (cfs - ds).tolist()
                low_npv = float(npf.npv(max(0.005, hurdle_rate * (1 - shock_pct)), base_s))
                high_npv = float(npf.npv(hurdle_rate * (1 + shock_pct), base_s))
                low_irr = high_irr = base_irr if base_irr is not None else np.nan
            else:
                low_s = [-total_initial_outlay] + (cfs - ds * (1 - shock_pct)).tolist()
                high_s = [-total_initial_outlay] + (cfs - ds * (1 + shock_pct)).tolist()
                low_npv, high_npv = float(npf.npv(hurdle_rate, low_s)), float(npf.npv(hurdle_rate, high_s))
                low_irr, high_irr = compute_robust_irr(low_s, hurdle_rate), compute_robust_irr(high_s, hurdle_rate)

            rows.append(
                {
                    "Driver": f"{label} (±{int(shock_pct*100)}%)",
                    "Low_Input_NPV": low_npv,
                    "High_Input_NPV": high_npv,
                    "Downside_Delta": min(low_npv, high_npv) - base_npv,
                    "Upside_Delta": max(low_npv, high_npv) - base_npv,
                    "NPV_Swing": abs(high_npv - low_npv),
                    "Low_IRR_Pct": (low_irr * 100) if not np.isnan(low_irr) else np.nan,
                    "High_IRR_Pct": (high_irr * 100) if not np.isnan(high_irr) else np.nan,
                    "IRR_Swing_Pct": abs((high_irr - low_irr) * 100)
                    if (not np.isnan(high_irr) and not np.isnan(low_irr))
                    else 0.0,
                }
            )

    return pd.DataFrame(rows).sort_values("NPV_Swing", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def run_monte_carlo(
    n_sims,
    use_mining_template,
    hurdle_rate,
    total_initial_outlay,
    debt_schedule,
    cash_flows,
    mining_df=None,
    price_vol=0.15,
    opex_vol=0.10,
    grade_vol=0.08,
    rec_vol=0.04,
    covenant_threshold=1.30,
    seed=42,
):
    """Runs vectorized Monte Carlo draws in ~2ms and returns distribution DataFrame & summary stats."""
    rng = np.random.default_rng(seed)
    n_years = len(cash_flows)
    ds_arr = np.array(debt_schedule, dtype=float)
    disc_factors = np.array([(1.0 + hurdle_rate) ** t for t in range(1, n_years + 1)], dtype=float)

    if use_mining_template and mining_df is not None:
        base_rev = np.zeros(n_years)
        base_aisc = np.zeros(n_years)
        base_closure = np.zeros(n_years)
        L = min(len(mining_df), n_years)
        base_rev[:L] = mining_df["Gross_Revenue"].astype(float).values[:L]
        base_aisc[:L] = mining_df["AISC_Cost"].astype(float).values[:L]
        base_closure[:L] = mining_df["Closure_Reserve"].astype(float).values[:L]

        price_draws = np.clip(rng.normal(1.0, price_vol, size=(n_sims, 1)), 0.40, 2.00)
        opex_draws = np.clip(rng.normal(1.0, opex_vol, size=(n_sims, 1)), 0.60, 1.80)
        grade_draws = np.clip(rng.normal(1.0, grade_vol, size=(n_sims, 1)), 0.50, 1.50)
        rec_draws = np.clip(rng.normal(1.0, rec_vol, size=(n_sims, 1)), 0.70, 1.12)

        metal_mult = grade_draws * rec_draws
        sim_op_cfs = (base_rev * price_draws * metal_mult) - (base_aisc * opex_draws * metal_mult) - base_closure
    else:
        base_cf_arr = np.array(cash_flows, dtype=float)
        rev_draws = np.clip(rng.normal(1.0, price_vol, size=(n_sims, 1)), 0.40, 2.00)
        cost_draws = np.clip(rng.normal(0.0, opex_vol, size=(n_sims, 1)), -0.35, 0.50)
        sim_op_cfs = base_cf_arr * (rev_draws - cost_draws)

    sim_net_cfs = sim_op_cfs - ds_arr
    sim_npvs = -total_initial_outlay + np.sum(sim_net_cfs / disc_factors, axis=1)

    active_mask = ds_arr > 0
    if np.any(active_mask):
        dscr_matrix = sim_op_cfs[:, active_mask] / ds_arr[active_mask]
        sim_min_dscrs = np.min(dscr_matrix, axis=1)
    else:
        sim_min_dscrs = np.full(n_sims, 99.0)

    # Vectorized Newton-Raphson IRR across all draws simultaneously
    r_est = np.full(n_sims, max(0.05, hurdle_rate), dtype=float)
    t_idx = np.arange(1, n_years + 1, dtype=float)
    for _ in range(18):
        disc = (1.0 + r_est[:, None]) ** t_idx[None, :]
        f_val = -total_initial_outlay + np.sum(sim_net_cfs / disc, axis=1)
        df_val = -np.sum((t_idx[None, :] * sim_net_cfs) / (disc * (1.0 + r_est[:, None])), axis=1)
        safe_df = np.where(np.abs(df_val) < 1e-9, 1e-9, df_val)
        step = np.clip(f_val / safe_df, -0.5, 0.5)
        r_est = np.clip(r_est - step, -0.95, 10.0)
    sim_irrs = np.where(np.sum(sim_net_cfs, axis=1) > 0, r_est * 100.0, np.nan)

    valid_irrs = sim_irrs[~np.isnan(sim_irrs)]
    prob_pos_npv = float(np.mean(sim_npvs > 0) * 100.0)
    prob_breach = float(np.mean(sim_min_dscrs < covenant_threshold) * 100.0)

    summary = {
        "npv_p10": float(np.percentile(sim_npvs, 10)),
        "npv_p50": float(np.percentile(sim_npvs, 50)),
        "npv_p90": float(np.percentile(sim_npvs, 90)),
        "irr_p10": float(np.percentile(valid_irrs, 10)) if len(valid_irrs) else np.nan,
        "irr_p50": float(np.percentile(valid_irrs, 50)) if len(valid_irrs) else np.nan,
        "irr_p90": float(np.percentile(valid_irrs, 90)) if len(valid_irrs) else np.nan,
        "dscr_p10": float(np.percentile(sim_min_dscrs, 10)),
        "dscr_p50": float(np.percentile(sim_min_dscrs, 50)),
        "dscr_p90": float(np.percentile(sim_min_dscrs, 90)),
        "prob_pos_npv": prob_pos_npv,
        "prob_breach": prob_breach,
    }
    dist_df = pd.DataFrame(
        {
            "NPV": sim_npvs,
            "IRR_Pct": sim_irrs,
            "Min_DSCR": sim_min_dscrs,
        }
    )
    return dist_df, summary


def evaluate_bankability(
    npv,
    irr,
    hurdle_rate,
    loan_amount,
    total_initial_outlay,
    cash_flows,
    debt_schedule,
    interest_rate,
):
    """Evaluates project against senior project-finance credit benchmarks."""
    reasons_pass = []
    reasons_warn = []
    reasons_fail = []

    active_dscrs = [cf / ds for cf, ds in zip(cash_flows, debt_schedule) if ds > 0 and cf > 0]
    min_dscr = float(min(active_dscrs)) if active_dscrs else 99.0
    avg_dscr = float(np.mean(active_dscrs)) if active_dscrs else 99.0

    if loan_amount <= 0:
        reasons_pass.append("All-equity capital structure (zero senior debt default risk).")
    elif min_dscr >= 1.35:
        reasons_pass.append(f"Strong Minimum DSCR of **{min_dscr:.2f}x** (exceeds 1.35x senior mining/project covenant).")
    elif min_dscr >= 1.25:
        reasons_warn.append(f"Tight Minimum DSCR of **{min_dscr:.2f}x** (within 1.25x–1.35x threshold; Debt Service Reserve Account likely required).")
    else:
        reasons_fail.append(f"Minimum DSCR of **{min_dscr:.2f}x** breaches the 1.25x senior-debt floor (avg DSCR: {avg_dscr:.2f}x).")

    if loan_amount > 0:
        disc_r = interest_rate if interest_rate > 0 else hurdle_rate
        debt_tenor_cfs = [cf for cf, ds in zip(cash_flows, debt_schedule) if ds > 0]
        pv_cfads = sum(cf / ((1.0 + disc_r) ** t) for t, cf in enumerate(debt_tenor_cfs, 1))
        llcr = pv_cfads / loan_amount
        if llcr >= 1.50:
            reasons_pass.append(f"Healthy Loan Life Coverage Ratio (LLCR) of **{llcr:.2f}x** (exceeds 1.50x target).")
        elif llcr >= 1.25:
            reasons_warn.append(f"Moderate LLCR of **{llcr:.2f}x** (between 1.25x and 1.50x; limited tail buffer).")
        else:
            reasons_fail.append(f"Insufficient LLCR of **{llcr:.2f}x** (below 1.25x minimum collateral coverage).")
    else:
        llcr = np.nan

    cum_cf = 0.0
    payback_year = None
    for yr, (cf, ds) in enumerate(zip(cash_flows, debt_schedule), 1):
        net_cf = cf - ds
        prev_cum = cum_cf
        cum_cf += net_cf
        if cum_cf >= total_initial_outlay and payback_year is None:
            frac = (total_initial_outlay - prev_cum) / net_cf if net_cf > 0 else 0.0
            payback_year = (yr - 1) + max(0.0, min(1.0, frac))

    horizon = max(1, len(cash_flows))
    if payback_year is None:
        reasons_fail.append(f"Equity outlay is **not recovered** within the {horizon}-year project horizon.")
    elif payback_year <= horizon * 0.50:
        reasons_pass.append(f"Rapid equity payback in **{payback_year:.1f} years** (under 50% of project life).")
    elif payback_year <= horizon * 0.75:
        reasons_warn.append(f"Extended equity payback of **{payback_year:.1f} years** (50%–75% of project life).")
    else:
        reasons_fail.append(f"Late equity payback of **{payback_year:.1f} years** (exceeds 75% of project life).")

    if npv <= 0:
        reasons_fail.append(f"Negative NPV (**${npv:,.0f}**) fails to clear the {hurdle_rate * 100:.1f}% hurdle rate.")
    elif irr is not None and not np.isnan(irr) and irr < hurdle_rate + 0.02:
        reasons_warn.append(f"Thin IRR spread (**{irr * 100:.1f}%** vs. {hurdle_rate * 100:.1f}% hurdle rate).")
    else:
        irr_txt = f"{irr * 100:.1f}%" if (irr is not None and not np.isnan(irr)) else "N/A"
        reasons_pass.append(f"Positive NPV (**${npv:,.0f}**) and IRR (**{irr_txt}**) comfortably exceed the {hurdle_rate * 100:.1f}% hurdle.")

    if len(reasons_fail) == 0 and len(reasons_warn) <= 1:
        status = "Likely bankable"
        badge = "success"
    elif len(reasons_fail) <= 1 and npv > 0 and min_dscr >= 1.10:
        status = "Borderline"
        badge = "warning"
    else:
        status = "Not bankable"
        badge = "error"

    return {
        "status": status,
        "badge": badge,
        "min_dscr": min_dscr,
        "llcr": llcr,
        "payback_year": payback_year,
        "reasons_pass": reasons_pass,
        "reasons_warn": reasons_warn,
        "reasons_fail": reasons_fail,
    }