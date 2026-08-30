import React, { useState, useEffect } from 'react';

export default function HeroSection({ onStart }) {
  const [cycleStep, setCycleStep] = useState(0); // 0: Normalization, 1: Contradiction, 2: Alignment

  // Subtle Content Animation Cycle every 8 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCycleStep((prev) => (prev + 1) % 3);
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="hero-section bg-graph-grid">
      <div className="container hero-asymmetric-grid">
        {/* LEFT: Bold Headline & Call-to-Action */}
        <div className="hero-left-col animate-fade-up">
          <span className="hero-micro-annotation font-mono">01 / PROPOSAL INTELLIGENCE</span>

          <h1 className="hero-bold-headline font-display">
            READ BETWEEN
            <br />
            THE TERMS.
          </h1>

          <p className="hero-sub-copy font-sans">
            PropIQ compares vendor proposals, catches conflicting terms and turns the evidence into a clear decision.
          </p>

          <div>
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

        {/* RIGHT: Art-Directed Asymmetric Overlapping Product Scene */}
        <div className="hero-right-stage">
          {/* Base Layer: Large Pale Blue Panel (#C8D6FF) */}
          <div className="hero-base-pale-panel">
            {/* White Proposal Card (Inside Pale Blue Panel) */}
            <div className="hero-white-proposal-card">
              <div className="proposal-card-vendor font-display">NORTHSTAR SYSTEMS</div>
              <div className="proposal-card-sub font-mono">COMMERCIAL PROPOSAL · SCHEDULE A</div>

              <div className="proposal-row-item">
                <span>Implementation Time:</span>
                <span className="font-mono" style={{ fontWeight: 700 }}>720 HOURS</span>
              </div>
              <div className="proposal-row-item">
                <span>SLA Uptime Guarantee:</span>
                <span className="font-mono" style={{ fontWeight: 700 }}>99.9%</span>
              </div>
              <div className="proposal-row-item">
                <span>Renewal Term:</span>
                <span className="font-mono" style={{ fontWeight: 700 }}>AUTOMATIC</span>
              </div>
            </div>

            {/* Overlapping Tag 1: Pink Contradiction Card (Overlaps bottom edge) */}
            <div
              className={`overlay-pink-contradiction-card ${
                cycleStep === 1 ? 'animate-fade-up' : ''
              }`}
            >
              <span className="pink-card-tag">CONTRADICTION DETECTED</span>
              <p className="pink-card-text">
                "No long-term commitment" vs "Renews for 24 months"
              </p>
            </div>

            {/* Overlapping Tag 2: Yellow Normalization Tag (Overlaps top-right) */}
            <div
              className={`overlay-yellow-normalization-tag ${
                cycleStep === 0 ? 'animate-fade-up' : ''
              }`}
            >
              720 HOURS → 30 DAYS
            </div>

            {/* Overlapping Tag 3: Cornflower Decision Tag (Overlaps left edge) */}
            <div
              className={`overlay-cornflower-decision-tag ${
                cycleStep === 2 ? 'animate-fade-up' : ''
              }`}
            >
              92.4 ALIGNMENT
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
