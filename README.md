# ⬡ ChainShieldAI

**Real-Time Intelligent Propagation & Pattern Learning Engine for Fraud Detection**

ChainShieldAI detects suspicious money movement patterns (money mule networks) across transaction graphs in real-time. It propagates risk scores through account networks, fingerprints temporal chains (Mobile → Wallet → ATM), and predicts cascading cash-outs before they happen.

![Status](https://img.shields.io/badge/status-prototype-blue)
![Backend](https://img.shields.io/badge/backend-FastAPI-009688)
![Frontend](https://img.shields.io/badge/frontend-React%20TypeScript-61DAFB)

---

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm 9+**
- Git

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd ChainShieldAI
```

### 2. Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

## 🎮 Demo Walkthrough

1. **Open the frontend** at `http://localhost:3000`
2. **Click "▶ NEXT TRANSACTION"** to process transactions one-by-one
3. **Watch the graph** build in real-time as accounts and edges appear
4. **Observe risk propagation** — nodes change color from green → yellow → red as risk increases
5. **High-risk alerts** appear in the Alert Feed on the right panel
6. **Suspicious chains** are detected and displayed in the chains table
7. **Click any node** in the graph to see its detailed risk breakdown
8. **Use channel filters** (MOBILE / WALLET / ATM / BANK) to filter the graph
9. **Adjust the risk threshold** slider to show only accounts above a certain risk level
10. **Click "↺ RESET SIMULATION"** to clear and start over

---

## 🏗 Architecture

```
┌──────────────────┐         WebSocket         ┌──────────────────────┐
│   FastAPI Backend │◄──────────────────────────►│  React Frontend     │
│                   │                            │                     │
│  - Graph Engine   │    REST API (/api/*)       │  - Force Graph 2D   │
│  - Risk Model     │◄──────────────────────────►│  - Recharts         │
│  - Data Generator │                            │  - Framer Motion    │
│  - WS Manager     │                            │  - Cyber Noir Theme │
└──────────────────┘                            └──────────────────────┘
```

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/next-transaction` | Process next synthetic transaction |
| GET | `/api/graph` | Get full graph snapshot |
| POST | `/api/reset` | Reset simulation |
| GET | `/api/stats` | Get current statistics |
| GET | `/api/transactions` | Get processed transaction log |
| WS | `/ws` | Real-time graph updates |

### Risk Propagation Algorithm

1. **Base Risk** = velocity_score + amount_anomaly + channel_risk + in/out_ratio
2. **Propagation**: Each node receives `0.3 × max(neighbor_risks)` per iteration
3. **3 iterations**, normalized to 0–10, capped at 10
4. **Community Detection** via NetworkX `greedy_modularity_communities`

---

## 🔮 ML Integration Roadmap

> **Current Status: All ML values are mocked** — displayed with `⚠ MOCK` badges in the UI.

### What Will Be Replaced

| Component | Current (Mock) | Future (ML) |
|-----------|---------------|-------------|
| Cash-out Probability | Deterministic formula based on chain length | LightGBM/XGBoost `model.predict_proba()` |
| Model Risk Contribution | Hash-based fixed value per account | Feature importance from trained model |
| Model Status | Always "pending" | Live model version, accuracy, last trained |
| Chain Risk Scoring | Rule-based BFS + temporal fingerprinting | GNN-enhanced chain scoring |

### Integration Steps

1. **Train a model** (separate pipeline, out of scope for this build)
2. **Replace `ml_placeholder.py`** functions with model loading + inference
3. **Remove `is_mock_score: true`** flag from `SuspiciousChain` responses
4. **Update `mockMLData.ts`** to fetch from actual backend ML endpoints
5. **Remove `⚠ MOCK` badges** from frontend components

### Files to Modify

- `backend/app/ml_placeholder.py` → Replace mock functions with model inference
- `frontend/src/utils/mockMLData.ts` → Replace with API calls
- Components using mock data: `SuspiciousChains.tsx`, `NodeTooltip.tsx`

---

## 📁 Project Structure

```
ChainShieldAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, routers, WebSocket
│   │   ├── graph_engine.py      # NetworkX graph + risk propagation
│   │   ├── risk_model.py        # Rule-based risk scoring + chain fingerprinting
│   │   ├── ml_placeholder.py    # ⚠️ Placeholder for future ML integration
│   │   ├── data_generator.py    # Synthetic transaction generator (in-memory)
│   │   ├── models.py            # Pydantic models
│   │   └── websocket_manager.py # WebSocket connection manager
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── Graph/           # GraphCanvas, NodeTooltip
│   │   │   ├── Dashboard/       # StatsBar, ControlPanel, AlertFeed,
│   │   │   │                    # SuspiciousChains, RiskBreakdown
│   │   │   └── Layout/          # Sidebar
│   │   ├── hooks/               # useWebSocket, useGraphData
│   │   ├── types/               # TypeScript interfaces
│   │   ├── utils/               # riskColors, mockMLData
│   │   └── styles/              # globals.css (Cyber Noir theme)
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── data/                        # Existing dataset (not used at runtime)
└── README.md
```

---

## 📄 License

MIT
