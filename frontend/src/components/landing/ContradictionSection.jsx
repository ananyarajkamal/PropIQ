import React from 'react';

export default function ContradictionSection() {
  return (
    <section className="landing-section contradiction-section">
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-eyebrow font-mono">CONTRADICTION INTELLIGENCE</span>
          <h2 className="section-title">Catch What Looks Fine at First Glance</h2>
          <p className="section-description">
            Important proposal conflicts can appear dozens of pages apart. PropIQ connects
            those statements and surfaces the contradiction with evidence.
          </p>
        </div>

        {/* Illustrative Contradiction Workflow Card */}
        <div className="contradiction-demo-card">
          <div className="demo-header font-mono">
            <span className="demo-title">INTRA-VENDOR STATEMENT COMPARISON</span>
            <span className="sample-badge">ILLUSTRATIVE EXAMPLE</span>
          </div>

          <div className="contradiction-flow-grid">
            {/* Statement A Excerpt */}
            <div className="statement-box statement-a bg-pastel-yellow">
              <div className="statement-header font-mono">
                <span className="doc-section">EXECUTIVE SUMMARY</span>
                <span className="page-num">PAGE 02</span>
              </div>
              <blockquote className="statement-quote font-mono">
                "No long-term commitment."
              </blockquote>
            </div>

            {/* Connecting Visual Element */}
            <div className="flow-connector font-mono">
              <span className="vs-tag">VS</span>
              <span className="connector-arrow font-mono">↓</span>
            </div>

            {/* Statement B Excerpt */}
            <div className="statement-box statement-b bg-pastel-peach">
              <div className="statement-header font-mono">
                <span className="doc-section">COMMERCIAL TERMS</span>
                <span className="page-num">PAGE 14</span>
              </div>
              <blockquote className="statement-quote font-mono">
                "Agreement automatically renews for an additional 24-month term unless cancellation notice is provided 120 days before renewal."
              </blockquote>
            </div>
          </div>

          {/* Surfaced Result Box */}
          <div className="contradiction-result-box">
            <div className="result-header font-mono">
              <span className="result-status-badge font-mono">CONFIRMED CONTRADICTION</span>
              <span className="result-vendor font-mono">Apex Procurement Technologies</span>
            </div>
            <p className="result-summary">
              <strong>Impact:</strong> Conflicting commitment terms detected across proposal sections.
              Executive summary promises zero long-term commitment, but detailed contract terms enforce a 24-month automatic renewal cycle with 120-day notice restrictions.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
