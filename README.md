# RepoGuard AI 🧠🔐

**RepoGuard AI** is a premium, AI-powered repository intelligence platform designed for engineering visibility. It synthesizes repository metadata, commit history, and code patterns into actionable insights regarding health, security, and maintenance risk.

## 🚀 Technology Stack

### Core Frameworks
- **[Streamlit](https://streamlit.io/) (Python)**: Powers the main analysis engine and the dynamic, data-rich user interface.
- **[React](https://reactjs.org/) + [Vite](https://vitejs.dev/)**: Used for the external Authentication (Login/Signup) and Pricing SPA (Single-Page Application).
- **[Node.js](https://nodejs.org/) & [Express](https://expressjs.com/)**: Provides a microservice layer for unified authentication and user profile management.

### AI & Analysis
- **[LiteLLM](https://github.com/BerriAI/litellm) / Google Gemini**: Drives the "Project Intelligence" engine, providing AI summaries and refactoring priorities.
- **Repository Scanning**: Custom Python logic for contributor risk mapping and health scoring.

### Backend & Security
- **[SQLite](https://www.sqlite.org/)**: Persistent storage for user profiles, analysis history, and subscription plans.
- **[JWT](https://jwt.io/) (JSON Web Tokens)**: Secure, cross-service session management (bridging the Hybrid Streamlit/React architecture).
- **[bcrypt](https://github.com/pyca/bcrypt)**: Industry-standard password hashing.

### Design & Aesthetics
- **Vanilla CSS**: Curated premium design system featuring:
    - **Glassmorphism**: Sleek, transparent UI layers.
    - **Micro-animations**: Smooth transitions and hover effects for a responsive feel.
    - **High-Contrast Dark Mode**: Optimized for readability and professional aesthetics.

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
    - `REACT_API_BASE`: Base URL for the Node.js microservice.
    - `GOOGLE_API_KEY`: Required for Gemini-driven AI analysis.

### Running the App
```bash
# Install dependencies
pip install -r requirements.txt

# Start the Streamlit Analysis Engine
streamlit run app.py
```
