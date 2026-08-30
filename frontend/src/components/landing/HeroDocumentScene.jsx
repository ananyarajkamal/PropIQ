import React, { useState, useEffect, useRef } from 'react';

export default function HeroDocumentScene({ onStart }) {
  const [animState, setAnimState] = useState(1); // 1: Clean, 2: Acid Highlight, 3: Signal Conflict, 4: Decision Reveal
  const [isPlaying, setIsPlaying] = useState(true);
  const [isHovered, setIsHovered] = useState(false);

  const containerRef = useRef(null);

  // Check prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      setIsPlaying(false);
      setAnimState(4);
    }
  }, []);

  // Sequence loop (12s total duration)
  useEffect(() => {
    if (!isPlaying || isHovered) return;

    const timer1 = setTimeout(() => setAnimState(2), 3000);  // 3s: Acid Butter Highlight
    const timer2 = setTimeout(() => setAnimState(3), 6500);  // 6.5s: Signal Red Conflict
    const timer3 = setTimeout(() => setAnimState(4), 9500);  // 9.5s: Decision Brief Reveal
    const timer4 = setTimeout(() => setAnimState(1), 12500); // 12.5s: Loop back to 1

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
    };
  }, [isPlaying, isHovered, animState]);

  return (
    <section className="hero-scene-section">
      <div className="container hero-canvas-grid">
        {/* LEFT: Sophisticated Editorial Headlines */}
        <div className="hero-left-content animate-fade-up">
          <h1 className="hero-sophisticated-headline">
            <span className="headline-light">KNOW WHAT</span>
            <br />
            <span className="headline-bold">THE PROPOSAL</span>
            <br />
            <span className="headline-bold">REALLY SAYS.</span>
          </h1>

          <p className="hero-short-sentence font-instrument">
            PropIQ compares vendor proposals, catches conflicting terms and turns the evidence into a clear decision.
          </p>

          <div>
            <button
              type="button"
              className="btn-primary"
              onClick={onStart}
            >
              <span>Analyze proposals</span>
              <span className="btn-arrow">↗</span>
            </button>
          </div>
        </div>

        {/* RIGHT: THE HERO OBJECT - Swiss Editorial Tactile Artwork */}
        <div
          className="hero-object-viewport"
          ref={containerRef}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <div className="proposal-stack-container" style={{ position: 'relative', width: '100%', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 20px 60px rgba(23,23,23,0.10)' }}>
            {/* Signal Red Vertical Scan Line Motif */}
            {animState !== 4 && <div className="signal-red-scan-line" />}

            {/* High-Resolution Editorial Hero Visual Asset */}
            <img
              src="/propiq_hero_visual.png"
              alt="PropIQ Tactile Vendor Proposal Document Intelligence Artwork"
              style={{ width: '100%', height: 'auto', display: 'block', borderRadius: '8px' }}
            />

            {/* Interactive Dynamic Highlight Overlay for State 2 */}
            {animState === 2 && (
              <div
                className="intelligence-annotation-tag tag-lavender animate-fade-up"
                style={{ top: '35%', right: '8%' }}
              >
                NORMALIZED: 30 DAYS
              </div>
            )}

            {/* Interactive Dynamic Conflict Overlay for State 3 */}
            {animState === 3 && (
              <div
                className="intelligence-annotation-tag tag-signal animate-fade-up"
                style={{ bottom: '25%', left: '15%' }}
              >
                CONFLICT DETECTED
              </div>
            )}

            {/* Interactive Dynamic Decision Reveal Card for State 4 */}
            {animState === 4 && (
              <div className="hero-decision-card-revealed animate-fade-up">
                <div className="decision-card-header">
                  <div>
                    <div className="decision-vendor-name">NORTHSTAR SYSTEMS</div>
                    <span className="sample-badge" style={{ backgroundColor: '#D9D7E8', marginTop: '0.3rem' }}>
                      RECOMMENDED WITH CONDITIONS
                    </span>
                  </div>
                  <div className="decision-score-val">92.4</div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.85rem' }}>
                  <div style={{ backgroundColor: '#F8F6F0', padding: '0.65rem', borderRadius: '4px' }}>
                    <span className="font-mono" style={{ fontSize: '0.65rem', fontWeight: 700, color: '#7A7A7A' }}>WHY</span>
                    <p style={{ fontSize: '0.8rem', marginTop: '0.2rem', color: '#171717' }}>Meets critical requirement SLA</p>
                  </div>
                  <div style={{ backgroundColor: '#F8F6F0', padding: '0.65rem', borderRadius: '4px' }}>
                    <span className="font-mono" style={{ fontSize: '0.65rem', fontWeight: 700, color: '#FF4D3D' }}>WATCH</span>
                    <p style={{ fontSize: '0.8rem', marginTop: '0.2rem', color: '#171717' }}>60-day auto-renewal notice</p>
                  </div>
                  <div style={{ backgroundColor: '#F8F6F0', padding: '0.65rem', borderRadius: '4px' }}>
                    <span className="font-mono" style={{ fontSize: '0.65rem', fontWeight: 700, color: '#171717' }}>CONFIRM</span>
                    <p style={{ fontSize: '0.8rem', marginTop: '0.2rem', color: '#171717' }}>Verify liability cap ($2M)</p>
                  </div>
                </div>
              </div>
            )}

            {/* Unobtrusive Play / Pause Control */}
            <button
              type="button"
              className="unobtrusive-pause-control"
              onClick={() => setIsPlaying(!isPlaying)}
              aria-label={isPlaying ? 'Pause animation' : 'Play animation'}
              style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(255,254,250,0.85)', padding: '0.25rem 0.5rem', borderRadius: '4px', border: '1px solid rgba(23,23,23,0.1)' }}
            >
              {isPlaying ? '⏸' : '▶'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
