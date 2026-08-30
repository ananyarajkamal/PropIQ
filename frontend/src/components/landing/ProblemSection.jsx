import React from 'react';

export default function ProblemSection() {
  return (
    <section className="landing-section problem-section">
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-eyebrow font-mono">THE PROBLEM</span>
          <h2 className="section-title">
            Vendor Proposals Shouldn't Take Hours to Compare
          </h2>
          <p className="section-description">
            Procurement teams receive proposals with different pricing structures,
            timelines, service commitments, and contractual terms. Important differences
            can be buried across dozens of pages and expressed in completely different ways.
          </p>
        </div>

        {/* 3 Focused Problem Editorial Blocks */}
        <div className="problem-grid">
          {/* Problem Block 01 */}
          <div className="problem-card bg-pastel-yellow">
            <div className="problem-card-header">
              <span className="problem-number font-mono">01</span>
              <span className="problem-tag font-mono">TERMINOLOGY GAP</span>
            </div>
            <h3 className="problem-card-heading">Different Terminology</h3>
            <p className="problem-card-body">
              One vendor might quote an implementation period in hours while another uses
              days or weeks. Manual comparison requires teams to normalize those values themselves.
            </p>
          </div>

          {/* Problem Block 02 */}
          <div className="problem-card bg-pastel-peach">
            <div className="problem-card-header">
              <span className="problem-number font-mono">02</span>
              <span className="problem-tag font-mono">LEGAL BLINDSPOTS</span>
            </div>
            <h3 className="problem-card-heading">Hidden Contract Risks</h3>
            <p className="problem-card-body">
              Renewal, liability, termination, support, and payment conditions may appear
              far away from the executive summary, hiding long-term commitments.
            </p>
          </div>

          {/* Problem Block 03 */}
          <div className="problem-card bg-pastel-blue">
            <div className="problem-card-header">
              <span className="problem-number font-mono">03</span>
              <span className="problem-tag font-mono">INFORMATION GAPS</span>
            </div>
            <h3 className="problem-card-heading">Missing Information</h3>
            <p className="problem-card-body">
              Important information may simply be absent or ambiguous, leaving procurement
              teams to manually determine what they need to ask each vendor.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
