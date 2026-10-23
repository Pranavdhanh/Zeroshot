// Sample mock data for UPI Shield AI
// Used when backend endpoints are still being developed or as development fallbacks.

export const SAMPLE_SENDERS = [
  {
    id: "U001",
    name: "Rahul Sharma",
    upiId: "rahul.sharma@okhdfcbank",
    bankName: "HDFC Bank",
    accountNumber: "•••• 4821",
    balance: 74500,
    device: "Samsung Galaxy S24 (Current)",
    city: "Chennai, Tamil Nadu"
  },
  {
    id: "U002",
    name: "Priya Sundaram",
    upiId: "priya.sundaram@oksbi",
    bankName: "State Bank of India",
    accountNumber: "•••• 9012",
    balance: 128000,
    device: "iPhone 15 Pro",
    city: "Vellore, Tamil Nadu"
  },
  {
    id: "U003",
    name: "Ananya Verma",
    upiId: "ananya.v@icici",
    bankName: "ICICI Bank",
    accountNumber: "•••• 3341",
    balance: 32400,
    device: "OnePlus 12",
    city: "Bengaluru, Karnataka"
  }
];

export const RECIPIENT_PRESETS = [
  // Known / Safe (ALLOW)
  {
    id: "REC_SAFE_1",
    name: "Kavitha Sharma (Mom)",
    upiId: "kavitha.sharma@okaxis",
    type: "known",
    badge: "Known Recipient",
    suggestedAmount: 2500,
    note: "Groceries & household",
    presetCategory: "Safe / Family",
    expectedOutcome: "ALLOW"
  },
  {
    id: "REC_SAFE_2",
    name: "Deepak Verma (Landlord)",
    upiId: "deepak.rentals@paytm",
    type: "known",
    badge: "Known Recipient",
    suggestedAmount: 18000,
    note: "October Apartment Rent",
    presetCategory: "Safe / Verified",
    expectedOutcome: "ALLOW"
  },
  {
    id: "REC_SAFE_3",
    name: "City Fresh Supermarket",
    upiId: "citymart@poshdfc",
    type: "known",
    badge: "Verified Merchant",
    suggestedAmount: 1450,
    note: "Weekly provisions",
    presetCategory: "Safe / Merchant",
    expectedOutcome: "ALLOW"
  },
  // New / Unverified (WARN)
  {
    id: "REC_WARN_1",
    name: "Ramesh Kumar (Auto Driver)",
    upiId: "ramesh.cab@ybl",
    type: "new",
    badge: "New Recipient",
    suggestedAmount: 480,
    note: "Cab fare to VIT campus",
    presetCategory: "New / Unverified VPA",
    expectedOutcome: "WARN"
  },
  {
    id: "REC_WARN_2",
    name: "Vikram Creative Studio",
    upiId: "vikram.creatives@icici",
    type: "new",
    badge: "High Amount New VPA",
    suggestedAmount: 24500,
    note: "Freelance web development advance",
    presetCategory: "Unusual Velocity / First-time",
    expectedOutcome: "WARN"
  },
  // Suspicious / Mule Account (HOLD)
  {
    id: "U009",
    name: "FastPay Global Desk (Mule Ring)",
    upiId: "u009.settle@ybl",
    type: "suspicious",
    badge: "Flagged Mule Account",
    suggestedAmount: 45000,
    note: "Urgent crypto collateral refund",
    presetCategory: "Mule Account / I4C Match",
    expectedOutcome: "HOLD"
  },
  {
    id: "REC_HOLD_2",
    name: "Telecom Lucky Prize Claim",
    upiId: "prize.claim2026@oksbi",
    type: "suspicious",
    badge: "Known Phishing Pattern",
    suggestedAmount: 15000,
    note: "Lottery processing fee",
    presetCategory: "Social Engineering Fraud",
    expectedOutcome: "HOLD"
  }
];

