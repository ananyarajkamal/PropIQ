import React, { useState, useEffect, useRef } from 'react';

const STAGE_INTERVAL_MS = 5500;

export default function ProductStoryStage({ onStart }) {
  const [activeStateIndex, setActiveStateIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [progress, setProgress] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const stageRef = useRef(null);

  const states = [
    {
      id: 'compare',
      num: '01',
      title: 'COMPARE',
      caption: 'Different proposals. One comparable view.',
      accentColor: '#7897FF', // Cornflower
      bgClass: 'stage-bg-cornflower',
    },
    {
      id: 'detect',
      num: '02',
      title: 'DETECT',
      caption: "PropIQ surfaces what doesn't add up.",
      accentColor: '#F06B91', // Pink
      bgClass: 'stage-bg-pink',
    },
    {
      id: 'clarify',
      num: '03',
      title: 'CLARIFY',
      caption: 'Missing information becomes the next question.',
      accentColor: '#C8D6FF', // Powder Blue
      bgClass: 'stage-bg-powder',
    },
    {
      id: 'decide',
      num: '04',
      title: 'DECIDE',
      caption: 'A decision backed by the evidence.',
      accentColor: '#7897FF', // Cornflower & Ink
      bgClass: 'stage-bg-ink',
    },
  ];

  // Check prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      setIsPlaying(false);
    }
  }, []);

  // Autoplay and Progress Timer Effect
  useEffect(() => {
    let animationFrameId;
    let startTime = null;

    const shouldPause = !isPlaying || isHovered || isFocused;

    if (shouldPause) {
      setProgress(0);
      return;
    }

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const pct = Math.min(100, (elapsed / STAGE_INTERVAL_MS) * 100);
      setProgress(pct);

      if (elapsed >= STAGE_INTERVAL_MS) {
        setActiveStateIndex((prev) => (prev + 1) % states.length);
        startTime = null;
        setProgress(0);
      } else {
        animationFrameId = requestAnimationFrame(step);
      }
    }

    animationFrameId = requestAnimationFrame(step);

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [isPlaying, isHovered, isFocused, activeStateIndex]);

  // Keyboard navigation listener
  function handleKeyDown(e) {
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      setActiveStateIndex((prev) => (prev + 1) % states.length);
      setProgress(0);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      setActiveStateIndex((prev) => (prev - 1 + states.length) % states.length);
      setProgress(0);
    } else if (e.key === ' ') {
      e.preventDefault();
      setIsPlaying((prev) => !prev);
    }
  }

  const currentState = states[activeStateIndex];

  return (
    <section
      className="one-viewport-stage-section"
      ref={stageRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      aria-label="Interactive Product Story Stage"
      role="region"
    >
      <div className="container stage-container-grid">
        {/* LEFT COLUMN: Stable Brand Statement & Main CTA */}
        <div className="stage-left-column">
          <h1 className="stage-main-headline font-display">
            READ BETWEEN
            <br />
            THE TERMS.
          </h1>

          <p className="stage-sub-paragraph font-sans">
            PropIQ turns complex vendor proposals into clear, evidence-backed decisions.
          </p>

          <div className="stage-cta-wrapper">
            <button
              type="button"
              className="btn-primary btn-yellow-cta"
              onClick={onStart}
            >
              <span>START ANALYZING PROPOSALS ↗</span>
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: Interactive Product Story Stage */}
        <div className="stage-right-column">
          <div className={`product-stage-card ${currentState.bgClass}`}>
            {/* Stage Header Indicator */}
            <div className="stage-card-topbar font-mono">
              <div className="topbar-left">
                <span className="stage-num-tag">{currentState.num} /</span>
                <span className="stage-title-tag">{currentState.title}</span>
              </div>
              <span className="stage-live-badge">PRODUCT WORKFLOW</span>
            </div>

            {/* STAGE STATE CONTENT (500ms Crossfade) */}
            <div className="stage-viewport-body">
              {/* STATE 01: COMPARE */}
              {activeStateIndex === 0 && (
                <div className="stage-state-content animate-fade-up">
                  <div className="compare-preview-surface">
                    <div className="compare-sheets-header font-mono">
                      <span>3 PROPOSALS STANDARDIZED</span>
                    </div>

                    <table className="compare-interactive-matrix font-mono">
                      <thead>
                        <tr>
                          <th>CRITERIA</th>
                          <th>NORTHSTAR</th>
                          <th>MERIDIAN</th>
                          <th>APEX</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr>
                          <td>COMMERCIAL PRICE</td>
                          <td><span className="matrix-status meets">✓ $180K</span></td>
                          <td><span className="matrix-status meets">✓ $195K</span></td>
                          <td><span className="matrix-status meets">✓ $210K</span></td>
                        </tr>
                        <tr>
                          <td>TIMELINE SLA</td>
                          <td><span className="matrix-status meets">✓ 30 DAYS</span></td>
                          <td><span className="matrix-status partial">! 45 DAYS</span></td>
                          <td><span className="matrix-status partial">! 60 DAYS</span></td>
                        </tr>
                        <tr>
                          <td>UPTIME GUARANTEE</td>
                          <td><span className="matrix-status meets">✓ 99.9%</span></td>
                          <td><span className="matrix-status meets">✓ 99.5%</span></td>
                          <td><span className="matrix-status missing">? UNSTATED</span></td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* STATE 02: DETECT */}
              {activeStateIndex === 1 && (
                <div className="stage-state-content animate-fade-up">
                  <div className="detect-preview-surface">
                    <div className="detect-excerpt-box">
                      <div className="excerpt-label font-mono">EXECUTIVE SUMMARY (PAGE 2)</div>
                      <div className="excerpt-quote font-sans">"No long-term commitment required."</div>
                    </div>

                    {/* Pink Contradiction Tag */}
                    <div className="detect-contradiction-tag font-mono">
                      <span>CONTRADICTION DETECTED</span>
                    </div>

                    <div className="detect-excerpt-box">
                      <div className="excerpt-label font-mono">COMMERCIAL TERMS (PAGE 14)</div>
                      <div className="excerpt-quote font-sans">"Agreement automatically renews for a further 24-month term."</div>
                    </div>
                  </div>
                </div>
              )}

              {/* STATE 03: CLARIFY */}
              {activeStateIndex === 2 && (
                <div className="stage-state-content animate-fade-up">
                  <div className="clarify-preview-surface">
                    <div className="clarify-gap-box font-mono">
                      <span className="gap-tag">UNSTATED TERM</span>
                      <span className="gap-val">LIABILITY CAP: NOT SPECIFIED</span>
                    </div>

                    <div className="clarify-question-card font-mono">
                      <div className="question-header">ASK THE VENDOR ↗</div>
                      <p className="question-text font-sans">
                        "Please confirm the maximum aggregate liability applicable under the agreement."
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* STATE 04: DECIDE */}
              {activeStateIndex === 3 && (
                <div className="stage-state-content animate-fade-up">
                  <div className="decide-preview-surface font-mono">
                    <div className="decide-header-row">
                      <div>
                        <div className="decide-vendor-name font-display">NORTHSTAR SYSTEMS</div>
                        <span className="sample-badge" style={{ backgroundColor: '#7897FF', color: '#FFFFFF' }}>
                          RECOMMENDED WITH CONDITIONS
                        </span>
                      </div>
                      <div className="decide-score font-display">92.4</div>
                    </div>

                    <div className="decide-brief-grid">
                      <div className="brief-col">
                        <span className="brief-label">WHY</span>
                        <p className="brief-val">Strongest requirement alignment & SLA uptime</p>
                      </div>
                      <div className="brief-col">
                        <span className="brief-label">WATCH</span>
                        <p className="brief-val">60-day auto-renewal notice window</p>
                      </div>
                      <div className="brief-col">
                        <span className="brief-label">BEFORE PROCEEDING</span>
                        <p className="brief-val">Confirm aggregate liability cap ($2M)</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Stage Caption Footnote */}
            <div className="stage-card-footer font-mono">
              <span className="stage-caption font-sans">{currentState.caption}</span>
            </div>
          </div>

          {/* BOTTOM INTERACTIVE STAGE NAVIGATION */}
          <div className="stage-nav-bar font-mono" role="tablist">
            <div className="stage-tabs-list">
              {states.map((st, idx) => {
                const isActive = idx === activeStateIndex;
                return (
                  <button
                    key={st.id}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    className={`stage-tab-btn ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      setActiveStateIndex(idx);
                      setProgress(0);
                    }}
                  >
                    <span>{st.num} {st.title}</span>
                    {isActive && (
                      <div
                        className="tab-progress-line"
                        style={{ width: `${progress}%` }}
                      />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Play / Pause Toggle Button */}
            <button
              type="button"
              className="stage-pause-btn"
              onClick={() => setIsPlaying(!isPlaying)}
              aria-label={isPlaying ? 'Pause auto transition' : 'Play auto transition'}
            >
              {isPlaying ? '⏸ PAUSE' : '▶ PLAY'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
