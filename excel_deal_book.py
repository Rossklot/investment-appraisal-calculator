import io
from datetime import datetime
import numpy as np
import pandas as pd


def _auto_fit_worksheet(ws, min_width=14, max_width=42):
    """Adjusts column widths automatically based on cell content length."""
    for col in ws.columns:
        col_letter = col[0].column_letter
        longest = 0
        for cell in col:
            val = "" if cell.value is None else str(cell.value)
            longest = max(longest, len(val))
        ws.column_dimensions[col_letter].width = min(max_width, max(min_width, longest + 3))


def _style_table_header(ws, header_row=1, fill_hex="1E3A8A"):
    """Applies navy header styling if openpyxl styles are available."""
    try:
        from openpyxl.styles import Alignment, Font, PatternFill

        fill = PatternFill(start_color=fill_hex, end_color=fill_hex, fill_type="solid")
        font = Font(color="FFFFFF", bold=True, size=11)
        align = Alignment(horizontal="center", vertical="center", wrap_text=True)

        for cell in ws[header_row]:
            cell.fill = fill
            cell.font = font
            cell.alignment = align
        ws.row_dimensions[header_row].height = 24
    except Exception:
        pass


def build_excel_deal_book(
    org_name,
    currency_symbol,
    summary_metrics,
    cash_flow_df,
    tax_waterfall_df=None,
    tornado_df=None,
    scenario_df=None,
    snapshots_df=None,
):
    """
    Generates an in-memory multi-sheet Excel (.xlsx) Deal Book and returns raw bytes
    ready for st.download_button.
    """
    output = io.BytesIO()

    # Prefer openpyxl for rich styling; fall back cleanly if another engine is installed
    engine = "openpyxl"
    try:
        import openpyxl  # noqa: F401
    except ImportError:
        engine = None

    with pd.ExcelWriter(output, engine=engine) as writer:
        # ---------------------------------------------------------
        # TAB 1: EXECUTIVE SUMMARY
        # ---------------------------------------------------------
        exec_rows = [
            {"Section": "Deal Metadata", "Metric": "Organization / Project", "Value": org_name or "Investment Appraisal"},
            {"Section": "Deal Metadata", "Metric": "Generated Timestamp", "Value": datetime.now().strftime("%Y-%m-%d %H:%M")},
            {"Section": "Deal Metadata", "Metric": "Reporting Currency", "Value": currency_symbol},
        ]
        for section, metric, val in summary_metrics:
            exec_rows.append({"Section": section, "Metric": metric, "Value": val})

        exec_df = pd.DataFrame(exec_rows)
        exec_df.to_excel(writer, sheet_name="Executive Summary", index=False)

        # ---------------------------------------------------------
        # TAB 2: CASH FLOW & TAX WATERFALL
        # ---------------------------------------------------------
        cf_export = cash_flow_df.copy() if cash_flow_df is not None else pd.DataFrame()
        if (
            tax_waterfall_df is not None
            and not tax_waterfall_df.empty
            and not cf_export.empty
            and "Year" in cf_export.columns
            and "Year" in tax_waterfall_df.columns
        ):
            extra_cols = [c for c in tax_waterfall_df.columns if c != "Year" and c not in cf_export.columns]
            if extra_cols:
                cf_export = cf_export.merge(tax_waterfall_df[["Year"] + extra_cols], on="Year", how="left")
        elif cf_export.empty and tax_waterfall_df is not None and not tax_waterfall_df.empty:
            cf_export = tax_waterfall_df.copy()

        if cf_export.empty:
            cf_export = pd.DataFrame([{"Notice": "No annual cash flow schedule available."}])
        cf_export.to_excel(writer, sheet_name="Cash Flow & Tax Waterfall", index=False)

        # ---------------------------------------------------------
        # TAB 3: TORNADO SENSITIVITY
        # ---------------------------------------------------------
        if tornado_df is not None and not tornado_df.empty:
            t_export = tornado_df.copy()
        else:
            t_export = pd.DataFrame([{"Notice": "Tornado sensitivity data not generated for this run."}])
        t_export.to_excel(writer, sheet_name="Tornado Sensitivity", index=False)

        # ---------------------------------------------------------
        # TAB 4: SCENARIO COMPARISON
        # ---------------------------------------------------------
        frames = []
        if scenario_df is not None and not scenario_df.empty:
            s_copy = scenario_df.copy()
            s_copy.insert(0, "Group", "3-Case Matrix")
            frames.append(s_copy)
        if snapshots_df is not None and not snapshots_df.empty:
            snap_copy = snapshots_df.copy()
            snap_copy.insert(0, "Group", "Saved Snapshot")
            frames.append(snap_copy)

        if frames:
            scen_export = pd.concat(frames, ignore_index=True)
        else:
            scen_export = pd.DataFrame([{"Notice": "No scenario comparison data available."}])
        scen_export.to_excel(writer, sheet_name="Scenario Comparison", index=False)

        # Apply clean styling & column auto-fit when using openpyxl
        if engine == "openpyxl":
            wb = writer.book
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                _style_table_header(ws, header_row=1)
                _auto_fit_worksheet(ws)
                ws.freeze_panes = "A2"

    output.seek(0)
    return output.getvalue()