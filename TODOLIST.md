# RepoGuard AI - Phase-wise TODOLIST

This roadmap breaks the project into small parts so we can build safely and verify each step.

## Phase 0 - Project Setup
- [ ] Create folder structure:
  - [x] `RepoGuardAI/app.py`
  - [x] `RepoGuardAI/analyzer.py`
  - [x] `RepoGuardAI/charts.py`
  - [x] `RepoGuardAI/pdf_generator.py`
  - [x] `RepoGuardAI/requirements.txt`
  - [x] `RepoGuardAI/.streamlit/config.toml`
- [x] Create Python virtual environment
- [x] Install dependencies from `requirements.txt`
- [x] Confirm app launches with `streamlit run app.py`

Definition of done:
- Basic Streamlit app opens without errors.

---

## Phase 1 - Frontend Skeleton (Streamlit)
- [x] Build page layout and title/branding for RepoGuard AI
- [x] Add dark gradient custom CSS
- [x] Add GitHub URL input box
- [x] Add `🚀 ANALYZE` button
- [x] Add placeholder metric cards (4 cards)
- [x] Add placeholder section for 7 charts
- [x] Add placeholder refactoring priorities table
- [x] Add disabled PDF download button placeholder

Definition of done:
- UI is visually complete with placeholders and no backend logic yet.

---

## Phase 2 - GitHub Data Collector (analyzer.py, non-AI)
- [x] Setup PyGithub client using `GITHUB_TOKEN`
- [x] Parse owner/repo from GitHub URL
- [x] Fetch repository metadata:
  - [x] stars
  - [x] forks and forks_count
  - [x] open issues
  - [x] pull requests
  - [x] languages
  - [x] last commit date
  - [x] license info
- [x] Fetch top 20 contributors
- [x] Fetch commit activity summary
- [x] Return normalized Python dict
- [x] Add robust error handling for:
  - [x] invalid URL
  - [x] rate limit
  - [x] missing token
  - [x] private repo access failure

Definition of done:
- Running analyzer data collector returns clean structured repo data.

---

## Phase 3 - GROK AI Integration (analyzer.py)
- [x] Add GROK API client via `requests`
- [x] Build 8 prompt templates for:
  - [x] repository health score
  - [x] bus factor
  - [x] technical debt
  - [x] security risk
  - [x] maintainability
  - [x] documentation quality
  - [x] contributor distribution
  - [x] refactoring priorities
- [x] Create strict JSON output schema for AI responses
- [x] Add parser + fallback defaults if AI output is malformed
- [x] Add timeout and retry strategy
- [x] Optimize for target total runtime (~15s)

Definition of done:
- Analyzer returns stable, structured JSON including all required scores and priorities.

---

## Phase 4 - Chart Engine (charts.py)
- [x] Implement Radar Chart
- [x] Implement Contributor Network Graph using NetworkX
- [x] Implement Technical Debt Heatmap
- [x] Implement Language Distribution Pie
- [x] Implement Issue Age Timeline
- [x] Implement Security Risk Matrix
- [x] Implement Dependency Risk Bar Chart
- [x] Return all 7 Plotly figures in a dictionary

Definition of done:
- 7 figures render correctly in Streamlit with sample data.

---

## Phase 5 - Dashboard Wiring (app.py + analyzer.py + charts.py)
- [x] Connect `🚀 ANALYZE` button to analyzer pipeline
- [x] Show loading/progress state while analysis runs
- [x] Display final metrics:
  - [x] Health Score (%)
  - [x] Bus Factor (%)
  - [x] Technical Debt (hours)
  - [x] Security Score (%)
- [x] Render all 7 charts from `charts.py`
- [x] Render Top 5 Refactoring Priorities table
- [x] Store analysis result in session state

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
- [x] 1) Create full folder/file scaffold under `RepoGuardAI/`
- [x] 2) Build Streamlit UI skeleton in `app.py`
- [x] 3) Implement non-AI GitHub data collector in `analyzer.py`
