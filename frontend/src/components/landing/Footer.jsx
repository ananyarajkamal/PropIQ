import React from 'react';

export default function Footer() {
  function handleScrollToSection(e, sectionId) {
    e.preventDefault();
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
    <footer className="landing-footer">
      <div className="container footer-content-flex">
        {/* Left Wordmark */}
        <a href="/" className="footer-logo-text">
          PropIQ
        </a>

        {/* Center Links */}
        <ul className="footer-nav-links font-sans">
          <li>
            <a href="#product" onClick={(e) => handleScrollToSection(e, 'product')}>PRODUCT</a>
          </li>
          <li>
            <a href="#workflow" onClick={(e) => handleScrollToSection(e, 'workflow')}>WORKFLOW</a>
          </li>
          <li>
            <a href="#intelligence" onClick={(e) => handleScrollToSection(e, 'intelligence')}>INTELLIGENCE</a>
          </li>
        </ul>

        {/* Right Copyright */}
        <div className="footer-copyright">
          © 2026 PropIQ Inc. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
