# RepoGuard AI - Phase-wise TODOLIST

This roadmap breaks the project into small parts so we can build safely and verify each step.

## Phase 0 - Project Setup
- [ ] Create folder structure:
  - [ ] `RepoGuardAI/app.py`
  - [ ] `RepoGuardAI/analyzer.py`
  - [ ] `RepoGuardAI/charts.py`
  - [ ] `RepoGuardAI/pdf_generator.py`
  - [ ] `RepoGuardAI/requirements.txt`
  - [ ] `RepoGuardAI/.streamlit/config.toml`
- [ ] Create Python virtual environment
- [ ] Install dependencies from `requirements.txt`
- [ ] Confirm app launches with `streamlit run app.py`

Definition of done:
- Basic Streamlit app opens without errors.

---

## Phase 1 - Frontend Skeleton (Streamlit)
- [ ] Build page layout and title/branding for RepoGuard AI
- [ ] Add dark gradient custom CSS
- [ ] Add GitHub URL input box
- [ ] Add `🚀 ANALYZE` button
- [ ] Add placeholder metric cards (4 cards)
- [ ] Add placeholder section for 7 charts
- [ ] Add placeholder refactoring priorities table
- [ ] Add disabled PDF download button placeholder

Definition of done:
- UI is visually complete with placeholders and no backend logic yet.

---

## Phase 2 - GitHub Data Collector (analyzer.py, non-AI)
- [ ] Setup PyGithub client using `GITHUB_TOKEN`
- [ ] Parse owner/repo from GitHub URL
- [ ] Fetch repository metadata:
  - [ ] stars
  - [ ] forks and forks_count
  - [ ] open issues
  - [ ] pull requests
  - [ ] languages
  - [ ] last commit date
  - [ ] license info
- [ ] Fetch top 20 contributors
- [ ] Fetch commit activity summary
- [ ] Return normalized Python dict
- [ ] Add robust error handling for:
  - [ ] invalid URL
  - [ ] rate limit
  - [ ] missing token
  - [ ] private repo access failure

Definition of done:
- Running analyzer data collector returns clean structured repo data.

---

## Phase 3 - GROK AI Integration (analyzer.py)
- [ ] Add GROK API client via `requests`
- [ ] Build 8 prompt templates for:
  - [ ] repository health score
  - [ ] bus factor
  - [ ] technical debt
  - [ ] security risk
  - [ ] maintainability
  - [ ] documentation quality
  - [ ] contributor distribution
  - [ ] refactoring priorities
- [ ] Create strict JSON output schema for AI responses
- [ ] Add parser + fallback defaults if AI output is malformed
- [ ] Add timeout and retry strategy
- [ ] Optimize for target total runtime (~15s)

Definition of done:
- Analyzer returns stable, structured JSON including all required scores and priorities.

---

## Phase 4 - Chart Engine (charts.py)
- [ ] Implement Radar Chart
- [ ] Implement Contributor Network Graph using NetworkX
- [ ] Implement Technical Debt Heatmap
- [ ] Implement Language Distribution Pie
- [ ] Implement Issue Age Timeline
- [ ] Implement Security Risk Matrix
- [ ] Implement Dependency Risk Bar Chart
- [ ] Return all 7 Plotly figures in a dictionary

Definition of done:
- 7 figures render correctly in Streamlit with sample data.

---

## Phase 5 - Dashboard Wiring (app.py + analyzer.py + charts.py)
- [ ] Connect `🚀 ANALYZE` button to analyzer pipeline
- [ ] Show loading/progress state while analysis runs
- [ ] Display final metrics:
  - [ ] Health Score (%)
  - [ ] Bus Factor (%)
  - [ ] Technical Debt (hours)
  - [ ] Security Score (%)
- [ ] Render all 7 charts from `charts.py`
- [ ] Render Top 5 Refactoring Priorities table
- [ ] Store analysis result in session state

Definition of done:
- End-to-end analysis and dashboard display works from URL input.

---

## Phase 6 - PDF Report Generator (pdf_generator.py)
- [ ] Build PDF document structure and styling
- [ ] Add cover page
- [ ] Add executive summary
- [ ] Add repository metadata section
- [ ] Add health score breakdown
- [ ] Add AI analysis tables
- [ ] Export Plotly charts as PNG for embedding
- [ ] Add contributor analysis section
- [ ] Add security review section
- [ ] Add technical debt summary
- [ ] Add Top 25 refactoring tickets
- [ ] Ensure total report is professional and multi-page (target ~20 pages)
- [ ] Save as `repo_health_report.pdf`

Definition of done:
- PDF is generated successfully and downloadable from app.

---

## Phase 7 - Performance and Reliability
- [ ] Profile total runtime on test repo (`facebook/react`)
- [ ] Add caching where safe (repo metadata, chart preparation)
- [ ] Reduce API calls and prompt size
- [ ] Add guardrails for missing/partial data
- [ ] Keep total runtime near 15 seconds

Definition of done:
- Typical analysis completes around target runtime with stable output.

---

## Phase 8 - HuggingFace Spaces Readiness
- [ ] Verify environment variables strategy:
  - [ ] `GITHUB_TOKEN`
  - [ ] `GROK_API_KEY`
- [ ] Confirm `requirements.txt` is complete
- [ ] Confirm Streamlit config works in hosted environment
- [ ] Final run command validation: `streamlit run app.py`

Definition of done:
- App is deployable on HuggingFace Spaces without code changes.

---

## Phase 9 - Final Validation (Test Case)
- [ ] Run input: `https://github.com/facebook/react`
- [ ] Verify key metrics are produced
- [ ] Verify all 7 charts are visible
- [ ] Verify top priorities table shows at least 5 rows
- [ ] Verify PDF download works and file opens correctly

Definition of done:
- All expected outputs are present and coherent.

---

## Phase 10 - Nice-to-Have Enhancements
- [ ] Add historical trend comparison (if rerun)
- [ ] Add export JSON button
- [ ] Add confidence score for each AI metric
- [ ] Add side-by-side comparison for two repos

Definition of done:
- Optional quality improvements implemented without breaking core flow.

---

## Immediate Next 3 Tasks
- [ ] 1) Create full folder/file scaffold under `RepoGuardAI/`
- [ ] 2) Build Streamlit UI skeleton in `app.py`
- [ ] 3) Implement non-AI GitHub data collector in `analyzer.py`
