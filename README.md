<div align="center">

# PaperLens

**Understand research. Your way.**

Turn dense research papers into structured, navigable reading experiences — at your level.

![Stage](https://img.shields.io/badge/stage-5%20AI%20analysis-8F2D3C)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-171717)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20PyMuPDF-171717)
![AI](https://img.shields.io/badge/AI-OpenAI%20structured%20analysis-8F2D3C)

</div>

---

## What is PaperLens?

PaperLens helps **students understand research papers**. Upload a PDF and get a clean research workspace: a navigable outline, readable sections with page references, figures and tables, linked citations and references, local search, and raw-extraction transparency.

> **Stage 5 adds the first real AI layer:** structured paper analysis (problem, methods, results, findings — each with page/section evidence) generated from the extracted document. Still no RAG, Q&A, or chat — those come later.

---

## ✨ Features (Stage 4)

| Area | What you get |
|---|---|
| 📄 **Upload flow** | Drag & drop PDF (≤ 20 MB) with honest processing milestones |
| 🔍 **PDF extraction** | Page-preserving text, layout-aware reading order (incl. two-column) |
| 🧠 **AI analysis** | Structured problem/methods/results/findings with page evidence (OpenAI, cached) |
| 🧭 **Paper outline** | Real detected sections, numbered + nested, scroll-synced |
| 📖 **Reading view** | Editorial typography, subsections, page ranges, “View source” |
| 🔗 **Citations** | Click `[12]` → jumps to and highlights Reference 12 |
| 🖼️ **Figures & Tables** | Captions, pages, and safely re-rendered image previews |
| 🔎 **Local search** | Full-text search with snippets — `/` to focus, `Esc` to close |
| 🧾 **Transparency** | Raw extracted text modal, document quality report |
| 🎨 **Branding** | Custom SVG favicon + wordmark, per-route browser titles |

---

## 🏗️ Architecture

```
PDF
 ↓  (multipart upload, 20 MB limit, UUID paper IDs)
FastAPI backend  ──  PyMuPDF extraction
 ↓  layout analysis → structure detection → entities → citations
Structured Paper JSON  (pages · sections · references · figures · quality)
 ↓  section-aware context (prioritized, budgeted) → OpenAI structured analysis
Paper Analysis JSON  (summary · problem · methods · findings · evidence)
 ↓  REST API (cached in analysis.json — no repeat calls)
React workspace  ──  outline · document · analysis · search · context panel
```

**Planned next:** Q&A / RAG / difficulty-adaptive explanations consume the structured paper + analysis — no rewrites needed.

---

## 🚀 Quick start

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+ (3.14 works)

### 1. Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

**AI setup (Stage 5):** copy `backend/.env.example` to `backend/.env` and add your key:

```bash
AI_PROVIDER=gemini             # default provider (or "openai" to swap back)
GEMINI_API_KEY=YOUR_KEY_HERE   # required for “Analyze paper”
# GEMINI_MODEL=gemini-3.6-flash  # optional override (free-tier default)
```

> 🔒 **Security note:** API keys live **only** in the backend environment (never
> `VITE_`-prefixed, never bundled into frontend code, never sent to the browser).
> All AI calls follow Frontend → FastAPI → provider. The provider is swappable:
> `AI_PROVIDER=openai` (+ `OPENAI_API_KEY`) restores the OpenAI implementation
> with no other changes.

```bash
python -m uvicorn app.main:app --port 8000
```

Health check → http://localhost:8000/api/health → `{"status":"ok","stage":"3"}`

### 2. Frontend

```bash
# project root
npm install
npm run dev                     # http://localhost:5174
```

The frontend talks to the backend via `VITE_BACKEND_URL` (see `.env.example`, defaults to `http://localhost:8000`).

### 3. Try it

1. Open http://localhost:5174
2. **Upload a paper** → pick any research-paper PDF
3. Read, navigate, search (`/`), click citations, inspect figures
4. In the workspace, open **AI Analysis** → **Analyze paper**
   - The backend sends section-aware content (title → abstract → sections,
     prioritized and budgeted) to the configured provider (Gemini by default)
     and saves structured JSON to `backend/data/papers/<id>/analysis.json`
   - Reopening the paper reuses the saved analysis — no repeat API calls
   - **Regenerate analysis** forces a fresh call (old result kept until the
     new one succeeds)
   - Without `GEMINI_API_KEY`, analysis reports “not configured” instead of failing silently

---

## 📁 Project structure

```
├── src/                        # React + TypeScript frontend
│   ├── components/
│   │   ├── layout/             # Navbar, Footer
│   │   ├── ui/                 # Button, Card, Badge, Select, BrandMark
│   │   ├── upload/             # Dropzone, file preview
│   │   └── workspace/          # TopBar, outline, document, search, panels
│   ├── pages/                  # Home, Upload, Workspace, PaperWorkspace
│   ├── lib/                    # api client, types, search, utils
│   └── main.tsx / App.tsx
├── backend/                    # FastAPI document-intelligence API
│   ├── app/
│   │   ├── api/routes/         # upload, retrieval, figure/table images
│   │   ├── services/           # pdf, layout, sections, references, entities
│   │   ├── models/             # internal Paper dataclasses
│   │   ├── schemas/            # Pydantic API contract
│   │   └── utils/              # config, storage, errors
│   ├── requirements.txt
│   └── .env.example
├── public/favicon.svg          # PaperLens brand mark
└── README.md
```

---

## 🔌 API overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service status |
| `POST` | `/api/papers/upload` | Upload PDF → `{ paper_id, filename, status }` |
| `GET` | `/api/papers/{paper_id}` | Full structured paper model (+ `analysis_status`) |
| `POST` | `/api/papers/{paper_id}/analyze` | Generate AI analysis (`{"force": false}` reuses cache) |
| `GET` | `/api/papers/{paper_id}/analysis` | Saved analysis, or 404 if none yet |
| `GET` | `/api/papers/{paper_id}/media/{figure\|table}/{index}/image` | Rendered region PNG (404 if unavailable) |

Upload errors are human-readable (`400` wrong type · `413` oversized · `422` corrupted/encrypted · `404` unknown paper). Internals never leak.

---

## 🗺️ Roadmap

- [x] **Stage 1** — Product foundation + design system
- [x] **Stage 2** — PDF processing + extraction API
- [x] **Stage 3** — Document intelligence (hierarchy, citations, entities, quality)
- [x] **Stage 4** — Research workspace + reading experience + branding
- [x] **Stage 5** — AI integration (structured analysis + evidence + caching)
- [ ] **Stage 6+** — Paper Q&A, RAG, difficulty adaptation, research gaps, viva, comparison

---

## 🎨 Design language

Restrained academic software — strong typography, hairline borders, generous whitespace, one burgundy accent (`#8F2D3C`) on paper (`#FAFAF8`). No gradients, no glow, no dashboards, no fake data. Every pixel earns its place.

---

<div align="center">

Built for students learning to read research. 📚

</div>
