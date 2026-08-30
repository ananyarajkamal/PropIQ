import React from 'react';
import Navbar from '../components/landing/Navbar';
import HeroSection from '../components/landing/HeroSection';
import WorkflowSection from '../components/landing/WorkflowSection';
import CapabilitiesSection from '../components/landing/CapabilitiesSection';
import WorkspacePreviewSection from '../components/landing/WorkspacePreviewSection';
import FinalCTASection from '../components/landing/FinalCTASection';
import Footer from '../components/landing/Footer';

export default function LandingPage({ onStart }) {
  return (
    <div className="editorial-site-wrapper">
      <Navbar onStart={onStart} />
      <main>
        <HeroSection onStart={onStart} />
        <WorkflowSection />
        <CapabilitiesSection />
        <WorkspacePreviewSection />
        <FinalCTASection onStart={onStart} />
      </main>
      <Footer />
    </div>
  );
}
