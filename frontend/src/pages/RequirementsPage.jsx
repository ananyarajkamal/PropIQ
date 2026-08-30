import React, { useState, useEffect } from 'react';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';
import FeatureGate from '../components/FeatureGate';
import { saveRequirements } from '../services/api';

/* ─────────── Importance color map ─────────── */
const IMPORTANCE_STYLES = {
  MUST_HAVE: { label: 'Must Have', bg: '#EB7096', color: '#FFFFFF', border: '#C45A7A' },
  HIGH:      { label: 'High',      bg: '#F4C84A', color: '#171717', border: '#C99A2E' },
  MEDIUM:    { label: 'Medium',    bg: '#C8D6FF', color: '#171717', border: '#8EA5E0' },
  LOW:       { label: 'Low',       bg: '#F7F3EA', color: '#6A6A60', border: '#C4BFB4' },
};

/* ─────────── Shared input / select styles ─────────── */
const INPUT_BASE = {
  height: '46px',
  border: '1.5px solid #171717',
  borderRadius: '4px',
  background: '#FFFFFF',
  padding: '0 14px',
  fontSize: '0.925rem',
  fontFamily: "'DM Sans', sans-serif",
  color: '#171717',
  width: '100%',
  outline: 'none',
  boxSizing: 'border-box',
};

const SELECT_BASE = {
  ...INPUT_BASE,
  appearance: 'none',
  WebkitAppearance: 'none',
  backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23171717' d='M6 8L1 3h10z'/%3E%3C/svg%3E\")",
  backgroundRepeat: 'no-repeat',
  backgroundPosition: 'right 12px center',
  paddingRight: '32px',
  cursor: 'pointer',
};

const LABEL_STYLE = {
  display: 'block',
  fontSize: '0.8rem',
  fontWeight: 700,
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
  color: '#171717',
  marginBottom: '6px',
  fontFamily: "'DM Sans', sans-serif",
};

const HELPER_STYLE = {
  fontSize: '0.75rem',
  color: '#6A6A60',
  marginTop: '4px',
  fontFamily: "'DM Sans', sans-serif",
};

/* ─────────── Sub-components ─────────── */

function ImportanceSelector({ value, onChange, id, disabled }) {
  const style = IMPORTANCE_STYLES[value] || IMPORTANCE_STYLES.MEDIUM;
  return (
    <div style={{ marginTop: '12px' }}>
      <span style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6A6A60', marginBottom: '5px', fontFamily: "'Space Mono', monospace" }}>
        IMPORTANCE
      </span>
      <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          style={{
            ...SELECT_BASE,
            height: '38px',
            fontSize: '0.8rem',
            fontWeight: 700,
            backgroundColor: style.bg,
            color: style.color,
            border: `1.5px solid ${style.border}`,
            borderRadius: '4px',
          }}
        >
          <option value="MUST_HAVE">Must Have</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>
    </div>
  );
}

function ReqCell({ children }) {
  return (
    <div style={{
      padding: '24px',
      borderBottom: '1.5px solid #171717',
      borderRight: '1.5px solid #171717',
      background: '#FFFFFF',
    }}>
      {children}
    </div>
  );
}

function SectionHeader({ num, title, subtitle, accentColor }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: '1.25rem',
      marginBottom: '0px',
      borderBottom: '2px solid #171717',
      background: '#F7F3EA',
      padding: '20px 24px',
    }}>
      <div style={{
        minWidth: '44px',
        height: '44px',
        background: accentColor,
        border: '2px solid #171717',
        borderRadius: '4px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'Space Mono', monospace",
        fontWeight: 700,
        fontSize: '1rem',
        color: accentColor === '#F4C84A' ? '#171717' : '#FFFFFF',
        flexShrink: 0,
        boxShadow: '2px 2px 0 #171717',
      }}>
        {num}
      </div>
      <div>
        <h3 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: '1.15rem', color: '#171717', margin: '0 0 2px 0', textTransform: 'uppercase', letterSpacing: '-0.01em' }}>
          {title}
        </h3>
        <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: '0.875rem', color: '#6A6A60', margin: 0 }}>
          {subtitle}
        </p>
      </div>
    </div>
  );
}

/* ─────────── Compound Input Components ─────────── */

