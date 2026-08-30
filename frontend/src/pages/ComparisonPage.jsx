import React, { useState, useEffect } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';
import FeatureGate from '../components/FeatureGate';

/* ─────────── Status styling badge map ─────────── */
const STATUS_STYLES = {
  MEETS:       { bg: '#C8D6FF', text: '#171717', label: 'MEETS' },
  PARTIAL:     { bg: '#F4C84A', text: '#171717', label: 'PARTIAL' },
  FAILS:       { bg: '#EB7096', text: '#FFFFFF', label: 'FAILS' },
  MISSING:     { bg: '#F5F2F0', text: '#171717', label: 'MISSING' },
  UNCLEAR:     { bg: '#EBBAC2', text: '#171717', label: 'UNCLEAR' },
  CONFLICTING: { bg: '#7897FF', text: '#FFFFFF', label: 'CONFLICTING' },
};

function getStatusBadgeStyle(statusStr) {
  return STATUS_STYLES[statusStr] || { bg: '#F5F2F0', text: '#171717', label: statusStr || 'N/A' };
}

function cleanVendorName(name) {
  if (!name) return '';
  return name.replace(/^\d+[\.\s\-]+/, '').trim();
}

function renderHighlightedExcerpt(excerpt, rawTerm) {
  if (!excerpt) return null;
  if (!rawTerm || !rawTerm.trim()) return excerpt;

  const numbers = rawTerm.match(/\b\d+[\d,.]*\b/g) || [];
  const words = rawTerm.split(/\s+/).filter(w => w.length > 3 && !['meets', 'fails', 'partial', 'none', 'null', 'true', 'false', 'usd', 'eur', 'gbp', 'requirement'].includes(w.toLowerCase()));
  const termsToHighlight = [...new Set([...numbers, ...words])];

  if (termsToHighlight.length === 0) return excerpt;

  try {
    const escaped = termsToHighlight.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const regex = new RegExp(`(${escaped.join('|')})`, 'gi');
    const parts = excerpt.split(regex);

    return parts.map((part, idx) => {
      const isMatch = termsToHighlight.some(t => t.toLowerCase() === part.toLowerCase());
      if (isMatch) {
        return (
          <mark key={idx} style={{ backgroundColor: '#F4C84A', color: '#171717', fontWeight: 700, padding: '0.1rem 0.25rem', borderRadius: '2px', border: '1px solid #171717' }}>
            {part}
          </mark>
        );
      }
      return part;
    });
  } catch (err) {
    return excerpt;
  }
}

