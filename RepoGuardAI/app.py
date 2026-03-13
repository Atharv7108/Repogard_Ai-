import pandas as pd
import plotly.graph_objects as go
import streamlit as st


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


def show_metric_card(label: str, value: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="subtext">Phase 1 placeholder</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_styles()

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

    analyze_clicked = st.button("🚀 ANALYZE", type="primary", use_container_width=True)
    if analyze_clicked:
        if not repo_url.strip():
            st.warning("Please enter a GitHub repository URL.")
        else:
            st.info("Phase 1 UI is ready. Analysis pipeline will be connected in Phase 5.")

    st.markdown('<div class="section-title">Repository Core Metrics</div>', unsafe_allow_html=True)
    metric_cols = st.columns(4)
    with metric_cols[0]:
        show_metric_card("Health Score", "-- %")
    with metric_cols[1]:
        show_metric_card("Bus Factor", "-- %")
    with metric_cols[2]:
        show_metric_card("Technical Debt", "-- hrs")
    with metric_cols[3]:
        show_metric_card("Security Score", "-- %")

    st.markdown('<div class="section-title">Analysis Visualizations (7)</div>', unsafe_allow_html=True)
    chart_titles = [
        "1) Repository Radar Chart",
        "2) Contributor Network Graph",
        "3) Technical Debt Heatmap",
        "4) Language Distribution Pie Chart",
        "5) Issue Age Timeline",
        "6) Security Risk Matrix",
        "7) Dependency Risk Bar Chart",
    ]

    left, right = st.columns(2)
    for idx, title in enumerate(chart_titles):
        target_col = left if idx % 2 == 0 else right
        with target_col:
            st.plotly_chart(placeholder_figure(title), use_container_width=True)

    st.markdown('<div class="section-title">Top 5 Refactoring Priorities</div>', unsafe_allow_html=True)
    priorities_df = pd.DataFrame(
        {
            "Priority": [1, 2, 3, 4, 5],
            "Area": ["Pending"] * 5,
            "Estimated Effort (hrs)": [0, 0, 0, 0, 0],
            "Risk": ["TBD"] * 5,
            "Recommendation": ["Will be generated after analysis"] * 5,
        }
    )
    st.dataframe(priorities_df, use_container_width=True, hide_index=True)

    st.download_button(
        label="Download PDF Report",
        data=b"",
        file_name="repo_health_report.pdf",
        mime="application/pdf",
        disabled=True,
        help="PDF generation will be enabled in Phase 6.",
    )


if __name__ == "__main__":
    main()
