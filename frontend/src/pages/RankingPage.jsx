import React, { useState, useEffect } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';
import FeatureGate from '../components/FeatureGate';

/* ─────────── Helper Functions ─────────── */
function cleanVendorName(name) {
  if (!name) return '';
  return name.replace(/^\d+[\.\s\-]+/, '').trim();
}

function formatDeduction(val) {
  const num = Number(val) || 0;
  if (num > 0) return `-${num}`;
  return '0';
}

function getRankBadgeStyle(rankStatus, rank, mustHaveFailures = 0) {
  if (mustHaveFailures > 0) {
    if (mustHaveFailures === 1 && rank === 1) {
      return { bg: '#F4C84A', label: 'CONDITIONAL LEADER', sublabel: '1 MANDATORY ITEM TO RESOLVE', text: '#171717' };
    }
    return { bg: '#FDE8EF', label: 'ACTION REQUIRED', sublabel: `${mustHaveFailures} MANDATORY GAPS`, text: '#9E1A47' };
  }
  if (rank === 1) {
    return { bg: '#C8D6FF', label: rankStatus || 'LEADING', text: '#171717' };
  }
  if (rankStatus === 'LEADING' || rankStatus === 'COMPETITIVE') {
    return { bg: '#F4C84A', label: rankStatus, text: '#171717' };
  }
  return { bg: '#F5F2F0', label: rankStatus || 'BEHIND', text: '#171717' };
}

function formatExplanationText(text, mustHaveFailures, rank) {
  if (!text) return '';
  if (mustHaveFailures === 1 && rank === 1) {
    return text.replace(/currently leads 1st with a/i, 'is the Conditional Leader with a')
               .replace(/is UNQUALIFIED due to 1 mandatory \(Must Have\) requirement failure with a/i, 'is the Conditional Leader with a');
  }
  return text;
}

function getStatusBadgeStyle(statusStr) {
  const map = {
    MEETS:       { bg: '#C8D6FF', text: '#171717', label: 'MEETS' },
    PARTIAL:     { bg: '#F4C84A', text: '#171717', label: 'PARTIAL' },
    FAILS:       { bg: '#EB7096', text: '#FFFFFF', label: 'FAILS' },
    MISSING:     { bg: '#F5F2F0', text: '#171717', label: 'MISSING' },
    UNCLEAR:     { bg: '#EBBAC2', text: '#171717', label: 'UNCLEAR' },
    CONFLICTING: { bg: '#7897FF', text: '#FFFFFF', label: 'CONFLICTING' },
  };
  return map[statusStr] || { bg: '#F5F2F0', text: '#171717', label: statusStr || 'N/A' };
}

