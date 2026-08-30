import React, { useState, useEffect, useRef } from 'react';
import { fetchHealthStatus, processProposals, searchEvidence } from '../services/api';
import SaasSessionPanel from '../components/SaasSessionPanel';
import Sidebar from '../components/Sidebar';

export default function DashboardPage({
  sessionId,
  proposals = [],
  requirements = null,
  sessionExpired = false,
  onNavigateHome,
  onNavigateRequirements,
  onNavigateComparison,
  onNavigateRisks,
  onNavigateClarifications,
  onNavigateRanking,
  onNavigateRecommendation,
  onProposalsProcessed,
  onNewAnalysis,
}) {
  // Navigation active tab
  const [activeTab, setActiveTab] = useState('dashboard');

  // Backend connection status
  const [backendAvailable, setBackendAvailable] = useState(true);

  // Selected proposal items for initial upload
  const [selectedProposals, setSelectedProposals] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Processing state & error
  const [processing, setProcessing] = useState(false);
  const [processStep, setProcessStep] = useState('');
  const [errorMsg, setErrorMsg] = useState(null);
  const [showNewAnalysisModal, setShowNewAnalysisModal] = useState(false);

  // Evidence Retrieval Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVendorFilter, setSelectedVendorFilter] = useState('');
  const [topK, setTopK] = useState(5);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState(null);
  const [expandedChunks, setExpandedChunks] = useState({});

  // Initial backend availability check
  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        const res = await fetchHealthStatus();
        if (isMounted) {
          setBackendAvailable(res && (res.status === 'ok' || res.connected === true));
        }
      } catch (err) {
        if (isMounted) {
          setBackendAvailable(false);
        }
      }
    }
    checkHealth();
    return () => {
      isMounted = false;
    };
  }, []);

  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function deriveVendorName(filename) {
    let name = filename.replace(/\.pdf$/i, '');
    name = name.replace(/[-_]/g, ' ');
    name = name.replace(/\b(proposal|enterprise|draft|final|v\d+)\b/gi, '').trim();
    if (!name) return 'Vendor Proposal';
    return name.charAt(0).toUpperCase() + name.slice(1);
  }

  function handleFilesAdded(fileList) {
    setErrorMsg(null);
    const newFiles = Array.from(fileList);

    const validNewProposals = [];
    let localError = null;

    newFiles.forEach((file) => {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        localError = `File '${file.name}' is not a PDF file.`;
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        localError = `File '${file.name}' exceeds the 20 MB limit per file.`;
        return;
      }

      const alreadyExists = selectedProposals.some(
        (p) => p.filename === file.name && p.file.size === file.size
      );
      if (!alreadyExists) {
        validNewProposals.push({
          id: 'prop_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
          file: file,
          filename: file.name,
          fileSizeFormatted: formatBytes(file.size),
          vendorName: deriveVendorName(file.name),
        });
      }
    });

    if (localError) {
      setErrorMsg(localError);
    }

    if (validNewProposals.length > 0) {
      const combined = [...selectedProposals, ...validNewProposals];
      if (combined.length > 5) {
        setErrorMsg('A maximum of 5 proposals can be uploaded per analysis.');
        setSelectedProposals(combined.slice(0, 5));
      } else {
        setSelectedProposals(combined);
      }
    }
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesAdded(e.dataTransfer.files);
    }
  }

  function handleVendorNameChange(id, value) {
    setSelectedProposals((prev) =>
      prev.map((item) => (item.id === id ? { ...item, vendorName: value } : item))
    );
  }

  function handleRemoveSelectedProposal(id) {
    setSelectedProposals((prev) => prev.filter((item) => item.id !== id));
  }

  function checkEligibility() {
    const count = selectedProposals.length;
    if (count < 2) {
      return { eligible: false, reason: 'Upload at least 2 proposals to compare vendors.' };
    }
    if (count > 5) {
      return { eligible: false, reason: 'Maximum 5 proposals supported per session.' };
    }

    const vNames = selectedProposals.map((p) => p.vendorName.trim());
    const hasEmpty = vNames.some((name) => !name);
    if (hasEmpty) {
      return { eligible: false, reason: 'All proposals must have a vendor name specified.' };
    }

    const lowerNames = vNames.map((n) => n.toLowerCase());
    const hasDuplicates = new Set(lowerNames).size !== lowerNames.length;
    if (hasDuplicates) {
      return { eligible: false, reason: 'Vendor names must be unique across all uploaded proposals.' };
    }

    return { eligible: true, reason: null };
  }

  async function handleProcessProposals() {
    const eligibility = checkEligibility();
    if (!eligibility.eligible) {
      setErrorMsg(eligibility.reason || 'Please complete proposal requirements.');
      return;
    }

    setProcessing(true);
    setProcessStep('Processing proposals...');
    setErrorMsg(null);

    try {
      setProcessStep('Extracting proposal text...');
      const filesToUpload = selectedProposals.map((p) => p.file);
      const vendorNamesToUpload = selectedProposals.map((p) => p.vendorName.trim());

      setProcessStep('Preparing analysis workspace...');
      const res = await processProposals(filesToUpload, vendorNamesToUpload);

      if (!res.success) {
        throw new Error(res.error || 'Failed to process vendor proposals.');
      }

      setProcessStep('Proposals uploaded successfully!');
      setSelectedProposals([]);

      const payload = res.data || res;
      if (onProposalsProcessed) {
        onProposalsProcessed(payload.session_id, payload.proposals);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Processing failed. Please check file validity.');
    } finally {
      setProcessing(false);
      setProcessStep('');
    }
  }

  async function handleExecuteSearch(e) {
    if (e) e.preventDefault();
    if (!searchQuery.trim() || !sessionId) return;

    setSearchLoading(true);
    setSearchError(null);
    try {
      const res = await searchEvidence(
        sessionId,
        searchQuery.trim(),
        selectedVendorFilter || null,
        topK
      );
      if (!res.success) {
        throw new Error(res.error || 'Search query failed.');
      }
      setSearchResults(res.data);
    } catch (err) {
      setSearchError(err.message || 'Could not retrieve proposal evidence.');
    } finally {
      setSearchLoading(false);
    }
  }

  function toggleChunkExpand(idx) {
    setExpandedChunks((prev) => ({ ...prev, [idx]: !prev[idx] }));
  }

  function handleConfirmNewAnalysis() {
    setShowNewAnalysisModal(false);
    setSelectedProposals([]);
    setSearchResults(null);
    setSearchQuery('');
    if (onNewAnalysis) {
      onNewAnalysis();
    }
  }

  const eligibility = checkEligibility();
  const activeProposalsList = proposals.length > 0 ? proposals : [];
  const uniqueVendorOptions = Array.from(
    new Set(activeProposalsList.map((p) => p.vendor_name).filter(Boolean))
  );

  return (
    <div className="dashboard-layout">
      {/* Left Sidebar */}
      <Sidebar
        activeTab="dashboard"
        sessionReady={!!sessionId}
        onNavigateHome={onNavigateHome}
        onNavigateDashboard={() => {}}
        onNavigateRequirements={onNavigateRequirements}
        onNavigateComparison={onNavigateComparison}
        onNavigateRisks={onNavigateRisks}
        onNavigateClarifications={onNavigateClarifications}
        onNavigateRanking={onNavigateRanking}
        onNavigateRecommendation={onNavigateRecommendation}
      />

      {/* Main Content Area */}
      <div className="dashboard-content">
        <header className="dashboard-header-bar">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h1 className="dashboard-title font-display">Dashboard</h1>
              <p className="dashboard-subtitle">
                Upload and manage vendor proposals to run deterministic procurement evaluations.
              </p>
            </div>
            {sessionId && (
              <button
                type="button"
                className="btn-secondary font-mono"
                onClick={() => setShowNewAnalysisModal(true)}
                style={{ fontSize: '0.8rem' }}
              >
                + New Analysis
              </button>
            )}
          </div>
        </header>

        {/* Backend Unreachable Banner */}
        {!backendAvailable && (
          <div className="error-banner" style={{ margin: '1rem 1.5rem 0 1.5rem' }}>
            Backend API server is unreachable. Ensure the FastAPI server is running on http://localhost:8000.
          </div>
        )}

        {/* Expired Session Notice Banner */}
        {sessionExpired && !sessionId && (
          <div className="main-panel" style={{ margin: '1rem 1.5rem 0 1.5rem', backgroundColor: '#FDE8EF', border: '2px solid #EB7096', borderRadius: '4px', padding: '1.25rem 1.5rem' }}>
            <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em', color: '#9E1A47', textTransform: 'uppercase' }}>
              SESSION EXPIRED
            </span>
            <h3 className="font-display" style={{ fontSize: '1.15rem', color: '#171717', margin: '0.2rem 0 0.4rem 0' }}>
              Your previous analysis session has expired
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#171717', margin: '0 0 1rem 0' }}>
              Start a new analysis by uploading 2 to 5 vendor proposal PDF documents below.
            </p>
          </div>
        )}

        <div className="workspace-grid" style={{ gridTemplateColumns: '1fr 280px', gap: '1.5rem', padding: '1.5rem', maxWidth: '1240px', minWidth: 0 }}>
          <div className="main-workspace-col" style={{ gap: '1.5rem', minWidth: 0, overflow: 'hidden' }}>

            {/* ════════════════════════════════════════════════════════════════
                ACTIVE ANALYSIS WORKSPACE (Rendered when proposals exist)
               ════════════════════════════════════════════════════════════════ */}
            {sessionId && activeProposalsList.length > 0 ? (
              <div>
                <div className="main-panel" style={{ backgroundColor: '#FFFFFF', border: '2px solid #171717', borderRadius: '4px', padding: '1.5rem', boxShadow: '3px 3px 0px #171717' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div>
                      <span className="sample-badge font-mono" style={{ backgroundColor: '#C8D6FF', color: '#171717', fontWeight: 700 }}>
                        CURRENT ANALYSIS
                      </span>
                      <h2 className="font-display" style={{ fontSize: '1.35rem', margin: '0.2rem 0 0 0', color: '#171717' }}>
                        {activeProposalsList.length} Vendor Proposals Loaded
                      </h2>
                    </div>
                    {onNavigateRequirements && (
                      <button type="button" className="btn-primary font-mono" onClick={onNavigateRequirements} style={{ padding: '0.65rem 1.25rem', fontSize: '0.85rem' }}>
                        <span>Define Requirements</span>
                        <span>→</span>
                      </button>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
                    {activeProposalsList.map((prop, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          backgroundColor: '#F5F2F0',
                          border: '1.5px solid #171717',
                          borderRadius: '3px',
                          padding: '0.85rem 1.1rem',
                        }}
                      >
                        <div>
                          <strong className="font-mono" style={{ fontSize: '1rem', color: '#171717' }}>
                            {prop.vendor_name}
                          </strong>
                          <div className="font-mono" style={{ fontSize: '0.8rem', color: '#6A6A60', marginTop: '0.15rem' }}>
                            {prop.filename}
                          </div>
                        </div>
                        <span className="sample-badge font-mono" style={{ backgroundColor: '#C8D6FF', color: '#171717', fontWeight: 700 }}>
                          Ready for Analysis
                        </span>
                      </div>
                    ))}
                  </div>

                  </div>
              </div>
            ) : (
              /* ════════════════════════════════════════════════════════════════
                  INITIAL PROPOSAL UPLOAD DROPZONE
                 ════════════════════════════════════════════════════════════════ */
              <div className="upload-container">
                <div className="upload-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
                  <div>
                    <h2 className="upload-title font-display" style={{ fontSize: '1.3rem', margin: 0, color: '#171717', textTransform: 'uppercase', letterSpacing: '-0.02em' }}>
                      UPLOAD VENDOR PROPOSALS
                    </h2>
                    <p className="upload-subtitle" style={{ fontSize: '0.875rem', color: '#6A6A60', margin: '0.2rem 0 0 0', fontWeight: 500 }}>
                      Select 2 to 5 vendor PDF proposals for processing.
                    </p>
                  </div>
                  <span className="sample-badge font-mono" style={{ backgroundColor: '#F4C84A', color: '#171717', fontWeight: 700, padding: '0.4rem 0.85rem', border: '1.5px solid #171717', borderRadius: '3px', boxShadow: '2px 2px 0px #171717' }}>
                    LIMIT: 2–5 PROPOSALS
                  </span>
                </div>

                {errorMsg && (
                  <div className="error-banner" style={{ marginBottom: '1rem' }}>
                    {errorMsg}
                  </div>
                )}

                {/* Dropzone area */}
                <div
                  className={`dropzone ${dragActive ? 'active' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current && fileInputRef.current.click()}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => e.target.files && handleFilesAdded(e.target.files)}
                    multiple
                    accept=".pdf,application/pdf"
                    style={{ display: 'none' }}
                  />

                  <div className="dropzone-icon-box">
                    <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>

                  <div className="dropzone-main">
                    Drag and drop vendor proposal PDF files here
                  </div>

                  <div className="dropzone-sub font-mono">
                    or click to browse local PDF files
                  </div>

                  <button type="button" className="btn-browse font-mono">
                    <span>Browse PDF Files</span>
                    <span style={{ fontSize: '1rem' }}>↑</span>
                  </button>

                  <div style={{ display: 'flex', justifyContent: 'center', gap: '0.65rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
                    <span className="font-mono" style={{ fontSize: '0.7rem', color: '#171717', backgroundColor: '#F5F2F0', border: '1.5px solid #171717', padding: '0.2rem 0.6rem', borderRadius: '3px', fontWeight: 700 }}>
                      PDF FORMAT ONLY
                    </span>
                    <span className="font-mono" style={{ fontSize: '0.7rem', color: '#171717', backgroundColor: '#F5F2F0', border: '1.5px solid #171717', padding: '0.2rem 0.6rem', borderRadius: '3px', fontWeight: 700 }}>
                      UP TO 20 MB / FILE
                    </span>
                    <span className="font-mono" style={{ fontSize: '0.7rem', color: '#171717', backgroundColor: '#F5F2F0', border: '1.5px solid #171717', padding: '0.2rem 0.6rem', borderRadius: '3px', fontWeight: 700 }}>
                      2 TO 5 VENDORS
                    </span>
                  </div>
                </div>

                {/* Selected File List */}
                {selectedProposals.length > 0 && (
                  <div className="proposals-list-section">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <h3 className="list-title font-display">
                        Selected Files ({selectedProposals.length} of 5)
                      </h3>
                      <button
                        type="button"
                        className="btn-remove font-mono"
                        onClick={() => setSelectedProposals([])}
                      >
                        Clear All
                      </button>
                    </div>

                    <div className="proposal-cards-stack">
                      {selectedProposals.map((item, index) => (
                        <div key={item.id} className="proposal-item-card">
                          <div className="proposal-info-left">
                            <span className="proposal-num-tag font-mono">
                              PROPOSAL {String(index + 1).padStart(2, '0')}
                            </span>

                            <div className="vendor-input-group">
                              <label htmlFor={`vname-${item.id}`} className="vendor-input-label">
                                Vendor Name:
                              </label>
                              <input
                                id={`vname-${item.id}`}
                                type="text"
                                className="vendor-input"
                                value={item.vendorName}
                                onChange={(e) => handleVendorNameChange(item.id, e.target.value)}
                                placeholder="Enter vendor name"
                              />
                            </div>

                            <div className="proposal-filename font-mono">
                              {item.filename} ({item.fileSizeFormatted})
                            </div>
                          </div>

                          <button
                            type="button"
                            className="btn-remove font-mono"
                            onClick={() => handleRemoveSelectedProposal(item.id)}
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>

                    {/* Process Action Bar */}
                    <div className="process-action-bar">
                      <button
                        type="button"
                        className="btn-primary font-mono"
                        disabled={!eligibility.eligible || processing}
                        onClick={handleProcessProposals}
                        style={{ fontSize: '1rem', padding: '0.9rem 2.25rem' }}
                      >
                        <span>{processing ? (processStep || 'Processing...') : 'Process Proposals'}</span>
                        <span>→</span>
                      </button>

                      {!eligibility.eligible && eligibility.reason && (
                        <div className="process-reason-text font-mono">{eligibility.reason}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Evidence Retrieval Search Panel */}
            {sessionId && (
              <div className="retrieval-test-panel main-panel" style={{ backgroundColor: '#FFFFFF', border: '2px solid #171717', borderRadius: '4px', padding: '1.5rem', boxShadow: '3px 3px 0px #171717', marginTop: '1.5rem' }}>
                <div className="retrieval-panel-header">
                  <h3 className="panel-title font-display" style={{ fontSize: '1.15rem', marginBottom: '0' }}>
                    Search Proposal Evidence
                  </h3>
                </div>
                <p className="panel-desc" style={{ marginTop: '0.4rem', color: '#6A6A60' }}>
                  Instantly search clauses, commercial terms, and evidence across active vendor proposals.
                </p>

                <form onSubmit={handleExecuteSearch} className="retrieval-form">
                  <div className="retrieval-input-row" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end', marginTop: '1rem' }}>
                    <div className="retrieval-query-group" style={{ flex: 1, minWidth: '240px' }}>
                      <label htmlFor="evidence-query-input" className="vendor-input-label">
                        Search Query:
                      </label>
                      <input
                        id="evidence-query-input"
                        type="text"
                        className="vendor-input"
                        style={{ maxWidth: '100%', width: '100%' }}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Enter term (e.g. payment terms, SLA uptime, warranty)..."
                      />
                    </div>

                    <div className="retrieval-filter-group">
                      <label htmlFor="vendor-filter-select" className="vendor-input-label">
                        Vendor Filter:
                      </label>
                      <select
                        id="vendor-filter-select"
                        className="vendor-input"
                        value={selectedVendorFilter}
                        onChange={(e) => setSelectedVendorFilter(e.target.value)}
                      >
                        <option value="">All Vendors</option>
                        {uniqueVendorOptions.map((vname, idx) => (
                          <option key={idx} value={vname}>
                            {vname}
                          </option>
                        ))}
                      </select>
                    </div>

                    <button
                      type="submit"
                      className="btn-primary font-mono"
                      disabled={searchLoading || !searchQuery.trim()}
                      style={{ padding: '0.75rem 1.5rem', fontSize: '0.85rem' }}
                    >
                      {searchLoading ? 'Searching...' : 'Search Evidence'}
                    </button>
                  </div>
                </form>

                {searchError && (
                  <div className="error-banner" style={{ marginTop: '1rem' }}>
                    {searchError}
                  </div>
                )}

                {/* Search Results Display */}
                {searchResults && searchResults.results && (
                  <div className="search-results-box" style={{ marginTop: '1.25rem' }}>
                    <div className="results-count-bar font-mono" style={{ fontSize: '0.8rem', fontWeight: 700, color: '#6A6A60', marginBottom: '0.75rem' }}>
                      FOUND {searchResults.results.length} EVIDENCE EXCERPTS FOR "{searchResults.query}"
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {searchResults.results.map((res, rIdx) => {
                        const isExpanded = !!expandedChunks[rIdx];
                        const excerpt = res.text || res.excerpt_text || '';
                        return (
                          <div
                            key={rIdx}
                            style={{
                              backgroundColor: '#F5F2F0',
                              border: '1.5px solid #171717',
                              borderRadius: '3px',
                              padding: '1rem',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                              <div>
                                <strong className="font-mono" style={{ fontSize: '0.9rem', color: '#171717' }}>
                                  {res.vendor_name}
                                </strong>
                                <span className="font-mono" style={{ fontSize: '0.75rem', color: '#6A6A60', marginLeft: '0.75rem' }}>
                                  {res.source_filename} · Page {res.start_page}
                                </span>
                              </div>
                              <span className="sample-badge font-mono" style={{ backgroundColor: '#C8D6FF', color: '#171717', fontSize: '0.7rem' }}>
                                Match Score: {(res.similarity_score * 100).toFixed(1)}%
                              </span>
                            </div>

                            <p style={{ fontSize: '0.85rem', lineHeight: 1.5, margin: '0 0 0.5rem 0', color: '#171717' }}>
                              "{isExpanded ? excerpt : excerpt.slice(0, 220) + (excerpt.length > 220 ? '...' : '')}"
                            </p>

                            {excerpt.length > 220 && (
                              <button
                                type="button"
                                className="font-mono"
                                onClick={() => toggleChunkExpand(rIdx)}
                                style={{ background: 'none', border: 'none', color: '#7897FF', fontWeight: 700, cursor: 'pointer', padding: 0, fontSize: '0.75rem' }}
                              >
                                {isExpanded ? 'Show Less' : 'Read Full Excerpt →'}
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>

          {/* Right SaaS Session Panel */}
          <SaasSessionPanel
            proposalsCount={activeProposalsList.length}
            definedVendorsCount={activeProposalsList.length}
            isProcessed={!!sessionId && activeProposalsList.length > 0}
            requirements={requirements}
            hasComparison={!!sessionId}
            onNavigate={(path) => {
              if (path === '/dashboard/requirements' && onNavigateRequirements) onNavigateRequirements();
              else if (path === '/dashboard/comparison' && onNavigateComparison) onNavigateComparison();
              else if (path === '/dashboard/risks' && onNavigateRisks) onNavigateRisks();
              else if (path === '/dashboard/ranking' && onNavigateRanking) onNavigateRanking();
              else if (path === '/dashboard/recommendation' && onNavigateRecommendation) onNavigateRecommendation();
            }}
          />
        </div>
      </div>

      {/* New Analysis Confirmation Modal */}
      {showNewAnalysisModal && (
        <div className="drawer-overlay" onClick={() => setShowNewAnalysisModal(false)}>
          <div className="drawer-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
            <div className="drawer-header">
              <div>
                <span className="sample-badge font-mono" style={{ backgroundColor: '#EB7096', color: '#FFFFFF' }}>START NEW ANALYSIS</span>
                <h2 className="drawer-title font-display" style={{ marginTop: '0.25rem' }}>
                  Start a new analysis?
                </h2>
              </div>
              <button type="button" className="btn-remove font-mono" onClick={() => setShowNewAnalysisModal(false)}>
                ✕ Close
              </button>
            </div>

            <div className="drawer-body" style={{ padding: '1.25rem 0' }}>
              <p style={{ fontSize: '0.9rem', color: '#171717', lineHeight: 1.5, margin: 0 }}>
                This will clear the current proposals and analysis results for this browser session. This action cannot be undone.
              </p>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button type="button" className="btn-secondary font-mono" onClick={() => setShowNewAnalysisModal(false)}>
                  Cancel
                </button>
                <button type="button" className="btn-primary font-mono" onClick={handleConfirmNewAnalysis} style={{ backgroundColor: '#EB7096', color: '#FFFFFF' }}>
                  Start New Analysis
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}