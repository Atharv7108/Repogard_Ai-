"""Launcher for Free view (3-token Pro variant for testing)."""

import os

# Force low-limit variant in this process.
os.environ["PLANS_VARIANT"] = "3"
os.environ["STREAMLIT_ANALYSIS_URL"] = "http://localhost:8516/?view=analysis"

from app import main


if __name__ == "__main__":
    main()
