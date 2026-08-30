import React, { useState, useEffect } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';
import FeatureGate from '../components/FeatureGate';

export default function RecommendationPage({
  sessionId,
  hasRequirements = false,
  hasComparison = false,
  scoringData,
  recommendationData,
  onRunRecommendation,
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
  const decision = recommendationData?.decision || null;
  const narrative = recommendationData?.narrative || null;

  const [copiedBrief, setCopiedBrief] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleTriggerRecommendation() {
    if (onRunRecommendation) {
      setLoading(true);
      setError(null);
      try {
        const res = await onRunRecommendation();
        if (res && !res.success) {
          setError(res.error || 'Failed to generate executive recommendation brief.');
        }
      } catch (err) {
        setError(err.message || 'Error generating recommendation brief.');
      } finally {
        setLoading(false);
      }
    }
  }

  function renderGate(eyebrow, title, description, ctaLabel, onCta) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="recommendation"
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
            <h1 className="dashboard-title font-display">Executive Decision Brief</h1>
            <p className="dashboard-subtitle">Synthesized executive recommendation and strategic decision framework.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow={eyebrow}
              title={title}
              description={description}
              ctaLabel={ctaLabel}
              onCta={onCta}
            />
          </div>
        </div>
      </div>
    );
  }

  if (!sessionId) {
    return renderGate(
      "PREREQUISITE REQUIRED",
      "UPLOAD PROPOSALS FIRST",
      "PropIQ needs vendor proposals before generating an executive recommendation brief.",
      "Upload Proposals",
      onNavigateDashboard
    );
  }

  if (!hasRequirements) {
    return renderGate(
      "PREREQUISITE REQUIRED",
      "SET REQUIREMENTS FIRST",
      "Define your procurement requirements before generating an executive decision brief.",
      "Set Requirements",
      onNavigateRequirements
    );
  }

  if (!scoringData) {
    return renderGate(
      "PREREQUISITE REQUIRED",
      "COMPLETE VENDOR RANKING FIRST",
      "Executive decision brief requires vendor alignment ranking to be calculated first.",
      "Go to Vendor Ranking",
      onNavigateRanking
    );
  }

  if (loading) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="recommendation"
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
            <h1 className="dashboard-title font-display">Executive Decision Brief</h1>
            <p className="dashboard-subtitle">Synthesizing executive recommendation and strategic decision framework...</p>
          </header>
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <div style={{ width: '40px', height: '40px', border: '4px solid #171717', borderTopColor: 'transparent', borderRadius: '50%', margin: '0 auto 1.5rem auto', animation: 'spin 1s linear infinite' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'Space Mono, monospace', color: '#171717' }}>Evaluating Procurement Recommendations</h3>
            <p style={{ color: '#555', marginTop: '0.5rem', fontSize: '0.9rem' }}>Synthesizing vendor scores, contract risks, and trade-offs into an executive decision brief...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return renderGate(
      "ANALYSIS ERROR",
      "RECOMMENDATION COULD NOT BE GENERATED",
      error,
      "Retry Recommendation Analysis",
      () => {
        setLoading(true);
        setError(null);
        onRunRecommendation()
          .then((res) => {
            setLoading(false);
            if (res && !res.success) setError(res.error || 'Failed to generate recommendation.');
          })
          .catch((err) => {
            setLoading(false);
            setError(err.message || 'Error generating recommendation.');
          });
      }
    );
  }

  if (!recommendationData || !decision) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="recommendation"
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
            <h1 className="dashboard-title font-display">Executive Decision Brief</h1>
            <p className="dashboard-subtitle">Synthesized executive recommendation and strategic decision framework.</p>
          </header>

          <div style={{ padding: '3rem 1rem', maxWidth: '640px', margin: '0 auto' }}>
            <div
              className={loading ? 'animate-pulse' : 'animate-fade-up'}
              style={{
                backgroundColor: loading ? '#F7F3EA' : '#FFFFFF',
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
                  backgroundColor: loading ? '#F4C84A' : '#C8D6FF',
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
                {loading ? 'GENERATING BRIEF...' : 'PREREQUISITES COMPLETE'}
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
                {loading ? 'Generating Executive Recommendation Brief' : 'Ready to Generate Recommendation Brief'}
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
                {loading
                  ? 'PropIQ is synthesizing requirement compliance, risk penalties, and clarification gaps into an executive recommendation brief...'
                  : 'All required upstream intelligence analyses are complete. Click below to generate the synthesized executive decision brief.'}
              </p>

              {error && (
                <div style={{ color: '#9E1A47', backgroundColor: '#FDE8EF', border: '1.5px solid #EB7096', padding: '0.75rem', borderRadius: '3px', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
                  {error}
                </div>
              )}

              <button
                type="button"
                className="btn-primary font-mono w-full"
                onClick={handleTriggerRecommendation}
                disabled={loading}
                style={{
                  width: '100%',
                  justifyContent: 'center',
                  padding: '0.9rem 1.5rem',
                  fontSize: '0.975rem',
                  opacity: loading ? 0.75 : 1,
                  cursor: loading ? 'not-allowed' : 'pointer',
                }}
              >
                <span>{loading ? 'Generating Recommendation Brief...' : 'Generate Executive Recommendation Brief'}</span>
                <span style={{ marginLeft: '0.4rem', display: 'inline-block' }}>
                  {loading ? '⌛' : '→'}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function getStateBadgeInfo(state) {
    switch (state) {
      case 'RECOMMENDED':
        return {
          label: 'RECOMMENDED',
          bg: '#B9B5EA',
          border: '#171717',
          text: '#171717',
          desc: 'Strongest alignment with procurement requirements and no critical concerns.',
        };
      case 'RECOMMENDED_WITH_CONDITIONS':
        return {
          label: 'CONDITIONAL LEADER (ACTION REQUIRED)',
          bg: '#F4C84A',
          border: '#171717',
          text: '#171717',
          desc: 'Leading candidate with strong requirement alignment, subject to resolution or waiver of 1 mandatory item before final award.',
        };
      case 'FURTHER_REVIEW_REQUIRED':
        return {
          label: 'FURTHER REVIEW REQUIRED',
          bg: '#EBBAC2',
          border: '#171717',
          text: '#171717',
          desc: 'Must Have gaps or critical contractual concerns require human procurement review.',
        };
      case 'NO_CLEAR_RECOMMENDATION':
        return {
          label: 'NO CLEAR RECOMMENDATION',
          bg: '#F5F2F0',
          border: '#171717',
          text: '#171717',
          desc: 'Top vendors are tied or score gap is too narrow to identify a preferred vendor.',
        };
      default:
        return {
          label: state || 'ANALYSIS INCOMPLETE',
          bg: '#F5F2F0',
          border: '#171717',
          text: '#171717',
          desc: 'Review proposal evaluation details.',
        };
    }
  }

  function handleCopyDecisionBrief() {
    if (!decision || !narrative) return;

    let text = `PropIQ Executive Decision Brief\n`;
    text += `===============================\n\n`;
    text += `RECOMMENDATION STATE: ${decision.recommendation_state}\n`;
    text += `RECOMMENDED VENDOR: ${decision.recommended_vendor || decision.leading_vendor || 'Tied / No clear recommendation'}\n`;
    text += `ALIGNMENT SCORE: ${decision.alignment_score}\n`;
    if (decision.score_gap > 0) text += `SCORE GAP: ${decision.score_gap} points\n`;
    text += `\nEXECUTIVE SUMMARY:\n${narrative.executive_summary}\n\n`;

    if (narrative.key_strengths_summary?.length > 0) {
      text += `KEY STRENGTHS:\n`;
      narrative.key_strengths_summary.forEach((s) => {
        text += `- ${s}\n`;
      });
      text += `\n`;
    }

    if (narrative.key_tradeoffs_summary?.length > 0) {
      text += `KEY TRADE-OFFS:\n`;
      narrative.key_tradeoffs_summary.forEach((t) => {
        text += `- ${t}\n`;
      });
      text += `\n`;
    }

    if (narrative.before_proceeding_summary?.length > 0) {
      text += `BEFORE PROCEEDING (ITEMS TO CONFIRM):\n`;
      narrative.before_proceeding_summary.forEach((c) => {
        text += `- ${c}\n`;
      });
      text += `\n`;
    }

    if (decision.runner_up_vendors?.length > 0) {
      const r2 = decision.runner_up_vendors[0];
      text += `ALTERNATIVE VENDOR:\n`;
      text += `- Vendor: ${r2.vendor_name} (Alignment Score: ${r2.alignment_score})\n`;
      text += `- Score Gap: ${r2.score_gap} points\n`;
      text += `- Primary Advantage: ${r2.key_advantage}\n`;
      text += `- Key Trade-off: ${r2.key_tradeoff}\n\n`;
    }

    text += `DECISION RATIONALE:\n${narrative.decision_rationale}\n`;

    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        setCopiedBrief(true);
        setTimeout(() => setCopiedBrief(false), 2000);
      }).catch((err) => {
        console.error('Copy brief failed:', err);
      });
    }
  }

  function handleExportBriefTxt() {
    if (!decision || !narrative) return;

    let content = `PropIQ Executive Decision Brief\n`;
    content += `===============================\n\n`;
    content += `Recommendation State: ${decision.recommendation_state}\n`;
    content += `Recommended Candidate: ${decision.recommended_vendor || decision.leading_vendor || 'Tied / No clear recommendation'}\n`;
    content += `Alignment Score: ${decision.alignment_score}\n`;
    content += `Score Gap: ${decision.score_gap} points\n`;
    content += `Policy Version: ${decision.recommendation_policy_version}\n\n`;

    content += `EXECUTIVE SUMMARY\n-----------------\n${narrative.executive_summary}\n\n`;
    content += `WHY THIS VENDOR\n---------------\n${narrative.why_this_vendor}\n\n`;

    if (narrative.key_strengths_summary?.length > 0) {
      content += `KEY STRENGTHS\n-------------\n`;
      narrative.key_strengths_summary.forEach((s) => (content += `* ${s}\n`));
      content += `\n`;
    }

    if (narrative.key_tradeoffs_summary?.length > 0) {
      content += `KEY TRADE-OFFS\n--------------\n`;
      narrative.key_tradeoffs_summary.forEach((t) => (content += `* ${t}\n`));
      content += `\n`;
    }

    if (narrative.before_proceeding_summary?.length > 0) {
      content += `BEFORE PROCEEDING\n-----------------\n`;
      narrative.before_proceeding_summary.forEach((c) => (content += `* ${c}\n`));
      content += `\n`;
    }

    if (decision.runner_up_vendors?.length > 0) {
      const r2 = decision.runner_up_vendors[0];
      content += `ALTERNATIVE VENDOR\n------------------\n`;
      content += `Vendor: ${r2.vendor_name}\nScore: ${r2.alignment_score}\nScore Gap: ${r2.score_gap} pts\nAdvantage: ${r2.key_advantage}\nTrade-off: ${r2.key_tradeoff}\n\n`;
    }

    content += `DECISION RATIONALE\n------------------\n${narrative.decision_rationale}\n`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `PropIQ_Executive_Decision_Brief.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  const badgeInfo = getStateBadgeInfo(decision?.recommendation_state);

  if (!sessionId) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="recommendation"
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
            <h1 className="dashboard-title font-display">Recommendation Brief</h1>
            <p className="dashboard-subtitle">Evidence-backed executive decision brief and vendor evaluation trade-offs.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              title="Recommendation Brief"
              description="PropIQ needs completed vendor analysis before it can generate an evidence-backed recommendation."
              onUpload={onNavigateDashboard}
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
        activeTab="recommendation"
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
              <h1 className="dashboard-title font-display">Procurement Recommendation</h1>
              <p className="dashboard-subtitle">
                Review the current vendor recommendation, key trade-offs, and items that should be confirmed before proceeding.
              </p>
            </div>
            {decision && (
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button type="button" className="btn-secondary font-mono" onClick={handleExportBriefTxt} style={{ fontSize: '0.85rem' }}>
                  Export Brief (.txt)
                </button>
                <button type="button" className="btn-primary font-mono" onClick={handleCopyDecisionBrief} style={{ fontSize: '0.85rem' }}>
                  {copiedBrief ? '✓ Copied Brief!' : 'Copy Decision Brief'}
                </button>
              </div>
            )}
          </div>
        </header>

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '2rem 1.5rem', maxWidth: '1180px' }}>
          {/* Main Workspace Column */}
          <div className="main-workspace-col">
            {/* Legal Decision Support Microcopy Banner */}
            <div className="privacy-microcopy" style={{ marginTop: '0', borderTop: 'none', paddingWait: '0', marginBottom: '1.5rem', backgroundColor: '#F5F2F0', border: '2px solid #171717', borderRadius: '2px', padding: '0.75rem 1rem' }}>
              <strong>Notice:</strong> PropIQ provides procurement decision support based on configured requirements and available proposal evidence. Final vendor selection should include appropriate procurement, financial, technical, and legal review.
            </div>

            {!decision ? (
              <div className="main-panel" style={{ textAlign: 'center', padding: '2.5rem 1.5rem' }}>
                <h3 className="panel-title font-display" style={{ fontSize: '1.1rem' }}>
                  Complete the vendor evaluation to generate a procurement recommendation.
                </h3>
                <p className="panel-desc" style={{ marginTop: '0.4rem' }}>
                  Define requirements and analyze proposals to view your evidence-backed decision brief.
                </p>
                <div style={{ marginTop: '1.25rem' }}>
                  <button type="button" className="btn-primary font-mono" onClick={onNavigateRequirements}>
                    <span>Define Requirements & Score Vendors</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Primary Recommendation Card */}
                <div
                  className="main-panel"
                  style={{
                    backgroundColor: badgeInfo.bg,
                    borderColor: '#171717',
                    borderWidth: '2px',
                    padding: '1.5rem 1.75rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1rem' }}>
                    <span className="sample-badge font-mono" style={{ backgroundColor: '#171717', color: '#FFFFFF', fontSize: '0.75rem', padding: '0.25rem 0.65rem' }}>
                      {badgeInfo.label}
                    </span>
                    <span className="sample-badge font-mono" style={{ backgroundColor: '#FFFFFF', border: '1.5px solid #171717' }}>
                      Policy v{decision.recommendation_policy_version}
                    </span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
                    <div>
                      <span className="summary-card-title font-mono" style={{ color: '#171717' }}>
                        {decision.recommendation_state === 'RECOMMENDED_WITH_CONDITIONS' && decision.must_have_failures > 0
                          ? 'CONDITIONAL LEADER (ACTION REQUIRED)'
                          : (decision.recommended_vendor ? 'PREFERRED RECOMMENDATION CANDIDATE' : 'TOP SCORING VENDOR (ACTION REQUIRED)')}
                      </span>
                      <h2 className="font-mono" style={{ fontSize: '1.8rem', margin: '0.2rem 0 0 0', color: '#171717' }}>
                        {decision.recommended_vendor || decision.leading_vendor || 'Tied / No clear choice'}
                      </h2>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span className="summary-card-title font-mono" style={{ color: '#171717' }}>LEADING VENDOR ALIGNMENT SCORE</span>
                      <div className="font-mono font-display" style={{ fontSize: '2.2rem', fontWeight: 700, color: '#171717', lineHeight: '1.1' }}>
                        {decision.alignment_score}
                      </div>
                      <span className="font-mono" style={{ fontSize: '0.72rem', color: '#555', fontWeight: 600, display: 'block', marginTop: '0.1rem' }}>
                        {(decision.recommended_vendor || decision.leading_vendor)}'s Net Score (out of 100)
                      </span>
                      {decision.score_gap > 0 && (
                        <span className="font-mono" style={{ fontSize: '0.75rem', color: '#171717', fontWeight: 700, display: 'block', marginTop: '0.25rem' }}>
                          +{decision.score_gap} pts score lead
                        </span>
                      )}
                    </div>
                  </div>

                  <p style={{ fontSize: '0.925rem', color: '#171717', lineHeight: '1.5', margin: 0 }}>
                    {badgeInfo.desc}
                  </p>

                  {/* Summary Metric Counters */}
                  <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1.5px solid #171717' }}>
                    <div style={{ fontSize: '0.8rem', color: '#171717' }}>
                      Must Have Gaps: <strong>{decision.must_have_failures}</strong>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#171717' }}>
                      Critical Risks: <strong>{decision.critical_risk_count}</strong>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#171717' }}>
                      High Priority Clarifications: <strong>{decision.high_priority_clarifications}</strong>
                    </div>
                  </div>
                </div>

                {/* Executive Summary Block */}
                {narrative && (
                  <div className="main-panel" style={{ backgroundColor: '#FFFFFF', padding: '1.5rem 1.75rem' }}>
                    <h3 className="panel-title font-display" style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Executive Summary</h3>
                    <p style={{ fontSize: '0.95rem', color: '#171717', lineHeight: '1.6', marginBottom: '1rem' }}>
                      {narrative.executive_summary}
                    </p>
                    {narrative.decision_rationale && (
                      <div style={{ backgroundColor: '#F5F2F0', padding: '0.75rem 1rem', borderRadius: '2px', borderLeft: '4px solid #171717', border: '1.5px solid #171717' }}>
                        <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#171717', display: 'block', marginBottom: '0.15rem' }}>
                          DECISION RATIONALE
                        </span>
                        <span style={{ fontSize: '0.875rem', color: '#171717' }}>
                          {narrative.decision_rationale}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Why This Vendor (Strengths Grid) */}
                {decision.key_strengths.length > 0 && (
                  <div className="main-panel" style={{ backgroundColor: '#FFFFFF', padding: '1.5rem 1.75rem' }}>
                    <h3 className="panel-title font-display" style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Why This Vendor (Key Strengths)</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      {decision.key_strengths.map((s, idx) => (
                        <div key={idx} style={{ backgroundColor: '#B9B5EA', border: '1.5px solid #171717', borderRadius: '2px', padding: '0.85rem 1rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                            <strong style={{ fontSize: '0.925rem', color: '#171717' }}>{s.title}</strong>
                            <span className="sample-badge font-mono" style={{ backgroundColor: '#FFFFFF' }}>{s.category}</span>
                          </div>
                          <p style={{ fontSize: '0.85rem', color: '#171717', margin: 0, lineHeight: '1.4' }}>
                            {s.description}
                          </p>
                          {s.evidence_citations && s.evidence_citations.length > 0 && (
                            <button
                              type="button"
                              className="btn-secondary font-mono"
                              onClick={() => setSelectedEvidence(s.evidence_citations[0])}
                              style={{ marginTop: '0.4rem', fontSize: '0.75rem' }}
                            >
                              View Citation ({s.evidence_citations[0].source_filename} — Page {s.evidence_citations[0].start_page})
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Trade-offs & Considerations */}
                {decision.key_tradeoffs.length > 0 && (
                  <div className="main-panel" style={{ backgroundColor: '#FFFFFF', padding: '1.5rem 1.75rem' }}>
                    <h3 className="panel-title font-display" style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Key Trade-offs & Considerations</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                      {decision.key_tradeoffs.map((t, idx) => (
                        <div key={idx} style={{ backgroundColor: '#EDB240', border: '1.5px solid #171717', borderRadius: '2px', padding: '0.85rem 1rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                            <strong style={{ fontSize: '0.925rem', color: '#171717' }}>{t.title}</strong>
                            <span className="sample-badge font-mono" style={{ backgroundColor: '#FFFFFF' }}>{t.severity_or_impact}</span>
                          </div>
                          <p style={{ fontSize: '0.85rem', color: '#171717', margin: 0, lineHeight: '1.4' }}>
                            {t.description}
                          </p>
                          {t.evidence_citations && t.evidence_citations.length > 0 && (
                            <button
                              type="button"
                              className="btn-secondary font-mono"
                              onClick={() => setSelectedEvidence(t.evidence_citations[0])}
                              style={{ marginTop: '0.4rem', fontSize: '0.75rem' }}
                            >
                              View Citation ({t.evidence_citations[0].source_filename} — Page {t.evidence_citations[0].start_page})
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Before Proceeding (Essential Checklist) */}
                {decision.conditions_to_confirm.length > 0 && (
                  <div className="main-panel" style={{ backgroundColor: '#FFFFFF', padding: '1.5rem 1.75rem' }}>
                    <h3 className="panel-title font-display" style={{ fontSize: '1.1rem', marginBottom: '0.4rem' }}>Before Proceeding (Items to Confirm)</h3>
                    <p className="panel-desc" style={{ marginBottom: '1rem' }}>
                      High-priority questions and contract concerns that should be confirmed before proceeding to contract award.
                    </p>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {decision.conditions_to_confirm.map((c, idx) => (
                        <div key={idx} style={{ backgroundColor: '#F5F2F0', border: '1.5px solid #171717', borderRadius: '2px', padding: '0.85rem 1rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.3rem', flexWrap: 'wrap' }}>
                            <span className="sample-badge font-mono" style={{ backgroundColor: '#171717', color: '#FFFFFF' }}>{c.item_type}</span>
                            <span className="sample-badge font-mono" style={{ backgroundColor: '#EDB240', color: '#171717' }}>{c.priority_or_severity}</span>
                            <strong style={{ fontSize: '0.9rem', color: '#171717' }}>{c.title}</strong>
                          </div>
                          <p style={{ fontSize: '0.85rem', color: '#171717', margin: 0, lineHeight: '1.4' }}>
                            <strong>Action:</strong> {c.action_required}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Alternative Vendor Context */}
                {decision.runner_up_vendors.length > 0 && (
                  <div className="main-panel" style={{ backgroundColor: '#F5F2F0', padding: '1.25rem 1.5rem' }}>
                    <span className="summary-card-title font-mono">ALTERNATIVE OPTION</span>
                    {decision.runner_up_vendors.map((r2, idx) => (
                      <div key={idx} style={{ marginTop: '0.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
                          <h4 className="font-mono" style={{ fontSize: '1.1rem', margin: 0, color: '#171717' }}>
                            {r2.vendor_name}
                          </h4>
                          <span className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                            {r2.alignment_score} Alignment Score ({r2.score_gap} pts gap)
                          </span>
                        </div>
                        <p style={{ fontSize: '0.85rem', color: '#171717', marginTop: '0.4rem', marginBottom: '0.2rem' }}>
                          <strong>Advantage:</strong> {r2.key_advantage}
                        </p>
                        <p style={{ fontSize: '0.85rem', color: '#171717', margin: 0 }}>
                          <strong>Trade-off:</strong> {r2.key_tradeoff}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right SaaS Session Panel */}
          <SaasSessionPanel
            proposalsCount={2}
            definedVendorsCount={2}
            isProcessed={true}
            hasRecommendation={true}
          />
        </div>
      </div>

      {/* Evidence Detail Drawer Modal */}
      {selectedEvidence && (
        <div className="drawer-overlay" onClick={() => setSelectedEvidence(null)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge font-mono">EVIDENCE CITATION</span>
                <h2 className="drawer-title font-display" style={{ marginTop: '0.2rem' }}>
                  {selectedEvidence.vendor_name}
                </h2>
              </div>
              <button type="button" className="btn-remove font-mono" onClick={() => setSelectedEvidence(null)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body">
              <div className="drawer-section">
                <span className="summary-card-title font-mono">SOURCE FILE & LOCATION</span>
                <p className="fact-summary-text" style={{ marginTop: '0.25rem' }}>
                  {selectedEvidence.source_filename} — Page {selectedEvidence.start_page === selectedEvidence.end_page ? selectedEvidence.start_page : `${selectedEvidence.start_page}-${selectedEvidence.end_page}`}
                </p>
                <div className="evidence-chunk-meta font-mono">Evidence Ref: <code>{selectedEvidence.chunk_id}</code></div>
              </div>

              <div className="drawer-section">
                <span className="summary-card-title font-mono">AUTHENTICATED PROPOSAL EXCERPT</span>
                <div className="evidence-excerpt-box" style={{ marginTop: '0.5rem' }}>
                  <p className="evidence-excerpt-text font-mono" style={{ fontSize: '0.8rem' }}>"{selectedEvidence.excerpt_text}"</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
