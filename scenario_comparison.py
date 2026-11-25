import numpy as np
import pandas as pd
import numpy_financial as npf
import plotly.graph_objects as go
from decision_intelligence import compute_robust_irr, evaluate_bankability


def _find_col(df, keywords):
    """Finds the first column matching any keyword (case-insensitive)."""
    if df is None or df.empty:
        return None
    for col in df.columns:
        low = str(col).lower()
        if any(k.lower() in low for k in keywords):
            return col
    return None


def _build_case_metrics(
    case_name,
    description,
    cash_flows,
    total_initial_outlay,
    hurdle_rate,
    debt_schedule,
    loan_amount,
    interest_rate,
):
    """Computes standardized institutional appraisal metrics for a single cash-flow scenario."""
    stream = [-float(total_initial_outlay)] + [float(cf) for cf in cash_flows]
    case_npv = float(npf.npv(hurdle_rate, stream))
    case_irr = compute_robust_irr(stream, hurdle_rate=hurdle_rate)

    bank = evaluate_bankability(
        npv=case_npv,
        irr=case_irr,
        hurdle_rate=hurdle_rate,
        loan_amount=loan_amount,
        total_initial_outlay=total_initial_outlay,
        cash_flows=cash_flows,
        debt_schedule=debt_schedule,
        interest_rate=interest_rate,
    )

    cumulative_cf = float(sum(cash_flows) - total_initial_outlay)
    pi = (
        (case_npv + total_initial_outlay) / total_initial_outlay
        if total_initial_outlay > 0
        else np.nan
    )

    return {
        "Scenario": case_name,
        "Assumptions": description,
        "Initial Outlay": float(total_initial_outlay),
        "Cumulative Net CF": cumulative_cf,
        "NPV": case_npv,
        "IRR (%)": float(case_irr * 100.0) if not np.isnan(case_irr) else np.nan,
        "Profitability Index": float(pi) if not np.isnan(pi) else np.nan,
        "Min DSCR": float(bank["min_dscr"]) if not np.isnan(bank["min_dscr"]) else np.nan,
        "LLCR": float(bank["llcr"]) if not np.isnan(bank["llcr"]) else np.nan,
        "Payback (Yrs)": float(bank["payback_year"]) if bank["payback_year"] is not None else np.nan,
        "Bankability": bank["status"],
    }


