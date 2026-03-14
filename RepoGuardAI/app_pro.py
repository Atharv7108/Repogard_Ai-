"""Launcher for Pro view (30-token Pro variant)."""

import os

# Force pro-limit variant in this process.
os.environ["PLANS_VARIANT"] = "30"
os.environ["STREAMLIT_ANALYSIS_URL"] = "http://localhost:8517/?view=analysis"

from app import main


if __name__ == "__main__":
    main()
