from __future__ import annotations

import math
from typing import Any


JURISDICTION_PRESETS: dict[str, dict[str, Any]] = {
    "DRC": {
        "en_label": "DR Congo (DRC)",
        "fr_label": "RD Congo (RDC)",
        "nsr_pct": 3.5,
        "tax_pct": 30.0,
        "reclamation_pct": 5.0,
        "en_note": "Mining Code royalties vary by substance (strategic vs. base/precious metals) with super-profit tax clauses under elevated price decks; community & closure obligations warrant early lender diligence.",
        "fr_note": "Les redevances du Code minier varient selon la substance (métaux stratégiques vs. métaux de base/précieux) avec clauses de super-profit en haut de cycle ; les obligations de fermeture et communautaires exigent une revue précoce.",
    },
    "Other Africa": {
        "en_label": "Other African Jurisdictions",
        "fr_label": "Autres Juridictions Africaines",
        "nsr_pct": 4.0,
        "tax_pct": 28.0,
        "reclamation_pct": 4.0,
        "en_note": "Typical sliding-scale or ad-valorem mineral royalties, local content/state participation expectations, and environmental bonding rules vary across West, Southern, and East African regimes.",
        "fr_note": "Les redevances minières progressives ou ad valorem, les attentes de participation locale/étatique et les règles de caution environnementale varient selon les régimes d'Afrique de l'Ouest, australe et de l'Est.",
    },
    "Canada": {
        "en_label": "Canada (Federal / Provincial)",
        "fr_label": "Canada (Fédéral / Provincial)",
        "nsr_pct": 2.0,
        "tax_pct": 26.5,
        "reclamation_pct": 6.0,
        "en_note": "Provincial mining taxes/royalties, Canadian Exploration/Development Expense (CEE/CDE) deductions, and Indigenous partnership & closure financial assurance rules shape net after-tax cash flows.",
        "fr_note": "Les taxes/redevances minières provinciales, les déductions CEE/CDE et les garanties financières de fermeture ainsi que les ententes avec les Premières Nations façonnent les flux nets.",
    },
    "Australia": {
        "en_label": "Australia (State Royalties)",
        "fr_label": "Australie (Redevances d'État)",
        "nsr_pct": 5.0,
        "tax_pct": 30.0,
        "reclamation_pct": 5.5,
        "en_note": "State-level ad-valorem or profit-based royalties (e.g., WA, QLD), 30% corporate tax rate, and strict rehabilitation cost estimation / security frameworks apply.",
        "fr_note": "Les redevances étatiques ad valorem ou sur bénéfices (ex. WA, QLD), l'impôt des sociétés à 30 % et les cadres stricts d'estimation et de garantie de réhabilitation s'appliquent.",
    },
}


def apply_reclamation_overlay(
    cash_flows: list[float],
    reclamation_pct: float,
    closure_years: int = 2,
) -> tuple[list[float], float]:
    """Distribute a percentage-based reclamation reserve across the tail/closure years."""
    cleaned = [float(x) for x in cash_flows]
    if not cleaned or reclamation_pct <= 0:
        return cleaned, 0.0

    positive_base = sum(max(0.0, cf) for cf in cleaned)
    total_reserve = positive_base * (float(reclamation_pct) / 100.0)
    if total_reserve <= 0:
        return cleaned, 0.0

    n = len(cleaned)
    tail_len = max(1, min(int(closure_years), n))
    per_year_charge = total_reserve / tail_len
    adjusted = list(cleaned)
    for idx in range(n - tail_len, n):
        adjusted[idx] = adjusted[idx] - per_year_charge
    return adjusted, total_reserve


def evaluate_esg_bankability_overlay(
    esg_score: int,
    reclamation_pct: float,
    esg_notes: str = "",
) -> dict[str, str]:
    """Produce a lightweight EN/FR ESG & reclamation adjustment note for credit/bankability review."""
    if esg_score >= 75 and reclamation_pct >= 3.0:
        en_stance = "Favorable ESG & Closure Buffer"
        fr_stance = "Profil ESG et Fermeture Favorable"
        en_detail = "Strong ESG posture and funded reclamation reserve support senior lender & strategic partner comfort."
        fr_detail = "Un score ESG solide et une réserve de fermeture provisionnée renforcent la confiance des prêteurs et partenaires."
    elif esg_score >= 50:
        en_stance = "Moderate ESG — Conditions Likely"
        fr_stance = "ESG Modéré — Conditions Probables"
        en_detail = "Acceptable baseline score; lenders may require binding environmental/reclamation milestones and community agreements."
        fr_detail = "Score intermédiaire ; les prêteurs pourront exiger des jalons de réhabilitation et accords communautaires."
    else:
        en_stance = "Elevated ESG / Closure Scrutiny"
        fr_stance = "Vigilance ESG / Fermeture Accrue"
        en_detail = "Lower ESG score or thin closure provisioning increases permitting, social-license, and credit-committee risk."
        fr_detail = "Un score ESG plus faible ou une provision de fermeture limitée accroît le risque d'autorisation et de comité de crédit."

    return {
        "en_stance": en_stance,
        "fr_stance": fr_stance,
        "en_detail": en_detail,
        "fr_detail": fr_detail,
        "notes": esg_notes.strip(),
    }


def compute_fire_coast_bridge(
    equity_proceeds_total: float,
    current_age: int,
    target_fire_age: int,
    annual_retirement_spend: float,
    current_portfolio: float = 0.0,
    expected_return_pct: float = 7.0,
    swr_pct: float = 4.0,
) -> dict[str, Any]:
    """Bridge project equity distributions into personal FIRE and Coast FIRE timelines."""
    r = max(0.0, float(expected_return_pct) / 100.0)
    swr = max(0.01, float(swr_pct) / 100.0)
    fire_number = max(0.0, float(annual_retirement_spend) / swr)
    years_to_target = max(1, int(target_fire_age) - int(current_age))

    baseline_fv = float(current_portfolio) * ((1.0 + r) ** years_to_target)
    post_deal_portfolio = float(current_portfolio) + max(0.0, float(equity_proceeds_total))
    post_deal_fv = post_deal_portfolio * ((1.0 + r) ** years_to_target)

    coast_fire_target_today = fire_number / ((1.0 + r) ** years_to_target) if fire_number > 0 else 0.0
    coast_achieved = post_deal_portfolio >= coast_fire_target_today

    years_to_fire_from_now: float | None = None
    if fire_number > 0 and post_deal_portfolio > 0:
        if post_deal_portfolio >= fire_number:
            years_to_fire_from_now = 0.0
        elif r > 0:
            years_to_fire_from_now = math.log(fire_number / post_deal_portfolio) / math.log(1.0 + r)

    estimated_fire_age = (
        round(float(current_age) + years_to_fire_from_now, 1)
        if years_to_fire_from_now is not None
        else None
    )

    return {
        "fire_number": fire_number,
        "coast_fire_target_today": coast_fire_target_today,
        "post_deal_portfolio": post_deal_portfolio,
        "coast_achieved": coast_achieved,
        "baseline_fv": baseline_fv,
        "post_deal_fv": post_deal_fv,
        "years_to_fire_from_now": years_to_fire_from_now,
        "estimated_fire_age": estimated_fire_age,
    }
