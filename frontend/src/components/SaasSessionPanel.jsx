import React from 'react';
import { getSaasSessionState } from '../utils/statusMapper';

export default function SaasSessionPanel({
  proposalsCount = 0,
  definedVendorsCount = 0,
  isProcessing = false,
  isProcessed = false,
  requirements = null,
  isExtracting = false,
  hasFactSheets = false,
  hasComparison = false,
  errorMsg = null,
  onNavigate,
}) {
  const sessionState = getSaasSessionState({
    proposalsCount,
    definedVendorsCount,
    isProcessing,
    isProcessed,
    requirements,
    isExtracting,
    hasFactSheets,
    hasComparison,
    errorMsg,
  });

  return (
    <div className="context-panel">
      {/* ── CURRENT ANALYSIS ── */}
      <div className="context-box">
        <div className="context-box-title">Current Analysis</div>

        {/* Proposals stat row */}
        <div className="context-row">
          <span>Proposals</span>
          <span className="context-value">{sessionState.proposalsText}</span>
        </div>

        {/* Vendors stat row */}
        <div className="context-row">
          <span>Vendors</span>
          <span className="context-value">{sessionState.vendorsCount}</span>
        </div>

        {/* Requirements stat row (conditional) */}
        {sessionState.requirementsCount !== null && (
          <div className="context-row">
            <span>Criteria</span>
            <span className="context-value">{sessionState.requirementsCount}</span>
          </div>
        )}

        {/* Divider */}
        <div style={{ height: '1px', background: '#171717', margin: '0.75rem 0', opacity: 0.2 }} />

        {/* Status */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          <span style={{
            fontFamily: "'Space Mono', monospace",
            fontSize: '0.68rem',
            fontWeight: 700,
            letterSpacing: '0.07em',
            color: '#6A6A60',
            textTransform: 'uppercase',
          }}>
            Status
          </span>
          <span style={{
            fontFamily: "'DM Sans', sans-serif",
            fontSize: '0.875rem',
            fontWeight: 700,
            color: '#171717',
          }}>
            {sessionState.status}
          </span>
        </div>
      </div>
    </div>
  );
}
