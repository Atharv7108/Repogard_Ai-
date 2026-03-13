import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analyzer import AnalysisError, analyze_repository
from charts import build_all_charts
from pdf_generator import generate_pdf_bytes


st.set_page_config(
    page_title="RepoGuard AI - Repository Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def placeholder_figure(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        x=0.5, y=0.5,
        text=f"<b>{title}</b><br><sup style='color:#5a8aaa'>Run analysis to populate this chart</sup>",
        showarrow=False,
        font={"size": 14, "color": "#5a8aaa"},
        xref="paper", yref="paper", align="center",
    )
    fig.update_layout(
        height=300,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        paper_bgcolor="rgba(5,18,30,0.9)",
        plot_bgcolor="rgba(5,18,30,0.9)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig


def section_header(icon: str, title: str) -> None:
    st.markdown(
        f"""<div class="sec-header">

            <span class="sec-title">{title}</span>
            <div class="sec-line"></div>
        </div>""",
        unsafe_allow_html=True,
    )


def risk_badge_html(risk: str) -> str:
    cls = f"risk-{risk.lower()}" if risk.lower() in ("low", "medium", "high", "critical") else "risk-medium"
    return f'<span class="risk-badge {cls}">{risk.upper()}</span>'


def show_metric_cards(summary: dict, subtext: str) -> None:
    h = summary.get("health_score", "--")
    b = summary.get("bus_factor_percent", "--")
    d = summary.get("technical_debt_hours", "--")
    s = summary.get("security_score", "--")

    health_val  = f"{h}%" if h != "--" else "--"
    bus_val     = f"{b}%" if b != "--" else "--"
    debt_val    = f"{d} hrs" if d != "--" else "--"
    sec_val     = f"{s}%" if s != "--" else "--"

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="mcard health">
                <div class="mcard-label">Health Score</div>
                <div class="mcard-value">{health_val}</div>
                <div class="mcard-sub">{subtext}</div>
            </div>
            <div class="mcard bus">
                <div class="mcard-label">Bus Factor</div>
                <div class="mcard-value">{bus_val}</div>
                <div class="mcard-sub">{subtext}</div>
            </div>
            <div class="mcard debt">
                <div class="mcard-label">Technical Debt</div>
                <div class="mcard-value">{debt_val}</div>
                <div class="mcard-sub">{subtext}</div>
            </div>
            <div class="mcard security">
                <div class="mcard-label">Security Score</div>
                <div class="mcard-value">{sec_val}</div>
                <div class="mcard-sub">{subtext}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_insight_boxes(analysis_result: dict) -> None:
    ai = analysis_result.get("ai_analysis", {})
    repo = analysis_result.get("repository_data", {})

    health_rationale   = ai.get("repository_health_score", {}).get("rationale", "N/A")[:260]
    security_rationale = ai.get("security_risk", {}).get("rationale", "N/A")[:260]
    bus_rationale      = ai.get("bus_factor", {}).get("rationale", "N/A")[:260]
    debt_rationale     = ai.get("technical_debt", {}).get("rationale", "N/A")[:260]

    st.markdown(
        f"""
        <div class="insight-grid">
            <div class="insight-box">
                <div class="ib-title">Health Insight</div>
                {health_rationale}
            </div>
            <div class="insight-box">
                <div class="ib-title">Security Insight</div>
                {security_rationale}
            </div>
            <div class="insight-box">
                <div class="ib-title">Bus Factor Insight</div>
                {bus_rationale}
            </div>
            <div class="insight-box">
                <div class="ib-title">Technical Debt Insight</div>
                {debt_rationale}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_priorities_table(priorities: list) -> None:
    if not priorities:
        st.info("No refactoring priorities available yet.")
        return

    rows_html = ""
    for idx, item in enumerate(priorities[:5], start=1):
        risk = item.get("risk", "medium")
        rows_html += f"""
        <tr>
            <td><b style="color:#e8f8ff">#{idx}</b></td>
            <td><b style="color:#e8f8ff">{item.get('title', 'N/A')}</b></td>
            <td style="color:#94c4de">{item.get('area', 'N/A')}</td>
            <td style="text-align:center"><b style="color:#fbbf24">{item.get('effort_hours', 0)}h</b></td>
            <td>{risk_badge_html(risk)}</td>
            <td style="color:#5a8aaa;font-size:0.79rem">{item.get('recommendation', '')[:140]}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="border:1px solid rgba(100,180,230,0.15);border-radius:16px;overflow:hidden;background:rgba(5,18,30,0.8)">
            <table class="priority-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Title</th>
                        <th>Area</th>
                        <th style="text-align:center">Effort</th>
                        <th>Risk</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_styles()

    # ── Session State ──────────────────────────
    for key in ("analysis_result", "analysis_error", "pdf_report_bytes", "pdf_error"):
        if key not in st.session_state:
            st.session_state[key] = None
    if "analysis_running" not in st.session_state:
        st.session_state.analysis_running = False

        # ── Top Navigation / Header ────────────────
        st.markdown(
                """
                <div class="top-nav">
                    <div class="nav-left">
                        <div class="brand">RepoGuard <span class="brand-accent">AI</span></div>
                        <div class="nav-sub">AI-powered GitHub repository intelligence</div>
                    </div>
                    <div class="nav-right">
                        <a class="icon-btn" href="#" title="Open on GitHub">🐙</a>
                        <a class="icon-btn" href="#" title="Settings">⚙️</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
        )

    # ── Input Panel ────────────────────────────
    st.markdown('<div class="input-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-label">Enter Repository URL</div>', unsafe_allow_html=True)
    col_url, col_btn = st.columns([6, 1])
    with col_url:
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/facebook/react",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Run Analysis ───────────────────────────
    if analyze_clicked:
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.")
        else:
            st.session_state.analysis_error = None
            st.session_state.pdf_report_bytes = None
            st.session_state.analysis_running = True
            try:
                with st.spinner("Collecting GitHub data and running LLM tasks..."):
                    st.session_state.analysis_result = analyze_repository(repo_url.strip())
            except AnalysisError as exc:
                st.session_state.analysis_result = None
                st.session_state.analysis_error = str(exc)
            except Exception as exc:
                st.session_state.analysis_result = None
                st.session_state.analysis_error = f"Unexpected error: {exc}"
            finally:
                st.session_state.analysis_running = False

    analysis_result = st.session_state.analysis_result
    analysis_error = st.session_state.analysis_error

    # ── Progress Steps (visual only when analysis running) ──
    if st.session_state.get("analysis_running"):
        st.markdown(
            """
            <div class="progress-wrap">
              <div class="progress-step active">1. Fetching repository data</div>
              <div class="progress-step">2. Analyzing contributors</div>
              <div class="progress-step">3. Evaluating technical debt</div>
              <div class="progress-step">4. Running AI risk analysis</div>
              <div class="progress-step">5. Generating insights</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if analysis_error:
        st.error(f"Error: {analysis_error}")

    # ── Defaults ───────────────────────────────
    meta_provider = "—"
    meta_model = "—"
    runtime_text = "No run yet"
    metric_subtext = "Awaiting analysis"
    summary = {"health_score": "--", "bus_factor_percent": "--", "technical_debt_hours": "--", "security_score": "--"}

    chart_specs = [
        ("radar",           "Repository Radar"),
        ("network",         "Contributor Network"),
        ("debt_heatmap",    "Technical Debt Heatmap"),
        ("language_pie",    "Language Distribution"),
        ("issue_timeline",  "Issue Age Timeline"),
        ("security_matrix", "Security Risk Matrix"),
        ("dependency_risk", "Dependency Risk"),
    ]
    chart_map = {key: placeholder_figure(title) for key, title in chart_specs}
    built_charts = None
    priorities: list = []

    # ── Populate from result ───────────────────
    if analysis_result:
        payload = analysis_result.get("summary", {})
        ai_meta = analysis_result.get("ai_analysis", {}).get("meta", {})
        meta_provider = str(ai_meta.get("provider", "—")).upper()
        meta_model = str(ai_meta.get("model", "—"))
        used_fallback = bool(ai_meta.get("used_fallback", False))
        fallback_count = int(ai_meta.get("fallback_count", 0)) if isinstance(ai_meta.get("fallback_count"), int) else 0
        failed_tasks = ai_meta.get("failed_tasks", {}) if isinstance(ai_meta.get("failed_tasks"), dict) else {}

        summary = {
            "health_score":          payload.get("health_score", "--"),
            "bus_factor_percent":    payload.get("bus_factor_percent", "--"),
            "technical_debt_hours":  payload.get("technical_debt_hours", "--"),
            "security_score":        payload.get("security_score", "--"),
        }

        priorities = payload.get("top_5_refactoring_priorities", [])

        runtime_ms = analysis_result.get("runtime", {}).get("total_elapsed_ms")
        if runtime_ms is not None:
            runtime_text = f"{runtime_ms:,} ms"

        if used_fallback:
            metric_subtext = "Partial AI (fallback used)"
            with st.expander(f"AI fallback active for {fallback_count} task(s) - click to see details"):
                for t, r in failed_tasks.items():
                    st.write(f"• **{t}**: {r}")
        else:
            metric_subtext = "Live AI - LLaMA 3.3 70B"
            st.success(f"Analysis complete in {runtime_text}")

        try:
            built_charts = build_all_charts(analysis_result)
            for key, _ in chart_specs:
                if key in built_charts:
                    chart_map[key] = built_charts[key]
        except Exception as exc:
            st.info(f"Chart engine note: {exc}")

        if st.session_state.pdf_report_bytes is None:
            try:
                st.session_state.pdf_report_bytes = generate_pdf_bytes(analysis_result, built_charts)
            except Exception as exc:
                st.session_state.pdf_error = f"PDF generation failed: {exc}"

    # ── Status Bar ─────────────────────────────
    dot = f'<span class="status-dot"></span>' if analysis_result else ""
    st.markdown(
        f"""
        <div class="status-bar">
            <span class="status-chip">{dot} Provider: <b style="color:#e8f8ff">{meta_provider}</b></span>
            <span class="status-chip">Model: <b style="color:#e8f8ff">{meta_model}</b></span>
            <span class="status-chip">Runtime: <b style="color:#e8f8ff">{runtime_text}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Core Metrics ───────────────────────────
    section_header("📊", "Core Repository Metrics")
    show_metric_cards(summary, metric_subtext)

    # ── AI Insights (only after analysis) ──────
    if analysis_result:
        with st.expander("AI Insights", expanded=False):
            show_insight_boxes(analysis_result)

    # ── Visualizations (Tabbed) ─────────────────
    section_header("📈", "Analysis Visualizations")

    tab_labels = [title for _, title in chart_specs]
    tabs = st.tabs(tab_labels)
    for i, ((key, _), tab) in enumerate(zip(chart_specs, tabs)):
        with tab:
            st.plotly_chart(
                chart_map.get(key, placeholder_figure(tab_labels[i])),
                use_container_width=True,
                config={"responsive": True, "displayModeBar": False},
            )

    # ── Refactoring Priorities ─────────────────
    section_header("🔧", "Top Refactoring Priorities")
    show_priorities_table(priorities)

    # ── PDF Download ───────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_col, _ = st.columns([2, 5])
    with pdf_col:
        if st.session_state.pdf_error:
            st.warning(st.session_state.pdf_error)
        pdf_data = st.session_state.pdf_report_bytes if st.session_state.pdf_report_bytes is not None else b""
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name="repogard_health_report.pdf",
            mime="application/pdf",
            disabled=st.session_state.pdf_report_bytes is None,
            use_container_width=True,
        )

    # ── Footer ─────────────────────────────────
    st.markdown(
        """
        <div class="footer">
            Built using Streamlit · Groq API · GitHub API<br>
            RepoGuard - Repository Intelligence Platform
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
