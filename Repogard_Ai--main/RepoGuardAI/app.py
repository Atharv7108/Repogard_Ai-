import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analyzer import AnalysisError, analyze_repository
from charts import build_all_charts
from pdf_generator import generate_pdf_bytes


st.set_page_config(page_title="RepoGuard AI", page_icon="🛡️", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

            .stApp {
                font-family: 'Space Grotesk', sans-serif;
                background:
                    radial-gradient(circle at 10% 10%, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95) 30%),
                    linear-gradient(120deg, #020617 0%, #0f172a 45%, #111827 100%);
                color: #e5e7eb;
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
            }

            .hero {
                padding: 1.2rem 1.4rem;
                border: 1px solid rgba(99, 102, 241, 0.35);
                border-radius: 16px;
                background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.7));
                box-shadow: 0 10px 30px rgba(2, 6, 23, 0.45);
                margin-bottom: 1rem;
            }

            .hero h1 {
                margin: 0;
                font-size: 2rem;
                letter-spacing: 0.02em;
            }

            .hero p {
                margin: 0.35rem 0 0;
                color: #cbd5e1;
                font-size: 0.98rem;
            }

            .metric-card {
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 14px;
                background: linear-gradient(160deg, rgba(15, 23, 42, 0.75), rgba(51, 65, 85, 0.4));
                padding: 1rem;
                min-height: 120px;
            }

            .metric-label {
                color: #94a3b8;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }

            .metric-value {
                color: #f8fafc;
                font-size: 1.9rem;
                font-weight: 700;
                margin-top: 0.2rem;
            }

            .section-title {
                font-size: 1.2rem;
                font-weight: 600;
                margin-top: 1.2rem;
                margin-bottom: 0.7rem;
            }

            .subtext {
                color: #94a3b8;
                font-size: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def placeholder_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=f"{title}<br><sup>Will render after analysis</sup>",
        showarrow=False,
        font={"size": 16, "color": "#cbd5e1"},
        xref="paper",
        yref="paper",
        align="center",
    )
    fig.update_layout(
        title={"text": title, "font": {"size": 14}},
        height=290,
        margin={"l": 20, "r": 20, "t": 45, "b": 20},
        paper_bgcolor="rgba(15, 23, 42, 0.85)",
        plot_bgcolor="rgba(15, 23, 42, 0.85)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig


def show_metric_card(label: str, value: str, subtext: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_styles()

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "analysis_error" not in st.session_state:
        st.session_state.analysis_error = None
    if "pdf_report_bytes" not in st.session_state:
        st.session_state.pdf_report_bytes = None
    if "pdf_error" not in st.session_state:
        st.session_state.pdf_error = None

    st.markdown(
        """
        <div class="hero">
            <h1>RepoGuard AI</h1>
            <p>AI-powered GitHub repository health diagnostics and reporting.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
    )

    analyze_clicked = st.button("🚀 ANALYZE", type="primary", width="stretch")
    if analyze_clicked:
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.")
        else:
            st.session_state.analysis_error = None
            with st.spinner("Analyzing repository with GitHub + LLM pipeline..."):
                try:
                    st.session_state.analysis_result = analyze_repository(repo_url.strip())
                    st.session_state.pdf_report_bytes = None
                    st.session_state.pdf_error = None
                except AnalysisError as exc:
                    st.session_state.analysis_result = None
                    st.session_state.analysis_error = str(exc)
                    st.session_state.pdf_report_bytes = None
                    st.session_state.pdf_error = None
                except Exception as exc:
                    st.session_state.analysis_result = None
                    st.session_state.analysis_error = f"Unexpected error: {exc}"
                    st.session_state.pdf_report_bytes = None
                    st.session_state.pdf_error = None

    analysis_result = st.session_state.analysis_result
    analysis_error = st.session_state.analysis_error

    if analysis_error:
        st.error(analysis_error)

    summary = {
        "health_score": "--",
        "bus_factor_percent": "--",
        "technical_debt_hours": "--",
        "security_score": "--",
    }
    chart_specs = [
        ("radar", "1) Repository Radar Chart"),
        ("network", "2) Contributor Network Graph"),
        ("debt_heatmap", "3) Technical Debt Heatmap"),
        ("language_pie", "4) Language Distribution Pie Chart"),
        ("issue_timeline", "5) Issue Age Timeline"),
        ("security_matrix", "6) Security Risk Matrix"),
        ("dependency_risk", "7) Dependency Risk Bar Chart"),
    ]
    chart_map = {key: placeholder_figure(title) for key, title in chart_specs}
    built_charts = None
    metric_subtext = "Awaiting analysis"
    priorities_df = pd.DataFrame(
        {
            "Priority": [1, 2, 3, 4, 5],
            "Area": ["Pending"] * 5,
            "Estimated Effort (hrs)": [0, 0, 0, 0, 0],
            "Risk": ["TBD"] * 5,
            "Recommendation": ["Will be generated after analysis"] * 5,
        }
    )

    if analysis_result:
        summary_payload = analysis_result.get("summary", {})
        ai_meta = analysis_result.get("ai_analysis", {}).get("meta", {})
        used_fallback = bool(ai_meta.get("used_fallback", False))
        fallback_count = int(ai_meta.get("fallback_count", 0)) if isinstance(ai_meta.get("fallback_count", 0), int) else 0
        failed_tasks = ai_meta.get("failed_tasks", {}) if isinstance(ai_meta.get("failed_tasks", {}), dict) else {}

        summary = {
            "health_score": f"{summary_payload.get('health_score', '--')} %",
            "bus_factor_percent": f"{summary_payload.get('bus_factor_percent', '--')} %",
            "technical_debt_hours": f"{summary_payload.get('technical_debt_hours', '--')} hrs",
            "security_score": f"{summary_payload.get('security_score', '--')} %",
        }

        if used_fallback:
            metric_subtext = "Fallback estimate"
            st.warning(
                f"AI fallback mode used for {fallback_count} task(s). "
                "If values look repeated across repos, verify GITHUB_TOKEN, GROQ_API_KEY, and LLM model access."
            )
            with st.expander("Show AI failure details"):
                if failed_tasks:
                    for task_name, reason in failed_tasks.items():
                        st.write(f"- {task_name}: {reason}")
                else:
                    st.write("No detailed failure reason available.")
        else:
            metric_subtext = "Live AI analysis"

        priorities = summary_payload.get("top_5_refactoring_priorities", [])
        if priorities:
            rows = []
            for idx, item in enumerate(priorities[:5], start=1):
                rows.append(
                    {
                        "Priority": idx,
                        "Area": item.get("area", "unknown"),
                        "Estimated Effort (hrs)": item.get("effort_hours", 0),
                        "Risk": item.get("risk", "medium"),
                        "Recommendation": item.get("recommendation", ""),
                    }
                )
            priorities_df = pd.DataFrame(rows)

        runtime = analysis_result.get("runtime", {}).get("total_elapsed_ms")
        if runtime is not None:
            st.success(f"Analysis complete in {runtime} ms")

        try:
            built = build_all_charts(analysis_result)
            built_charts = built
            for key, _ in chart_specs:
                if key in built:
                    chart_map[key] = built[key]
        except Exception as exc:
            st.info(f"Chart engine fallback active: {exc}")

        if st.session_state.pdf_report_bytes is None:
            try:
                st.session_state.pdf_report_bytes = generate_pdf_bytes(analysis_result, built_charts)
                st.session_state.pdf_error = None
            except Exception as exc:
                st.session_state.pdf_report_bytes = None
                st.session_state.pdf_error = f"PDF generation failed: {exc}"

    st.markdown('<div class="section-title">Repository Core Metrics</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    with metric_cols[0]:
        show_metric_card("Health Score", str(summary["health_score"]), metric_subtext)
    with metric_cols[1]:
        show_metric_card("Bus Factor", str(summary["bus_factor_percent"]), metric_subtext)
    with metric_cols[2]:
        show_metric_card("Technical Debt", str(summary["technical_debt_hours"]), metric_subtext)
    with metric_cols[3]:
        show_metric_card("Security Score", str(summary["security_score"]), metric_subtext)

    st.markdown('<div class="section-title">Analysis Visualizations (7)</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    for idx, (key, title) in enumerate(chart_specs):
        target_col = left if idx % 2 == 0 else right
        with target_col:
            st.plotly_chart(chart_map.get(key, placeholder_figure(title)), config={"responsive": True})

    st.markdown('<div class="section-title">Top 5 Refactoring Priorities</div>', unsafe_allow_html=True)
    st.dataframe(priorities_df, width="stretch", hide_index=True)

    if st.session_state.pdf_error:
        st.warning(st.session_state.pdf_error)

    st.download_button(
        label="Download PDF Report",
        data=st.session_state.pdf_report_bytes or b"",
        file_name="repo_health_report.pdf",
        mime="application/pdf",
        disabled=st.session_state.pdf_report_bytes is None,
        help="Download the generated repository health report.",
    )


if __name__ == "__main__":
    main()
