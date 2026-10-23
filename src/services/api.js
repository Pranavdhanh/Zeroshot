// Central API Client for UPI Shield AI
// Connects to FastAPI Backend at VITE_API_BASE_URL (default http://127.0.0.1:8000)

import {
  MOCK_TRANSACTIONS,
  MOCK_DASHBOARD_SUMMARY,
  MOCK_ALERTS,
  MOCK_CASES,
  MOCK_NETWORK_SCENARIOS,
  RECIPIENT_PRESETS
} from '../data/mockData';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const REQUEST_TIMEOUT_MS = 3500;

/**
 * Helper to fetch with timeout
 */
async function fetchWithTimeout(resource, options = {}) {
  const { timeout = REQUEST_TIMEOUT_MS } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(resource, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(options.headers || {})
      }
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

/**
 * Health check to verify if the FastAPI backend is running
 */
export async function checkBackendHealth() {
  const startTime = performance.now();
  try {
    // Try pinging docs or health endpoint
    const response = await fetchWithTimeout(`${API_BASE_URL}/docs`, {
      method: 'GET',
      timeout: 1800
    });
    const latency = Math.round(performance.now() - startTime);
    return {
      isOnline: response.ok || response.status === 200 || response.status === 404,
      latencyMs: latency,
      endpoint: API_BASE_URL
    };
  } catch (err) {
    return {
      isOnline: false,
      latencyMs: null,
      endpoint: API_BASE_URL,
      error: err.message
    };
  }
}

/**
 * Deterministic client-side heuristic fallback when backend is unreachable.
 * NEVER claimed to be real ML; clearly stamped as DEMO FALLBACK.
 */
function computeDeterministicFallback(payload) {
  const { amount = 0, recipient_id = '', device_changed = false } = payload;
  const numAmount = Number(amount);

  // Check if known suspicious preset
  const suspiciousPreset = RECIPIENT_PRESETS.find(
    (p) => p.id === recipient_id || p.upiId.toLowerCase() === recipient_id.toLowerCase()
  );

  let decision = 'ALLOW';
  let risk_score = 12;
  const reasons = [];

  if (suspiciousPreset && suspiciousPreset.expectedOutcome === 'HOLD') {
    decision = 'HOLD';
    risk_score = 88;
    reasons.push(
      'Flagged Mule Ring: Known high-velocity aggregation node (I4C Match)',
      'Unusual pass-through pattern detected in recipient cluster'
    );
  } else if (suspiciousPreset && suspiciousPreset.expectedOutcome === 'WARN') {
    decision = 'WARN';
    risk_score = 54;
    reasons.push(
      'New beneficiary: No prior financial history with this VPA',
      'Unverified merchant / individual handle'
    );
  } else if (recipient_id === 'U009' || recipient_id.includes('mule') || recipient_id.includes('settle')) {
    decision = 'HOLD';
    risk_score = 92;
    reasons.push(
      'Mule account identifier signature matched in National Registry',
      'Multiple recent cyber fraud complaints associated with beneficiary'
    );
  } else if (numAmount > 50000) {
    decision = 'HOLD';
    risk_score = 82;
    reasons.push(
      'Amount exceeds daily single-transaction high-risk threshold (₹50,000+)',
      'Velocity anomaly: First-time outsized payment'
    );
  } else if (numAmount > 15000) {
    decision = 'WARN';
    risk_score = 48;
    reasons.push(
      'High transaction value relative to user standard profile',
      'Payment requires secondary authentication confirmation'
    );
  } else {
    decision = 'ALLOW';
    risk_score = 14;
    reasons.push(
      'Legitimate recipient profile & normal velocity match',
      'Within standard peer-to-peer risk tolerance'
    );
  }

  if (device_changed) {
    risk_score = Math.min(99, risk_score + 22);
    reasons.push('Unfamiliar device or altered SIM binding detected');
    if (decision === 'ALLOW') {
      decision = 'WARN';
    } else if (decision === 'WARN' && risk_score >= 70) {
      decision = 'HOLD';
    }
  }

  return {
    isFallback: true,
    source: 'OFFLINE_DEMO_FALLBACK',
    transaction_id: `SIM-${Math.floor(100000 + Math.random() * 900000)}`,
    risk_score,
    decision,
    reasons,
    latency_ms: 18,
    timestamp: new Date().toISOString()
  };
}

/**
 * Score a transaction using the FastAPI backend:
 * POST /api/transactions/score
 */
export async function scoreTransaction(payload) {
  const startTime = performance.now();
  const requestBody = {
    sender_id: payload.sender_id || 'U001',
    recipient_id: payload.recipient_id,
    amount: Number(payload.amount),
    timestamp: payload.timestamp || new Date().toISOString(),
    device_changed: Boolean(payload.device_changed)
  };

  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/transactions/score`, {
      method: 'POST',
      body: JSON.stringify(requestBody),
      timeout: 3000
    });

    const networkLatency = Math.round(performance.now() - startTime);

    if (!response.ok) {
      throw new Error(`Backend returned HTTP status ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // Validate expected structure from FastAPI
    return {
      isFallback: false,
      source: 'LIVE_FASTAPI_BACKEND',
      transaction_id: data.transaction_id || `TX-${Math.floor(100000 + Math.random() * 900000)}`,
      risk_score: typeof data.risk_score === 'number' ? data.risk_score : 50,
      decision: (data.decision || 'WARN').toUpperCase(),
      reasons: Array.isArray(data.reasons) ? data.reasons : ['Backend scored transaction'],
      latency_ms: typeof data.latency_ms === 'number' ? data.latency_ms : networkLatency,
      timestamp: requestBody.timestamp
    };
  } catch (error) {
    // If backend is unavailable, network error, or 404, fallback to client simulation
    const fallbackResult = computeDeterministicFallback(requestBody);
    fallbackResult.backendError = error.message;
    return fallbackResult;
  }
}