function CompoundCurrencyInput({ currency, onCurrencyChange, value, onValueChange, placeholder, disabled, id }) {
  return (
    <div style={{ display: 'flex', border: '1.5px solid #171717', borderRadius: '4px', overflow: 'hidden', background: '#FFFFFF' }}>
      <select
        id={`${id}-currency`}
        value={currency}
        onChange={(e) => onCurrencyChange(e.target.value)}
        disabled={disabled}
        style={{
          height: '46px',
          border: 'none',
          borderRight: '1.5px solid #171717',
          padding: '0 10px 0 12px',
          fontSize: '0.85rem',
          fontWeight: 700,
          fontFamily: "'DM Sans', sans-serif",
          background: '#F7F3EA',
          color: '#171717',
          cursor: 'pointer',
          appearance: 'none',
          WebkitAppearance: 'none',
          minWidth: '90px',
          backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 12 12'%3E%3Cpath fill='%23171717' d='M6 8L1 3h10z'/%3E%3C/svg%3E\")",
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 8px center',
          paddingRight: '22px',
          outline: 'none',
        }}
      >
        <option value="USD">USD ($)</option>
        <option value="EUR">EUR (€)</option>
        <option value="GBP">GBP (£)</option>
        <option value="INR">INR (₹)</option>
      </select>
      <input
        id={id}
        type="number"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        disabled={disabled}
        style={{ ...INPUT_BASE, height: '46px', border: 'none', borderRadius: '0', flex: 1 }}
      />
    </div>
  );
}

function CompoundValueUnitInput({ value, onValueChange, unit, onUnitChange, valuePlaceholder, unitOptions, disabled, id }) {
  return (
    <div style={{ display: 'flex', border: '1.5px solid #171717', borderRadius: '4px', overflow: 'hidden', background: '#FFFFFF' }}>
      <input
        id={id}
        type="number"
        placeholder={valuePlaceholder}
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        disabled={disabled}
        style={{ ...INPUT_BASE, height: '46px', border: 'none', borderRadius: '0', flex: 1 }}
      />
      <select
        id={`${id}-unit`}
        value={unit}
        onChange={(e) => onUnitChange(e.target.value)}
        disabled={disabled}
        style={{
          height: '46px',
          border: 'none',
          borderLeft: '1.5px solid #171717',
          padding: '0 10px 0 12px',
          fontSize: '0.85rem',
          fontWeight: 700,
          fontFamily: "'DM Sans', sans-serif",
          background: '#F7F3EA',
          color: '#171717',
          cursor: 'pointer',
          appearance: 'none',
          WebkitAppearance: 'none',
          minWidth: '95px',
          backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 12 12'%3E%3Cpath fill='%23171717' d='M6 8L1 3h10z'/%3E%3C/svg%3E\")",
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 8px center',
          paddingRight: '22px',
          outline: 'none',
        }}
      >
        {unitOptions.map((u) => (
          <option key={u.value} value={u.value}>{u.label}</option>
        ))}
      </select>
    </div>
  );
}

function SlaInput({ value, onValueChange, disabled, id }) {
  return (
    <div style={{ display: 'flex', border: '1.5px solid #171717', borderRadius: '4px', overflow: 'hidden', background: '#FFFFFF', alignItems: 'center' }}>
      <input
        id={id}
        type="number"
        step="0.01"
        placeholder="99.9"
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        disabled={disabled}
        style={{ ...INPUT_BASE, height: '46px', border: 'none', borderRadius: '0', flex: 1 }}
      />
      <span style={{ padding: '0 14px', fontWeight: 700, fontSize: '0.9rem', color: '#6A6A60', fontFamily: "'Space Mono', monospace", borderLeft: '1.5px solid #171717', background: '#F7F3EA', height: '46px', display: 'flex', alignItems: 'center' }}>%</span>
    </div>
  );
}

/* ─────────── Main Page Component ─────────── */

