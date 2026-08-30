import React from 'react';

export default function WorkflowSection() {
  const steps = [
    {
      num: '01',
      title: 'UPLOAD',
      desc: 'Drop 2+ vendor proposals (PDF) into the secure processing workspace.',
      colorClass: 'pink',
    },
    {
      num: '02',
      title: 'REQUIREMENTS',
      desc: 'Define critical commercial, technical, and SLA thresholds.',
      colorClass: 'yellow',
    },
    {
      num: '03',
      title: 'ANALYZE',
      desc: 'PropIQ extracts terms, catches contradictions, and flags unstated risks.',
      colorClass: 'blue',
    },
    {
      num: '04',
      title: 'DECIDE',
      desc: 'Receive an evidence-backed ranking and executive recommendation brief.',
      colorClass: 'pale',
    },
  ];

  return (
    <section id="workflow" className="workflow-section">
      <div className="container">
        <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em' }}>
          02 / WORKFLOW
        </span>
        <h2 className="section-editorial-title font-display" style={{ marginTop: '0.5rem' }}>
          HOW IT WORKS.
        </h2>

        <div className="timeline-horizontal-container">
          <div className="timeline-steps-grid">
            {steps.map((step) => (
              <div key={step.num} className="timeline-step-item">
                <div className={`step-oversized-num ${step.colorClass}`}>
                  {step.num}
                </div>
                <h3 className="step-item-title">{step.title}</h3>
                <p className="step-item-desc">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
