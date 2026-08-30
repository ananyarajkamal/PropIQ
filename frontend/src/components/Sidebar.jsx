import React from 'react';

/**
 * PropIQ Sidebar Navigation
 *
 * Groups:
 *  WORKSPACE   → Dashboard, Requirements, Comparison
 *  INTELLIGENCE → Risks & Contradictions, Clarifications
 *  DECISION    → Vendor Ranking, Recommendation Brief
 *
 * "Proposals" is intentionally absent — proposal upload lives on Dashboard.
 */
export default function Sidebar({
  activeTab = 'dashboard',
  sessionReady = false,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
}) {
  function NavItem({ id, label, isActive, isLocked, onClick }) {
    const classes = [
      'sidebar-nav-item',
      isActive ? 'active' : '',
      isLocked && !isActive ? 'locked' : '',
    ].filter(Boolean).join(' ');

    return (
      <li>
        <a
          href="javascript:void(0)"
          className={classes}
          onClick={(e) => {
            e.preventDefault();
            if (onClick) onClick();
          }}
        >
          {label}
        </a>
      </li>
    );
  }

  function NavGroup({ label, children }) {
    return (
      <div className="sidebar-group">
        <span className="sidebar-group-label">{label}</span>
        <ul className="sidebar-group-nav">
          {children}
        </ul>
      </div>
    );
  }

  return (
    <aside className="sidebar">
      {/* ── Wordmark ── */}
      <div className="sidebar-header">
        <a
          href="#top"
          className="sidebar-logo font-display"
          onClick={(e) => {
            e.preventDefault();
            if (onNavigateHome) onNavigateHome();
          }}
        >
          PropIQ
        </a>
      </div>

      {/* ── Navigation groups ── */}
      <nav aria-label="Dashboard Navigation" style={{ flex: 1 }}>

        <NavGroup label="WORKSPACE">
          <NavItem
            id="dashboard"
            label="Dashboard"
            isActive={activeTab === 'dashboard'}
            onClick={onNavigateDashboard}
          />
          <NavItem
            id="requirements"
            label="Requirements"
            isActive={activeTab === 'requirements'}
            onClick={onNavigateRequirements}
          />
          <NavItem
            id="comparison"
            label="Comparison"
            isActive={activeTab === 'comparison'}
            isLocked={!sessionReady}
            onClick={onNavigateComparison}
          />
        </NavGroup>

        <NavGroup label="INTELLIGENCE">
          <NavItem
            id="risks"
            label="Risks & Contradictions"
            isActive={activeTab === 'risks'}
            isLocked={!sessionReady}
            onClick={onNavigateRisks}
          />
          <NavItem
            id="clarifications"
            label="Clarifications"
            isActive={activeTab === 'clarifications'}
            isLocked={!sessionReady}
            onClick={onNavigateClarifications}
          />
        </NavGroup>

        <NavGroup label="DECISION">
          <NavItem
            id="ranking"
            label="Vendor Ranking"
            isActive={activeTab === 'ranking'}
            isLocked={!sessionReady}
            onClick={onNavigateRanking}
          />
          <NavItem
            id="recommendation"
            label="Recommendation Brief"
            isActive={activeTab === 'recommendation'}
            isLocked={!sessionReady}
            onClick={onNavigateRecommendation}
          />
        </NavGroup>



      </nav>
    </aside>
  );
}