export const MOCK_TRANSACTIONS = [
  {
    transaction_id: "TX-984102",
    sender_id: "U001",
    sender_name: "Rahul Sharma",
    sender_upi: "rahul.sharma@okhdfcbank",
    recipient_id: "REC_SAFE_1",
    recipient_name: "Kavitha Sharma",
    recipient_upi: "kavitha.sharma@okaxis",
    amount: 2500,
    risk_score: 8,
    decision: "ALLOW",
    reasons: ["Verified family contact", "Consistent transaction history", "Trusted device signature"],
    latency_ms: 9,
    timestamp: "2026-10-23T08:52:14+05:30",
    utr: "429188391029",
    device_changed: false
  },
  {
    transaction_id: "TX-984101",
    sender_id: "U001",
    sender_name: "Rahul Sharma",
    sender_upi: "rahul.sharma@okhdfcbank",
    recipient_id: "U009",
    recipient_name: "FastPay Global Desk",
    recipient_upi: "u009.settle@ybl",
    amount: 45000,
    risk_score: 88,
    decision: "HOLD",
    reasons: [
      "Recipient flagged in I4C Mule Ring DB",
      "Immediate rapid pass-through velocity detected",
      "High amount anomaly (+420% vs average)",
      "Unfamiliar device fingerprint"
    ],
    latency_ms: 14,
    timestamp: "2026-10-23T08:41:20+05:30",
    utr: "429188390881",
    device_changed: true
  },
  {
    transaction_id: "TX-984100",
    sender_id: "U002",
    sender_name: "Priya Sundaram",
    sender_upi: "priya.sundaram@oksbi",
    recipient_id: "REC_WARN_1",
    recipient_name: "Ramesh Kumar",
    recipient_upi: "ramesh.cab@ybl",
    amount: 1200,
    risk_score: 42,
    decision: "WARN",
    reasons: [
      "First time transacting with this VPA",
      "Recipient handle registered < 48 hours ago",
      "Slight deviation from normal spending pattern"
    ],
    latency_ms: 11,
    timestamp: "2026-10-23T08:15:02+05:30",
    utr: "429188390144",
    device_changed: false
  },
  {
    transaction_id: "TX-984099",
    sender_id: "U003",
    sender_name: "Ananya Verma",
    sender_upi: "ananya.v@icici",
    recipient_id: "REC_SAFE_2",
    recipient_name: "Deepak Verma",
    recipient_upi: "deepak.rentals@paytm",
    amount: 18000,
    risk_score: 12,
    decision: "ALLOW",
    reasons: ["Monthly recurring pattern matched", "Beneficiary verified > 6 months"],
    latency_ms: 8,
    timestamp: "2026-10-23T07:45:10+05:30",
    utr: "429188389410",
    device_changed: false
  },
  {
    transaction_id: "TX-984098",
    sender_id: "U001",
    sender_name: "Rahul Sharma",
    sender_upi: "rahul.sharma@okhdfcbank",
    recipient_id: "REC_HOLD_2",
    recipient_name: "Telecom Lucky Prize Claim",
    recipient_upi: "prize.claim2026@oksbi",
    amount: 15000,
    risk_score: 94,
    decision: "HOLD",
    reasons: [
      "Keywords match known social engineering lottery phishing scam",
      "Recipient VPA has 14 prior fraud reports this week",
      "Mule account cluster connection detected"
    ],
    latency_ms: 16,
    timestamp: "2026-10-23T06:30:18+05:30",
    utr: "429188388102",
    device_changed: true
  },
  {
    transaction_id: "TX-984097",
    sender_id: "U002",
    sender_name: "Priya Sundaram",
    sender_upi: "priya.sundaram@oksbi",
    recipient_id: "REC_SAFE_3",
    recipient_name: "City Fresh Supermarket",
    recipient_upi: "citymart@poshdfc",
    amount: 1450,
    risk_score: 5,
    decision: "ALLOW",
    reasons: ["Verified merchant QR", "Trusted terminal"],
    latency_ms: 7,
    timestamp: "2026-10-23T06:12:00+05:30",
    utr: "429188387091",
    device_changed: false
  },
  {
    transaction_id: "TX-984096",
    sender_id: "U003",
    sender_name: "Ananya Verma",
    sender_upi: "ananya.v@icici",
    recipient_id: "REC_WARN_2",
    recipient_name: "Vikram Creative Studio",
    recipient_upi: "vikram.creatives@icici",
    amount: 24500,
    risk_score: 58,
    decision: "WARN",
    reasons: [
      "High amount to newly created merchant account",
      "Absence of historical reciprocal transactions",
      "Off-peak transaction hour"
    ],
    latency_ms: 13,
    timestamp: "2026-10-23T04:20:15+05:30",
    utr: "429188386119",
    device_changed: false
  }
];

