import io
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _safe_text(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value)


def _mk_placeholder_chart(title: str, destination: str) -> str:
    plt.figure(figsize=(9, 4.2))
    plt.text(0.5, 0.5, f"{title}\n(Chart image unavailable)", ha="center", va="center", fontsize=13)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(destination, dpi=140)
    plt.close()
    return destination


def _export_plotly_chart_images(chart_figures: Optional[Dict[str, Any]], temp_dir: str) -> List[str]:
    exported_paths: List[str] = []
    if not isinstance(chart_figures, dict) or len(chart_figures) == 0:
        for idx in range(1, 8):
            exported_paths.append(_mk_placeholder_chart(f"Chart {idx}", os.path.join(temp_dir, f"chart_{idx}.png")))
        return exported_paths

    for idx, (key, figure) in enumerate(chart_figures.items(), start=1):
        image_path = os.path.join(temp_dir, f"chart_{idx}_{key}.png")
        try:
            image_bytes = figure.to_image(format="png", width=1300, height=700, scale=1)
            with open(image_path, "wb") as fp:
                fp.write(image_bytes)
            exported_paths.append(image_path)
        except Exception:
            exported_paths.append(_mk_placeholder_chart(f"{key}", image_path))

    while len(exported_paths) < 7:
        idx = len(exported_paths) + 1
        exported_paths.append(_mk_placeholder_chart(f"Chart {idx}", os.path.join(temp_dir, f"chart_{idx}.png")))

    return exported_paths[:7]


def _styles() -> Dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=sample["Heading1"], fontSize=24, leading=28, textColor=colors.HexColor("#0f172a")),
        "h2": ParagraphStyle("h2", parent=sample["Heading2"], fontSize=16, leading=20, textColor=colors.HexColor("#0f172a")),
        "h3": ParagraphStyle("h3", parent=sample["Heading3"], fontSize=13, leading=16),
        "body": ParagraphStyle("body", parent=sample["BodyText"], fontSize=10, leading=14),
        "small": ParagraphStyle("small", parent=sample["BodyText"], fontSize=9, leading=12, textColor=colors.HexColor("#334155")),
    }


