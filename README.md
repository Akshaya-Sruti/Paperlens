<div align="center">

# PaperLens

**Understand research. Your way.**

Turn dense research papers into structured, navigable reading experiences — at your level.

![Stage](https://img.shields.io/badge/stage-4%20workspace-8F2D3C)
![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-171717)
![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20PyMuPDF-171717)
![AI](https://img.shields.io/badge/AI-not%20yet-F3F3F0)

</div>

---

## What is PaperLens?

PaperLens helps **students understand research papers**. Upload a PDF and get a clean research workspace: a navigable outline, readable sections with page references, figures and tables, linked citations and references, local search, and raw-extraction transparency.

> **No AI yet — by design.** Stages 1–4 build a rock-solid document foundation (upload → extraction → document intelligence → reading experience). LLM features (explanations, Q&A, research-gap analysis) plug into this foundation in later stages.

---

## ✨ Features (Stage 4)

| Area | What you get |
|---|---|
| 📄 **Upload flow** | Drag & drop PDF (≤ 20 MB) with honest processing milestones |
| 🔍 **PDF extraction** | Page-preserving text, layout-aware reading order (incl. two-column) |
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
 ↓  REST API
React workspace  ──  outline · document · search · context panel
```

**Planned next:** AI layer (explanations, Q&A, RAG) consumes the structured paper model — no rewrites needed.

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
| `GET` | `/api/papers/{paper_id}` | Full structured paper model |
| `GET` | `/api/papers/{paper_id}/media/{figure\|table}/{index}/image` | Rendered region PNG (404 if unavailable) |

Upload errors are human-readable (`400` wrong type · `413` oversized · `422` corrupted/encrypted · `404` unknown paper). Internals never leak.

---

## 🗺️ Roadmap

- [x] **Stage 1** — Product foundation + design system
- [x] **Stage 2** — PDF processing + extraction API
- [x] **Stage 3** — Document intelligence (hierarchy, citations, entities, quality)
- [x] **Stage 4** — Research workspace + reading experience + branding
- [ ] **Stage 5+** — AI explanations, paper Q&A, research-gap analysis (LLM/RAG)

---

## 🎨 Design language

Restrained academic software — strong typography, hairline borders, generous whitespace, one burgundy accent (`#8F2D3C`) on paper (`#FAFAF8`). No gradients, no glow, no dashboards, no fake data. Every pixel earns its place.

---

<div align="center">

Built for students learning to read research. 📚

</div>
