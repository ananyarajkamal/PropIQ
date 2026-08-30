import React, { useState } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';

export default function VendorDetailsPage({
  factSheetsData,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateComparison,
}) {
  const factSheets = factSheetsData?.vendor_fact_sheets || [];
  const [selectedVendorIdx, setSelectedVendorIdx] = useState(0);
  const [selectedFact, setSelectedFact] = useState(null);

  if (factSheets.length === 0) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="requirements"
          sessionReady={false}
          onNavigateHome={onNavigateHome}
          onNavigateDashboard={onNavigateDashboard}
          onNavigateRequirements={onNavigateRequirements}
          onNavigateComparison={onNavigateComparison}
        />
        <div className="dashboard-content" style={{ padding: '2rem' }}>
          <div className="error-banner">No vendor fact sheets available. Please analyze vendor proposals first.</div>
          <button type="button" className="btn-secondary" onClick={onNavigateRequirements}>
            Go to Requirements
          </button>
        </div>
      </div>
    );
  }

  const activeVendor = factSheets[selectedVendorIdx] || factSheets[0];

  function getStatusBadgeStyle(status) {
    switch (status) {
      case 'FOUND':
        return { bg: '#E8F5E9', label: 'FOUND', icon: '✓' };
      case 'NOT_FOUND':
        return { bg: '#F5F5F0', label: 'NOT FOUND', icon: '—' };
      case 'UNCLEAR':
        return { bg: '#FFF8E1', label: 'UNCLEAR', icon: '?' };
      case 'CONFLICTING':
        return { bg: '#FFEBEE', label: 'CONFLICTING', icon: '!' };
      default:
        return { bg: '#F5F5F0', label: status, icon: '—' };
    }
  }

  return (
    <div className="dashboard-layout">
      {/* Left Sidebar */}
      <Sidebar
        activeTab="requirements"
        sessionReady={true}
        onNavigateHome={onNavigateHome}
        onNavigateDashboard={onNavigateDashboard}
        onNavigateRequirements={onNavigateRequirements}
        onNavigateComparison={onNavigateComparison}
      />

      {/* Main Content Area */}
      <div className="dashboard-content">
        <header className="dashboard-header-bar">
          <h1 className="dashboard-title">Vendor Details & Fact Sheets</h1>
          <p className="dashboard-subtitle">
            Evidence-grounded structured facts extracted directly from vendor proposal PDFs.
          </p>
        </header>

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '2rem 1.5rem' }}>
          {/* Main Area */}
          <div className="main-workspace-col">

            {/* Vendor Selector Tabs */}
            <div className="vendor-tabs-bar" style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
              {factSheets.map((sheet, vIdx) => (
                <button
                  key={vIdx}
                  type="button"
                  className={`btn-secondary ${vIdx === selectedVendorIdx ? 'active-vendor-tab' : ''}`}
                  onClick={() => setSelectedVendorIdx(vIdx)}
                  style={{
                    backgroundColor: vIdx === selectedVendorIdx ? '#1B1D1B' : '#FFFFFF',
                    color: vIdx === selectedVendorIdx ? '#FEF9EC' : '#1B1D1B',
                  }}
                >
                  {sheet.vendor_name} ({sheet.found_count || sheet.categories.length} facts)
                </button>
              ))}
            </div>

            {/* Fact Sheet Grid for Active Vendor */}
            <div className="fact-sheet-card" style={{ backgroundColor: '#FFFFFF', border: '1.5px solid #1B1D1B', borderRadius: '6px', padding: '1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', borderBottom: '1px solid #1B1D1B', paddingBottom: '0.5rem' }}>
                <h2 className="panel-title" style={{ marginBottom: 0 }}>{activeVendor.vendor_name} Fact Sheet</h2>
                <span className="sample-badge">{activeVendor.categories.length} Categories</span>
              </div>

              <div className="categories-facts-grid" style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1rem' }}>
                {activeVendor.categories.map((fact, fIdx) => {
                  const badge = getStatusBadgeStyle(fact.status);
                  return (
                    <div key={fIdx} className="fact-item-box" style={{ border: '1px solid #1B1D1B', borderRadius: '4px', padding: '1rem', backgroundColor: '#FEF9EC' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                        <strong style={{ fontSize: '0.95rem', color: '#1B1D1B', fontFamily: 'Space Mono, monospace' }}>
                          {fact.category}
                        </strong>
                        <span className="fact-status-badge" style={{ backgroundColor: badge.bg }}>
                          <span>{badge.icon}</span>
                          <span>{badge.label}</span>
                        </span>
                      </div>

                      {fact.summary && (
                        <p className="fact-summary-text" style={{ fontSize: '0.9rem', color: '#1B1D1B', marginBottom: '0.35rem' }}>
                          {fact.summary}
                        </p>
                      )}

                      {fact.raw_value && (
                        <div className="fact-raw-value" style={{ fontSize: '0.8rem', color: '#4A4A45', marginBottom: '0.4rem' }}>
                          <strong>Original wording:</strong> "{fact.raw_value}"
                        </div>
                      )}

                      {fact.evidence_citations && fact.evidence_citations.length > 0 && (
                        <button
                          type="button"
                          className="btn-expand-chunk"
                          onClick={() => setSelectedFact({ vendorName: activeVendor.vendor_name, fact })}
                          style={{ marginTop: '0.2rem' }}
                        >
                          View {fact.evidence_citations.length} Citation{fact.evidence_citations.length > 1 ? 's' : ''}
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right SaaS Session Panel Component */}
          <SaasSessionPanel
            proposalsCount={factSheets.length}
            definedVendorsCount={factSheets.length}
            isProcessed={true}
            hasFactSheets={true}
          />
        </div>
      </div>

      {/* Citation Detail Modal */}
      {selectedFact && (
        <div className="drawer-overlay" onClick={() => setSelectedFact(null)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge">{selectedFact.fact.category}</span>
                <h2 className="drawer-title" style={{ marginTop: '0.2rem' }}>
                  {selectedFact.vendorName}
                </h2>
              </div>
              <button type="button" className="btn-remove" onClick={() => setSelectedFact(null)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body">
              <div className="drawer-section">
                <span className="summary-card-title">FACT SUMMARY</span>
                <p className="fact-summary-text" style={{ marginTop: '0.35rem' }}>
                  {selectedFact.fact.summary}
                </p>
              </div>

              {selectedFact.fact.raw_value && (
                <div className="drawer-section">
                  <span className="summary-card-title">ORIGINAL WORDING</span>
                  <div className="fact-raw-value" style={{ marginTop: '0.35rem' }}>
                    "{selectedFact.fact.raw_value}"
                  </div>
                </div>
              )}

              <div className="drawer-section">
                <span className="summary-card-title">PAGE CITATIONS</span>
                <div className="evidence-citations-drawer" style={{ marginTop: '0.5rem' }}>
                  {selectedFact.fact.evidence_citations.map((cit, citIdx) => (
                    <div key={citIdx} className="citation-item-box">
                      <div className="citation-meta-header">
                        <span className="rank-badge">{cit.evidence_id}</span>
                        <strong className="evidence-vendor-name">{cit.vendor_name}</strong>
                        <span className="evidence-citation">
                          {cit.source_filename} — Page {cit.start_page === cit.end_page ? cit.start_page : `${cit.start_page}-${cit.end_page}`}
                        </span>
                      </div>
                      <div className="evidence-excerpt-box" style={{ marginTop: '0.4rem' }}>
                        <p className="evidence-excerpt-text">"{cit.excerpt_text}"</p>
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
