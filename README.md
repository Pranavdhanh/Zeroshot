# UPI Shield AI — Real-Time UPI Fraud Detection & Mule Account Intelligence

[![Hackathon](https://img.shields.io/badge/VIT%20College-Track%204%3A%20FinTech%20%26%20GovTech%20Intelligence-06B6D4?style=flat-square)](#)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?style=flat-square&logo=vite&logoColor=white)](#)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react&logoColor=black)](#)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](#)
[![React Flow](https://img.shields.io/badge/React_Flow-xyflow-FF0072?style=flat-square)](#)
[![Recharts](https://img.shields.io/badge/Recharts-2.15-22D3EE?style=flat-square)](#)

> **VIT College Hackathon — Track 4: FinTech & GovTech Intelligence**  
> An AI-powered, real-time UPI transaction scoring and mule account intelligence platform designed to intercept social engineering scams, smurfing rings, and illicit money laundering **before** the debit switch executes.

---

## 🚀 Key Modules & Capabilities

### 1. Payment Simulator (`/`)
- Realistic Indian UPI-style payment interface branded **UPI Shield AI**.
- Sender account switcher (Rahul Sharma - HDFC, Priya Sundaram - SBI, Ananya Verma - ICICI).
- Presets categorized into **Known Recipients** (ALLOW), **New Recipients** (WARN), and **Suspicious / Mule Rings** (HOLD).
- Amount input (₹ INR) with quick selection chips (₹500 to ₹60,000) and balance validation.
- **Hardware & Telemetry simulation toggle**: Test "Device Changed / Unfamiliar SIM" to simulate SIM-swap fraud.
- Multi-stage real-time scoring animation (Hardware fingerprint -> Ingress velocity -> Mule graph query -> ML classifier).
- **ALLOW Outcome**: Realistic Indian UPI payment receipt with bank reference (UTR), timestamp, and share/audit buttons.
- **WARN Outcome**: Elevated risk warning with English/Tamil reasons and an explicit confirmation checkpoint.
- **HOLD Outcome**: Interception screen halting the payment prior to banking debit, with direct escalation to the National Cyber Crime Reporting Portal (1930 / I4C).
- *Strict Academic Simulation Notice: No real money is transferred.*

### 2. Fraud Decision Component
- Risk score meter ranging from **0 to 100** with dynamic color tiering (0–35 Green, 36–70 Amber, 71–100 Red).
- Displays backend decision (**ALLOW**, **WARN**, **HOLD**) and actual returned reasons.
- Displays inference latency in milliseconds (`latency_ms`).
- **Bilingual English & Tamil (தமிழ்) translation** for all risk reasons, headings, and security prompts.
- **Demo Fallback Transparency**: If the Python FastAPI backend is offline, the interface explicitly displays:
  `[DEMO FALLBACK - BACKEND OFFLINE] (Heuristic rule preview, not live ML prediction)`. Live ML results are never fabricated.

### 3. Transaction History (`/transactions`)
- Real-time audit log of all scored peer-to-peer and merchant transactions.
- Filter by decision (`ALL`, `ALLOW`, `WARN`, `HOLD`) and live search by UTR, VPA, sender, or transaction ID.
- Inspect modal displaying complete forensic details, sender device, bank account, and risk factors.
- **Export to CSV**: One-click download of audit logs for regulatory compliance.

### 4. Fraud Analyst Dashboard (`/dashboard`)
- 5 Executive KPI cards: Evaluated Volume (₹ Cr), Flagged Friction (WARN), Blocked Holds, Intercepted Mule Accounts, and Mean Latency.
- **Recharts Visualizations**:
  - 24-Hour Transaction & Fraud Volume Trend (Area Chart highlighting late-night attack surges).
  - Risk Score Distribution Histogram (Bar Chart across 0-100 buckets).
  - Intercepted Threat Typology Breakdown (Donut Chart: Mule rings, phishing, smurfing, SIM swaps).
- Real-time Anomaly Alerts table with clickable rows opening an alert investigation dossier.

### 5. Mule Account Network Graph (`/network`)
- Interactive graph visualization powered by **React Flow (`@xyflow/react`)**.
- Custom account nodes displaying VPA, role, risk score badge, balance, and status.
- Directed animated edges displaying transfer amounts (₹) and directions.
- **3 Investigation Scenarios**:
  1. *3-Tier Layering Ring (Smurfing)*: Victims → Tier-1 Mules → Tier-2 Aggregator Hub → Crypto Off-ramp.
  2. *Rapid Fan-Out Disbursement*: Compromised entity rapidly dissipating funds across retail cash-out mules.
  3. *Normal Peer & Merchant Flow*: Legitimate consumer salary, rent, and grocery purchases.
- Account Dossier inspection panel with transit velocity window, connected inflow/outflow streams, and sandbox actions: **"Freeze VPA in Sandbox"** and **"File I4C Intelligence Dossier"**.

### 6. Case Management & GovTech Dossiers (`/cases`)
- Investigation list with statuses: `OPEN`, `INVESTIGATING`, `CLOSED`.
- Priority filters (`CRITICAL`, `HIGH`, `LOW`) and search.
- Case Dossier modal with forensic evidence traces, victim counts, capital at risk, and analyst notes box.
- Status update workflow integrated with backend `PATCH /api/cases/{case_id}` (or sandbox local state if offline).

### 7. Bilingual English & Tamil (தமிழ்) Support
- Instant language toggle in the navigation bar.
- Pre-mapped translations for all backend anomaly reasons and security warnings to assist Tamil Nadu regional cyber crime units and end users.

---

## 🛠️ Quickstart & Run Commands

### Prerequisites
- Node.js (v18+ recommended)
- npm or yarn

### 1. Installation
```powershell
npm install
```

### 2. Environment Setup
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Default configuration:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Start Development Server
```powershell
npm run dev
```
Open your browser at `http://localhost:5173`.

### 4. Production Build
```powershell
npm run build
npm run preview
```

---

## 🔌 FastAPI Backend Integration Contract

The frontend connects to the Python FastAPI backend at `http://127.0.0.1:8000`.

### Core Endpoint: `POST /api/transactions/score`

#### Request Payload:
```json
{
  "sender_id": "U001",
  "recipient_id": "U009",
  "amount": 15000,
  "timestamp": "2026-10-23T22:30:00.000Z",
  "device_changed": true
}
```

#### Expected Response:
```json
{
  "transaction_id": "TX1001",
  "risk_score": 82,
  "decision": "HOLD",
  "reasons": [
    "New recipient",
    "Amount is unusually high",
    "Unfamiliar device"
  ],
  "latency_ms": 12
}
```

### Optional Endpoints Supported:
- `GET /api/transactions`: Returns list of historical evaluated transactions.
- `GET /api/dashboard/summary`: Returns aggregate metrics, risk distribution, and hourly trends.
- `GET /api/alerts`: Returns active anomaly alerts.
- `GET /api/network?scenario={id}`: Returns custom nodes and edges for the account graph.
- `POST /api/network/simulate`: Triggers a dynamic mule simulation on the backend.
- `GET /api/cases`: Returns cyber cell investigation dossiers.
- `PATCH /api/cases/{case_id}`: Updates case status (`OPEN`, `INVESTIGATING`, `CLOSED`) with analyst notes.

*Note: All endpoints are isolated in `src/services/api.js`. If any endpoint is not yet implemented in the backend, the frontend gracefully falls back to calibrated hackathon demonstration data without crashing.*

---

## 📁 Project Structure

```
c:\Users\Welcome\Downloads\Zeroshot-main\
├── .env.example                       # API Base URL configuration template
├── .env                               # Local environment config
├── .gitignore                         # Excludes node_modules, dist, .env
├── index.html                         # Dark mode root with Google Fonts
├── package.json                       # Dependencies & scripts
├── postcss.config.js                  # PostCSS plugins
├── tailwind.config.js                 # Custom navy, cyan & risk color palette
├── vite.config.js                     # Vite build configuration
├── src/
│   ├── main.jsx                       # Application entry point
│   ├── App.jsx                        # React Router routes & global state
│   ├── index.css                      # Tailwind base & custom UI styles
│   ├── services/
│   │   └── api.js                     # Central API client, health check & fallbacks
│   ├── context/
│   │   ├── LanguageContext.jsx        # English/Tamil dictionary & reason mapping
│   │   ├── ToastContext.jsx           # Global toast notification provider
│   │   └── BackendStatusContext.jsx   # FastAPI heartbeat connectivity monitor
│   ├── data/
│   │   └── mockData.js                # Calibrated baseline presets & test scenarios
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.jsx             # Top bar, status badge & language switcher
│   │   │   └── Footer.jsx             # Hackathon track & simulation disclaimer
│   │   ├── payment/
│   │   │   ├── PaymentForm.jsx        # Indian UPI simulator form with presets
│   │   │   ├── FraudDecisionComponent.jsx # Risk gauge, reasons & latency
│   │   │   ├── PaymentReceipt.jsx     # ALLOW outcome receipt with UTR
│   │   │   ├── WarnDecisionModal.jsx  # WARN confirmation checkpoint
│   │   │   └── HoldDecisionScreen.jsx # HOLD security interception screen
│   │   └── network/
│   │       └── AccountCustomNode.jsx  # React Flow custom account card node
│   └── pages/
│       ├── PaymentSimulatorPage.jsx   # End-to-end payment state machine
│       ├── TransactionsPage.jsx       # Real-time transaction audit & CSV export
│       ├── DashboardPage.jsx          # Recharts metrics, trends & alerts
│       ├── MuleNetworkPage.jsx        # Interactive React Flow mule graph
│       └── CaseManagementPage.jsx     # GovTech I4C investigation dossiers
└── dist/                              # Verified production build output
```

---

## 🏆 Hackathon Presentation Tips
1. **Live vs Offline Indicator**: Point to the status pill in the top-right navbar. When your teammate's FastAPI server runs on `http://127.0.0.1:8000`, it immediately turns green (`FastAPI Connected (12ms)`). When disconnected, it clearly shows `Backend Offline (Demo Fallback)`.
2. **Tamil Localization**: Click the `தமிழ்` button in the header during the demo to show the bilingual accessibility designed for Tamil Nadu state enforcement and regional users.
3. **Mule Network Tab**: Walk the judges through **Scenario 1 (3-Tier Layering Ring)** and click on `U009.settle@ybl` to demonstrate the automated fund freezing and I4C dossier generation.