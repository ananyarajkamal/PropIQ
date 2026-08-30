/**
 * Status Mapping Utility for PropIQ SaaS Session Panel.
 *
 * Converts internal session states into clean, user-facing SaaS workflow status labels,
 * next-step guidance messages, and primary action buttons.
 */

export function getSaasSessionState({
  proposalsCount = 0,
  definedVendorsCount = 0,
  isProcessing = false,
  isProcessed = false,
  requirements = null,
  isExtracting = false,
  hasFactSheets = false,
  hasComparison = false,
  isAnalyzingRisks = false,
  hasRisks = false,
  isGeneratingClarifications = false,
  hasClarifications = false,
  isCalculatingScoring = false,
  hasScoring = false,
  isGeneratingRecommendation = false,
  hasRecommendation = false,
  errorMsg = null,
}) {
  const reqCount = requirements ? getActiveRequirementsCount(requirements) : 0;

  // 1. Error / Needs Attention State
  if (errorMsg) {
    return {
      status: 'Needs attention',
      proposalsText: proposalsCount > 0 ? `${proposalsCount} of 5` : '0 of 5',
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: typeof errorMsg === 'string' ? errorMsg : 'Review your proposals and try again.',
      cta: null,
    };
  }

  // 2. Executive Recommendation Ready State (Phase 8)
  if (hasRecommendation) {
    return {
      status: 'Recommendation ready',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Review executive decision brief, vendor trade-offs, and items to confirm before award.',
      cta: {
        label: 'View Recommendation',
        path: '/dashboard/recommendation',
      },
    };
  }

  // 3. Recommendation Generation In Progress State
  if (isGeneratingRecommendation) {
    return {
      status: 'Preparing recommendation',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Summarizing vendor alignment, trade-offs, and unresolved items.',
      cta: null,
    };
  }

  // 4. Scoring & Vendor Ranking Ready State (Phase 7)
  if (hasScoring) {
    return {
      status: 'Vendor ranking ready',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Review how each vendor aligns with your requirements and explore score breakdowns.',
      cta: {
        label: 'View Vendor Ranking',
        path: '/dashboard/ranking',
      },
    };
  }

  // 5. Scoring Calculation In Progress State
  if (isCalculatingScoring) {
    return {
      status: 'Calculating vendor alignment',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Evaluating requirement fit, identified concerns, and unresolved information.',
      cta: null,
    };
  }

  // 6. Clarifications Ready State (Phase 6)
  if (hasClarifications) {
    return {
      status: 'Clarifications ready',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Review unanswered questions and information gaps before making a procurement decision.',
      cta: {
        label: 'Review Clarifications',
        path: '/dashboard/clarifications',
      },
    };
  }

  // 7. Clarification Generation In Progress State
  if (isGeneratingClarifications) {
    return {
      status: 'Preparing clarification questions',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Reviewing unresolved vendor details and requirement gaps.',
      cta: null,
    };
  }

  // 8. Risk Review Ready State (Phase 5)
  if (hasRisks) {
    return {
      status: 'Review ready',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Review potential contract risks and inconsistencies found across vendor proposals.',
      cta: {
        label: 'Review Risks',
        path: '/dashboard/risks',
      },
    };
  }

  // 9. Risk Analysis In Progress State
  if (isAnalyzingRisks) {
    return {
      status: 'Reviewing contract terms',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount > 0 ? reqCount : null,
      nextStepMessage: 'Checking for potential contractual risks and statement inconsistencies.',
      cta: null,
    };
  }

  // 10. Comparison Ready State (Phase 4)
  if (hasComparison) {
    return {
      status: 'Comparison ready',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount,
      nextStepMessage: 'Review how each vendor matches your requirements or proceed to contract risk analysis.',
      cta: {
        label: 'View Comparison',
        path: '/dashboard/comparison',
      },
    };
  }

  // 11. Vendor Details Ready State (Phase 3)
  if (hasFactSheets) {
    return {
      status: 'Vendor details ready',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount,
      nextStepMessage: 'Review extracted terms and continue to comparison.',
      cta: {
        label: 'View Vendor Details',
        path: '/dashboard/vendor-details',
      },
    };
  }

  // 12. Extraction / AI Analysis Running State
  if (isExtracting) {
    return {
      status: 'Analyzing vendor terms',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount,
      nextStepMessage: 'Finding pricing, SLA, payment, delivery, and contract details from your proposals.',
      cta: null,
    };
  }

  // 13. Requirements Defined (Ready to Extract)
  if (reqCount > 0) {
    return {
      status: 'Requirements set',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: reqCount,
      nextStepMessage: 'Analyze vendor proposals against your defined requirements.',
      cta: {
        label: 'Analyze Vendor Details',
        path: '/dashboard/requirements',
      },
    };
  }

  // 14. Proposals Processed (Indexed & Ready for Requirements)
  if (isProcessed) {
    return {
      status: 'Ready for analysis',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: null,
      nextStepMessage: 'Define the procurement requirements you want PropIQ to evaluate.',
      cta: {
        label: 'Define Requirements',
        path: '/dashboard/requirements',
      },
    };
  }

  // 15. Processing State
  if (isProcessing) {
    return {
      status: 'Preparing proposals',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: null,
      nextStepMessage: 'Reading proposal content and preparing searchable evidence.',
      cta: null,
    };
  }

  // 16. 2 or More Proposals Uploaded (Ready to Process)
  if (proposalsCount >= 2) {
    return {
      status: 'Ready to process',
      proposalsText: `${proposalsCount} of 5`,
      vendorsCount: definedVendorsCount,
      requirementsCount: null,
      nextStepMessage: 'Review vendor names and process your proposals.',
      cta: null,
    };
  }

  // 17. 1 Proposal Uploaded
  if (proposalsCount === 1) {
    return {
      status: 'More proposals needed',
      proposalsText: '1 of 5',
      vendorsCount: definedVendorsCount,
      requirementsCount: null,
      nextStepMessage: 'Add at least 1 more proposal to continue.',
      cta: null,
    };
  }

  // 18. Default Empty State (0 proposals)
  return {
    status: 'Waiting for proposals',
    proposalsText: '0 of 5',
    vendorsCount: 0,
    requirementsCount: null,
    nextStepMessage: 'Add at least 2 vendor proposals to begin your analysis.',
    cta: null,
  };
}

/**
 * Count defined non-null fields in ProcurementRequirements.
 */
function getActiveRequirementsCount(reqs) {
  if (!reqs) return 0;
  let count = 0;
  if (reqs.budget_ceiling !== null && reqs.budget_ceiling !== undefined) count++;
  if (reqs.timeline_value !== null && reqs.timeline_value !== undefined) count++;
  if (reqs.minimum_sla !== null && reqs.minimum_sla !== undefined) count++;
  if (reqs.payment_terms) count++;
  if (reqs.certifications && reqs.certifications.length > 0) count += reqs.certifications.length;
  if (reqs.warranty_value !== null && reqs.warranty_value !== undefined) count++;
  if (reqs.liability_requirement) count++;
  if (reqs.renewal_preference) count++;
  if (reqs.termination_requirement) count++;
  if (reqs.support_requirement) count++;
  if (reqs.custom_requirements && reqs.custom_requirements.length > 0) {
    count += reqs.custom_requirements.filter((c) => c.trim()).length;
  }
  return count;
}
