import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('PropIQ Runtime Boundary Caught Error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.href = '/dashboard';
    }
  };

  render() {
    if (this.state.hasError) {
      const errorMsg = this.state.error?.message || String(this.state.error || 'An unexpected display error occurred.');
      return (
        <div className="editorial-site-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '2rem' }}>
          <div className="main-panel" style={{ maxWidth: '640px', width: '100%', textAlign: 'center', padding: '3rem 2rem' }}>
            <div className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#EB7096', marginBottom: '0.5rem' }}>
              PROPIQ APPLICATION NOTICE
            </div>
            <h2 className="panel-title font-display" style={{ fontSize: '1.4rem', marginBottom: '0.75rem' }}>
              Something went wrong while loading this view.
            </h2>
            <div style={{
              backgroundColor: '#FFE0E0',
              border: '1.5px solid #EB7096',
              borderRadius: '4px',
              padding: '0.85rem 1rem',
              marginBottom: '1.5rem',
              fontFamily: "'Space Mono', monospace",
              fontSize: '0.825rem',
              color: '#7A1A3A',
              wordBreak: 'break-word',
              textAlign: 'left'
            }}>
              <strong>Error details:</strong> {errorMsg}
            </div>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button type="button" className="btn-secondary font-mono" onClick={() => window.location.reload()}>
                Try Again
              </button>
              <button type="button" className="btn-primary font-mono" onClick={this.handleReset}>
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
