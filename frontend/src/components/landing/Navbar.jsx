import React, { useState } from 'react';

export default function Navbar({ onStart }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function handleScrollToSection(e, sectionId) {
    e.preventDefault();
    setMobileMenuOpen(false);
    const element = document.getElementById(sectionId);
    if (element) {
      const navOffset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - navOffset;
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });
    }
  }

  return (
    <header className="landing-nav" style={{ position: 'relative' }}>
      <div className="container landing-nav-container">
        {/* Left: Square Blue Logo + Brand Wordmark */}
        <a href="/" className="landing-logo">
          <div className="landing-logo-box">P</div>
          <span className="landing-logo-text">PropIQ</span>
        </a>

        {/* Center: Desktop Nav Links */}
        <nav className="desktop-nav-links" aria-label="Main Navigation">
          <a
            href="#product"
            className="nav-link-item"
            onClick={(e) => handleScrollToSection(e, 'product')}
          >
            PRODUCT
          </a>
          <a
            href="#workflow"
            className="nav-link-item"
            onClick={(e) => handleScrollToSection(e, 'workflow')}
          >
            WORKFLOW
          </a>
          <a
            href="#intelligence"
            className="nav-link-item"
            onClick={(e) => handleScrollToSection(e, 'intelligence')}
          >
            INTELLIGENCE
          </a>
        </nav>

        {/* Right: CTA Button */}
        <div className="desktop-nav-actions" style={{ display: 'flex', alignItems: 'center' }}>
          <button
            type="button"
            className="btn-primary"
            onClick={onStart}
          >
            <span>START ANALYZING ↗</span>
          </button>
        </div>

        {/* Mobile Hamburger Toggle (Only below 768px) */}
        <button
          type="button"
          className="mobile-menu-toggle"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {mobileMenuOpen ? (
              <path d="M18 6L6 18M6 6l12 12" />
            ) : (
              <path d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Drawer Navigation */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer">
          <div className="mobile-nav-list">
            <a
              href="#product"
              className="mobile-nav-item"
              onClick={(e) => handleScrollToSection(e, 'product')}
            >
              PRODUCT
            </a>
            <a
              href="#workflow"
              className="mobile-nav-item"
              onClick={(e) => handleScrollToSection(e, 'workflow')}
            >
              WORKFLOW
            </a>
            <a
              href="#intelligence"
              className="mobile-nav-item"
              onClick={(e) => handleScrollToSection(e, 'intelligence')}
            >
              INTELLIGENCE
            </a>
          </div>

          <button
            type="button"
            className="btn-primary w-full text-center"
            onClick={onStart}
            style={{ justifyContent: 'center' }}
          >
            <span>START ANALYZING ↗</span>
          </button>
        </div>
      )}
    </header>
  );
}