def generate_three_case_matrix(
    use_mining_template,
    base_cash_flows,
    total_initial_outlay,
    hurdle_rate,
    debt_schedule,
    loan_amount,
    interest_rate,
    mining_df=None,
    downside_price_shock=-0.15,
    downside_opex_shock=0.10,
    downside_capex_shock=0.15,
    upside_price_shock=0.15,
    upside_opex_shock=-0.05,
    upside_capex_shock=-0.05,
):
    """Generates Downside, Base Case, and Upside scenarios from current model parameters."""
    cases = []

    price_col = _find_col(mining_df, ["price"]) if use_mining_template else None
    aisc_col = _find_col(mining_df, ["aisc", "opex", "cost"]) if use_mining_template else None
    capex_col = _find_col(mining_df, ["capex", "sustaining"]) if use_mining_template else None
    closure_col = _find_col(mining_df, ["closure", "reclam"]) if use_mining_template else None
    payable_col = _find_col(mining_df, ["payable"]) if use_mining_template else None

    if (
        use_mining_template
        and mining_df is not None
        and not mining_df.empty
        and all([price_col, aisc_col, payable_col])
    ):
        def _calc_mining_cfs(df_mod):
            capex_vals = df_mod[capex_col] if capex_col else 0.0
            closure_vals = df_mod[closure_col] if closure_col else 0.0
            return (
                df_mod[payable_col] * (df_mod[price_col] - df_mod[aisc_col])
                - capex_vals
                - closure_vals
            ).tolist()

        # --- DOWNSIDE CASE (Mining) ---
        down_df = mining_df.copy()
        down_df[price_col] = down_df[price_col] * (1.0 + downside_price_shock)
        down_df[aisc_col] = down_df[aisc_col] * (1.0 + downside_opex_shock)
        if capex_col:
            down_df[capex_col] = down_df[capex_col] * (1.0 + downside_capex_shock)
        down_cfs = _calc_mining_cfs(down_df)
        down_outlay = float(total_initial_outlay) * (1.0 + downside_capex_shock)

        # --- UPSIDE CASE (Mining) ---
        up_df = mining_df.copy()
        up_df[price_col] = up_df[price_col] * (1.0 + upside_price_shock)
        up_df[aisc_col] = up_df[aisc_col] * (1.0 + upside_opex_shock)
        if capex_col:
            up_df[capex_col] = up_df[capex_col] * (1.0 + upside_capex_shock)
        up_cfs = _calc_mining_cfs(up_df)
        up_outlay = float(total_initial_outlay) * (1.0 + upside_capex_shock)

        down_desc = (
            
            f"CapEx {downside_capex_shock:+.0%}"
        )
        up_desc = (
            f"Price {upside_price_shock:+.0%}, AISC {upside_opex_shock:+.0%}, "
            f"CapEx {upside_capex_shock:+.0%}"
        )
    else:
        # --- GENERAL / NON-MINING CASH FLOW MODE ---
        down_cfs = [
            float(cf) * (1.0 + downside_price_shock) if cf > 0 else float(cf) * (1.0 + downside_opex_shock)
            for cf in base_cash_flows
        ]
        down_outlay = float(total_initial_outlay) * (1.0 + downside_capex_shock)

        up_cfs = [
            float(cf) * (1.0 + upside_price_shock) if cf > 0 else float(cf) * (1.0 + upside_opex_shock)
            for cf in base_cash_flows
        ]
        up_outlay = float(total_initial_outlay) * (1.0 + upside_capex_shock)

        down_desc = f"Inflows {downside_price_shock:+.0%}, Outlay {downside_capex_shock:+.0%}"
        up_desc = f"Inflows {upside_price_shock:+.0%}, Outlay {upside_capex_shock:+.0%}"

    cases.append(
        _build_case_metrics(
            case_name="Downside Stress",
            description=down_desc,
            cash_flows=down_cfs,
            total_initial_outlay=down_outlay,
            hurdle_rate=hurdle_rate,
            debt_schedule=debt_schedule,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
        )
    )
    cases.append(
        _build_case_metrics(
            case_name="Base Case (Active)",
            description="Current active model inputs",
            cash_flows=base_cash_flows,
            total_initial_outlay=total_initial_outlay,
            hurdle_rate=hurdle_rate,
            debt_schedule=debt_schedule,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
        )
    )
    cases.append(
        _build_case_metrics(
            case_name="Upside Case",
            description=up_desc,
            cash_flows=up_cfs,
            total_initial_outlay=up_outlay,
            hurdle_rate=hurdle_rate,
            debt_schedule=debt_schedule,
            loan_amount=loan_amount,
            interest_rate=interest_rate,
        )
    )

    return pd.DataFrame(cases)


def make_snapshot_record(
    snapshot_name,
    notes,
    cash_flows,
    total_initial_outlay,
    hurdle_rate,
    debt_schedule,
    loan_amount,
    interest_rate,
):
    """Captures the active deal structure as a reusable snapshot row."""
    return _build_case_metrics(
        case_name=snapshot_name,
        description=notes if notes.strip() else "Saved deal snapshot",
        cash_flows=cash_flows,
        total_initial_outlay=total_initial_outlay,
        hurdle_rate=hurdle_rate,
        debt_schedule=debt_schedule,
        loan_amount=loan_amount,
        interest_rate=interest_rate,
    )


def plot_scenario_comparison(df, currency_symbol="$"):
    """Creates a clean side-by-side Plotly comparison chart for NPV across scenarios."""
    palette = ["#DC2626", "#1D4ED8", "#059669", "#7C3AED", "#D97706", "#0891B2"]
    bar_colors = [palette[i % len(palette)] for i in range(len(df))]

    fig = go.Figure(
        data=[
            go.Bar(
                x=df["Scenario"],
                y=df["NPV"],
                marker_color=bar_colors,
                text=[f"{currency_symbol}{v:,.0f}" for v in df["NPV"]],
                textposition="outside",
            )
        ]
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#64748B")
    fig.update_layout(
        title="Net Present Value (NPV) Comparison Across Scenarios",
        yaxis_title=f"NPV ({currency_symbol})",
        xaxis_title="",
        template="plotly_white",
        height=380,
        margin=dict(t=55, b=30, l=20, r=20),
    )
    return fig