export default function ComparisonPage({
  sessionId,
  hasRequirements = false,
  requirements = null,
  comparisonData,
  factsReady = false,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateVendorDetails,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
  onRunComparison,
}) {
  const matrixRows = comparisonData?.matrix_rows || [];
  const summaryCounts = comparisonData?.vendor_summary_counts || {};

  const vendors = Object.keys(summaryCounts).length > 0
    ? Object.keys(summaryCounts)
    : matrixRows.length > 0 && matrixRows[0]?.vendor_evaluations
    ? Object.keys(matrixRows[0].vendor_evaluations)
    : [];

  const [selectedCell, setSelectedCell] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [compareStep, setCompareStep] = useState(''); // 'analyzing' | 'comparing' | ''
  const [compareError, setCompareError] = useState(null);
  const [isSessionExpired, setIsSessionExpired] = useState(false);
  const [activeFilter, setActiveFilter] = useState('ALL');

  const SIDEBAR_PROPS = {
    activeTab: 'comparison',
    sessionReady: !!sessionId,
    onNavigateHome,
    onNavigateDashboard,
    onNavigateRequirements,
    onNavigateComparison,
    onNavigateRisks,
    onNavigateClarifications,
    onNavigateRanking,
    onNavigateRecommendation,
  };

  async function handleRunComparison() {
    setIsComparing(true);
    setCompareError(null);
    setIsSessionExpired(false);
    setCompareStep(factsReady ? 'comparing' : 'analyzing');
    try {
      if (onRunComparison) {
        await onRunComparison();
      }
      setCompareStep('');
    } catch (err) {
      const msg = err?.message || 'Comparison could not be completed. Please try again.';
      setCompareError(msg);
      if (msg.toLowerCase().includes('expired') || msg.toLowerCase().includes('re-upload')) {
        setIsSessionExpired(true);
      }
      setCompareStep('');
    } finally {
      setIsComparing(false);
    }
  }

  // Filter matrix rows by active status filter
  function rowMatchesFilter(row) {
    if (activeFilter === 'ALL') return true;
    return Object.values(row.vendor_evaluations || {}).some(
      (ev) => ev.status === activeFilter
    );
  }

  const filteredRows = matrixRows.filter(rowMatchesFilter);

  // STATE A: No Session / Proposals
  if (!sessionId) {
    return (
      <div className="dashboard-layout">
        <Sidebar {...SIDEBAR_PROPS} />
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Requirement Comparison</h1>
            <p className="dashboard-subtitle">Compare vendor responses against defined procurement requirements.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow="PREREQUISITE REQUIRED"
              title="UPLOAD PROPOSALS FIRST"
              description="Add at least 2 vendor proposals before comparing vendors."
              ctaLabel="Upload Proposals"
              onCta={onNavigateDashboard}
            />
          </div>
        </div>
      </div>
    );
  }

  // STATE B: Proposals exist but Requirements missing
  if (!hasRequirements) {
    return (
      <div className="dashboard-layout">
        <Sidebar {...SIDEBAR_PROPS} />
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Requirement Comparison</h1>
            <p className="dashboard-subtitle">Compare vendor responses against defined procurement requirements.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow="PREREQUISITE REQUIRED"
              title="SET REQUIREMENTS FIRST"
              description="Define the criteria you want to use to evaluate vendors."
              ctaLabel="Set Requirements"
              onCta={onNavigateRequirements}
            />
          </div>
        </div>
      </div>
    );
  }

  // STATE C/D: Session + requirements ready, but comparison matrix not generated yet
  if (matrixRows.length === 0) {
    return (
      <div className="dashboard-layout">
        <Sidebar {...SIDEBAR_PROPS} />
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Requirement Comparison</h1>
            <p className="dashboard-subtitle">Compare vendor responses against defined procurement requirements.</p>
          </header>

          <div style={{ padding: '2rem', maxWidth: '700px' }}>
            {compareError && (
              <div className="error-banner" style={{ marginBottom: '1rem' }}>
                {compareError}
                {isSessionExpired && onNavigateDashboard && (
                  <div style={{ marginTop: '0.75rem' }}>
                    <button type="button" className="btn-primary" onClick={onNavigateDashboard}
                      style={{ fontSize: '0.85rem', padding: '0.5rem 1.25rem' }}>
                      Go to Dashboard
                    </button>
                  </div>
                )}
              </div>
            )}

            <div className="main-panel" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
              <div className="font-mono" style={{
                fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em',
                color: '#6A6A60', textTransform: 'uppercase', marginBottom: '0.75rem'
              }}>
                READY TO COMPARE
              </div>
              <h2 className="font-display" style={{ fontSize: '1.5rem', color: '#171717', margin: '0 0 0.75rem 0' }}>
                Your proposals and requirements are ready.
              </h2>
              <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: '0.95rem', color: '#6A6A60', marginBottom: '1.75rem', lineHeight: 1.55 }}>
                Compare vendor proposals against your procurement requirements to see where each proposal meets, misses, or requires review.
              </p>
              <button
                type="button"
                className="btn-primary font-mono"
                disabled={isComparing}
                onClick={handleRunComparison}
                style={{ fontSize: '1rem', padding: '0.9rem 2.5rem' }}
              >
                {isComparing ? (
                  <span>
                    {compareStep === 'analyzing' ? 'Preparing vendor details…' : 'Comparing requirements…'}
                  </span>
                ) : (
                  <>
                    <span>Compare Vendors</span>
                    <span>→</span>
                  </>
                )}
              </button>
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem' }}>
              <button type="button" className="btn-secondary" onClick={onNavigateRequirements}>
                Back to Requirements
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // STATE E: REQUIREMENT COMPARISON MATRIX VIEW
  const FILTER_OPTIONS = ['ALL', 'MEETS', 'PARTIAL', 'FAILS', 'MISSING', 'UNCLEAR', 'CONFLICTING'];

  return (
    <div className="dashboard-layout">
      <Sidebar {...SIDEBAR_PROPS} />
      <div className="dashboard-content">
        {/* Page Header */}
        <header className="dashboard-header-bar">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1 className="dashboard-title font-display">Requirement Comparison</h1>
              <p className="dashboard-subtitle">
                Detailed criterion-by-criterion matrix comparing vendor proposals against your defined procurement requirements.
              </p>
            </div>
            {onNavigateRanking && (
              <button type="button" className="btn-primary font-mono" onClick={onNavigateRanking} style={{ fontSize: '0.85rem' }}>
                <span>View Vendor Ranking</span>
                <span>→</span>
              </button>
            )}
          </div>
        </header>

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '2rem 1.5rem', maxWidth: '1240px', minWidth: 0 }}>
          {/* Main Workspace Column */}
          <div className="main-workspace-col" style={{ gap: '1.5rem', minWidth: 0, overflow: 'hidden' }}>

            {/* Vendor Summary Cards Strip */}
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.max(vendors.length, 1)}, 1fr)`, gap: '1rem' }}>
              {vendors.map((vName) => {
                const counts = summaryCounts[vName] || {};
                return (
                  <div key={vName} className="main-panel" style={{ padding: '1rem', backgroundColor: '#FFFFFF', minWidth: 0, boxShadow: '3px 3px 0px #171717', border: '2px solid #171717' }}>
                    <span className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#171717', display: 'block', marginBottom: '0.6rem' }}>
                      {cleanVendorName(vName)}
                    </span>
                    <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                      <span className="sample-badge font-mono" style={{ backgroundColor: '#C8D6FF', color: '#171717', fontSize: '0.7rem' }}>
                        MEETS: {counts.MEETS || 0}
                      </span>
                      <span className="sample-badge font-mono" style={{ backgroundColor: '#F4C84A', color: '#171717', fontSize: '0.7rem' }}>
                        PARTIAL: {counts.PARTIAL || 0}
                      </span>
                      <span className="sample-badge font-mono" style={{ backgroundColor: '#EB7096', color: '#FFFFFF', fontSize: '0.7rem' }}>
                        FAILS: {counts.FAILS || 0}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Status Filter Tabs */}
            <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#6A6A60', marginRight: '0.5rem' }}>FILTER STATUS:</span>
              {FILTER_OPTIONS.map((fOpt) => {
                const isActive = activeFilter === fOpt;
                return (
                  <button
                    key={fOpt}
                    type="button"
                    onClick={() => setActiveFilter(fOpt)}
                    className="font-mono"
                    style={{
                      padding: '0.35rem 0.75rem',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      border: '1.5px solid #171717',
                      borderRadius: '3px',
                      cursor: 'pointer',
                      backgroundColor: isActive ? '#171717' : '#FFFFFF',
                      color: isActive ? '#FFFFFF' : '#171717',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {fOpt}
                  </button>
                );
              })}
            </div>

            {/* Comparison Matrix Table with Bounded Horizontal Scroll */}
            <div className="main-panel" style={{ padding: 0, overflow: 'hidden', border: '2px solid #171717', boxShadow: '3px 3px 0px #171717' }}>
              <div style={{ overflowX: 'auto', maxWidth: '100%' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left', minWidth: '700px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#F5F2F0', borderBottom: '2px solid #171717' }}>
                      <th style={{
                        padding: '1rem', fontWeight: 700, color: '#171717', width: '220px', minWidth: '200px',
                        position: 'sticky', left: 0, backgroundColor: '#F5F2F0', zIndex: 2, borderRight: '2px solid #171717'
                      }}>
                        REQUIREMENT
                      </th>
                      {vendors.map((vName) => (
                        <th key={vName} style={{ padding: '1rem', fontWeight: 700, color: '#171717', minWidth: '180px' }}>
                          {cleanVendorName(vName)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRows.length === 0 ? (
                      <tr>
                        <td colSpan={vendors.length + 1} style={{ padding: '2rem', textAlign: 'center', color: '#6A6A60' }}>
                          No requirements matching filter "{activeFilter}".
                        </td>
                      </tr>
                    ) : (
                      filteredRows.map((row, rIdx) => (
                        <tr key={rIdx} style={{ borderBottom: rIdx < filteredRows.length - 1 ? '1.5px solid #171717' : 'none' }}>
                          {/* Requirement Label Sticky Cell */}
                          <td style={{
                            padding: '1rem', fontWeight: 700, color: '#171717',
                            position: 'sticky', left: 0, backgroundColor: '#FFFFFF', zIndex: 1, borderRight: '2px solid #171717'
                          }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                              <span>{row.requirement_label || row.requirement_name || row.category}</span>
                              {row.buyer_target_summary && (
                                <span className="font-mono" style={{ fontSize: '0.7rem', color: '#6A6A60', fontWeight: 400 }}>
                                  Target: {row.buyer_target_summary}
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Vendor Evaluation Cells */}
                          {vendors.map((vName) => {
                            const ev = row.vendor_evaluations?.[vName] || {};
                            const sStyle = getStatusBadgeStyle(ev.status);
                            const hasEvidence = ev.evidence_citations && ev.evidence_citations.length > 0;

                            return (
                              <td
                                key={vName}
                                style={{
                                  padding: '1rem',
                                  verticalAlign: 'top',
                                  backgroundColor: selectedCell === ev ? '#F7F3EA' : 'transparent',
                                  cursor: hasEvidence ? 'pointer' : 'default',
                                  transition: 'background-color 0.15s ease',
                                }}
                                onClick={() => {
                                  if (hasEvidence) setSelectedCell({ ...ev, requirement_label: row.requirement_label, category: row.category });
                                }}
                              >
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', height: '100%' }}>
                                  <div>
                                    <span
                                      className="sample-badge font-mono"
                                      style={{
                                        backgroundColor: sStyle.bg,
                                        color: sStyle.text,
                                        fontSize: '0.7rem',
                                        fontWeight: 700,
                                        display: 'inline-block',
                                      }}
                                    >
                                      {sStyle.label}
                                    </span>
                                  </div>

                                  {/* Vendor Raw / Normalized Wording */}
                                  <div style={{ fontSize: '0.85rem', color: '#171717', lineHeight: '1.4', flex: 1 }}>
                                    {ev.raw_vendor_value ? (
                                      <span>{ev.raw_vendor_value}</span>
                                    ) : ev.explanation ? (
                                      <span>{ev.explanation}</span>
                                    ) : (
                                      <span style={{ color: '#6A6A60', fontStyle: 'italic' }}>No explicit term stated</span>
                                    )}
                                  </div>

                                  {/* Compact Normalization String */}
                                  {ev.normalized_vendor_value && ev.normalized_vendor_value !== ev.raw_vendor_value && (
                                    <div className="font-mono" style={{ fontSize: '0.7rem', color: '#6A6A60', backgroundColor: '#F5F2F0', padding: '0.2rem 0.4rem', borderRadius: '2px' }}>
                                      {ev.raw_vendor_value} → {ev.normalized_vendor_value}
                                    </div>
                                  )}

                                  {/* Evidence Citation Tag */}
                                  {hasEvidence && (
                                    <div style={{ marginTop: 'auto', paddingTop: '0.3rem' }}>
                                      <span className="font-mono" style={{ fontSize: '0.68rem', color: '#7897FF', fontWeight: 700, textDecoration: 'underline' }}>
                                        Evidence · Page {ev.evidence_citations[0]?.start_page || 1} →
                                      </span>
                                    </div>
                                  )}
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Bottom Action Nav Footer */}
            <div className="action-nav-footer" style={{ marginTop: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button type="button" className="btn-secondary font-mono" onClick={onNavigateRequirements}>
                Back to Requirements
              </button>
              {onNavigateRisks && (
                <button type="button" className="btn-secondary font-mono" onClick={onNavigateRisks}>
                  Review Risks
                </button>
              )}
              {onNavigateRanking && (
                <button type="button" className="btn-primary font-mono" onClick={onNavigateRanking}>
                  <span>View Vendor Ranking</span>
                  <span>→</span>
                </button>
              )}
            </div>

          </div>

          {/* Right SaaS Session Panel */}
          <SaasSessionPanel
            proposalsCount={vendors.length}
            definedVendorsCount={vendors.length}
            isProcessed={true}
            requirements={requirements || { total: matrixRows.length }}
            hasComparison={true}
            onNavigate={(path) => {
              if (path === '/dashboard/requirements' && onNavigateRequirements) onNavigateRequirements();
              else if (path === '/dashboard/risks' && onNavigateRisks) onNavigateRisks();
              else if (path === '/dashboard/ranking' && onNavigateRanking) onNavigateRanking();
              else if (path === '/dashboard/recommendation' && onNavigateRecommendation) onNavigateRecommendation();
              else if (onNavigateDashboard) onNavigateDashboard();
            }}
          />
        </div>
      </div>

      {/* ── Evidence Citation Drawer Modal ── */}
      {selectedCell && (
        <div className="drawer-overlay" onClick={() => setSelectedCell(null)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '580px' }}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge font-mono">PROPOSAL EVIDENCE</span>
                <h2 className="drawer-title font-display" style={{ marginTop: '0.2rem' }}>
                  {cleanVendorName(selectedCell.vendor_name) || 'Vendor'} Excerpt
                </h2>
              </div>
              <button type="button" className="btn-remove font-mono" onClick={() => setSelectedCell(null)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body">
              {/* Requirement Context Banner */}
              {selectedCell.requirement_label && (
                <div style={{ backgroundColor: '#F5F2F0', border: '1.5px solid #171717', borderRadius: '3px', padding: '0.6rem 0.85rem', marginBottom: '1rem' }}>
                  <span className="font-mono" style={{ fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.05em', color: '#6A6A60', textTransform: 'uppercase', display: 'block' }}>
                    EVALUATED REQUIREMENT
                  </span>
                  <strong style={{ fontSize: '0.9rem', color: '#171717' }}>
                    {selectedCell.category ? `${selectedCell.category}: ` : ''}{selectedCell.requirement_label}
                  </strong>
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="sample-badge font-mono" style={{ backgroundColor: getStatusBadgeStyle(selectedCell.status).bg, color: getStatusBadgeStyle(selectedCell.status).text }}>
                  {selectedCell.status}
                </span>
                <span className="font-mono" style={{ fontSize: '0.8rem', color: '#171717', backgroundColor: '#FFFFFF', border: '1.5px solid #171717', padding: '0.25rem 0.6rem', borderRadius: '3px' }}>
                  Raw Term: {selectedCell.raw_vendor_value || 'None'}
                </span>
              </div>

              {selectedCell.evidence_citations.map((cit, cIdx) => (
                <div key={cIdx} className="citation-item-box" style={{ marginBottom: '1rem', backgroundColor: '#FFFFFF', padding: '1rem', borderRadius: '3px', border: '1.5px solid #171717', boxShadow: '2px 2px 0px #171717' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', alignItems: 'center' }}>
                    <strong className="font-mono" style={{ fontSize: '0.85rem', color: '#171717' }}>{cit.source_filename}</strong>
                    <span className="sample-badge font-mono" style={{ fontSize: '0.7rem', backgroundColor: '#C8D6FF', color: '#171717' }}>
                      Evidence · Page {cit.start_page}
                    </span>
                  </div>
                  <div className="evidence-excerpt-box" style={{ marginTop: '0.5rem', backgroundColor: '#F5F2F0', padding: '0.85rem', borderRadius: '3px', border: '1px solid #171717' }}>
                    <p className="evidence-excerpt-text font-mono" style={{ fontSize: '0.825rem', lineHeight: 1.55, margin: 0, color: '#171717' }}>
                      "{renderHighlightedExcerpt(cit.excerpt_text, selectedCell.raw_vendor_value)}"
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