export default function RankingPage({
  sessionId,
  hasRequirements = false,
  hasComparison = false,
  hasRisks = false,
  hasClarifications = false,
  scoringData,
  onRunScoring,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateVendorDetails,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
}) {
  const vendorScores = scoringData?.vendor_scores || [];
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalError, setEvalError] = useState(null);

  // Determine explicit step statuses
  const stepProposals = !!sessionId ? "COMPLETED" : "NOT_STARTED";
  const stepRequirements = hasRequirements ? "COMPLETED" : "NOT_STARTED";
  const stepComparison = hasComparison ? "COMPLETED" : "NOT_STARTED";
  const stepRisks = hasRisks ? "COMPLETED" : "NOT_STARTED";
  const stepClarifications = hasClarifications ? "COMPLETED" : "NOT_STARTED";

  const isPrerequisiteIncomplete =
    stepProposals !== "COMPLETED" ||
    stepRequirements !== "COMPLETED" ||
    stepComparison !== "COMPLETED" ||
    stepRisks !== "COMPLETED" ||
    stepClarifications !== "COMPLETED";

  async function handleTriggerScoring() {
    if (onRunScoring) {
      setIsEvaluating(true);
      setEvalError(null);
      try {
        await onRunScoring();
      } catch (err) {
        setEvalError(err?.message || 'Scoring evaluation failed');
      } finally {
        setIsEvaluating(false);
      }
    }
  }

  if (isPrerequisiteIncomplete) {
    let firstIncompleteNav = onNavigateDashboard;
    let ctaLabel = "Upload Proposals";

    if (stepProposals !== "COMPLETED") {
      firstIncompleteNav = onNavigateDashboard;
      ctaLabel = "Upload Proposals";
    } else if (stepRequirements !== "COMPLETED") {
      firstIncompleteNav = onNavigateRequirements;
      ctaLabel = "Set Requirements";
    } else if (stepComparison !== "COMPLETED") {
      firstIncompleteNav = onNavigateComparison;
      ctaLabel = "Run Comparison";
    } else if (stepRisks !== "COMPLETED") {
      firstIncompleteNav = onNavigateRisks;
      ctaLabel = "Analyze Risks & Contradictions";
    } else if (stepClarifications !== "COMPLETED") {
      firstIncompleteNav = onNavigateClarifications;
      ctaLabel = "Generate Clarifications";
    }

    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="ranking"
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
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Vendor Alignment Ranking</h1>
            <p className="dashboard-subtitle">See how vendors rank based on requirement alignment and identified issues.</p>
          </header>

          <div style={{ padding: '2rem 1rem', maxWidth: '680px', margin: '0 auto' }}>
            <div
              className="animate-fade-up"
              style={{
                backgroundColor: '#FFFFFF',
                borderRadius: '4px',
                border: '2px solid #171717',
                padding: '2.75rem 2.5rem',
                boxShadow: '6px 6px 0px #171717',
              }}
            >
              <div
                className="font-mono"
                style={{
                  display: 'inline-block',
                  backgroundColor: '#EB7096',
                  color: '#FFFFFF',
                  border: '1.5px solid #171717',
                  borderRadius: '3px',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.725rem',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  marginBottom: '1.25rem',
                  boxShadow: '2px 2px 0px #171717',
                  textTransform: 'uppercase',
                }}
              >
                PREREQUISITES INCOMPLETE
              </div>

              <h2
                className="font-display"
                style={{
                  fontSize: '1.75rem',
                  color: '#171717',
                  textTransform: 'uppercase',
                  marginBottom: '0.85rem',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.1,
                }}
              >
                Complete Required Intelligence Analysis
              </h2>

              <p
                className="font-sans"
                style={{
                  color: '#171717',
                  fontSize: '0.975rem',
                  marginBottom: '1.75rem',
                  lineHeight: '1.6',
                  fontWeight: 500,
                }}
              >
                PropIQ calculates vendor rankings only when all upstream intelligence modules (Comparison, Risks & Contradictions, Clarifications) are complete for the active session.
              </p>

              <div
                style={{
                  backgroundColor: '#F7F3EA',
                  border: '2px solid #171717',
                  borderRadius: '4px',
                  padding: '1.5rem',
                  marginBottom: '2rem',
                  boxShadow: '3.5px 3.5px 0px #171717',
                }}
              >
                <div
                  className="font-mono"
                  style={{
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    color: '#171717',
                    marginBottom: '1.1rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                  }}
                >
                  ANALYSIS PROGRESS:
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <span
                      className="font-mono"
                      style={{
                        width: '26px',
                        height: '26px',
                        backgroundColor: stepProposals === 'COMPLETED' ? '#C8D6FF' : '#FFFFFF',
                        color: stepProposals === 'COMPLETED' ? '#171717' : '#9A9A90',
                        border: '1.5px solid #171717',
                        borderRadius: '3px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        boxShadow: stepProposals === 'COMPLETED' ? '1.5px 1.5px 0px #171717' : 'none',
                      }}
                    >
                      {stepProposals === 'COMPLETED' ? '✓' : '○'}
                    </span>
                    <span
                      className="font-sans"
                      style={{
                        color: stepProposals === 'COMPLETED' ? '#171717' : '#6A6A60',
                        fontWeight: stepProposals === 'COMPLETED' ? 700 : 500,
                        fontSize: '0.925rem',
                      }}
                    >
                      Proposal Analysis
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <span
                      className="font-mono"
                      style={{
                        width: '26px',
                        height: '26px',
                        backgroundColor: stepRequirements === 'COMPLETED' ? '#C8D6FF' : '#FFFFFF',
                        color: stepRequirements === 'COMPLETED' ? '#171717' : '#9A9A90',
                        border: '1.5px solid #171717',
                        borderRadius: '3px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        boxShadow: stepRequirements === 'COMPLETED' ? '1.5px 1.5px 0px #171717' : 'none',
                      }}
                    >
                      {stepRequirements === 'COMPLETED' ? '✓' : '○'}
                    </span>
                    <span
                      className="font-sans"
                      style={{
                        color: stepRequirements === 'COMPLETED' ? '#171717' : '#6A6A60',
                        fontWeight: stepRequirements === 'COMPLETED' ? 700 : 500,
                        fontSize: '0.925rem',
                      }}
                    >
                      Requirements Definition
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <span
                      className="font-mono"
                      style={{
                        width: '26px',
                        height: '26px',
                        backgroundColor: stepComparison === 'COMPLETED' ? '#C8D6FF' : '#FFFFFF',
                        color: stepComparison === 'COMPLETED' ? '#171717' : '#9A9A90',
                        border: '1.5px solid #171717',
                        borderRadius: '3px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        boxShadow: stepComparison === 'COMPLETED' ? '1.5px 1.5px 0px #171717' : 'none',
                      }}
                    >
                      {stepComparison === 'COMPLETED' ? '✓' : '○'}
                    </span>
                    <span
                      className="font-sans"
                      style={{
                        color: stepComparison === 'COMPLETED' ? '#171717' : '#6A6A60',
                        fontWeight: stepComparison === 'COMPLETED' ? 700 : 500,
                        fontSize: '0.925rem',
                      }}
                    >
                      Requirement Comparison
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <span
                      className="font-mono"
                      style={{
                        width: '26px',
                        height: '26px',
                        backgroundColor: stepRisks === 'COMPLETED' ? '#C8D6FF' : '#FFFFFF',
                        color: stepRisks === 'COMPLETED' ? '#171717' : '#9A9A90',
                        border: '1.5px solid #171717',
                        borderRadius: '3px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        boxShadow: stepRisks === 'COMPLETED' ? '1.5px 1.5px 0px #171717' : 'none',
                      }}
                    >
                      {stepRisks === 'COMPLETED' ? '✓' : '○'}
                    </span>
                    <span
                      className="font-sans"
                      style={{
                        color: stepRisks === 'COMPLETED' ? '#171717' : '#6A6A60',
                        fontWeight: stepRisks === 'COMPLETED' ? 700 : 500,
                        fontSize: '0.925rem',
                      }}
                    >
                      Risks & Contradictions Analysis
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <span
                      className="font-mono"
                      style={{
                        width: '26px',
                        height: '26px',
                        backgroundColor: stepClarifications === 'COMPLETED' ? '#C8D6FF' : '#FFFFFF',
                        color: stepClarifications === 'COMPLETED' ? '#171717' : '#9A9A90',
                        border: '1.5px solid #171717',
                        borderRadius: '3px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        boxShadow: stepClarifications === 'COMPLETED' ? '1.5px 1.5px 0px #171717' : 'none',
                      }}
                    >
                      {stepClarifications === 'COMPLETED' ? '✓' : '○'}
                    </span>
                    <span
                      className="font-sans"
                      style={{
                        color: stepClarifications === 'COMPLETED' ? '#171717' : '#6A6A60',
                        fontWeight: stepClarifications === 'COMPLETED' ? 700 : 500,
                        fontSize: '0.925rem',
                      }}
                    >
                      Clarification Needs
                    </span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                className="btn-primary font-mono w-full"
                onClick={firstIncompleteNav}
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  padding: '0.9rem 1.5rem',
                  fontSize: '0.975rem',
                }}
              >
                <span>{ctaLabel}</span>
                <span className="btn-arrow">↗</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!scoringData) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="ranking"
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
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Vendor Alignment Ranking</h1>
            <p className="dashboard-subtitle">See how vendors rank based on requirement alignment and identified issues.</p>
          </header>

          <div style={{ padding: '3rem 1rem', maxWidth: '640px', margin: '0 auto' }}>
            <div
              className={isEvaluating ? 'animate-pulse' : 'animate-fade-up'}
              style={{
                backgroundColor: isEvaluating ? '#F7F3EA' : '#FFFFFF',
                borderRadius: '4px',
                border: '2px solid #171717',
                padding: '2.75rem 2.5rem',
                boxShadow: '6px 6px 0px #171717',
                textAlign: 'center',
              }}
            >
              <span
                className="font-mono"
                style={{
                  display: 'inline-block',
                  backgroundColor: isEvaluating ? '#F4C84A' : '#C8D6FF',
                  color: '#171717',
                  border: '1.5px solid #171717',
                  borderRadius: '3px',
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.725rem',
                  fontWeight: 700,
                  letterSpacing: '0.08em',
                  marginBottom: '1.25rem',
                  boxShadow: '2px 2px 0px #171717',
                  textTransform: 'uppercase',
                }}
              >
                {isEvaluating ? 'CALCULATING SCORES...' : 'PREREQUISITES COMPLETE'}
              </span>

              <h2
                className="font-display"
                style={{
                  fontSize: '1.75rem',
                  color: '#171717',
                  textTransform: 'uppercase',
                  marginBottom: '0.85rem',
                  letterSpacing: '-0.02em',
                  lineHeight: 1.1,
                }}
              >
                {isEvaluating ? 'Calculating Vendor Alignment Rankings' : 'Ready to Calculate Vendor Ranking'}
              </h2>

              <p
                className="font-sans"
                style={{
                  color: '#171717',
                  fontSize: '0.975rem',
                  marginBottom: '1.75rem',
                  lineHeight: '1.6',
                  fontWeight: 500,
                }}
              >
                {isEvaluating
                  ? 'PropIQ is synthesizing requirement compliance matrix, risk findings, and clarification gaps into transparent, deterministic vendor rankings...'
                  : 'All required upstream intelligence analyses (Comparison, Risks & Contradictions, Clarifications) are complete. Click below to calculate vendor alignment rankings.'}
              </p>

              {evalError && (
                <div style={{ color: '#9E1A47', backgroundColor: '#FDE8EF', border: '1.5px solid #EB7096', padding: '0.75rem', borderRadius: '3px', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
                  {evalError}
                </div>
              )}

              <button
                type="button"
                className="btn-primary font-mono w-full"
                onClick={handleTriggerScoring}
                disabled={isEvaluating}
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  padding: '0.9rem 1.5rem',
                  fontSize: '0.975rem',
                  opacity: isEvaluating ? 0.75 : 1,
                  cursor: isEvaluating ? 'not-allowed' : 'pointer',
                }}
              >
                <span>{isEvaluating ? 'Calculating Vendor Rankings...' : 'Calculate Vendor Alignment Ranking'}</span>
                <span style={{ marginLeft: '0.4rem', display: 'inline-block' }}>
                  {isEvaluating ? '⌛' : '→'}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const hasScoringData = vendorScores.length > 0;
  const allVendorsFailed =
    hasScoringData &&
    vendorScores.every(
      (v) => v.alignment_score === 0 || v.must_have_failures_count > 0
    );

  // CASE D: Real Vendor Ranking View
  return (
    <div className="dashboard-layout">
      {/* Left Sidebar */}
      <Sidebar
        activeTab="ranking"
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
              <h1 className="dashboard-title font-display">Vendor Alignment Ranking</h1>
              <p className="dashboard-subtitle">
                See how vendors rank based on requirement alignment, identified risks, and clarifications.
              </p>
            </div>
            {onNavigateRecommendation && (
              <button type="button" className="btn-primary font-mono" onClick={onNavigateRecommendation} style={{ fontSize: '0.85rem' }}>
                <span>View Recommendation</span>
                <span>→</span>
              </button>
            )}
          </div>
        </header>

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '2rem 1.5rem', maxWidth: '1240px', minWidth: 0 }}>
          {/* Main Workspace Column */}
          <div className="main-workspace-col" style={{ gap: '1.25rem', minWidth: 0, overflow: 'hidden' }}>

            {/* Vendor Stacked Rank Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {vendorScores.map((v, idx) => {
                const isUnmet = v.must_have_failures_count > 0;
                const badge = getRankBadgeStyle(v.rank_status, v.rank, v.must_have_failures_count);
                const cleanName = cleanVendorName(v.vendor_name);
                const topBorderColor = isUnmet ? (v.must_have_failures_count === 1 && v.rank === 1 ? '#F4C84A' : '#EB7096') : (v.rank === 1 ? '#7897FF' : '#171717');

                return (
                  <div
                    key={idx}
                    className="main-panel"
                    style={{
                      backgroundColor: '#FFFFFF',
                      border: '2px solid #171717',
                      borderRadius: '4px',
                      padding: '1.5rem 1.75rem',
                      boxShadow: '3px 3px 0px #171717',
                      position: 'relative',
                    }}
                  >
                    {/* Top Color Strip */}
                    <div style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      right: 0,
                      height: '4px',
                      backgroundColor: topBorderColor,
                      borderRadius: '2px 2px 0 0'
                    }} />

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.4rem', flexWrap: 'wrap' }}>
                          <span className="sample-badge font-mono" style={{
                            backgroundColor: '#171717',
                            color: '#FFFFFF',
                            fontWeight: 700
                          }}>
                            RANK #{v.rank}
                          </span>
                          <span className="sample-badge font-mono" style={{ backgroundColor: badge.bg, color: badge.text, border: '1.5px solid #171717', fontWeight: 700 }}>
                            {badge.label}
                          </span>
                          {isUnmet && (
                            <span className="sample-badge font-mono" style={{ backgroundColor: '#F5F2F0', color: '#171717', border: '1.5px solid #171717', fontWeight: 700 }}>
                              {v.must_have_failures_count} Mandatory Failure{v.must_have_failures_count > 1 ? 's' : ''}
                            </span>
                          )}
                        </div>

                        <h2 className="font-mono" style={{ fontSize: '1.4rem', margin: 0, color: '#171717', fontWeight: 700 }}>
                          {cleanName}
                        </h2>
                      </div>

                      {/* Alignment Score Display */}
                      <div style={{ textAlign: 'right' }}>
                        <span className="summary-card-title font-mono" style={{ color: '#171717' }}>ALIGNMENT SCORE</span>
                        <div className="font-mono font-display" style={{ fontSize: '2.5rem', fontWeight: 700, color: '#171717', lineHeight: '1' }}>
                          {v.alignment_score}
                        </div>
                        <span className="font-mono" style={{ fontSize: '0.75rem', color: '#6A6A60', fontWeight: 700 }}>out of 100.0</span>
                      </div>
                    </div>

                    {/* Evidence-Backed Explanation */}
                    <p className="cell-explanation-text" style={{ fontSize: '0.875rem', color: '#171717', lineHeight: '1.55', marginBottom: '1.25rem' }}>
                      {formatExplanationText(v.ranking_explanation, v.must_have_failures_count, v.rank)}
                    </p>

                    {/* Score Summary Metrics Grid */}
                    <div className="summary-cards-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
                      <div className="summary-card" style={{ backgroundColor: '#F5F2F0' }}>
                        <span className="summary-card-title font-mono">REQUIREMENTS</span>
                        <span className="summary-card-value font-mono" style={{ fontSize: '1.3rem' }}>{v.base_alignment_score}</span>
                        <span className="summary-card-sub">Base Score</span>
                      </div>

                      <div className="summary-card" style={{ backgroundColor: '#F5F2F0' }}>
                        <span className="summary-card-title font-mono">RISK DEDUCTION</span>
                        <span className="summary-card-value font-mono" style={{ fontSize: v.risk_analysis_status === 'NOT_ANALYZED' ? '0.9rem' : '1.3rem', color: v.total_risk_penalty > 0 ? '#EB7096' : '#171717', fontWeight: 700 }}>
                          {v.risk_analysis_status === 'NOT_ANALYZED' ? 'Not analyzed' : (v.total_risk_penalty === 0 ? '0' : formatDeduction(v.total_risk_penalty))}
                        </span>
                        <span className="summary-card-sub">
                          {v.risk_analysis_status === 'NOT_ANALYZED' ? 'Pending Analysis' : (v.total_risk_penalty === 0 ? 'No Risk Penalties' : 'Risk Adjustments')}
                        </span>
                      </div>

                      <div className="summary-card" style={{ backgroundColor: '#F5F2F0' }}>
                        <span className="summary-card-title font-mono">CONTRADICTIONS</span>
                        <span className="summary-card-value font-mono" style={{ fontSize: v.contradiction_analysis_status === 'NOT_ANALYZED' ? '0.9rem' : '1.3rem', color: v.total_contradiction_penalty > 0 ? '#EB7096' : '#171717', fontWeight: 700 }}>
                          {v.contradiction_analysis_status === 'NOT_ANALYZED' ? 'Not analyzed' : (v.total_contradiction_penalty === 0 ? '0' : formatDeduction(v.total_contradiction_penalty))}
                        </span>
                        <span className="summary-card-sub">
                          {v.contradiction_analysis_status === 'NOT_ANALYZED' ? 'Pending Analysis' : (v.total_contradiction_penalty === 0 ? 'No Contradictions' : 'Intra-vendor Conflicts')}
                        </span>
                      </div>

                      <div className="summary-card" style={{ backgroundColor: '#F5F2F0' }}>
                        <span className="summary-card-title font-mono">CLARIFICATIONS</span>
                        <span className="summary-card-value font-mono" style={{ fontSize: v.clarification_analysis_status === 'NOT_ANALYZED' ? '0.9rem' : '1.3rem', color: v.total_clarification_penalty > 0 ? '#EB7096' : '#171717', fontWeight: 700 }}>
                          {v.clarification_analysis_status === 'NOT_ANALYZED' ? 'Not analyzed' : (v.total_clarification_penalty === 0 ? '0' : formatDeduction(v.total_clarification_penalty))}
                        </span>
                        <span className="summary-card-sub">
                          {v.clarification_analysis_status === 'NOT_ANALYZED' ? 'Pending Analysis' : (v.total_clarification_penalty === 0 ? 'No Gap Penalties' : 'Information Gaps')}
                        </span>
                      </div>
                    </div>

                    {/* Action Button */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        type="button"
                        className="btn-secondary font-mono"
                        onClick={() => setSelectedVendor(v)}
                        style={{ fontSize: '0.825rem' }}
                      >
                        View Score Breakdown →
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom Action Footer */}
            <div className="action-nav-footer" style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button type="button" className="btn-secondary font-mono" onClick={onNavigateClarifications}>
                ← Back to Clarifications
              </button>
              {onNavigateRecommendation && (
                <button type="button" className="btn-primary font-mono" onClick={onNavigateRecommendation}>
                  <span>View Recommendation Brief</span>
                  <span>→</span>
                </button>
              )}
            </div>
          </div>

          {/* Right SaaS Session Panel */}
          <SaasSessionPanel
            proposalsCount={vendorScores.length}
            definedVendorsCount={vendorScores.length}
            isProcessed={true}
            hasComparison={true}
            hasScoring={hasScoringData}
            onNavigate={(path) => {
              if (path === '/dashboard/recommendation' && onNavigateRecommendation) onNavigateRecommendation();
              else if (path === '/dashboard/comparison' && onNavigateComparison) onNavigateComparison();
              else if (onNavigateDashboard) onNavigateDashboard();
            }}
          />
        </div>
      </div>

      {/* Score Breakdown Modal Drawer */}
      {selectedVendor && (
        <div className="drawer-overlay" onClick={() => setSelectedVendor(null)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '680px' }}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge font-mono">SCORE BREAKDOWN</span>
                <h2 className="drawer-title font-display" style={{ marginTop: '0.2rem' }}>
                  {cleanVendorName(selectedVendor.vendor_name)} ({selectedVendor.must_have_failures_count > 0 ? 'UNQUALIFIED' : `Rank #${selectedVendor.rank}`})
                </h2>
              </div>
              <button type="button" className="btn-remove font-mono" onClick={() => setSelectedVendor(null)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body">
              {/* Formula & Overall Math */}
              <div className="drawer-section" style={{ backgroundColor: '#F5F2F0', padding: '1rem', borderRadius: '2px', border: '1.5px solid #171717' }}>
                <span className="summary-card-title font-mono">ALIGNMENT SCORE FORMULA</span>
                <div className="font-mono" style={{ fontSize: '1.25rem', fontWeight: 700, marginTop: '0.2rem', color: '#171717' }}>
                  {selectedVendor.alignment_score} / 100.0
                </div>
                <p className="fact-summary-text" style={{ marginTop: '0.4rem', fontSize: '0.8rem' }}>
                  Calculated from Base Requirement Score ({selectedVendor.base_alignment_score}%) minus Risk Penalties ({formatDeduction(selectedVendor.total_risk_penalty)} pts), Contradiction Penalties ({formatDeduction(selectedVendor.total_contradiction_penalty)} pts), and Clarification Penalties ({formatDeduction(selectedVendor.total_clarification_penalty)} pts). Clamped [0.0, 100.0].
                </p>
              </div>

              {/* Requirement Component Points Table */}
              <div className="drawer-section">
                <span className="summary-card-title font-mono">REQUIREMENT CONTRIBUTION BREAKDOWN</span>
                <div style={{ overflowX: 'auto', marginTop: '0.5rem' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem', textAlign: 'left', border: '1.5px solid #171717' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid #171717', backgroundColor: '#B9B5EA' }}>
                        <th style={{ padding: '0.5rem' }}>Requirement</th>
                        <th style={{ padding: '0.5rem' }}>Priority</th>
                        <th style={{ padding: '0.5rem' }}>Status</th>
                        <th style={{ padding: '0.5rem', textAlign: 'right' }}>Points</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedVendor.requirement_components.map((comp, idx) => {
                        const sBadge = getStatusBadgeStyle(comp.comparison_status);
                        return (
                          <tr key={idx} style={{ borderBottom: '1px solid #171717' }}>
                            <td style={{ padding: '0.5rem', fontWeight: 600 }}>{comp.requirement_label}</td>
                            <td style={{ padding: '0.5rem' }}>{comp.priority} ({comp.weight})</td>
                            <td style={{ padding: '0.5rem' }}>
                              <span className="sample-badge font-mono" style={{ backgroundColor: sBadge.bg, color: sBadge.text }}>{sBadge.label}</span>
                            </td>
                            <td style={{ padding: '0.5rem', textAlign: 'right', fontFamily: 'Space Mono, monospace' }}>
                              {comp.weighted_points} / {comp.max_points}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Itemized Deductions List */}
              {selectedVendor.deductions.length > 0 && (
                <div className="drawer-section">
                  <span className="summary-card-title font-mono">APPLIED DEDUCTIONS ({formatDeduction(selectedVendor.total_risk_penalty + selectedVendor.total_contradiction_penalty + selectedVendor.total_clarification_penalty)} PTS TOTAL)</span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginTop: '0.5rem' }}>
                    {selectedVendor.deductions.map((ded, idx) => (
                      <div key={idx} className="citation-item-box" style={{ backgroundColor: '#F5F2F0', border: '1.5px solid #171717' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ fontSize: '0.875rem', color: '#171717' }}>{ded.label}</strong>
                          <span className="sample-badge font-mono" style={{ backgroundColor: '#EB7096', color: '#FFFFFF' }}>
                            {formatDeduction(ded.final_deduction)} pts
                          </span>
                        </div>
                        <p className="evidence-excerpt-text" style={{ fontSize: '0.8rem', marginTop: '0.3rem', margin: 0 }}>
                          {ded.explanation}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
