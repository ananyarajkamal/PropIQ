import React from 'react';

export default function NormalizationSection() {
  return (
    <section className="landing-section normalization-section">
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-eyebrow font-mono">NORMALIZED COMPARISON</span>
          <h2 className="section-title">Compare Terms on the Same Basis</h2>
          <p className="section-description">
            PropIQ normalizes comparable commercial and technical values before evaluating
            vendor alignment against your procurement requirements.
          </p>
        </div>

        {/* Concrete Normalization Step Visual Flow */}
        <div className="normalization-flow-card">
          <div className="flow-card-header font-mono">
            <span>AUTOMATED TERMINOLOGY NORMALIZATION</span>
            <span className="sample-badge">ILLUSTRATIVE EXAMPLE</span>
          </div>

          <div className="norm-steps-row">
            {/* Step 1: Raw Vendor Proposal Text */}
            <div className="norm-step-box">
              <span className="norm-step-label font-mono">VENDOR PROPOSAL</span>
              <span className="norm-value-display raw font-mono">720 hours</span>
              <span className="norm-step-note">Unstandardized proposal term</span>
            </div>

            {/* Arrow */}
            <div className="norm-flow-arrow font-mono">↓</div>

            {/* Step 2: Normalized Value */}
            <div className="norm-step-box bg-pastel-sage">
              <span className="norm-step-label font-mono">NORMALIZED</span>
              <span className="norm-value-display norm font-mono">30 days</span>
              <span className="norm-step-note">Standardized duration unit</span>
            </div>

            {/* Arrow */}
            <div className="norm-flow-arrow font-mono">↓</div>

            {/* Step 3: Buyer Requirement */}
            <div className="norm-step-box">
              <span className="norm-step-label font-mono">YOUR REQUIREMENT</span>
              <span className="norm-value-display req font-mono">Max 30 days</span>
              <span className="norm-step-note">Configured deployment ceiling</span>
            </div>

            {/* Arrow */}
            <div className="norm-flow-arrow font-mono">↓</div>

            {/* Step 4: Comparison Result */}
            <div className="norm-step-box bg-pastel-sage result font-mono">
              <span className="norm-step-label font-mono">RESULT</span>
              <span className="meets-badge font-mono">MEETS</span>
              <span className="norm-step-note">Requirements Compliant</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
