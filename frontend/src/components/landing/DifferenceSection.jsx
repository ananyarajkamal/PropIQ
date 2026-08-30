import React from 'react';

export default function DifferenceSection() {
  const genericFeatures = [
    'Summarizes documents',
    'Answers basic questions',
    'Extracts unstructured text',
    'Generates text explanations',
  ];

  const propiqFeatures = [
    'Normalizes vendor terminology',
    'Checks requirements consistently',
    'Detects contradictions',
    'Flags contractual concerns',
    'Identifies missing information',
    'Generates clarification questions',
    'Scores vendors deterministically',
    'Links findings back to evidence',
    'Produces a structured recommendation',
  ];

  return (
    <section id="why-propiq" className="landing-section difference-section">
      <div className="container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-eyebrow font-mono">WHY PROPIQ</span>
          <h2 className="section-title">Not Just Another AI PDF Summarizer</h2>
          <p className="section-description">
            Summarizing a proposal is useful. Procurement decisions require more than a summary.
          </p>
        </div>

        {/* Side-by-Side Comparison Box */}
        <div className="difference-comparison-grid">
          {/* Left: Typical Document AI */}
          <div className="diff-card diff-generic">
            <div className="diff-card-header">
              <span className="diff-card-title font-mono">TYPICAL DOCUMENT AI</span>
              <span className="diff-badge generic font-mono">GENERIC SUMMARY</span>
            </div>
            <ul className="diff-list">
              {genericFeatures.map((feat) => (
                <li key={feat} className="diff-item generic-item">
                  <span className="diff-icon font-mono">•</span>
                  <span>{feat}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Right: PropIQ (Visually Stronger) */}
          <div className="diff-card diff-propiq">
            <div className="diff-card-header">
              <span className="diff-card-title font-mono">PROPIQ</span>
              <span className="diff-badge propiq font-mono">DECISION ENGINE</span>
            </div>
            <ul className="diff-list">
              {propiqFeatures.map((feat) => (
                <li key={feat} className="diff-item propiq-item">
                  <span className="diff-check font-mono">✓</span>
                  <span>{feat}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
