# RepoGuard AI 🧠🔐

**RepoGuard AI** is a premium, AI-powered repository intelligence platform designed for engineering visibility. It synthesizes repository metadata, commit history, and code patterns into actionable insights regarding health, security, and maintenance risk.

## 🚀 Technology Stack (Used + Why)

### Frontend Experience
- **[React 18](https://reactjs.org/)**: Built for the Login/Pricing SPA and checkout flow. Chosen for fast component-based UI updates and easy routing.
- **[Vite](https://vitejs.dev/)**: Development and build tool for the React app. Chosen for very fast startup and lightweight production bundles.
- **[React Router](https://reactrouter.com/)**: Handles `/login` and `/pricing` SPA navigation cleanly.
- **Vanilla CSS**: Custom visual system (glass effects, animation, gradients) without heavy UI frameworks, keeping bundle size and styling control tight.

### Python Analysis Layer
- **[Streamlit](https://streamlit.io/)**: Main analysis interface and dashboard rendering. Chosen for rapid shipping of data-rich UI.
- **[PyGithub](https://pygithub.readthedocs.io/)** + **[requests](https://docs.python-requests.org/)**: GitHub API access and service-to-service HTTP calls.
- **[pandas](https://pandas.pydata.org/)**: Metric shaping and tabular data handling.
- **[plotly](https://plotly.com/python/)** + **[networkx](https://networkx.org/)**: Interactive charts and contributor/network analysis views.
- **[reportlab](https://www.reportlab.com/)** + **[matplotlib](https://matplotlib.org/)** + **[kaleido](https://github.com/plotly/Kaleido)**: PDF report generation and chart image export.

### API, Auth, and Payments
- **[Node.js](https://nodejs.org/) + [Express](https://expressjs.com/)**: Auth and payment API (`/api/login`, `/api/register`, `/api/upgrade-plan`, Razorpay order endpoints).
- **[jwt-simple](https://www.npmjs.com/package/jwt-simple)**: Lightweight JWT encode/decode in Node API.
- **[bcryptjs](https://www.npmjs.com/package/bcryptjs)** + **[bcrypt](https://github.com/pyca/bcrypt)**: Password hashing support across Node and Python auth utilities.
- **[Razorpay](https://razorpay.com/docs/)**: Upgrade payment checkout and order creation flow.
- **[cors](https://www.npmjs.com/package/cors)** + **[dotenv](https://www.npmjs.com/package/dotenv)** + **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Cross-origin handling and environment-based secret management.

### Data Storage
- **[SQLite](https://www.sqlite.org/)** (`repoguard.db`): Local relational storage for app data and hackathon simplicity.
- **JSON stores** (`.users.json`, `.usage.json`): Lightweight auth/usage persistence used by the current Node flow.

### AI Provider
- **Groq (OpenAI-compatible API)**: Used for Project Intelligence tasks through configured model endpoint.
- Why: low-latency LLM inference and straightforward API integration with retry/fallback logic in analyzer.

---

## 🏗️ Architectural Overview

RepoGuard AI uses a **Hybrid Frontend Architecture**:

1.  **Landing & Context**: The user lands on a Streamlit-powered dashboard designed for high-performance data rendering.
2.  **Authentication Bridge**: When a user needs to log in or upgrade, they are seamlessly redirected to a **React SPA**. 
3.  **Secure Handshake**: Upon successful login, the React app generates a **JWT** and redirects the user back to the Streamlit app.
4.  **Session Restoration**: Streamlit captures the token from the URL, validates it via the Node.js API, and restores the user's session and "Pro" plan limits in real-time.

---

## 🛠️ Requirements & Setup

- **Python 3.9+**
- **Node.js 18+**
- Environment Variables:
    - `REPOGUARD_JWT_SECRET`: Shared secret for token signing.
    - `GITHUB_TOKEN`: GitHub API token used by repository analyzer.
    - `GROQ_API_KEY`: Key for AI summary/insight generation.
    - `LLM_PROVIDER`, `LLM_API_URL`, `LLM_MODEL`: LLM routing and model configuration.
    - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`: Payment configuration (server-side).
    - `REACT_API_BASE`: Streamlit-to-API base URL.

### Running the App
```bash
# Install dependencies
pip install -r requirements.txt

# Start the Streamlit Analysis Engine
streamlit run app.py
```

## Clean Local Run (Recommended)

Use the service scripts to avoid manual port/process conflicts.

```bash
cd RepoGuardAI

# First-time setup
pip install -r requirements.txt
cd web && npm install && cd ..

# Start all services (API + React + Free Streamlit + Pro Streamlit)
./scripts/dev-up.sh

# Check health
./scripts/dev-status.sh

# Stop everything
./scripts/dev-down.sh
```

### Service URLs

- Web (React): http://localhost:5173
- API (Node/Express): http://localhost:5174
- Streamlit Free: http://localhost:8516
- Streamlit Pro: http://localhost:8517
