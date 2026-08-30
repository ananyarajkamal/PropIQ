import React from 'react';

export default function CapabilitiesSection() {
  return (
    <section id="intelligence" className="capabilities-section">
      <div className="container">
        <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em' }}>
          03 / CORE INTELLIGENCE
        </span>
        <h2 className="section-editorial-title font-display" style={{ marginTop: '0.5rem' }}>
          EVERY DETAIL EXPOSED.
        </h2>

        <div className="asymmetric-cap-grid">
          {/* Block 1: COMPARE (Large White Block) */}
          <div className="cap-asymmetric-block cap-block-compare">
            <span className="cap-block-num">01 / MATRIX</span>
            <div>
              <h3 className="cap-block-title">COMPARE</h3>
              <p className="cap-block-desc">
                Standardize non-uniform proposal terms, pricing models, and SLA commitments into one unified side-by-side matrix.
              </p>
            </div>
          </div>

          {/* Block 2: DETECT (Narrow Pink Block) */}
          <div className="cap-asymmetric-block cap-block-detect">
            <span className="cap-block-num">02 / RISKS</span>
            <div>
              <h3 className="cap-block-title">DETECT</h3>
              <p className="cap-block-desc">
                Surface intra-document contradictions and hidden auto-renewal traps before signing.
              </p>
            </div>
          </div>

          {/* Block 3: CLARIFY (Medium Pale Blue Block) */}
          <div className="cap-asymmetric-block cap-block-clarify">
            <span className="cap-block-num">03 / GAPS</span>
            <div>
              <h3 className="cap-block-title">CLARIFY</h3>
              <p className="cap-block-desc">
                Identify missing liability caps or unstated terms and generate targeted vendor questions.
              </p>
            </div>
          </div>

          {/* Block 4: DECIDE (Wide Yellow Block) */}
          <div className="cap-asymmetric-block cap-block-decide">
            <span className="cap-block-num">04 / DECISION</span>
            <div>
              <h3 className="cap-block-title">DECIDE</h3>
              <p className="cap-block-desc">
                Produce executive decision briefs backed by exact page citations and evidence.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
