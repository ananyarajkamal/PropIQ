import React from 'react';

/**
 * FeatureGate — PropIQ workflow gate component.
 *
 * Renders a clear, editorial prerequisite empty state
 * inside the requested page when required prerequisites are missing.
 * Does NOT perform silent route redirects.
 */
export default function FeatureGate({
  eyebrow = 'PREREQUISITE REQUIRED',
  title = 'Upload proposals first',
  description,
  ctaLabel = 'Upload Proposals',
  onCta,
}) {
  return (
    <div className="feature-gate-wrapper">
      {/* Mono eyebrow */}
      <span className="feature-gate-eyebrow font-mono">{eyebrow}</span>

      {/* Main heading */}
      <h2 className="feature-gate-heading font-display">
        {title}
      </h2>

      {/* Description */}
      {description && (
        <p className="feature-gate-desc">
          {description}
        </p>
      )}

      {/* CTA */}
      {onCta && (
        <button
          type="button"
          className="btn-primary font-mono feature-gate-cta"
          onClick={onCta}
        >
          <span>{ctaLabel}</span>
          <span className="btn-arrow">↗</span>
        </button>
      )}
    </div>
  );
}

