import React from 'react';

export default function WorkspacePreviewSection() {
  return (
    <section id="product" className="workspace-preview-section">
      <div className="container">
        <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em' }}>
          04 / PRODUCT PREVIEW
        </span>
        <h2 className="section-editorial-title font-display" style={{ marginTop: '0.5rem' }}>
          THE PROPIQ WORKSPACE.
        </h2>

        <div className="preview-graphic-card">
          <div className="preview-graphic-topbar">
            <span>PROPIQ WORKSPACE · LIVE EVALUATION</span>
            <span>SESSION: PRO-2026-X8</span>
          </div>

          <div className="preview-graphic-layout">
            <div className="preview-main-padding">
              <div className="preview-scores-grid">
                <div className="preview-score-box leading">
                  <div className="score-box-name">NORTHSTAR SYSTEMS</div>
                  <div className="score-box-num">92.4</div>
                  <span className="sample-badge" style={{ marginTop: '0.4rem' }}>RECOMMENDED</span>
                </div>
                <div className="preview-score-box">
                  <div className="score-box-name">MERIDIAN LABS</div>
                  <div className="score-box-num">84.1</div>
                  <span className="sample-badge" style={{ backgroundColor: '#F4C84A', marginTop: '0.4rem' }}>CONDITIONAL</span>
                </div>
                <div className="preview-score-box">
                  <div className="score-box-name">APEX PROCUREMENT</div>
                  <div className="score-box-num">78.5</div>
                  <span className="sample-badge" style={{ backgroundColor: '#EB7096', color: '#FFFFFF', marginTop: '0.4rem' }}>FURTHER REVIEW</span>
                </div>
              </div>

              <table className="preview-matrix-table font-sans">
                <thead>
                  <tr>
                    <th>REQUIREMENT</th>
                    <th>NORTHSTAR SYSTEMS</th>
                    <th>MERIDIAN LABS</th>
                    <th>APEX PROCUREMENT</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Commercial Ceiling</td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#C8D6FF' }}>$180,000 (MEETS)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4C84A' }}>$195,000 (PARTIAL)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#C8D6FF' }}>$210,000 (MEETS)</span></td>
                  </tr>
                  <tr>
                    <td>Implementation SLA</td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#C8D6FF' }}>30 DAYS (MEETS)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4C84A' }}>45 DAYS (PARTIAL)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4C84A' }}>60 DAYS (PARTIAL)</span></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="preview-side-padding">
              <div className="side-indicator-card">
                <div className="indicator-card-title">CONTRADICTIONS</div>
                <div className="indicator-card-val" style={{ color: '#EB7096' }}>1 DETECTED</div>
              </div>

              <div className="side-indicator-card">
                <div className="indicator-card-title font-mono">UNSTATED TERMS</div>
                <div className="indicator-card-val" style={{ color: '#7897FF' }}>2 QUESTIONS</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