export const MOCK_DASHBOARD_SUMMARY = {
  total_transactions: 142850,
  total_volume_inr: 894500000,
  flagged_transactions: 3420,
  blocked_holds: 812,
  active_alerts: 24,
  avg_latency_ms: 11.4,
  mule_accounts_intercepted: 138,
  recovered_amount_inr: 42100000,
  risk_distribution: [
    { range: "0-20 (Very Low)", count: 112400, color: "#10B981" },
    { range: "21-40 (Low)", count: 21800, color: "#34D399" },
    { range: "41-60 (Moderate)", count: 5230, color: "#F59E0B" },
    { range: "61-80 (Elevated)", count: 2608, color: "#F97316" },
    { range: "81-100 (Critical Hold)", count: 812, color: "#EF4444" }
  ],
  hourly_trends: [
    { hour: "00:00", total: 1820, suspicious: 42, holds: 12 },
    { hour: "02:00", total: 940, suspicious: 65, holds: 28 }, // late night fraud spike
    { hour: "04:00", total: 680, suspicious: 58, holds: 24 },
    { hour: "06:00", total: 1450, suspicious: 22, holds: 6 },
    { hour: "08:00", total: 4200, suspicious: 54, holds: 14 },
    { hour: "10:00", total: 9800, suspicious: 112, holds: 31 },
    { hour: "12:00", total: 14200, suspicious: 198, holds: 48 },
    { hour: "14:00", total: 12800, suspicious: 176, holds: 41 },
    { hour: "16:00", total: 15400, suspicious: 215, holds: 52 },
    { hour: "18:00", total: 18600, suspicious: 240, holds: 61 },
    { hour: "20:00", total: 21400, suspicious: 310, holds: 78 },
    { hour: "22:00", total: 16200, suspicious: 280, holds: 82 }
  ],
  typology_breakdown: [
    { name: "Mule Account Ring", percentage: 38, count: 1299, color: "#EF4444" },
    { name: "Phishing & Impersonation", percentage: 26, count: 889, color: "#F97316" },
    { name: "Velocity Smurfing", percentage: 21, count: 718, color: "#F59E0B" },
    { name: "Device SIM Hijack", percentage: 15, count: 514, color: "#06B6D4" }
  ]
};

export const MOCK_ALERTS = [
  {
    alert_id: "ALT-2026-8801",
    timestamp: "10 mins ago",
    account: "u009.settle@ybl",
    severity: "CRITICAL",
    risk_score: 96,
    trigger: "Mule Layering Detected (₹4.8L inbound across 14 VPAs in 12 mins)",
    action_taken: "Account Automated Freeze + I4C Escalation",
    status: "INVESTIGATING"
  },
  {
    alert_id: "ALT-2026-8802",
    timestamp: "24 mins ago",
    account: "prize.claim2026@oksbi",
    severity: "HIGH",
    risk_score: 92,
    trigger: "Social Engineering Pattern Match (Lottery keywords in 22 requests)",
    action_taken: "VPA Inbound Transactions Blocked",
    status: "OPEN"
  },
  {
    alert_id: "ALT-2026-8803",
    timestamp: "45 mins ago",
    account: "fastcrypto.p2p@axis",
    severity: "HIGH",
    risk_score: 84,
    trigger: "Rapid Off-ramp to P2P crypto exchange aggregator",
    action_taken: "Mandatory KYC Biometric Verification Enforced",
    status: "INVESTIGATING"
  },
  {
    alert_id: "ALT-2026-8804",
    timestamp: "1 hour ago",
    account: "ramesh.cab@ybl",
    severity: "MEDIUM",
    risk_score: 52,
    trigger: "New VPA Spike: 4 first-time payers within 15 minutes",
    action_taken: "Friction Warn Prompt Shown to Users",
    status: "CLOSED"
  }
];

