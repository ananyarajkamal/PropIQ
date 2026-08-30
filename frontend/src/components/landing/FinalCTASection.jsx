import React from 'react';

export default function FinalCTASection({ onStart }) {
  return (
    <section className="final-cta-section">
      <div className="final-cta-split-grid">
        {/* Left Side: Yellow Background */}
        <div className="cta-left-yellow">
          <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', marginBottom: '1rem' }}>
            READY TO START?
          </span>
          <h2 className="cta-huge-title">
            READ BETWEEN
            <br />
            THE TERMS.
          </h2>
        </div>

        {/* Right Side: Near-Black Ink Background */}
        <div className="cta-right-ink">
          <p className="cta-sub-copy font-sans">
            Upload your vendor proposals now to extract requirements, catch hidden contradictions, and generate an evidence-backed recommendation.
          </p>

          <button
            type="button"
            className="btn-primary"
            onClick={onStart}
          >
            <span>START ANALYZING PROPOSALS</span>
            <span className="btn-arrow">↗</span>
          </button>
        </div>
      </div>
    </section>
  );
}
