const API_BASE_URL = 'http://localhost:8000/api';

/**
 * Safely extract a human-readable string from a FastAPI error response.
 * FastAPI detail can be a string OR an array of validation error objects.
 */
function extractErrorMessage(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((e) => (e.msg || JSON.stringify(e))).join('; ');
  }
  if (typeof detail === 'object') return detail.msg || JSON.stringify(detail);
  return String(detail);
}

/**
 * Fetch backend system health status.
 */
export async function fetchHealthStatus() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Failed to connect to backend server.');
  }
  return response.json();
}

/**
 * Fetch session summary metadata for hydration.
 */
export async function fetchSessionSummary(sessionId) {
  const response = await fetch(`${API_BASE_URL}/proposals/session/${sessionId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return {
      success: false,
      error: extractErrorMessage(errorData.detail, 'Session expired or not found.'),
    };
  }
  const data = await response.json();
  return { success: true, data };
}


/**
 * Process proposal PDF files.
 */
export async function processProposals(files, vendorNames = []) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  vendorNames.forEach((name) => {
    formData.append('vendor_names', name);
  });

  const response = await fetch(`${API_BASE_URL}/proposals/process`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to process proposal PDFs.') };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Perform evidence search across processed proposal vector index.
 */
export async function searchEvidence(sessionId, query, vendorName = null, topK = 5) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    query: query,
    top_k: topK,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/retrieval/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to retrieve proposal evidence.') };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Extract structured vendor fact sheets.
 */
export async function extractVendorFacts(sessionId, requirements, vendorName = null) {
  if (!sessionId) {
    throw new Error('Proposals must be uploaded and processed before analyzing vendor details.');
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/analysis/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(extractErrorMessage(errorData.detail, 'Failed to extract vendor fact sheets.'));
  }

  return response.json();
}

/**
 * Save procurement evaluation requirements for active session (Zero Groq calls required).
 */
export async function saveRequirements(sessionId, requirements) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };

  const response = await fetch(`${API_BASE_URL}/analysis/requirements`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return {
      success: false,
      error: extractErrorMessage(
        errorData.detail,
        'Unable to save requirements. Please check the highlighted fields and try again.'
      ),
    };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Perform deterministic requirement comparison evaluation.
 * Requires facts to already be cached via prepareComparison — makes 0 Groq calls.
 */
export async function evaluateComparison(sessionId, requirements, vendorName = null) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/comparison/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to evaluate requirement comparison.') };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Extract and cache vendor fact sheets (Groq extraction step).
 * Must be called once per session before evaluateComparison.
 * After this call, evaluateComparison is deterministic and makes 0 Groq calls.
 */
export async function prepareComparison(sessionId, requirements, vendorName = null) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/comparison/prepare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to prepare vendor analysis.') };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Analyze contract risks and intra-vendor contradictions.
 */
export async function analyzeRisks(sessionId, requirements = null, vendorName = null) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/risks/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to analyze contract risks.') };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Generate vendor clarification questions from analysis gaps.
 */
export async function generateClarifications(sessionId, requirements = null, vendorName = null) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/clarifications/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to generate vendor clarifications.') };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Evaluate transparent deterministic vendor alignment scores and ranking.
 */
export async function evaluateScoring(sessionId, requirements = null, vendorName = null) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };
  if (vendorName) {
    payload.vendor_name = vendorName;
  }

  const response = await fetch(`${API_BASE_URL}/scoring/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return {
      success: false,
      status: response.status,
      errorData: errorData,
      error: extractErrorMessage(errorData.detail, 'Failed to evaluate vendor scoring.'),
    };
  }

  const data = await response.json();
  return { success: true, data };
}

/**
 * Fetch authoritative session workflow state and module statuses.
 */
export async function fetchWorkflowState(sessionId) {
  if (!sessionId) return { success: false, error: 'Session ID missing.' };
  const response = await fetch(`${API_BASE_URL}/analysis/workflow-state/${sessionId}`);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, error: extractErrorMessage(errorData.detail, 'Failed to fetch workflow state.') };
  }
  const data = await response.json();
  return { success: true, data };
}

/**
 * Generate evidence-backed executive recommendation decision brief.
 */
export async function generateRecommendation(sessionId, requirements = null) {
  if (!sessionId) {
    return { success: false, error: 'Session ID missing. Upload proposals first.' };
  }

  const payload = {
    session_id: sessionId,
    requirements: requirements,
  };

  const response = await fetch(`${API_BASE_URL}/recommendation/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return {
      success: false,
      status: response.status,
      errorData: errorData,
      error: extractErrorMessage(errorData.detail, 'Failed to generate recommendation brief.'),
    };
  }

  const data = await response.json();
  return { success: true, data };
}
