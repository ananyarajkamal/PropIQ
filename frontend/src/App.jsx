import React, { useState, useEffect } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import HeroPage from './pages/HeroPage';
import DashboardPage from './pages/DashboardPage';
import RequirementsPage from './pages/RequirementsPage';
import VendorDetailsPage from './pages/VendorDetailsPage';
import ComparisonPage from './pages/ComparisonPage';
import RisksPage from './pages/RisksPage';
import ClarificationsPage from './pages/ClarificationsPage';
import RankingPage from './pages/RankingPage';
import RecommendationPage from './pages/RecommendationPage';
import {
  fetchSessionSummary,
  prepareComparison,
  evaluateComparison,
  analyzeRisks,
  generateClarifications,
  evaluateScoring,
  generateRecommendation,
} from './services/api';

export default function App() {
  function getNormalizedPath() {
    let path = window.location.pathname || '/';
    if (path.length > 1 && path.endsWith('/')) {
      path = path.slice(0, -1);
    }
    return path;
  }

  const [currentPath, setCurrentPath] = useState(getNormalizedPath());

  // Canonical analysis session state
  const [sessionId, setSessionId] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [requirements, setRequirements] = useState(null);
  const [factSheetsData, setFactSheetsData] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  const [factsReady, setFactsReady] = useState(false);
  const [risksData, setRisksData] = useState(null);
  const [clarificationsData, setClarificationsData] = useState(null);
  const [scoringData, setScoringData] = useState(null);
  const [recommendationData, setRecommendationData] = useState(null);

  // Session hydration & expiry states
  const [isHydrating, setIsHydrating] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);

  // Session Hydration from sessionStorage on initial load / refresh
  useEffect(() => {
    let isMounted = true;
    async function hydrateSession() {
      const persistedSid = sessionStorage.getItem('propiq_session_id');
      if (persistedSid && persistedSid !== 'undefined') {
        try {
          const res = await fetchSessionSummary(persistedSid);
          if (isMounted) {
            if (res.success && res.data) {
              setSessionId(persistedSid);
              setProposals(res.data.proposals || []);
              setFactsReady(true);
              setSessionExpired(false);

              // Hydrate saved requirements
              const savedReqs = sessionStorage.getItem('propiq_requirements');
              if (savedReqs) {
                try { setRequirements(JSON.parse(savedReqs)); } catch (e) {}
              }

              // Hydrate saved comparison data
              const savedComp = sessionStorage.getItem('propiq_comparison_data');
              if (savedComp) {
                try { setComparisonData(JSON.parse(savedComp)); } catch (e) {}
              }

              // Hydrate saved scoring data
              const savedScore = sessionStorage.getItem('propiq_scoring_data');
              if (savedScore) {
                try { setScoringData(JSON.parse(savedScore)); } catch (e) {}
              }

              // Hydrate saved risks data
              const savedRisks = sessionStorage.getItem('propiq_risks_data');
              if (savedRisks) {
                try { setRisksData(JSON.parse(savedRisks)); } catch (e) {}
              }

              // Hydrate saved clarifications data
              const savedClar = sessionStorage.getItem('propiq_clarifications_data');
              if (savedClar) {
                try { setClarificationsData(JSON.parse(savedClar)); } catch (e) {}
              }

              // Hydrate saved recommendation data
              const savedRec = sessionStorage.getItem('propiq_recommendation_data');
              if (savedRec) {
                try { setRecommendationData(JSON.parse(savedRec)); } catch (e) {}
              }
            } else {
              clearAllSessionStorage();
              setSessionId(null);
              setProposals([]);
              setSessionExpired(true);
            }
          }
        } catch (err) {
          if (isMounted) {
            clearAllSessionStorage();
            setSessionId(null);
            setProposals([]);
            setSessionExpired(true);
          }
        }
      } else if (persistedSid === 'undefined') {
        clearAllSessionStorage();
      }

      if (isMounted) {
        setIsHydrating(false);
      }
    }
    hydrateSession();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    function handlePopState() {
      setCurrentPath(getNormalizedPath());
    }

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  function clearAllSessionStorage() {
    sessionStorage.removeItem('propiq_session_id');
    sessionStorage.removeItem('propiq_requirements');
    sessionStorage.removeItem('propiq_comparison_data');
    sessionStorage.removeItem('propiq_scoring_data');
    sessionStorage.removeItem('propiq_risks_data');
    sessionStorage.removeItem('propiq_clarifications_data');
    sessionStorage.removeItem('propiq_recommendation_data');
  }

  function navigateTo(path) {
    window.history.pushState({}, '', path);
    setCurrentPath(getNormalizedPath());
    window.scrollTo(0, 0);
  }

  function handleProposalsProcessed(sId, proposalList) {
    if (!sId || sId === 'undefined') return;
    sessionStorage.setItem('propiq_session_id', sId);
    setSessionId(sId);
    setProposals(proposalList || []);
    setSessionExpired(false);
    setFactsReady(false);
    setComparisonData(null);
    setRisksData(null);
    setClarificationsData(null);
    setScoringData(null);
    setRecommendationData(null);

    sessionStorage.removeItem('propiq_comparison_data');
    sessionStorage.removeItem('propiq_scoring_data');
    sessionStorage.removeItem('propiq_risks_data');
    sessionStorage.removeItem('propiq_clarifications_data');
    sessionStorage.removeItem('propiq_recommendation_data');
  }

  function handleNewAnalysis() {
    clearAllSessionStorage();
    setSessionId(null);
    setProposals([]);
    setRequirements(null);
    setFactSheetsData(null);
    setComparisonData(null);
    setFactsReady(false);
    setRisksData(null);
    setClarificationsData(null);
    setScoringData(null);
    setRecommendationData(null);
    setSessionExpired(false);
  }

  function handleSaveRequirements(reqs) {
    setRequirements(reqs);
    try {
      sessionStorage.setItem('propiq_requirements', JSON.stringify(reqs));
    } catch (e) {}

    // Invalidate requirement-dependent downstream analysis in React state
    setClarificationsData(null);
    setScoringData(null);
    setRecommendationData(null);

    sessionStorage.removeItem('propiq_clarifications_data');
    sessionStorage.removeItem('propiq_scoring_data');
    sessionStorage.removeItem('propiq_recommendation_data');

    if (sessionId && factsReady) {
      evaluateComparison(sessionId, reqs)
        .then((compRes) => {
          if (compRes.success) {
            setComparisonData(compRes.data);
            try { sessionStorage.setItem('propiq_comparison_data', JSON.stringify(compRes.data)); } catch (e) {}
          }
        })
        .catch(() => {});
    }
  }

  async function handleRunComparison() {
    if (!sessionId || !requirements) {
      throw new Error('Session or requirements missing. Please upload proposals and save requirements first.');
    }

    if (!factsReady) {
      const prepRes = await prepareComparison(sessionId, requirements);
      if (!prepRes.success) {
        const rawError = prepRes.error || '';
        if (rawError.toLowerCase().includes('not found') || rawError.toLowerCase().includes('index not built')) {
          throw new Error(
            'Your proposal session has expired. Please return to the Dashboard and re-upload your proposals.'
          );
        }
        if (rawError.toLowerCase().includes('rate limit') || rawError.toLowerCase().includes('rate limited')) {
          throw new Error(
            'Vendor analysis is temporarily rate limited. Please wait 30 seconds and try again.'
          );
        }
        throw new Error(rawError || 'Vendor analysis could not complete. Please try again.');
      }
      setFactsReady(true);
    }

    const compRes = await evaluateComparison(sessionId, requirements);
    if (compRes.success) {
      setComparisonData(compRes.data);
      try { sessionStorage.setItem('propiq_comparison_data', JSON.stringify(compRes.data)); } catch (e) {}
      // Clear dependent scoring & recommendation
      setScoringData(null);
      setRecommendationData(null);
      sessionStorage.removeItem('propiq_scoring_data');
      sessionStorage.removeItem('propiq_recommendation_data');
    } else {
      const rawError = compRes.error || '';
      if (rawError.includes('FACTS_NOT_READY')) {
        setFactsReady(false);
        throw new Error(
          'Vendor analysis cache was cleared. Click Compare Vendors again to re-analyze.'
        );
      }
      if (rawError.toLowerCase().includes('not found') || rawError.toLowerCase().includes('index not built')) {
        throw new Error(
          'Your proposal session has expired. Please return to the Dashboard and re-upload your proposals.'
        );
      }
      throw new Error(rawError || 'Comparison could not be completed. Please try again.');
    }
  }

  async function handleRunRiskAnalysis() {
    if (sessionId) {
      const riskRes = await analyzeRisks(sessionId, requirements);
      if (riskRes.success) {
        setRisksData(riskRes.data);
        try { sessionStorage.setItem('propiq_risks_data', JSON.stringify(riskRes.data)); } catch (e) {}
      }
    }
  }

  async function handleRunClarifications() {
    if (sessionId) {
      const clrfRes = await generateClarifications(sessionId, requirements);
      if (clrfRes.success) {
        setClarificationsData(clrfRes.data);
        try { sessionStorage.setItem('propiq_clarifications_data', JSON.stringify(clrfRes.data)); } catch (e) {}
      }
    }
  }

  async function handleRunScoring() {
    if (sessionId) {
      const scoreRes = await evaluateScoring(sessionId, requirements);
      if (scoreRes.success) {
        setScoringData(scoreRes.data);
        try { sessionStorage.setItem('propiq_scoring_data', JSON.stringify(scoreRes.data)); } catch (e) {}
        return scoreRes.data;
      }
      return scoreRes;
    }
    return { success: false, error: 'Session ID missing' };
  }

  async function handleRunRecommendation(reqsOverride = null) {
    if (sessionId) {
      const activeReqs = reqsOverride || requirements;
      const recRes = await generateRecommendation(sessionId, activeReqs);
      if (recRes.success) {
        setRecommendationData(recRes.data);
        try { sessionStorage.setItem('propiq_recommendation_data', JSON.stringify(recRes.data)); } catch (e) {}
      }
      return recRes;
    }
    return { success: false, error: 'Session ID missing' };
  }

  const commonNavProps = {
    onNavigateHome: () => navigateTo('/'),
    onNavigateDashboard: () => navigateTo('/dashboard'),
    onNavigateRequirements: () => navigateTo('/dashboard/requirements'),
    onNavigateComparison: () => navigateTo('/dashboard/comparison'),
    onNavigateRisks: () => navigateTo('/dashboard/risks'),
    onNavigateClarifications: () => navigateTo('/dashboard/clarifications'),
    onNavigateRanking: () => navigateTo('/dashboard/ranking'),
    onNavigateRecommendation: () => navigateTo('/dashboard/recommendation'),
  };

  if (isHydrating) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#F5F2F0', fontFamily: 'Space Mono, monospace', fontSize: '0.9rem', fontWeight: 700, color: '#171717' }}>
        Restoring analysis session...
      </div>
    );
  }

  return (
    <ErrorBoundary onReset={() => navigateTo('/dashboard')}>
      {currentPath === '/dashboard/recommendation' ? (
        <RecommendationPage
          sessionId={sessionId}
          hasRequirements={!!requirements}
          hasComparison={!!comparisonData}
          scoringData={scoringData}
          recommendationData={recommendationData}
          onRunRecommendation={handleRunRecommendation}
          {...commonNavProps}
          onNavigateVendorDetails={() => navigateTo('/dashboard/vendor-details')}
        />
      ) : currentPath === '/dashboard/ranking' ? (
        <RankingPage
          sessionId={sessionId}
          hasRequirements={!!requirements}
          hasComparison={!!comparisonData}
          hasRisks={!!risksData}
          hasClarifications={!!clarificationsData}
          scoringData={scoringData}
          onRunScoring={handleRunScoring}
          {...commonNavProps}
          onNavigateVendorDetails={() => navigateTo('/dashboard/vendor-details')}
        />
      ) : currentPath === '/dashboard/comparison' ? (
        <ComparisonPage
          sessionId={sessionId}
          hasRequirements={!!requirements}
          requirements={requirements}
          comparisonData={comparisonData}
          factsReady={factsReady}
          {...commonNavProps}
          onNavigateVendorDetails={() => navigateTo('/dashboard/vendor-details')}
          onRunComparison={handleRunComparison}
        />
      ) : currentPath === '/dashboard/clarifications' ? (
        <ClarificationsPage
          sessionId={sessionId}
          hasRequirements={!!requirements}
          clarificationsData={clarificationsData}
          {...commonNavProps}
          onNavigateVendorDetails={() => navigateTo('/dashboard/vendor-details')}
          onRunClarifications={handleRunClarifications}
        />
      ) : currentPath === '/dashboard/risks' ? (
        <RisksPage
          sessionId={sessionId}
          hasRequirements={!!requirements}
          risksData={risksData}
          {...commonNavProps}
          onNavigateVendorDetails={() => navigateTo('/dashboard/vendor-details')}
          onRunRiskAnalysis={handleRunRiskAnalysis}
        />
      ) : currentPath === '/dashboard/vendor-details' ? (
        <VendorDetailsPage
          factSheetsData={factSheetsData}
          {...commonNavProps}
        />
      ) : currentPath === '/dashboard/requirements' ? (
        <RequirementsPage
          sessionId={sessionId}
          proposals={proposals}
          requirements={requirements}
          {...commonNavProps}
          onExtractionComplete={() => {}}
          onSaveRequirements={handleSaveRequirements}
        />
      ) : currentPath === '/dashboard' ? (
        <DashboardPage
          sessionId={sessionId}
          proposals={proposals}
          requirements={requirements}
          sessionExpired={sessionExpired}
          {...commonNavProps}
          onProposalsProcessed={handleProposalsProcessed}
          onNewAnalysis={handleNewAnalysis}
        />
      ) : currentPath.startsWith('/dashboard') ? (
        <DashboardPage
          sessionId={sessionId}
          proposals={proposals}
          requirements={requirements}
          sessionExpired={sessionExpired}
          {...commonNavProps}
          onProposalsProcessed={handleProposalsProcessed}
          onNewAnalysis={handleNewAnalysis}
        />
      ) : (
        <HeroPage onStart={() => navigateTo('/dashboard')} />
      )}
    </ErrorBoundary>
  );
}