export const MOCK_CASES = [
  {
    case_id: "CASE-2026-9042",
    title: "Vellore-Chennai Mule Ring #14 (Coordinated Smurfing)",
    suspect_upi: "u009.settle@ybl",
    suspect_name: "Rajesh K. (Alleged Mule Broker)",
    priority: "CRITICAL",
    status: "INVESTIGATING",
    created_at: "2026-10-23 06:14",
    victims_count: 18,
    amount_at_risk: "₹14,80,000",
    typology: "3-Tier Mule Layering",
    summary: "Incoming rapid micro-deposits from 18 victims funneled into a central aggregation VPA within 20 minutes, followed by immediate cashout attempts at midnight ATMs.",
    evidence: [
      "18 concurrent UPI payments under ₹10,000 threshold to evade single-txn AML flags",
      "All source accounts initiated after SMS phishing lure link clicked",
      "IMEI and SIM IMSI mismatch across 12 mobile transactions"
    ],
    assigned_analyst: "GovTech Special Cyber Unit - Team 4",
    bank_actions: "VPA Suspended, Lien placed on target account"
  },
  {
    case_id: "CASE-2026-9041",
    title: "Telecom Rewards Phishing Campaign",
    suspect_upi: "prize.claim2026@oksbi",
    suspect_name: "Unknown / Disguised Corporate VPA",
    priority: "HIGH",
    status: "OPEN",
    created_at: "2026-10-23 05:22",
    victims_count: 24,
    amount_at_risk: "₹3,60,000",
    typology: "Phishing Impersonation",
    summary: "Fake SMS blast offering 5G data coupons directing users to enter UPI PIN under the guise of receiving a refund/reward.",
    evidence: [
      "Transaction collect requests disguised as credit vouchers",
      "VPA handle generated using temporary burner virtual numbers",
      "Matched against CERT-In phishing intelligence registry"
    ],
    assigned_analyst: "National Cyber Fraud Reporting Portal (I4C)",
    bank_actions: "Collect Request permissions revoked"
  },
  {
    case_id: "CASE-2026-9039",
    title: "Cryptocurrency P2P Layering Conduit",
    suspect_upi: "fastcrypto.p2p@axis",
    suspect_name: "CryptoDesk Node Delta",
    priority: "HIGH",
    status: "INVESTIGATING",
    created_at: "2026-10-22 23:45",
    victims_count: 9,
    amount_at_risk: "₹9,25,000",
    typology: "Crypto Off-ramp",
    summary: "Funds originating from reported extortion and loan-app blackmail converted to USDT within 7 minutes of UPI settlement.",
    evidence: [
      "Zero account balance maintained outside transaction bursts",
      "High frequency API-based UPI collect polling",
      "Associated IP addresses geolocated to offshore VPN exit nodes"
    ],
    assigned_analyst: "FinTech Intelligence Unit",
    bank_actions: "Enhanced ED monitoring applied"
  },
  {
    case_id: "CASE-2026-9035",
    title: "Cab Aggregator Fare Overcharge Ring",
    suspect_upi: "ramesh.cab@ybl",
    suspect_name: "Ramesh Kumar (Device Clone)",
    priority: "LOW",
    status: "CLOSED",
    created_at: "2026-10-22 18:30",
    victims_count: 3,
    amount_at_risk: "₹4,200",
    typology: "QR Code Tampering",
    summary: "QR code sticker on auto-rickshaw was found replaced with a third-party clone. Driver identified and notified, sticker removed.",
    evidence: [
      "Physical QR code mismatch reported by auto driver himself",
      "Small amounts totaling under ₹5,000 refunded via customer dispute desk"
    ],
    assigned_analyst: "Regional Dispute Cell",
    bank_actions: "Resolved & Closed"
  }
];