export default function RequirementsPage({
  sessionId,
  proposals,
  requirements = null,
  onNavigateHome,
  onNavigateDashboard,
  onNavigateRequirements,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
  onExtractionComplete,
  onSaveRequirements,
}) {

  // Form State for Procurement Requirements & Priorities (Default: MEDIUM)
  const [budgetCeiling, setBudgetCeiling] = useState('');
  const [budgetCurrency, setBudgetCurrency] = useState('USD');
  const [budgetPriority, setBudgetPriority] = useState('MEDIUM');

  const [timelineValue, setTimelineValue] = useState('');
  const [timelineUnit, setTimelineUnit] = useState('days');
  const [timelinePriority, setTimelinePriority] = useState('MEDIUM');

  const [minimumSla, setMinimumSla] = useState('');
  const [slaPriority, setSlaPriority] = useState('MEDIUM');

  const [paymentTerms, setPaymentTerms] = useState('');
  const [paymentPriority, setPaymentPriority] = useState('MEDIUM');

  const [certificationsText, setCertificationsText] = useState('');
  const [certificationsPriority, setCertificationsPriority] = useState('MEDIUM');

  const [warrantyValue, setWarrantyValue] = useState('');
  const [warrantyUnit, setWarrantyUnit] = useState('months');
  const [warrantyPriority, setWarrantyPriority] = useState('MEDIUM');

  const [liabilityRequirement, setLiabilityRequirement] = useState('');
  const [liabilityPriority, setLiabilityPriority] = useState('MEDIUM');

  const [renewalPreference, setRenewalPreference] = useState('');
  const [renewalPriority, setRenewalPriority] = useState('MEDIUM');

  const [terminationRequirement, setTerminationRequirement] = useState('');
  const [terminationPriority, setTerminationPriority] = useState('MEDIUM');

  const [supportRequirement, setSupportRequirement] = useState('');
  const [supportPriority, setSupportPriority] = useState('MEDIUM');

  const [customReq1, setCustomReq1] = useState('');
  const [customPrio1, setCustomPrio1] = useState('MEDIUM');
  const [customReq2, setCustomReq2] = useState('');
  const [customPrio2, setCustomPrio2] = useState('MEDIUM');
  const [customReq3, setCustomReq3] = useState('');
  const [customPrio3, setCustomPrio3] = useState('MEDIUM');

  // Hydrate saved requirements values if passed from parent
  useEffect(() => {
    if (requirements) {
      if (requirements.budget_ceiling !== undefined && requirements.budget_ceiling !== null) {
        setBudgetCeiling(String(requirements.budget_ceiling));
      }
      if (requirements.budget_currency) setBudgetCurrency(requirements.budget_currency);
      if (requirements.budget_priority) setBudgetPriority(requirements.budget_priority);

      if (requirements.timeline_value !== undefined && requirements.timeline_value !== null) {
        setTimelineValue(String(requirements.timeline_value));
      }
      if (requirements.timeline_unit) setTimelineUnit(requirements.timeline_unit);
      if (requirements.timeline_priority) setTimelinePriority(requirements.timeline_priority);

      if (requirements.minimum_sla !== undefined && requirements.minimum_sla !== null) {
        setMinimumSla(String(requirements.minimum_sla));
      }
      if (requirements.sla_priority) setSlaPriority(requirements.sla_priority);

      if (requirements.payment_terms) setPaymentTerms(requirements.payment_terms);
      if (requirements.payment_priority) setPaymentPriority(requirements.payment_priority);

      if (requirements.certifications && Array.isArray(requirements.certifications)) {
        setCertificationsText(requirements.certifications.join(', '));
      }
      if (requirements.certifications_priority) setCertificationsPriority(requirements.certifications_priority);

      if (requirements.warranty_value !== undefined && requirements.warranty_value !== null) {
        setWarrantyValue(String(requirements.warranty_value));
      }
      if (requirements.warranty_unit) setWarrantyUnit(requirements.warranty_unit);
      if (requirements.warranty_priority) setWarrantyPriority(requirements.warranty_priority);

      if (requirements.liability_requirement) setLiabilityRequirement(requirements.liability_requirement);
      if (requirements.liability_priority) setLiabilityPriority(requirements.liability_priority);

      if (requirements.renewal_preference) setRenewalPreference(requirements.renewal_preference);
      if (requirements.renewal_priority) setRenewalPriority(requirements.renewal_priority);

      if (requirements.termination_requirement) setTerminationRequirement(requirements.termination_requirement);
      if (requirements.termination_priority) setTerminationPriority(requirements.termination_priority);

      if (requirements.support_requirement) setSupportRequirement(requirements.support_requirement);
      if (requirements.support_priority) setSupportPriority(requirements.support_priority);

      if (requirements.custom_requirements && Array.isArray(requirements.custom_requirements)) {
        if (requirements.custom_requirements[0]) setCustomReq1(requirements.custom_requirements[0]);
        if (requirements.custom_requirements[1]) setCustomReq2(requirements.custom_requirements[1]);
        if (requirements.custom_requirements[2]) setCustomReq3(requirements.custom_requirements[2]);
      }
      if (requirements.custom_priorities && Array.isArray(requirements.custom_priorities)) {
        if (requirements.custom_priorities[0]) setCustomPrio1(requirements.custom_priorities[0]);
        if (requirements.custom_priorities[1]) setCustomPrio2(requirements.custom_priorities[1]);
        if (requirements.custom_priorities[2]) setCustomPrio3(requirements.custom_priorities[2]);
      }
    }
  }, [requirements]);


  // UI Processing & Error State
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);

  // Helper to parse comma-separated certifications string
  function parseCertifications(input) {
    if (!input || !input.trim()) return [];
    return input
      .split(',')
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }

  // Pre-fill sample values locally (Zero Groq calls)
  function handleFillSampleValues() {
    setBudgetCeiling('200000');
    setBudgetCurrency('USD');
    setBudgetPriority('HIGH');

    setTimelineValue('30');
    setTimelineUnit('days');
    setTimelinePriority('HIGH');

    setMinimumSla('99.5');
    setSlaPriority('MUST_HAVE');

    setPaymentTerms('Net 30');
    setPaymentPriority('MEDIUM');

    setCertificationsText('SOC 2 Type II, ISO 27001');
    setCertificationsPriority('MUST_HAVE');

    setWarrantyValue('12');
    setWarrantyUnit('months');
    setWarrantyPriority('MEDIUM');

    setLiabilityRequirement('Minimum 1x annual contract value cap');
    setLiabilityPriority('MEDIUM');

    setRenewalPreference('No automatic renewal without 60-day notice');
    setRenewalPriority('HIGH');

    setTerminationRequirement('Termination for convenience with 30-day notice');
    setTerminationPriority('MEDIUM');

    setSupportRequirement('24/7 technical support with 1-hour critical response');
    setSupportPriority('MEDIUM');

    setCustomReq1('Data hosting must remain in India');
    setCustomPrio1('MUST_HAVE');
    setCustomReq2('');
    setCustomReq3('');

    setErrorMsg(null);
    setSaveSuccessMsg(null);
  }

  // Handle Form Submission (Save Requirements locally via Pydantic schema validation - Zero Groq calls!)
  async function handleSubmit(e) {
    e.preventDefault();
    setErrorMsg(null);
    setSaveSuccessMsg(null);

    const certList = parseCertifications(certificationsText);
    const customList = [customReq1, customReq2, customReq3].filter((c) => c.trim().length > 0);
    const customPrioList = [
      ...(customReq1.trim() ? [customPrio1] : []),
      ...(customReq2.trim() ? [customPrio2] : []),
      ...(customReq3.trim() ? [customPrio3] : []),
    ];

    const hasAnyField =
      budgetCeiling.trim() !== '' ||
      timelineValue.trim() !== '' ||
      minimumSla.trim() !== '' ||
      paymentTerms.trim() !== '' ||
      certList.length > 0 ||
      warrantyValue.trim() !== '' ||
      liabilityRequirement.trim() !== '' ||
      renewalPreference.trim() !== '' ||
      terminationRequirement.trim() !== '' ||
      supportRequirement.trim() !== '' ||
      customList.length > 0;

    if (!hasAnyField) {
      setErrorMsg('Please specify at least one procurement requirement criterion.');
      return;
    }

    const reqPayload = {
      budget_ceiling: budgetCeiling.trim() ? parseFloat(budgetCeiling) : null,
      budget_currency: budgetCurrency,
      budget_priority: budgetPriority,

      timeline_value: timelineValue.trim() ? parseFloat(timelineValue) : null,
      timeline_unit: timelineUnit,
      timeline_priority: timelinePriority,

      minimum_sla: minimumSla.trim() ? parseFloat(minimumSla) : null,
      sla_priority: slaPriority,

      payment_terms: paymentTerms.trim() ? paymentTerms.trim() : null,
      payment_priority: paymentPriority,

      certifications: certList,
      certifications_priority: certificationsPriority,

      warranty_value: warrantyValue.trim() ? parseFloat(warrantyValue) : null,
      warranty_unit: warrantyUnit,
      warranty_priority: warrantyPriority,

      liability_requirement: liabilityRequirement.trim() ? liabilityRequirement.trim() : null,
      liability_priority: liabilityPriority,

      renewal_preference: renewalPreference.trim() ? renewalPreference.trim() : null,
      renewal_priority: renewalPriority,

      termination_requirement: terminationRequirement.trim() ? terminationRequirement.trim() : null,
      termination_priority: terminationPriority,

      support_requirement: supportRequirement.trim() ? supportRequirement.trim() : null,
      support_priority: supportPriority,

      custom_requirements: customList,
      custom_priorities: customPrioList,
    };

    if (!sessionId) {
      if (onSaveRequirements) {
        onSaveRequirements(reqPayload);
      }
      setSaveSuccessMsg('Requirements saved locally.');
      if (onNavigateDashboard) {
        onNavigateDashboard();
      }
      return;
    }

    setIsSaving(true);

    try {
      const res = await saveRequirements(sessionId, reqPayload);
      if (res.success) {
        if (onSaveRequirements) {
          onSaveRequirements(reqPayload);
        }
        setSaveSuccessMsg('Requirements saved successfully.');
      } else {
        setErrorMsg(res.error || 'Unable to save requirements. Please try again.');
      }
    } catch (err) {
      console.error('Requirements save error:', err);
      setErrorMsg('Unable to save requirements. Please check the highlighted fields and try again.');
    } finally {
      setIsSaving(false);
    }
  }

  /* ─── Grid Layout for Two-Column Req Grid ─── */
  const twoColGrid = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    border: '2px solid #171717',
    borderBottom: 'none',
    borderRight: 'none',
  };

  const oneColGrid = {
    display: 'grid',
    gridTemplateColumns: '1fr',
    border: '2px solid #171717',
    borderBottom: 'none',
    borderRight: 'none',
  };

  if (!sessionId) {
    return (
      <div className="dashboard-layout">
        <Sidebar
          activeTab="requirements"
          sessionReady={false}
          onNavigateHome={onNavigateHome}
          onNavigateDashboard={onNavigateDashboard}
          onNavigateRequirements={onNavigateRequirements}
          onNavigateComparison={onNavigateComparison}
          onNavigateRisks={onNavigateRisks}
          onNavigateClarifications={onNavigateClarifications}
          onNavigateRanking={onNavigateRanking}
          onNavigateRecommendation={onNavigateRecommendation}
        />
        <div className="dashboard-content">
          <header className="dashboard-header-bar">
            <h1 className="dashboard-title font-display">Requirements</h1>
            <p className="dashboard-subtitle">Define procurement requirements before evaluating vendor proposals.</p>
          </header>
          <div style={{ padding: '2rem' }}>
            <FeatureGate
              eyebrow="PREREQUISITE REQUIRED"
              title="UPLOAD PROPOSALS FIRST"
              description="PropIQ needs vendor proposals before you can configure procurement criteria."
              ctaLabel="Upload Proposals"
              onCta={onNavigateDashboard}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      {/* Left Sidebar */}
      <Sidebar
        activeTab="requirements"
        sessionReady={!!sessionId}
        onNavigateHome={onNavigateHome}
        onNavigateDashboard={onNavigateDashboard}
        onNavigateRequirements={onNavigateRequirements}
        onNavigateComparison={onNavigateComparison}
        onNavigateRisks={onNavigateRisks}
        onNavigateClarifications={onNavigateClarifications}
        onNavigateRanking={onNavigateRanking}
        onNavigateRecommendation={onNavigateRecommendation}
      />

      {/* Main Content Area */}
      <div className="dashboard-content" style={{ overflowY: 'auto' }}>

        {/* Page Header */}
        <header style={{
          borderBottom: '2px solid #171717',
          padding: '1.5rem 2rem',
          background: '#F7F3EA',
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-between',
        }}>
          <div>
            <span style={{ fontFamily: "'Space Mono', monospace", fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', color: '#7897FF', display: 'block', marginBottom: '4px' }}>
              TARGET CRITERIA / 01
            </span>
            <h1 style={{ fontFamily: "'Archivo Black', sans-serif", fontSize: '1.85rem', color: '#171717', letterSpacing: '-0.02em', margin: '0 0 4px 0' }}>
              Define what matters.
            </h1>
            <p style={{ fontFamily: "'DM Sans', sans-serif", fontSize: '0.9rem', color: '#6A6A60', margin: 0 }}>
              Set the requirements PropIQ should use when evaluating vendor proposals.
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary"
            onClick={handleFillSampleValues}
            disabled={isSaving}
            style={{ fontSize: '0.825rem', padding: '0.5rem 1rem', whiteSpace: 'nowrap' }}
          >
            Load Sample Criteria
          </button>
        </header>

        {/* Info strip */}
        <div style={{
          background: '#C8D6FF',
          borderBottom: '2px solid #171717',
          padding: '0.75rem 2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}>
          <span style={{ fontFamily: "'Space Mono', monospace", fontSize: '0.7rem', fontWeight: 700, color: '#171717', whiteSpace: 'nowrap' }}>
            WHAT HAPPENS NEXT
          </span>
          <span style={{ fontFamily: "'DM Sans', sans-serif", fontSize: '0.875rem', color: '#171717' }}>
            PropIQ compares every vendor against these criteria and uses their importance when calculating alignment scores.
          </span>
        </div>

        {/* Error Banner */}
        {errorMsg && (
          <div style={{
            margin: '1.5rem 2rem 0',
            background: '#FFE0E0',
            border: '2px solid #EB7096',
            borderRadius: '4px',
            padding: '0.85rem 1.25rem',
            fontFamily: "'DM Sans', sans-serif",
            fontSize: '0.9rem',
            color: '#7A1A3A',
            boxShadow: '3px 3px 0 #EB7096',
          }}>
            {errorMsg}
          </div>
        )}

        {/* Workspace */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 270px', gap: '1.5rem', padding: '2rem', maxWidth: '1200px', alignItems: 'start' }}>

          {/* Main Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>

            {!sessionId && (
              <div className="req-pre-upload-note">
                <span className="req-pre-upload-note-label">YOU CAN START HERE</span>
                <span className="req-pre-upload-note-text">
                  Define your procurement requirements now, then upload vendor proposals when you're ready to evaluate them.
                </span>
              </div>
            )}

            {/* ── SECTION 1: COMMERCIAL & TIMELINE ── */}
            <div style={{
              border: '2px solid #171717',
              borderRadius: '4px',
              overflow: 'hidden',
              boxShadow: '4px 4px 0 #171717',
              marginBottom: '2.5rem',
            }}>
              <SectionHeader
                num="01"
                title="Commercial & Timeline"
                subtitle="Cost, implementation and service expectations."
                accentColor="#7897FF"
              />

              {/* Row 1: Budget + Timeline */}
              <div style={twoColGrid}>
                <ReqCell>
                  <label htmlFor="budget-ceiling" style={LABEL_STYLE}>Budget Ceiling</label>
                  <CompoundCurrencyInput
                    id="budget-ceiling"
                    currency={budgetCurrency}
                    onCurrencyChange={setBudgetCurrency}
                    value={budgetCeiling}
                    onValueChange={setBudgetCeiling}
                    placeholder="200,000"
                    disabled={isSaving}
                  />
                  <ImportanceSelector value={budgetPriority} onChange={setBudgetPriority} id="budget-prio" disabled={isSaving} />
                </ReqCell>

                <ReqCell>
                  <label htmlFor="timeline-value" style={LABEL_STYLE}>Max Deployment Timeline</label>
                  <CompoundValueUnitInput
                    id="timeline-value"
                    value={timelineValue}
                    onValueChange={setTimelineValue}
                    unit={timelineUnit}
                    onUnitChange={setTimelineUnit}
                    valuePlaceholder="30"
                    unitOptions={[{ value: 'days', label: 'days' }, { value: 'weeks', label: 'weeks' }, { value: 'months', label: 'months' }]}
                    disabled={isSaving}
                  />
                  <ImportanceSelector value={timelinePriority} onChange={setTimelinePriority} id="timeline-prio" disabled={isSaving} />
                </ReqCell>
              </div>

              {/* Row 2: SLA + Payment */}
              <div style={twoColGrid}>
                <ReqCell>
                  <label htmlFor="minimum-sla" style={LABEL_STYLE}>Minimum Uptime SLA</label>
                  <SlaInput id="minimum-sla" value={minimumSla} onValueChange={setMinimumSla} disabled={isSaving} />
                  <ImportanceSelector value={slaPriority} onChange={setSlaPriority} id="sla-prio" disabled={isSaving} />
                </ReqCell>

                <ReqCell>
                  <label htmlFor="payment-terms" style={LABEL_STYLE}>Payment Terms</label>
                  <input
                    id="payment-terms"
                    type="text"
                    placeholder="Net 30"
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value)}
                    disabled={isSaving}
                    style={INPUT_BASE}
                  />
                  <ImportanceSelector value={paymentPriority} onChange={setPaymentPriority} id="payment-prio" disabled={isSaving} />
                </ReqCell>
              </div>
            </div>

            {/* ── SECTION 2: CONTRACT & COMPLIANCE ── */}
            <div style={{
              border: '2px solid #171717',
              borderRadius: '4px',
              overflow: 'hidden',
              boxShadow: '4px 4px 0 #171717',
              marginBottom: '2.5rem',
            }}>
              <SectionHeader
                num="02"
                title="Contract & Compliance"
                subtitle="Security, legal and operational requirements."
                accentColor="#EB7096"
              />

              {/* Row 1: Certifications + Warranty */}
              <div style={twoColGrid}>
                <ReqCell>
                  <label htmlFor="certifications-text" style={LABEL_STYLE}>Required Certifications</label>
                  <input
                    id="certifications-text"
                    type="text"
                    placeholder="SOC 2 Type II, ISO 27001"
                    value={certificationsText}
                    onChange={(e) => setCertificationsText(e.target.value)}
                    disabled={isSaving}
                    style={INPUT_BASE}
                  />
                  <p style={HELPER_STYLE}>Separate multiple certifications with commas.</p>
                  <ImportanceSelector value={certificationsPriority} onChange={setCertificationsPriority} id="cert-prio" disabled={isSaving} />
                </ReqCell>

                <ReqCell>
                  <label htmlFor="warranty-value" style={LABEL_STYLE}>Minimum Warranty</label>
                  <CompoundValueUnitInput
                    id="warranty-value"
                    value={warrantyValue}
                    onValueChange={setWarrantyValue}
                    unit={warrantyUnit}
                    onUnitChange={setWarrantyUnit}
                    valuePlaceholder="12"
                    unitOptions={[{ value: 'months', label: 'months' }, { value: 'years', label: 'years' }]}
                    disabled={isSaving}
                  />
                  <ImportanceSelector value={warrantyPriority} onChange={setWarrantyPriority} id="warranty-prio" disabled={isSaving} />
                </ReqCell>
              </div>

              {/* Row 2: Liability + Renewal */}
              <div style={twoColGrid}>
                <ReqCell>
                  <label htmlFor="liability-req" style={LABEL_STYLE}>Limitation of Liability</label>
                  <input
                    id="liability-req"
                    type="text"
                    placeholder="1× annual fees cap"
                    value={liabilityRequirement}
                    onChange={(e) => setLiabilityRequirement(e.target.value)}
                    disabled={isSaving}
                    style={INPUT_BASE}
                  />
                  <ImportanceSelector value={liabilityPriority} onChange={setLiabilityPriority} id="liab-prio" disabled={isSaving} />
                </ReqCell>

                <ReqCell>
                  <label htmlFor="renewal-pref" style={LABEL_STYLE}>Contract Renewal Preference</label>
                  <input
                    id="renewal-pref"
                    type="text"
                    placeholder="No automatic renewal"
                    value={renewalPreference}
                    onChange={(e) => setRenewalPreference(e.target.value)}
                    disabled={isSaving}
                    style={INPUT_BASE}
                  />
                  <ImportanceSelector value={renewalPriority} onChange={setRenewalPriority} id="renew-prio" disabled={isSaving} />
                </ReqCell>
              </div>

              {/* Row 3: Termination + Support */}
              <div style={twoColGrid}>
                <ReqCell>
                  <label htmlFor="termination-req" style={LABEL_STYLE}>Exit / Termination Terms</label>
                  <input
                    id="termination-req"
                    type="text"
                    placeholder="30-day termination for convenience"
                    value={terminationRequirement}
                    onChange={(e) => setTerminationRequirement(e.target.value)}
                    disabled={isSaving}
                    style={INPUT_BASE}
                  />
                  <ImportanceSelector value={terminationPriority} onChange={setTerminationPriority} id="term-prio" disabled={isSaving} />
                </ReqCell>

                <ReqCell>
                  <label htmlFor="support-req" style={LABEL_STYLE}>Support Availability</label>
                  <input
                    id="support-req"
                    type="text"
                    placeholder="24/7 priority support"
                    value={supportRequirement}
                    onChange={(e) => setSupportRequirement(e.target.value)}
                    disabled={isSaving}
                    style={INPUT_BASE}
                  />
                  <ImportanceSelector value={supportPriority} onChange={setSupportPriority} id="supp-prio" disabled={isSaving} />
                </ReqCell>
              </div>
            </div>

            {/* ── SECTION 3: CUSTOM REQUIREMENTS ── */}
            <div style={{
              border: '2px solid #171717',
              borderRadius: '4px',
              overflow: 'hidden',
              boxShadow: '4px 4px 0 #171717',
              marginBottom: '2.5rem',
            }}>
              <SectionHeader
                num="03"
                title="Custom Requirements"
                subtitle="Add criteria specific to this procurement."
                accentColor="#F4C84A"
              />

              {/* Custom Req 1 */}
              <div style={oneColGrid}>
                <ReqCell>
                  <label htmlFor="custom-req-1" style={LABEL_STYLE}>Custom Requirement 01</label>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                      id="custom-req-1"
                      type="text"
                      placeholder="e.g. Data must be hosted in India"
                      value={customReq1}
                      onChange={(e) => setCustomReq1(e.target.value)}
                      disabled={isSaving}
                      style={{ ...INPUT_BASE, flex: 1 }}
                    />
                    <div style={{ minWidth: '140px' }}>
                      <span style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6A6A60', marginBottom: '5px', fontFamily: "'Space Mono', monospace" }}>
                        IMPORTANCE
                      </span>
                      <select
                        id="c1-prio"
                        value={customPrio1}
                        onChange={(e) => setCustomPrio1(e.target.value)}
                        disabled={isSaving}
                        style={{
                          ...SELECT_BASE,
                          height: '46px',
                          fontWeight: 700,
                          backgroundColor: IMPORTANCE_STYLES[customPrio1]?.bg || '#FFFFFF',
                          color: IMPORTANCE_STYLES[customPrio1]?.color || '#171717',
                          border: `1.5px solid ${IMPORTANCE_STYLES[customPrio1]?.border || '#171717'}`,
                        }}
                      >
                        <option value="MUST_HAVE">Must Have</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                      </select>
                    </div>
                  </div>
                </ReqCell>
              </div>

              {/* Custom Req 2 */}
              <div style={oneColGrid}>
                <ReqCell>
                  <label htmlFor="custom-req-2" style={LABEL_STYLE}>Custom Requirement 02</label>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                      id="custom-req-2"
                      type="text"
                      placeholder="e.g. Dedicated account manager included"
                      value={customReq2}
                      onChange={(e) => setCustomReq2(e.target.value)}
                      disabled={isSaving}
                      style={{ ...INPUT_BASE, flex: 1 }}
                    />
                    <div style={{ minWidth: '140px' }}>
                      <span style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6A6A60', marginBottom: '5px', fontFamily: "'Space Mono', monospace" }}>
                        IMPORTANCE
                      </span>
                      <select
                        id="c2-prio"
                        value={customPrio2}
                        onChange={(e) => setCustomPrio2(e.target.value)}
                        disabled={isSaving}
                        style={{
                          ...SELECT_BASE,
                          height: '46px',
                          fontWeight: 700,
                          backgroundColor: IMPORTANCE_STYLES[customPrio2]?.bg || '#FFFFFF',
                          color: IMPORTANCE_STYLES[customPrio2]?.color || '#171717',
                          border: `1.5px solid ${IMPORTANCE_STYLES[customPrio2]?.border || '#171717'}`,
                        }}
                      >
                        <option value="MUST_HAVE">Must Have</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                      </select>
                    </div>
                  </div>
                </ReqCell>
              </div>

              {/* Custom Req 3 */}
              <div style={oneColGrid}>
                <ReqCell>
                  <label htmlFor="custom-req-3" style={LABEL_STYLE}>Custom Requirement 03</label>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                      id="custom-req-3"
                      type="text"
                      placeholder="e.g. Free sandbox environment provided"
                      value={customReq3}
                      onChange={(e) => setCustomReq3(e.target.value)}
                      disabled={isSaving}
                      style={{ ...INPUT_BASE, flex: 1 }}
                    />
                    <div style={{ minWidth: '140px' }}>
                      <span style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6A6A60', marginBottom: '5px', fontFamily: "'Space Mono', monospace" }}>
                        IMPORTANCE
                      </span>
                      <select
                        id="c3-prio"
                        value={customPrio3}
                        onChange={(e) => setCustomPrio3(e.target.value)}
                        disabled={isSaving}
                        style={{
                          ...SELECT_BASE,
                          height: '46px',
                          fontWeight: 700,
                          backgroundColor: IMPORTANCE_STYLES[customPrio3]?.bg || '#FFFFFF',
                          color: IMPORTANCE_STYLES[customPrio3]?.color || '#171717',
                          border: `1.5px solid ${IMPORTANCE_STYLES[customPrio3]?.border || '#171717'}`,
                        }}
                      >
                        <option value="MUST_HAVE">Must Have</option>
                        <option value="HIGH">High</option>
                        <option value="MEDIUM">Medium</option>
                        <option value="LOW">Low</option>
                      </select>
                    </div>
                  </div>
                </ReqCell>
              </div>
            </div>

            {/* ── PRIMARY ACTION BAR ── */}
            {saveSuccessMsg && (
              <div style={{
                marginTop: '1rem',
                backgroundColor: '#B9B5EA',
                border: '2px solid #171717',
                borderRadius: '4px',
                padding: '0.75rem 1rem',
                fontFamily: "'Space Mono', monospace",
                fontWeight: 700,
                fontSize: '0.85rem',
                color: '#171717',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <span>✓ {saveSuccessMsg}</span>
                {onNavigateComparison && (
                  <button
                    type="button"
                    onClick={onNavigateComparison}
                    className="btn-primary font-mono"
                    style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                  >
                    Open Comparison →
                  </button>
                )}
              </div>
            )}

            <div style={{
              borderTop: '2px solid #171717',
              paddingTop: '1.5rem',
              marginTop: '1.5rem',
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              gap: '1rem',
            }}>
              {isSaving && (
                <span style={{ fontFamily: "'Space Mono', monospace", fontSize: '0.75rem', color: '#6A6A60' }}>
                  Saving requirements…
                </span>
              )}
              <button
                type="submit"
                disabled={isSaving}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  fontFamily: "'DM Sans', sans-serif",
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  color: '#171717',
                  background: isSaving ? '#E8D88A' : '#F4C84A',
                  border: '2px solid #171717',
                  padding: '0.85rem 2rem',
                  borderRadius: '4px',
                  cursor: isSaving ? 'not-allowed' : 'pointer',
                  boxShadow: isSaving ? 'none' : '4px 4px 0 #171717',
                  transition: 'transform 0.12s ease, box-shadow 0.12s ease',
                  opacity: isSaving ? 0.7 : 1,
                }}
              >
                <span>
                  {isSaving
                    ? 'Saving Requirements…'
                    : 'Save Requirements'}
                </span>
                {!isSaving && <span>→</span>}
              </button>
            </div>
          </form>

          {/* Right SaaS Session Panel */}
          <SaasSessionPanel
            proposalsCount={proposals.length}
            definedVendorsCount={proposals.length}
            isProcessed={true}
            isExtracting={isSaving}
            requirements={{
              budget_ceiling: budgetCeiling ? parseFloat(budgetCeiling) : null,
              timeline_value: timelineValue ? parseFloat(timelineValue) : null,
              minimum_sla: minimumSla ? parseFloat(minimumSla) : null,
              payment_terms: paymentTerms || null,
              certifications: parseCertifications(certificationsText),
              warranty_value: warrantyValue ? parseFloat(warrantyValue) : null,
              liability_requirement: liabilityRequirement || null,
              renewal_preference: renewalPreference || null,
              termination_requirement: terminationRequirement || null,
              support_requirement: supportRequirement || null,
              custom_requirements: [customReq1, customReq2, customReq3].filter((c) => c.trim().length > 0),
            }}
          />
        </div>
      </div>
    </div>
  );
}
