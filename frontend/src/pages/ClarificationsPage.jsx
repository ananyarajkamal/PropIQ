import React, { useState } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';
import FeatureGate from '../components/FeatureGate';

export default function ClarificationsPage({
  sessionId,
  hasRequirements = false,
  clarificationsData,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateVendorDetails,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
  onRunClarifications,
}) {
  const questions = clarificationsData?.questions || [];
  const [selectedVendor, setSelectedVendor] = useState('ALL');
  const [selectedPriority, setSelectedPriority] = useState('ALL');
  const [selectedReason, setSelectedReason] = useState('ALL');
  const [copiedId, setCopiedId] = useState(null);
  const [copiedVendor, setCopiedVendor] = useState(null);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Extract unique vendors and reasons
  const allVendors = Array.from(new Set(questions.map((q) => q.vendor_name))).filter(Boolean);
  const allReasons = Array.from(new Set(questions.map((q) => q.reason))).filter(Boolean);

  // Filter questions
  const filteredQuestions = questions.filter((q) => {
    if (selectedVendor !== 'ALL' && q.vendor_name !== selectedVendor) return false;
    if (selectedPriority !== 'ALL' && q.priority !== selectedPriority) return false;
    if (selectedReason !== 'ALL' && q.reason !== selectedReason) return false;
    return true;
  });

  // Group questions by vendor
  const questionsByVendor = filteredQuestions.reduce((acc, q) => {
    if (!acc[q.vendor_name]) acc[q.vendor_name] = [];
    acc[q.vendor_name].push(q);
    return acc;
  }, {});

  function getPriorityBadgeStyle(priority) {
    switch (priority) {
      case 'HIGH':
        return { bg: '#EB7096', label: 'HIGH', text: '#FFFFFF' };
      case 'MEDIUM':
        return { bg: '#EDB240', label: 'MEDIUM', text: '#171717' };
      case 'LOW':
        return { bg: '#B9B5EA', label: 'LOW', text: '#171717' };
      default:
        return { bg: '#F5F2F0', label: priority, text: '#171717' };
    }
  }

  async function handleTriggerClarificationAnalysis() {
    if (onRunClarifications) {
      setIsAnalyzing(true);
      try {
        await onRunClarifications();
      } finally {
        setIsAnalyzing(false);
      }
    }
  }

  function handleCopyQuestion(q) {
    const textToCopy = q.question;
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        setCopiedId(q.clarification_id);
        setTimeout(() => setCopiedId(null), 2000);
      }).catch((err) => {
        console.error('Clipboard copy failed:', err);
      });
    }
  }

  function handleCopyAllVendor(vname, vQuestions) {
    let textToCopy = `${vname} Clarification Questions\n\n`;
    vQuestions.forEach((q, idx) => {
      textToCopy += `${idx + 1}. [${q.priority}] ${q.question}\n`;
      if (q.context) textToCopy += `   Context: ${q.context}\n`;
      textToCopy += `\n`;
    });

    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        setCopiedVendor(vname);
        setTimeout(() => setCopiedVendor(null), 2000);
      }).catch((err) => {
        console.error('Clipboard copy all failed:', err);
      });
    }
  }

  function handleExportTxt() {
    let content = `PropIQ Vendor Clarification Questions\n======================================\n\n`;
    Object.keys(questionsByVendor).forEach((vname) => {
      const vQs = questionsByVendor[vname];
      content += `VENDOR: ${vname.toUpperCase()}\n`;
      content += `-`.repeat(40) + `\n`;
      vQs.forEach((q, idx) => {
        const reqStr = q.requirement_label ? ` (${q.requirement_label})` : '';
        content += `${idx + 1}. [${q.priority}]${reqStr} ${q.question}\n`;
        if (q.context) content += `   Context: ${q.context}\n`;
        content += `\n`;
      });
      content += `\n`;
    });

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `PropIQ_Vendor_Clarifications.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  if (!sessionId) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="clarifications"
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
            <h1 className="dashboard-title font-display">Clarifications</h1>
            <p className="dashboard-subtitle">Review questions and gaps identified across vendor proposals.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow="PREREQUISITE REQUIRED"
              title="UPLOAD PROPOSALS FIRST"
              description="PropIQ needs proposal content before it can identify missing, unclear, or conflicting information."
              ctaLabel="Upload Proposals"
              onCta={onNavigateDashboard}
            />
          </div>
        </div>
      </div>
    );
  }

  if (!hasRequirements) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="clarifications"
          sessionReady={true}
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
            <h1 className="dashboard-title font-display">Vendor Clarifications</h1>
            <p className="dashboard-subtitle">Review questions and gaps identified across vendor proposals.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow="PREREQUISITE REQUIRED"
              title="DEFINE REQUIREMENTS FIRST"
              description="Define commercial, technical, and SLA requirement criteria before running clarification analysis."
              ctaLabel="Define Requirements"
              onCta={onNavigateRequirements}
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
        activeTab="clarifications"
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1 className="dashboard-title font-display">Vendor Clarifications</h1>
              <p className="dashboard-subtitle">
                Review unanswered questions and information gaps before making a procurement decision.
              </p>
            </div>
            {questions.length > 0 && (
              <button type="button" className="btn-secondary font-mono" onClick={handleExportTxt} style={{ fontSize: '0.85rem' }}>
                Export Questions (.txt)
              </button>
            )}
          </div>
        </header>

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '2rem 1.5rem', maxWidth: '1180px' }}>
          {/* Main Workspace Column */}
          <div className="main-workspace-col">
            {/* Disclaimer Microcopy Banner */}
            <div className="privacy-microcopy" style={{ marginTop: '0', borderTop: 'none', paddingWait: '0', marginBottom: '1.5rem', backgroundColor: '#F5F2F0', border: '2px solid #171717', borderRadius: '2px', padding: '0.75rem 1rem' }}>
              <strong>Notice:</strong> Clarification questions require human procurement review before being sent to vendors. PropIQ does not send automatic emails.
            </div>

            {!clarificationsData ? (
              <div className="main-panel" style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
                <span className="sample-badge font-mono" style={{ backgroundColor: '#B9B5EA', color: '#171717', marginBottom: '0.5rem', display: 'inline-block' }}>
                  READY FOR ANALYSIS
                </span>
                <h3 className="panel-title font-display" style={{ fontSize: '1.25rem', marginTop: '0.4rem' }}>
                  READY FOR CLARIFICATION ANALYSIS
                </h3>
                <p className="panel-desc" style={{ marginTop: '0.4rem', maxWidth: '520px', marginInline: 'auto' }}>
                  Your proposals are ready to be checked for missing, unclear, and conflicting information.
                </p>
                <div style={{ marginTop: '1.25rem' }}>
                  <button
                    type="button"
                    className="btn-primary font-mono"
                    onClick={handleTriggerClarificationAnalysis}
                    disabled={isAnalyzing}
                  >
                    <span>{isAnalyzing ? 'Analyzing Clarifications...' : 'Generate Clarification Questions'}</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Summary Counters */}
                <div className="summary-cards-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.85rem', marginBottom: '1.5rem' }}>
                  <div className="summary-card bg-pastel-yellow">
                    <span className="summary-card-title font-mono">OPEN QUESTIONS</span>
                    <span className="summary-card-value font-mono">{clarificationsData?.total_questions || 0}</span>
                    <span className="summary-card-sub">Total Gaps</span>
                  </div>

                  <div className="summary-card bg-pastel-peach">
                    <span className="summary-card-title font-mono">HIGH PRIORITY</span>
                    <span className="summary-card-value font-mono">{clarificationsData?.high_priority_count || 0}</span>
                    <span className="summary-card-sub">Critical Gaps</span>
                  </div>

                  <div className="summary-card bg-pastel-sage">
                    <span className="summary-card-title font-mono">VENDORS</span>
                    <span className="summary-card-value font-mono">{allVendors.length}</span>
                    <span className="summary-card-sub">Analyzed</span>
                  </div>

                  <div className="summary-card bg-pastel-berry" style={{ color: '#FFFFFF' }}>
                    <span className="summary-card-title font-mono" style={{ color: '#FFFFFF' }}>CONFLICTING DETAILS</span>
                    <span className="summary-card-value font-mono" style={{ color: '#FFFFFF' }}>{clarificationsData?.conflicting_details_count || 0}</span>
                    <span className="summary-card-sub" style={{ color: '#FFFFFF' }}>Inconsistencies</span>
                  </div>
                </div>

                {/* Filters Bar */}
                <div className="main-panel" style={{ padding: '1rem 1.25rem', marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                    <div className="retrieval-filter-group" style={{ margin: 0 }}>
                      <label htmlFor="clrf-vendor-filter" className="vendor-input-label">Vendor:</label>
                      <select
                        id="clrf-vendor-filter"
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
                      <label htmlFor="clrf-priority-filter" className="vendor-input-label">Priority:</label>
                      <select
                        id="clrf-priority-filter"
                        className="vendor-input"
                        value={selectedPriority}
                        onChange={(e) => setSelectedPriority(e.target.value)}
                      >
                        <option value="ALL">All Priorities</option>
                        <option value="HIGH">HIGH</option>
                        <option value="MEDIUM">MEDIUM</option>
                        <option value="LOW">LOW</option>
                      </select>
                    </div>

                    <div className="retrieval-filter-group" style={{ margin: 0 }}>
                      <label htmlFor="clrf-reason-filter" className="vendor-input-label">Reason:</label>
                      <select
                        id="clrf-reason-filter"
                        className="vendor-input"
                        value={selectedReason}
                        onChange={(e) => setSelectedReason(e.target.value)}
                      >
                        <option value="ALL">All Reasons</option>
                        {allReasons.map((r, i) => (
                          <option key={i} value={r}>{r}</option>
                        ))}
                      </select>
                    </div>

                    {(selectedVendor !== 'ALL' || selectedPriority !== 'ALL' || selectedReason !== 'ALL') && (
                      <button
                        type="button"
                        className="btn-secondary font-mono"
                        onClick={() => {
                          setSelectedVendor('ALL');
                          setSelectedPriority('ALL');
                          setSelectedReason('ALL');
                        }}
                        style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                </div>

                {/* Questions Grouped by Vendor */}
                {Object.keys(questionsByVendor).length === 0 ? (
                  <div className="main-panel" style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
                    <h3 className="panel-title font-display" style={{ fontSize: '1.1rem' }}>
                      No material clarification questions were required for the evaluated proposals.
                    </h3>
                    <p className="panel-desc" style={{ marginTop: '0.4rem' }}>
                      No unanswered questions or information gaps matching your selected filters were found from proposal evidence and requirements.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                    {Object.keys(questionsByVendor).map((vname, vIdx) => {
                      const vQuestions = questionsByVendor[vname];
                      return (
                        <div key={vIdx} className="vendor-clarification-group">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '2px solid #171717', paddingBottom: '0.5rem' }}>
                            <div>
                              <h2 className="font-mono" style={{ fontSize: '1.15rem', margin: 0, color: '#171717' }}>
                                {vname}
                              </h2>
                              <span className="panel-desc" style={{ fontSize: '0.8rem' }}>
                                {vQuestions.length} open question{vQuestions.length > 1 ? 's' : ''}
                              </span>
                            </div>
                            <button
                              type="button"
                              className="btn-secondary font-mono"
                              onClick={() => handleCopyAllVendor(vname, vQuestions)}
                              style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                            >
                              {copiedVendor === vname ? '✓ Copied All!' : 'Copy All'}
                            </button>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {vQuestions.map((q, qIdx) => {
                              const badge = getPriorityBadgeStyle(q.priority);
                              return (
                                <div key={qIdx} className="main-panel" style={{ backgroundColor: '#FFFFFF', padding: '1.1rem 1.25rem' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.6rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                      <span className="sample-badge font-mono" style={{ backgroundColor: badge.bg, color: badge.text }}>
                                        {badge.label}
                                      </span>
                                      <span className="sample-badge font-mono">{q.reason.replace(/_/g, ' ')}</span>
                                      {q.requirement_label && (
                                        <span className="normalized-indicator-badge font-mono" style={{ margin: 0 }}>
                                          {q.requirement_label}
                                        </span>
                                      )}
                                    </div>
                                    <button
                                      type="button"
                                      className="btn-secondary font-mono"
                                      onClick={() => handleCopyQuestion(q)}
                                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.55rem' }}
                                    >
                                      {copiedId === q.clarification_id ? '✓ Copied' : 'Copy Question'}
                                    </button>
                                  </div>

                                  <p style={{ fontSize: '0.95rem', fontWeight: 600, color: '#171717', lineHeight: '1.4', marginBottom: '0.5rem' }}>
                                    "{q.question}"
                                  </p>

                                  {q.context && (
                                    <p className="cell-explanation-text" style={{ fontSize: '0.825rem', color: '#171717', marginBottom: '0.65rem' }}>
                                      <strong>Context:</strong> {q.context}
                                    </p>
                                  )}

                                  {q.evidence_citations && q.evidence_citations.length > 0 ? (
                                    <button
                                      type="button"
                                      className="btn-secondary font-mono"
                                      onClick={() => setSelectedQuestion(q)}
                                      style={{ fontSize: '0.75rem' }}
                                    >
                                      View Evidence Citation ({q.evidence_citations[0].source_filename} — Page {q.evidence_citations[0].start_page})
                                    </button>
                                  ) : (
                                    <span className="cell-explanation-text font-mono" style={{ fontSize: '0.75rem', color: '#171717' }}>
                                      Source Status: <strong>{q.source_status}</strong> (Linked to procurement requirement)
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Bottom Action Footer */}
                <div className="action-nav-footer" style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                  <button type="button" className="btn-secondary font-mono" onClick={onNavigateRisks}>
                    ← Back to Risks
                  </button>
                  {onNavigateRanking && (
                    <button type="button" className="btn-primary font-mono" onClick={onNavigateRanking}>
                      <span>View Vendor Ranking</span>
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
            hasClarifications={true}
            hasScoring={true}
          />
        </div>
      </div>

      {/* Evidence Detail Drawer Modal */}
      {selectedQuestion && (
        <div className="drawer-overlay" onClick={() => setSelectedQuestion(null)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge font-mono">{selectedQuestion.reason}</span>
                <h2 className="drawer-title font-display" style={{ marginTop: '0.2rem' }}>
                  {selectedQuestion.vendor_name}
                </h2>
              </div>
              <button type="button" className="btn-remove font-mono" onClick={() => setSelectedQuestion(null)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body">
              <div className="drawer-section">
                <span className="summary-card-title font-mono">CLARIFICATION QUESTION</span>
                <h3 style={{ fontSize: '1.05rem', marginTop: '0.25rem', color: '#171717' }}>
                  "{selectedQuestion.question}"
                </h3>
              </div>

              {selectedQuestion.context && (
                <div className="drawer-section">
                  <span className="summary-card-title font-mono">BACKGROUND CONTEXT</span>
                  <p className="fact-summary-text" style={{ marginTop: '0.25rem' }}>
                    {selectedQuestion.context}
                  </p>
                </div>
              )}

              <div className="drawer-section">
                <span className="summary-card-title font-mono">AUTHENTICATED EVIDENCE CITATIONS</span>
                <div className="evidence-citations-drawer" style={{ marginTop: '0.5rem' }}>
                  {selectedQuestion.evidence_citations.map((cit, idx) => (
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
