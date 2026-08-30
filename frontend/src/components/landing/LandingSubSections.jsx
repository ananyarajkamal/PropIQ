import React, { useState } from 'react';

export default function LandingSubSections({ onStart }) {
  const [activeDetail, setActiveDetail] = useState('01');

  const details = [
    {
      num: '01',
      title: 'CONFLICT',
      tag: 'INTRA-VENDOR CONTRADICTIONS',
      desc: 'PropIQ catches discrepancies where executive summaries promise zero commitment but contract terms specify 24-month automatic renewal.',
    },
    {
      num: '02',
      title: 'RISK',
      tag: 'UNFAVORABLE CLAUSES',
      desc: 'Highlight short cancellation notice windows, restrictive liability caps, and unstated termination fees before you sign.',
    },
    {
      num: '03',
      title: 'MISSING',
      tag: 'INFORMATION GAPS',
      desc: 'Automatically flag missing SLA guarantees or unstated liability caps and generate specific questions to send vendors.',
    },
  ];

  return (
    <>
      {/* SECTION 1: FROM PROPOSALS TO PROOF */}
      <section id="how-it-works" className="after-hero-section">
        <div className="container">
          <h2 className="section-editorial-title">
            FROM PROPOSALS
            <br />
            TO PROOF.
          </h2>
          <p className="section-lead-text font-instrument">
            PropIQ standardizes inconsistent vendor language into structured evidence you can compare directly.
          </p>

          <div className="before-after-container">
            {/* Raw Proposal Excerpt */}
            <div className="before-col">
              <div className="before-label">RAW VENDOR PROPOSAL</div>
              <div className="before-raw-box font-sans">
                "Implementation period: 720 hours from project kickoff."
              </div>
            </div>

            {/* PropIQ Structured Interpretation */}
            <div className="after-col">
              <div className="after-label">PROPIQ INTERPRETATION</div>
              <div className="after-propiq-box">
                <div>
                  <span className="font-mono" style={{ fontSize: '0.7rem', color: '#7A7A7A', display: 'block' }}>
                    NORMALIZED VALUE
                  </span>
                  <span className="after-val">30 DAYS</span>
                </div>
                <div>
                  <span className="font-mono" style={{ fontSize: '0.7rem', color: '#7A7A7A', display: 'block' }}>
                    REQUIREMENT (≤ 30 DAYS)
                  </span>
                  <span className="sample-badge" style={{ backgroundColor: '#FFFEFA', color: '#171717', border: '1px solid rgba(23,23,23,0.12)' }}>
                    ✓ MEETS
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: THE DETAILS THAT CHANGE THE DECISION */}
      <section className="after-hero-section">
        <div className="container">
          <h2 className="section-editorial-title">
            THE DETAILS THAT
            <br />
            CHANGE THE DECISION.
          </h2>

          <div className="details-editorial-grid">
            {details.map((item) => (
              <div
                key={item.num}
                className="detail-item-card"
                onMouseEnter={() => setActiveDetail(item.num)}
              >
                <div className="detail-num">{item.num} / {item.title}</div>
                <h3 className="detail-title">{item.tag}</h3>
                <p className="detail-desc">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 3: EVERY VENDOR. ONE CLEAR VIEW. */}
      <section className="after-hero-section">
        <div className="container">
          <h2 className="section-editorial-title">
            EVERY VENDOR.
            <br />
            ONE CLEAR VIEW.
          </h2>

          <div className="product-reveal-card">
            <div className="reveal-topbar">
              <span>PROPIQ WORKSPACE</span>
              <span>LIVE EVALUATION</span>
            </div>

            <div className="reveal-body">
              <table className="results-table font-sans">
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
                    <td><span className="sample-badge" style={{ backgroundColor: '#D9D7E8' }}>$180,000 (MEETS)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4E66A' }}>$195,000 (PARTIAL)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#D9D7E8' }}>$210,000 (MEETS)</span></td>
                  </tr>
                  <tr>
                    <td>Implementation SLA</td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#D9D7E8' }}>30 DAYS (MEETS)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4E66A' }}>45 DAYS (PARTIAL)</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4E66A' }}>60 DAYS (PARTIAL)</span></td>
                  </tr>
                  <tr>
                    <td>Auto-Renewal Window</td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#D9D7E8' }}>60 DAYS NOTICE</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#FF4D3D', color: '#FFFEFA' }}>24 MO AUTO-RENEW</span></td>
                    <td><span className="sample-badge" style={{ backgroundColor: '#F4E66A' }}>15 DAYS NOTICE</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL DARK CTA */}
      <section className="final-cta-dark-section">
        <div className="final-cta-scan-motif" />

        <div className="container final-cta-content">
          <h2 className="final-cta-headline">
            READY TO KNOW
            <br />
            WHAT YOU'RE SIGNING?
          </h2>

          <button
            type="button"
            className="btn-primary"
            onClick={onStart}
            style={{ backgroundColor: '#FFFEFA', color: '#171717' }}
          >
            <span>Analyze proposals</span>
            <span className="btn-arrow">↗</span>
          </button>
        </div>
      </section>
    </>
  );
}
