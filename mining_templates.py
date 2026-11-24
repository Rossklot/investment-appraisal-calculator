import numpy as np
import pandas as pd

# Price decks (USD): Downside / Base / Upside
# Gold in USD/oz; Copper in USD/lb (1 metric tonne = 2,204.62262 lbs)
LBS_PER_TONNE = 2204.6226247
TROY_OZ_PER_TONNE = 32150.7466

MINING_ARCHETYPES = {
    "open_pit_copper": {
        "label": {
            "EN": "Open-Pit Copper (Ramp-Up to Closure)",
            "FR": "Cuivre à Ciel Ouvert (Montée en Puissance à Fermeture)",
        },
        "commodity": "Copper",
        "price_unit": "USD/lb",
        "price_decks": {
            "Downside": 4.50,
            "Base": 5.60,
            "Upside": 6.60,
        },
        "defaults": {
            "annual_tonnes": 4_000_000.0,   # Ore milled per steady-state year
            "grade_pct": 0.85,              # Cu head grade (%)
            "recovery_pct": 88.0,           # Metallurgical recovery (%)
            "aisc_per_unit": 2.95,          # All-In Sustaining Cost (USD/lb payable Cu)
            "mine_life_years": 8,
            "capex": 140_000_000.0,
            "closure_pct_of_capex": 8.0,    # Final year reclamation / closure cost (% of CapEx)
            "ramp_up_factor": 0.65,         # Year 1 production factor vs steady state
            "closure_factor": 0.50,         # Final year production factor before closure drag
        },
    },
    "small_scale_gold": {
        "label": {
            "EN": "Small-Scale Gold (High-Grade / Lean CapEx)",
            "FR": "Or à Petite Échelle (Haute Teneur / CapEx Léger)",
        },
        "commodity": "Gold",
        "price_unit": "USD/oz",
        "price_decks": {
            "Downside": 3100.0,
            "Base": 3650.0,
            "Upside": 4200.0,
        },
        "defaults": {
            "annual_tonnes": 250_000.0,     # Ore processed per steady-state year
            "grade_g_t": 3.40,              # Au head grade (g/t)
            "recovery_pct": 90.0,           # Metallurgical recovery (%)
            "aisc_per_unit": 1650.0,        # All-In Sustaining Cost (USD/oz payable Au)
            "mine_life_years": 6,
            "capex": 28_000_000.0,
            "closure_pct_of_capex": 6.0,
            "ramp_up_factor": 0.60,
            "closure_factor": 0.55,
        },
    },
}


def build_phase_multipliers(
    mine_life: int,
    ramp_up_factor: float = 0.65,
    closure_factor: float = 0.50,
) -> tuple[list[float], list[str]]:
    """
    Generates year-by-year production multipliers and phase labels:
    Ramp-Up -> Steady-State -> Closure.
    """
    mine_life = max(1, int(mine_life))
    if mine_life == 1:
        return [1.0], ["Steady-State"]
    if mine_life == 2:
        return [ramp_up_factor, closure_factor], ["Ramp-Up", "Closure"]

    multipliers = [ramp_up_factor]
    phases = ["Ramp-Up"]

    steady_years = mine_life - 2
    multipliers.extend([1.0] * steady_years)
    phases.extend(["Steady-State"] * steady_years)

    multipliers.append(closure_factor)
    phases.append("Closure")
    return multipliers, phases


def generate_mining_schedule(
    archetype_key: str,
    annual_tonnes: float,
    grade_value: float,
    recovery_pct: float,
    aisc_per_unit: float,
    mine_life_years: int,
    capex: float,
    commodity_price: float,
    closure_pct_of_capex: float = 7.0,
    ramp_up_factor: float = 0.65,
    closure_factor: float = 0.50,
) -> pd.DataFrame:
    """
    Builds a multi-year operating cash-flow (NOI) schedule from high-level mining inputs.
    """
    multipliers, phases = build_phase_multipliers(
        mine_life=mine_life_years,
        ramp_up_factor=ramp_up_factor,
        closure_factor=closure_factor,
    )
    rec_frac = recovery_pct / 100.0
    closure_reserve_final = capex * (closure_pct_of_capex / 100.0)

    rows = []
    for idx, (mult, phase) in enumerate(zip(multipliers, phases), start=1):
        tonnes_yr = annual_tonnes * mult

        if archetype_key == "open_pit_copper":
            # grade_value is Cu % -> fraction of tonne
            payable_units = tonnes_yr * (grade_value / 100.0) * rec_frac * LBS_PER_TONNE
        else:
            # grade_value is Au g/t -> grams to troy oz (1 troy oz = 31.1034768 g)
            grams_recovered = tonnes_yr * grade_value * rec_frac
            payable_units = grams_recovered / 31.1034768

        gross_revenue = payable_units * commodity_price
        op_cost = payable_units * aisc_per_unit
        closure_drag = closure_reserve_final if idx == len(multipliers) else 0.0
        noi = gross_revenue - op_cost - closure_drag

        rows.append({
            "Year": idx,
            "Phase": phase,
            "Tonnes_Milled": round(tonnes_yr, 0),
            "Payable_Metal": round(payable_units, 2),
            "Gross_Revenue": round(gross_revenue, 2),
            "AISC_Cost": round(op_cost, 2),
            "Closure_Reserve": round(closure_drag, 2),
            "Annual_NOI": round(noi, 2),
        })

    return pd.DataFrame(rows)