// React Flow Network Graph Scenarios
export const MOCK_NETWORK_SCENARIOS = {
  mule_ring_3tier: {
    id: "mule_ring_3tier",
    title: "Scenario 1: 3-Tier Mule Layering Ring (Smurfing)",
    description: "Innocent victim accounts are tricked into sending small funds to Tier-1 recruit mules. Funds are rapidly consolidated into a Tier-2 hub and pumped to an offshore crypto/cashout node.",
    nodes: [
      // Victims
      { id: "V1", type: "accountNode", position: { x: 40, y: 60 }, data: { id: "V1", name: "Rahul S. (Victim)", upi: "rahul@okhdfc", role: "Victim", riskScore: 12, balance: "₹45,000", status: "Compromised" } },
      { id: "V2", type: "accountNode", position: { x: 40, y: 190 }, data: { id: "V2", name: "Priya M. (Victim)", upi: "priya@oksbi", role: "Victim", riskScore: 8, balance: "₹62,000", status: "Compromised" } },
      { id: "V3", type: "accountNode", position: { x: 40, y: 320 }, data: { id: "V3", name: "Karthik R. (Victim)", upi: "karthik@icici", role: "Victim", riskScore: 15, balance: "₹18,000", status: "Compromised" } },
      { id: "V4", type: "accountNode", position: { x: 40, y: 450 }, data: { id: "V4", name: "Deepa N. (Victim)", upi: "deepa@paytm", role: "Victim", riskScore: 9, balance: "₹34,000", status: "Compromised" } },
      
      // Tier 1 Mule recruits
      { id: "M1", type: "accountNode", position: { x: 340, y: 120 }, data: { id: "M1", name: "Mule Account #101", upi: "mule101@axis", role: "Tier 1 Mule", riskScore: 78, balance: "₹1,400", status: "Suspicious", transitTime: "< 4 mins" } },
      { id: "M2", type: "accountNode", position: { x: 340, y: 380 }, data: { id: "M2", name: "Mule Account #102", upi: "mule102@kotak", role: "Tier 1 Mule", riskScore: 82, balance: "₹890", status: "Suspicious", transitTime: "< 2 mins" } },
      
      // Tier 2 Aggregator
      { id: "HUB", type: "accountNode", position: { x: 640, y: 250 }, data: { id: "HUB", name: "Mule Hub (U009)", upi: "u009.settle@ybl", role: "Tier 2 Hub", riskScore: 96, balance: "₹2,40,000", status: "Critical Flag", transitTime: "Immediate" } },
      
      // Off-ramp
      { id: "OFFRAMP", type: "accountNode", position: { x: 940, y: 250 }, data: { id: "OFFRAMP", name: "Crypto P2P Desk", upi: "crypto.settle@offshore", role: "Off-ramp Exfiltration", riskScore: 99, balance: "₹18,50,000", status: "Blocked/Frozen" } },
    ],
    edges: [
      { id: "e-v1-m1", source: "V1", target: "M1", animated: true, label: "₹15,000", style: { stroke: "#F59E0B", strokeWidth: 2 } },
      { id: "e-v2-m1", source: "V2", target: "M1", animated: true, label: "₹22,000", style: { stroke: "#F59E0B", strokeWidth: 2 } },
      { id: "e-v3-m2", source: "V3", target: "M2", animated: true, label: "₹18,500", style: { stroke: "#F59E0B", strokeWidth: 2 } },
      { id: "e-v4-m2", source: "V4", target: "M2", animated: true, label: "₹28,000", style: { stroke: "#F59E0B", strokeWidth: 2 } },
      { id: "e-m1-hub", source: "M1", target: "HUB", animated: true, label: "₹36,500", style: { stroke: "#EF4444", strokeWidth: 3 } },
      { id: "e-m2-hub", source: "M2", target: "HUB", animated: true, label: "₹46,000", style: { stroke: "#EF4444", strokeWidth: 3 } },
      { id: "e-hub-off", source: "HUB", target: "OFFRAMP", animated: true, label: "₹82,500 [INTERCEPTED]", style: { stroke: "#EF4444", strokeDasharray: "5,5", strokeWidth: 4 } },
    ]
  },
  fan_out_disbursement: {
    id: "fan_out_disbursement",
    title: "Scenario 2: Rapid Fan-Out Disbursement",
    description: "A compromised high-value business account suddenly initiates 8 simultaneous outward payments to dispersed retail accounts to rapidly dissipate stolen capital.",
    nodes: [
      { id: "CORP", type: "accountNode", position: { x: 100, y: 250 }, data: { id: "CORP", name: "Apex Retail Pvt Ltd", upi: "apex.biz@hdfc", role: "Compromised Entity", riskScore: 89, balance: "₹12,40,000", status: "Compromised Token" } },
      { id: "R1", type: "accountNode", position: { x: 500, y: 60 }, data: { id: "R1", name: "Mule Cash-out A", upi: "cash.01@oksbi", role: "Disbursement Node", riskScore: 91, balance: "₹49,000", status: "Active" } },
      { id: "R2", type: "accountNode", position: { x: 500, y: 180 }, data: { id: "R2", name: "Mule Cash-out B", upi: "cash.02@axis", role: "Disbursement Node", riskScore: 88, balance: "₹48,500", status: "Active" } },
      { id: "R3", type: "accountNode", position: { x: 500, y: 310 }, data: { id: "R3", name: "Mule Cash-out C", upi: "cash.03@icici", role: "Disbursement Node", riskScore: 93, balance: "₹49,200", status: "Active" } },
      { id: "R4", type: "accountNode", position: { x: 500, y: 440 }, data: { id: "R4", name: "Mule Cash-out D", upi: "cash.04@paytm", role: "Disbursement Node", riskScore: 87, balance: "₹47,800", status: "Active" } },
    ],
    edges: [
      { id: "e-c-r1", source: "CORP", target: "R1", animated: true, label: "₹49,000 (02:14 AM)", style: { stroke: "#EF4444", strokeWidth: 2 } },
      { id: "e-c-r2", source: "CORP", target: "R2", animated: true, label: "₹48,500 (02:15 AM)", style: { stroke: "#EF4444", strokeWidth: 2 } },
      { id: "e-c-r3", source: "CORP", target: "R3", animated: true, label: "₹49,200 (02:15 AM)", style: { stroke: "#EF4444", strokeWidth: 2 } },
      { id: "e-c-r4", source: "CORP", target: "R4", animated: true, label: "₹47,800 (02:16 AM)", style: { stroke: "#EF4444", strokeWidth: 2 } },
    ]
  },
  legitimate_merchant: {
    id: "legitimate_merchant",
    title: "Scenario 3: Normal Peer & Verified Merchant Flow",
    description: "Typical consumer behavior: regular salary deposit, rent transfer, and verified supermarket purchases exhibiting normal velocity and low risk scores.",
    nodes: [
      { id: "SALARY", type: "accountNode", position: { x: 80, y: 220 }, data: { id: "SALARY", name: "TechCorp Payroll", upi: "payroll@techcorp.biz", role: "Verified Corporate", riskScore: 2, balance: "₹85,00,000", status: "Whitelisted" } },
      { id: "USER", type: "accountNode", position: { x: 420, y: 220 }, data: { id: "USER", name: "Rahul Sharma", upi: "rahul@okhdfc", role: "Consumer", riskScore: 6, balance: "₹74,500", status: "Healthy" } },
      { id: "LANDLORD", type: "accountNode", position: { x: 780, y: 100 }, data: { id: "LANDLORD", name: "Deepak Verma", upi: "deepak.rentals@paytm", role: "Verified Landlord", riskScore: 4, balance: "₹1,20,000", status: "Verified" } },
      { id: "STORE", type: "accountNode", position: { x: 780, y: 340 }, data: { id: "STORE", name: "City Supermarket", upi: "citymart@poshdfc", role: "Verified Merchant", riskScore: 3, balance: "₹4,80,000", status: "Verified" } },
    ],
    edges: [
      { id: "e-s-u", source: "SALARY", target: "USER", animated: false, label: "₹95,000 (Monthly Salary)", style: { stroke: "#10B981", strokeWidth: 2 } },
      { id: "e-u-l", source: "USER", target: "LANDLORD", animated: false, label: "₹18,000 (Rent)", style: { stroke: "#10B981", strokeWidth: 2 } },
      { id: "e-u-s", source: "USER", target: "STORE", animated: false, label: "₹1,450 (Groceries)", style: { stroke: "#10B981", strokeWidth: 2 } },
    ]
  }
};