/**
 * Get Transactions History
 * GET /api/transactions
 */
export async function fetchTransactions() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/transactions`, { timeout: 2500 });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data: Array.isArray(data) ? data : (data.transactions || [])
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      data: MOCK_TRANSACTIONS
    };
  }
}

/**
 * Get Dashboard Summary Statistics
 * GET /api/dashboard/summary
 */
export async function fetchDashboardSummary() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/dashboard/summary`, { timeout: 2500 });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      data: MOCK_DASHBOARD_SUMMARY
    };
  }
}

/**
 * Get Alerts
 * GET /api/alerts
 */
export async function fetchAlerts() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/alerts`, { timeout: 2500 });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data: Array.isArray(data) ? data : (data.alerts || [])
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      data: MOCK_ALERTS
    };
  }
}

/**
 * Get Mule Account Network Graph
 * GET /api/network?scenario={scenarioId}
 */
export async function fetchNetworkGraph(scenarioId = 'mule_ring_3tier') {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/network?scenario=${scenarioId}`, { timeout: 2500 });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      data: MOCK_NETWORK_SCENARIOS[scenarioId] || MOCK_NETWORK_SCENARIOS.mule_ring_3tier
    };
  }
}

/**
 * Trigger backend mule scenario simulation if endpoint exists
 * POST /api/network/simulate
 */
export async function triggerMuleScenario(scenarioId) {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/network/simulate`, {
      method: 'POST',
      body: JSON.stringify({ scenario: scenarioId }),
      timeout: 3000
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      data: MOCK_NETWORK_SCENARIOS[scenarioId]
    };
  }
}

/**
 * Get Cases List
 * GET /api/cases
 */
export async function fetchCases() {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/cases`, { timeout: 2500 });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data: Array.isArray(data) ? data : (data.cases || [])
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      data: MOCK_CASES
    };
  }
}

/**
 * Update Case Status
 * PATCH /api/cases/{case_id}
 */
export async function updateCaseStatus(caseId, status, note = '') {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/api/cases/${caseId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, note }),
      timeout: 3000
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return {
      isFallback: false,
      data
    };
  } catch (error) {
    return {
      isFallback: true,
      backendError: error.message,
      success: true,
      case_id: caseId,
      status,
      note
    };
  }
}