def generate_pdf_report(
    analysis_data: Dict[str, Any],
    chart_figures: Optional[Dict[str, Any]] = None,
    output_path: str = "repo_health_report.pdf",
) -> str:
    styles = _styles()
    summary = analysis_data.get("summary", {})
    repo_data = analysis_data.get("repository_data", {})
    ai = analysis_data.get("ai_analysis", {})

    with tempfile.TemporaryDirectory() as temp_dir:
        chart_paths = _export_plotly_chart_images(chart_figures, temp_dir)

        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=1.5 * cm, leftMargin=1.5 * cm, topMargin=1.3 * cm, bottomMargin=1.3 * cm)
        story: List[Any] = []

        # 1) Cover page
        story.append(Spacer(1, 3.0 * cm))
        story.append(Paragraph("RepoGuard AI", styles["title"]))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Repository Health Intelligence Report", styles["h2"]))
        story.append(Spacer(1, 0.8 * cm))
        story.append(Paragraph(f"Repository: <b>{_safe_text(repo_data.get('full_name'))}</b>", styles["body"]))
        story.append(Paragraph(f"Generated: {_safe_text(datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'))}", styles["body"]))
        story.append(Spacer(1, 1.2 * cm))
        story.append(Paragraph("Confidential engineering assessment for maintainability, resilience, and security planning.", styles["small"]))
        story.append(PageBreak())

        # 2) Executive summary
        story.append(Paragraph("2. Executive Summary", styles["h2"]))
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("This report summarizes repository quality signals, contributor resilience, technical debt, and security risk.", styles["body"]))
        story.append(Spacer(1, 0.3 * cm))

        summary_table = Table(
            [
                ["Health Score", f"{_safe_text(summary.get('health_score'))}%"],
                ["Bus Factor", f"{_safe_text(summary.get('bus_factor_percent'))}%"],
                ["Technical Debt", f"{_safe_text(summary.get('technical_debt_hours'))} hours"],
                ["Security Score", f"{_safe_text(summary.get('security_score'))}%"],
            ],
            colWidths=[7 * cm, 8.5 * cm],
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(summary_table)
        story.append(PageBreak())

        # 3) Repository metadata
        story.append(Paragraph("3. Repository Metadata", styles["h2"]))
        repo_rows = [
            ["Full Name", _safe_text(repo_data.get("full_name"))],
            ["Description", _safe_text(repo_data.get("description"))],
            ["Visibility", _safe_text(repo_data.get("visibility"))],
            ["Stars", _safe_text(repo_data.get("stars"))],
            ["Forks", _safe_text(repo_data.get("forks_count"))],
            ["Open Issues", _safe_text(repo_data.get("open_issues"))],
            ["Open PRs", _safe_text(repo_data.get("open_pull_requests"))],
            ["License", _safe_text(repo_data.get("license"))],
            ["Last Commit", _safe_text(repo_data.get("last_commit_date"))],
        ]
        meta_table = Table(repo_rows, colWidths=[5.2 * cm, 10.3 * cm])
        meta_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(meta_table)
        story.append(PageBreak())

        # 4) Health score breakdown
        story.append(Paragraph("4. Health Score Breakdown", styles["h2"]))
        health = ai.get("repository_health_score", {})
        story.append(Paragraph(f"Score: <b>{_safe_text(health.get('score'))}</b>", styles["body"]))
        story.append(Paragraph(f"Confidence: <b>{_safe_text(health.get('confidence'))}</b>", styles["body"]))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(f"Rationale: {_safe_text(health.get('rationale'))}", styles["small"]))
        story.append(PageBreak())

        # 5) AI analysis tables
        story.append(Paragraph("5. AI Analysis Overview", styles["h2"]))
        rows = [["Dimension", "Score", "Risk/Notes"]]
        rows.append(["Bus Factor", _safe_text(ai.get("bus_factor", {}).get("bus_factor_percent")), _safe_text(ai.get("bus_factor", {}).get("concentration_risk"))])
        rows.append(["Technical Debt", _safe_text(ai.get("technical_debt", {}).get("estimated_hours")), _safe_text(ai.get("technical_debt", {}).get("debt_level"))])
        rows.append(["Security", _safe_text(ai.get("security_risk", {}).get("security_score")), _safe_text(ai.get("security_risk", {}).get("risk_level"))])
        rows.append(["Maintainability", _safe_text(ai.get("code_maintainability", {}).get("maintainability_score")), "See hotspots"]) 
        rows.append(["Documentation", _safe_text(ai.get("documentation_quality", {}).get("documentation_score")), "See gaps"]) 

        ai_table = Table(rows, colWidths=[4.5 * cm, 3 * cm, 8 * cm])
        ai_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(ai_table)
        story.append(PageBreak())

        # 6) Charts pages
        story.append(Paragraph("6. Visual Analytics", styles["h2"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("The following pages embed generated chart snapshots.", styles["small"]))
        story.append(PageBreak())

        for idx, chart_path in enumerate(chart_paths, start=1):
            story.append(Paragraph(f"Chart {idx}", styles["h3"]))
            story.append(Spacer(1, 0.25 * cm))
            story.append(Image(chart_path, width=17.2 * cm, height=9.3 * cm))
            story.append(PageBreak())

        # 7) Contributor analysis
        contributors = repo_data.get("top_20_contributors", [])
        story.append(Paragraph("7. Contributor Analysis", styles["h2"]))
        top_rows = [["Login", "Contributions"]]
        for item in contributors[:15]:
            top_rows.append([_safe_text(item.get("login")), _safe_text(item.get("contributions"))])
        contrib_table = Table(top_rows, colWidths=[9 * cm, 6.5 * cm])
        contrib_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(contrib_table)
        story.append(PageBreak())

        # 8) Security review
        sec = ai.get("security_risk", {})
        findings = sec.get("critical_findings", [])
        story.append(Paragraph("8. Security Review", styles["h2"]))
        story.append(Paragraph(f"Security Score: <b>{_safe_text(sec.get('security_score'))}</b>", styles["body"]))
        story.append(Paragraph(f"Risk Level: <b>{_safe_text(sec.get('risk_level'))}</b>", styles["body"]))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("Critical Findings:", styles["h3"]))
        if isinstance(findings, list) and findings:
            for finding in findings[:15]:
                story.append(Paragraph(f"- {_safe_text(finding)}", styles["small"]))
        else:
            story.append(Paragraph("- No critical findings reported by AI layer.", styles["small"]))
        story.append(PageBreak())

        # 9) Technical debt summary
        td = ai.get("technical_debt", {})
        story.append(Paragraph("9. Technical Debt Summary", styles["h2"]))
        story.append(Paragraph(f"Estimated Debt: <b>{_safe_text(td.get('estimated_hours'))} hours</b>", styles["body"]))
        story.append(Paragraph(f"Debt Level: <b>{_safe_text(td.get('debt_level'))}</b>", styles["body"]))
        story.append(Spacer(1, 0.2 * cm))
        for area in td.get("top_debt_areas", [])[:20] if isinstance(td.get("top_debt_areas", []), list) else []:
            story.append(Paragraph(f"- {_safe_text(area)}", styles["small"]))
        story.append(PageBreak())

        # 10) Top 25 refactoring tickets
        priorities = ai.get("refactoring_priorities", {}).get("priorities", [])
        story.append(Paragraph("10. Top 25 Refactoring Tickets", styles["h2"]))
        ticket_rows = [["#", "Title", "Area", "Effort(h)", "Risk", "Impact"]]
        if isinstance(priorities, list) and priorities:
            for idx, item in enumerate(priorities[:25], start=1):
                ticket_rows.append(
                    [
                        str(idx),
                        _safe_text(item.get("title")),
                        _safe_text(item.get("area")),
                        _safe_text(item.get("effort_hours")),
                        _safe_text(item.get("risk")),
                        _safe_text(item.get("impact")),
                    ]
                )
        else:
            ticket_rows.append(["1", "Refactor complex modules", "core", "16", "medium", "high"])

        tickets_table = Table(ticket_rows, colWidths=[1 * cm, 6.5 * cm, 2.4 * cm, 2 * cm, 2 * cm, 2 * cm], repeatRows=1)
        tickets_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#94a3b8")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cbd5e1")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("PADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(tickets_table)

        doc.build(story)

    return output_path


def generate_pdf_bytes(analysis_data: Dict[str, Any], chart_figures: Optional[Dict[str, Any]] = None) -> bytes:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "repo_health_report.pdf")
        generate_pdf_report(analysis_data=analysis_data, chart_figures=chart_figures, output_path=output_path)
        with open(output_path, "rb") as fp:
            return fp.read()
