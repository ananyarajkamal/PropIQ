import React, { useState } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';
import FeatureGate from '../components/FeatureGate';

export default function RisksPage({
  sessionId,
  risksData,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateVendorDetails,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
  onRunRiskAnalysis,
}) {
  const riskFindings = risksData?.risk_findings || [];
  const contradictionFindings = risksData?.contradiction_findings || [];

  // Filter States
  const [selectedVendor, setSelectedVendor] = useState('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedType, setSelectedType] = useState('ALL'); // 'ALL', 'RISK', 'CONTRADICTION'

  // Detail Drawer Modal State
  const [selectedItem, setSelectedItem] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  async function handleTriggerRiskAnalysis() {
    if (onRunRiskAnalysis) {
      setIsAnalyzing(true);
      try {
        await onRunRiskAnalysis();
      } finally {
        setIsAnalyzing(false);
      }
    } else if (onNavigateRequirements) {
      onNavigateRequirements();
    }
  }

  // Extract unique vendor names
  const allVendors = Array.from(
    new Set([
      ...riskFindings.map((r) => r.vendor_name),
      ...contradictionFindings.map((c) => c.vendor_name),
    ])
  ).filter(Boolean);

  // Extract unique category names
  const allCategories = Array.from(
    new Set([
      ...riskFindings.map((r) => r.category),
      ...contradictionFindings.map((c) => c.category),
    ])
  ).filter(Boolean);

  // Filter risk findings
  const filteredRisks = riskFindings.filter((item) => {
    if (selectedType === 'CONTRADICTION') return false;
    if (selectedVendor !== 'ALL' && item.vendor_name !== selectedVendor) return false;
    if (selectedSeverity !== 'ALL' && item.severity !== selectedSeverity) return false;
    if (selectedCategory !== 'ALL' && item.category !== selectedCategory) return false;
    return true;
  });

  // Filter contradiction findings
  const filteredContradictions = contradictionFindings.filter((item) => {
    if (selectedType === 'RISK') return false;
    if (selectedVendor !== 'ALL' && item.vendor_name !== selectedVendor) return false;
    if (selectedSeverity !== 'ALL' && item.severity !== selectedSeverity) return false;
    if (selectedCategory !== 'ALL' && item.category !== selectedCategory) return false;
    return true;
  });

  function getSeverityBadgeStyle(severity) {
    switch (severity) {
      case 'CRITICAL':
        return { bg: '#EB7096', label: 'CRITICAL', text: '#FFFFFF' };
      case 'HIGH':
        return { bg: '#EBBAC2', label: 'HIGH', text: '#171717' };
      case 'MEDIUM':
        return { bg: '#EDB240', label: 'MEDIUM', text: '#171717' };
      case 'LOW':
        return { bg: '#B9B5EA', label: 'LOW', text: '#171717' };
      default:
        return { bg: '#F5F2F0', label: severity, text: '#171717' };
    }
  }

  function formatRequirementTag(reqId) {
    switch (reqId) {
      case 'REQ_RENEWAL':
        return 'Renewal Requirement';
      case 'REQ_LIABILITY':
        return 'Liability Requirement';
      case 'REQ_TERMINATION':
        return 'Termination Requirement';
      case 'REQ_SUPPORT':
        return 'Support Requirement';
      default:
        return reqId;
    }
  }

  if (!sessionId) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="risks"
          sessionReady={false}
          onNavigateHome={onNavigateHome}
          onNavigateDashboard={onNavigateDashboard}
          onNavigateRequirements={onNavigateRequirements}
          onNavigateComparison={onNavigateComparison}
          onNavigateRisks={onNavigateRisks}
          onNavigateClarifications={onNavigateClarifications}
          onNavigateRanking={onNavigateRanking}
          onNavigateRecommendation={onNavigateRecommendation}
        />
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Risks & Contradictions</h1>
            <p className="dashboard-subtitle">Review potentially unfavorable terms and inconsistencies found across vendor proposals.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow="PREREQUISITE REQUIRED"
              title="UPLOAD PROPOSALS FIRST"
              description="PropIQ needs proposal content to identify risky clauses, conflicting terms and contractual inconsistencies."
              ctaLabel="Upload Proposals"
              onCta={onNavigateDashboard}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      {/* Left Sidebar */}
      <Sidebar
        activeTab="risks"
        sessionReady={!!sessionId}
        onNavigateHome={onNavigateHome}
        onNavigateDashboard={onNavigateDashboard}
        onNavigateRequirements={onNavigateRequirements}
        onNavigateComparison={onNavigateComparison}
        onNavigateRisks={onNavigateRisks}
        onNavigateClarifications={onNavigateClarifications}
        onNavigateRanking={onNavigateRanking}
        onNavigateRecommendation={onNavigateRecommendation}
      />

      {/* Main Content Area */}
      <div className="dashboard-content">
        <header className="dashboard-header-bar">
          <h1 className="dashboard-title font-display">Risks & Contradictions</h1>
          <p className="dashboard-subtitle">
            Review potentially unfavorable terms and inconsistencies found across vendor proposals.
          </p>
        </header>

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '2rem 1.5rem', maxWidth: '1180px' }}>
          {/* Main Workspace Column */}
          <div className="main-workspace-col">
            {/* Legal Decision-Support Disclaimer Microcopy Banner */}
            <div className="privacy-microcopy" style={{ marginTop: '0', borderTop: 'none', paddingWait: '0', marginBottom: '1.5rem', backgroundColor: '#F5F2F0', border: '2px solid #171717', borderRadius: '2px', padding: '0.75rem 1rem' }}>
              <strong>Legal Disclaimer:</strong> PropIQ highlights potential procurement and contractual concerns based on proposal evidence. Findings should be reviewed by your procurement or legal team.
            </div>

            {/* Workflow state if risk analysis has not been executed yet */}
            {!risksData ? (
              <div
                className={`main-panel ${isAnalyzing ? 'animate-pulse' : ''}`}
                style={{
                  textAlign: 'center',
                  padding: '2.5rem 1.5rem',
                  backgroundColor: isAnalyzing ? '#F7F3EA' : '#FFFFFF',
                  border: '2px solid #171717',
                  boxShadow: '4px 4px 0px #171717',
                }}
              >
                <span
                  className="sample-badge font-mono"
                  style={{
                    backgroundColor: isAnalyzing ? '#EB7096' : '#EDB240',
                    color: isAnalyzing ? '#FFFFFF' : '#171717',
                    marginBottom: '0.65rem',
                    display: 'inline-block',
                  }}
                >
                  {isAnalyzing ? 'ANALYZING RISKS...' : 'READY FOR ANALYSIS'}
                </span>
                <h3 className="panel-title font-display" style={{ fontSize: '1.25rem', marginTop: '0.4rem' }}>
                  {isAnalyzing ? 'ANALYZING CONTRACTUAL RISKS & CONTRADICTIONS...' : 'READY FOR RISK ANALYSIS'}
                </h3>
                <p className="panel-desc" style={{ marginTop: '0.4rem', maxWidth: '520px', marginInline: 'auto' }}>
                  {isAnalyzing
                    ? 'PropIQ is scanning vendor proposal evidence for risky liability terms, hidden renewal clauses, and intra-vendor conflicting statements...'
                    : 'Your proposals are ready to be checked for contractual risks and conflicting terms.'}
                </p>
                <div style={{ marginTop: '1.25rem' }}>
                  <button
                    type="button"
                    className="btn-primary font-mono"
                    onClick={handleTriggerRiskAnalysis}
                    disabled={isAnalyzing}
                    style={{
                      opacity: isAnalyzing ? 0.75 : 1,
                      cursor: isAnalyzing ? 'not-allowed' : 'pointer',
                    }}
                  >
                    <span>{isAnalyzing ? 'Analyzing Contract Risks...' : 'Analyze Contract Risks'}</span>
                    <span style={{ marginLeft: '0.4rem', display: 'inline-block' }}>
                      {isAnalyzing ? '⌛' : '→'}
                    </span>
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Summary Counters */}
                <div className="summary-cards-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.85rem', marginBottom: '1.5rem' }}>
                  <div className="summary-card bg-pastel-rose" style={{ color: '#FFFFFF' }}>
                    <span className="summary-card-title font-mono" style={{ color: '#FFFFFF' }}>HIGH PRIORITY</span>
                    <span className="summary-card-value font-mono" style={{ color: '#FFFFFF' }}>{risksData?.high_priority_count || 0}</span>
                    <span className="summary-card-sub" style={{ color: '#FFFFFF' }}>High / Critical</span>
                  </div>

                  <div className="summary-card bg-pastel-yellow">
                    <span className="summary-card-title font-mono">MEDIUM PRIORITY</span>
                    <span className="summary-card-value font-mono">{risksData?.medium_priority_count || 0}</span>
                    <span className="summary-card-sub">Commercial review</span>
                  </div>

                  <div className="summary-card bg-pastel-peach">
                    <span className="summary-card-title font-mono">NEEDS CLARIFICATION</span>
                    <span className="summary-card-value font-mono">{risksData?.needs_clarification_count || 0}</span>
                    <span className="summary-card-sub">Informational</span>
                  </div>

                  <div className="summary-card bg-pastel-berry" style={{ color: '#FFFFFF' }}>
                    <span className="summary-card-title font-mono" style={{ color: '#FFFFFF' }}>CONTRADICTIONS</span>
                    <span className="summary-card-value font-mono" style={{ color: '#FFFFFF' }}>{risksData?.contradictions_count || 0}</span>
                    <span className="summary-card-sub" style={{ color: '#FFFFFF' }}>Intra-vendor</span>
                  </div>
                </div>

                {/* Filters Bar */}
                <div className="main-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <div className="retrieval-filter-group" style={{ margin: 0 }}>
                      <label htmlFor="risk-vendor-filter" className="vendor-input-label">Vendor:</label>
                      <select
                        id="risk-vendor-filter"
                        className="vendor-input"
                        value={selectedVendor}
                        onChange={(e) => setSelectedVendor(e.target.value)}
                      >
                        <option value="ALL">All Vendors</option>
                        {allVendors.map((v, i) => (
                          <option key={i} value={v}>{v}</option>
                        ))}
                      </select>
                    </div>

                    <div className="retrieval-filter-group" style={{ margin: 0 }}>
                      <label htmlFor="risk-severity-filter" className="vendor-input-label">Severity:</label>
                      <select
                        id="risk-severity-filter"
                        className="vendor-input"
                        value={selectedSeverity}
                        onChange={(e) => setSelectedSeverity(e.target.value)}
                      >
                        <option value="ALL">All Severities</option>
                        <option value="CRITICAL">CRITICAL</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>
                    </div>

                    <div className="retrieval-filter-group" style={{ margin: 0 }}>
                      <label htmlFor="risk-category-filter" className="vendor-input-label">Category:</label>
                      <select
                        id="risk-category-filter"
                        className="vendor-input"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                      >
                        <option value="ALL">All Categories</option>
                        {allCategories.map((c, i) => (
                          <option key={i} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    <div className="retrieval-filter-group" style={{ margin: 0 }}>
                      <label htmlFor="risk-type-filter" className="vendor-input-label">Finding Type:</label>
                      <select
                        id="risk-type-filter"
                        className="vendor-input"
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                      >
                        <option value="ALL">All Types</option>
                        <option value="RISK">Contract Risks Only</option>
                        <option value="CONTRADICTION">Contradictions Only</option>
                      </select>
                    </div>

                    {(selectedVendor !== 'ALL' || selectedSeverity !== 'ALL' || selectedCategory !== 'ALL' || selectedType !== 'ALL') && (
                      <button
                        type="button"
                        className="btn-secondary font-mono"
                        onClick={() => {
                          setSelectedVendor('ALL');
                          setSelectedSeverity('ALL');
                          setSelectedCategory('ALL');
                          setSelectedType('ALL');
                        }}
                        style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                </div>

                {/* Findings List Area */}
                {filteredRisks.length === 0 && filteredContradictions.length === 0 ? (
                  <div className="main-panel" style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
                    <h3 className="panel-title font-display" style={{ fontSize: '1.1rem' }}>
                      No material proposal risks were identified from the available evidence.
                    </h3>
                    <p className="panel-desc" style={{ marginTop: '0.4rem' }}>
                      No contractual risks or intra-vendor contradictions matching your selected filters were found in proposal evidence.
                    </p>
                    <p className="privacy-microcopy">This does not replace procurement or legal review.</p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Contradiction Cards */}
                    {filteredContradictions.map((ctr, cIdx) => {
                      const badge = getSeverityBadgeStyle(ctr.severity);
                      return (
                        <div key={`ctr_${cIdx}`} className="main-panel" style={{ borderLeft: '4px solid #171717', backgroundColor: '#F5F2F0' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                              <span className="sample-badge font-mono" style={{ backgroundColor: '#6C5CE7', color: '#FFFFFF' }}>POTENTIAL CONTRADICTION</span>
                              <strong className="font-mono" style={{ fontSize: '0.9rem', color: '#171717' }}>{ctr.vendor_name}</strong>
                              <span className="sample-badge font-mono">{ctr.category}</span>
                            </div>
                            <span className="sample-badge font-mono" style={{ backgroundColor: badge.bg, color: badge.text }}>
                              {badge.label}
                            </span>
                          </div>

                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '0.85rem' }}>
                            <div style={{ backgroundColor: '#FFFFFF', border: '1.5px solid #171717', padding: '0.75rem', borderRadius: '2px' }}>
                              <strong className="font-mono" style={{ fontSize: '0.75rem', color: '#171717', display: 'block', marginBottom: '0.25rem' }}>STATEMENT A ({ctr.context_a || 'Proposal'})</strong>
                              <p style={{ fontSize: '0.85rem', color: '#171717' }}>"{ctr.statement_a}"</p>
                            </div>

                            <div style={{ backgroundColor: '#FFFFFF', border: '1.5px solid #171717', padding: '0.75rem', borderRadius: '2px' }}>
                              <strong className="font-mono" style={{ fontSize: '0.75rem', color: '#171717', display: 'block', marginBottom: '0.25rem' }}>STATEMENT B ({ctr.context_b || 'Proposal'})</strong>
                              <p style={{ fontSize: '0.85rem', color: '#171717' }}>"{ctr.statement_b}"</p>
                            </div>
                          </div>

                          <p className="cell-explanation-text" style={{ fontSize: '0.85rem', marginBottom: '0.75rem' }}>
                            <strong>Reason:</strong> {ctr.reason}
                          </p>

                          <button
                            type="button"
                            className="btn-secondary font-mono"
                            onClick={() => setSelectedItem({ type: 'CONTRADICTION', data: ctr })}
                            style={{ fontSize: '0.75rem' }}
                          >
                            View Dual Evidence Citations
                          </button>
                        </div>
                      );
                    })}

                    {/* Contract Risk Cards */}
                    {filteredRisks.map((risk, rIdx) => {
                      const badge = getSeverityBadgeStyle(risk.severity);
                      return (
                        <div key={`rsk_${rIdx}`} className="main-panel" style={{ backgroundColor: '#FFFFFF' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.65rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                              <span className="sample-badge font-mono" style={{ backgroundColor: '#EDB240', color: '#171717' }}>CONTRACT RISK</span>
                              <strong className="font-mono" style={{ fontSize: '0.9rem', color: '#171717' }}>{risk.vendor_name}</strong>
                              <span className="sample-badge font-mono">{risk.category}</span>
                              {risk.related_requirement_ids && risk.related_requirement_ids.length > 0 && (
                                <span className="normalized-indicator-badge font-mono" style={{ margin: 0 }}>
                                  {formatRequirementTag(risk.related_requirement_ids[0])}
                                </span>
                              )}
                            </div>
                            <span className="sample-badge font-mono" style={{ backgroundColor: badge.bg, color: badge.text }}>
                              {badge.label}
                            </span>
                          </div>

                          <h3 className="panel-title font-display" style={{ fontSize: '1.05rem', marginBottom: '0.35rem' }}>
                            {risk.title}
                          </h3>
                          <p className="panel-desc" style={{ fontSize: '0.875rem', marginBottom: '0.75rem', color: '#171717' }}>
                            {risk.summary}
                          </p>

                          <div style={{ backgroundColor: '#F5F2F0', border: '1.5px solid #171717', padding: '0.65rem 0.85rem', borderRadius: '2px', marginBottom: '0.75rem', fontSize: '0.825rem' }}>
                            <div style={{ marginBottom: '0.2rem' }}>
                              <strong>Procurement Impact:</strong> {risk.procurement_impact}
                            </div>
                            <div>
                              <strong>Review Guidance:</strong> {risk.review_reason}
                            </div>
                          </div>

                          <button
                            type="button"
                            className="btn-secondary font-mono"
                            onClick={() => setSelectedItem({ type: 'RISK', data: risk })}
                            style={{ fontSize: '0.75rem' }}
                          >
                            View {risk.evidence_citations.length} Evidence Citation{risk.evidence_citations.length > 1 ? 's' : ''}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Bottom Action Footer */}
                <div className="action-nav-footer" style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <button type="button" className="btn-secondary font-mono" onClick={onNavigateComparison}>
                    ← Back to Comparison
                  </button>
                  {onNavigateClarifications && (
                    <button type="button" className="btn-primary font-mono" onClick={onNavigateClarifications}>
                      <span>Review Vendor Clarifications</span>
                      <span>→</span>
                    </button>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Right SaaS Session Panel */}
          <SaasSessionPanel
            proposalsCount={allVendors.length}
            definedVendorsCount={allVendors.length}
            isProcessed={true}
            hasRisks={true}
            hasClarifications={true}
          />
        </div>
      </div>

      {/* Evidence Detail Drawer Modal */}
      {selectedItem && (
        <div className="drawer-overlay" onClick={() => setSelectedItem(null)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge font-mono">{selectedItem.data.category}</span>
                <h2 className="drawer-title font-display" style={{ marginTop: '0.2rem' }}>
                  {selectedItem.data.vendor_name}
                </h2>
              </div>
              <button type="button" className="btn-remove font-mono" onClick={() => setSelectedItem(null)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body">
              {selectedItem.type === 'RISK' ? (
                <>
                  <div className="drawer-section">
                    <span className="summary-card-title font-mono">RISK TITLE</span>
                    <h3 style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>{selectedItem.data.title}</h3>
                  </div>

                  <div className="drawer-section">
                    <span className="summary-card-title font-mono">SUMMARY & IMPACT</span>
                    <p className="fact-summary-text" style={{ marginTop: '0.35rem' }}>
                      {selectedItem.data.summary}
                    </p>
                    <div className="evidence-chunk-meta font-mono" style={{ marginTop: '0.5rem' }}>
                      Impact: {selectedItem.data.procurement_impact}
                    </div>
                  </div>

                  <div className="drawer-section">
                    <span className="summary-card-title font-mono">AUTHENTICATED EVIDENCE CITATIONS</span>
                    <div className="evidence-citations-drawer" style={{ marginTop: '0.5rem' }}>
                      {selectedItem.data.evidence_citations.map((cit, idx) => (
                        <div key={idx} className="citation-item-box" style={{ border: '1.5px solid #171717', padding: '0.75rem', borderRadius: '2px', marginBottom: '0.5rem' }}>
                          <div className="citation-meta-header" style={{ marginBottom: '0.35rem' }}>
                            <span className="sample-badge font-mono">{cit.evidence_id}</span>
                            <strong className="evidence-vendor-name font-mono">{cit.vendor_name}</strong>
                            <span className="evidence-citation font-mono" style={{ fontSize: '0.75rem' }}>
                              {cit.source_filename} — Page {cit.start_page === cit.end_page ? cit.start_page : `${cit.start_page}-${cit.end_page}`}
                            </span>
                          </div>
                          <div className="evidence-chunk-meta font-mono">Chunk ID: <code>{cit.chunk_id}</code></div>
                          <div className="evidence-excerpt-box" style={{ marginTop: '0.4rem' }}>
                            <p className="evidence-excerpt-text font-mono" style={{ fontSize: '0.8rem' }}>"{cit.excerpt_text}"</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="drawer-section">
                    <span className="summary-card-title font-mono">STATEMENT A EVIDENCE</span>
                    <div className="evidence-citations-drawer" style={{ marginTop: '0.5rem' }}>
                      {selectedItem.data.evidence_a.map((cit, idx) => (
                        <div key={idx} className="citation-item-box" style={{ border: '1.5px solid #171717', padding: '0.75rem', borderRadius: '2px', marginBottom: '0.5rem' }}>
                          <div className="citation-meta-header" style={{ marginBottom: '0.35rem' }}>
                            <span className="sample-badge font-mono">{cit.evidence_id}</span>
                            <strong className="evidence-vendor-name font-mono">{cit.vendor_name}</strong>
                            <span className="evidence-citation font-mono" style={{ fontSize: '0.75rem' }}>
                              {cit.source_filename} — Page {cit.start_page === cit.end_page ? cit.start_page : `${cit.start_page}-${cit.end_page}`}
                            </span>
                          </div>
                          <div className="evidence-excerpt-box" style={{ marginTop: '0.4rem' }}>
                            <p className="evidence-excerpt-text font-mono" style={{ fontSize: '0.8rem' }}>"{cit.excerpt_text}"</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="drawer-section">
                    <span className="summary-card-title font-mono">STATEMENT B EVIDENCE</span>
                    <div className="evidence-citations-drawer" style={{ marginTop: '0.5rem' }}>
                      {selectedItem.data.evidence_b.map((cit, idx) => (
                        <div key={idx} className="citation-item-box" style={{ border: '1.5px solid #171717', padding: '0.75rem', borderRadius: '2px', marginBottom: '0.5rem' }}>
                          <div className="citation-meta-header" style={{ marginBottom: '0.35rem' }}>
                            <span className="sample-badge font-mono">{cit.evidence_id}</span>
                            <strong className="evidence-vendor-name font-mono">{cit.vendor_name}</strong>
                            <span className="evidence-citation font-mono" style={{ fontSize: '0.75rem' }}>
                              {cit.source_filename} — Page {cit.start_page === cit.end_page ? cit.start_page : `${cit.start_page}-${cit.end_page}`}
                            </span>
                          </div>
                          <div className="evidence-excerpt-box" style={{ marginTop: '0.4rem' }}>
                            <p className="evidence-excerpt-text font-mono" style={{ fontSize: '0.8rem' }}>"{cit.excerpt_text}"</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="drawer-section">
                    <span className="summary-card-title font-mono">INCOMPATIBILITY REASON</span>
                    <p className="fact-summary-text" style={{ marginTop: '0.35rem' }}>
                      {selectedItem.data.reason}
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
