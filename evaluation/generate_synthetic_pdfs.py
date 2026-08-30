"""Synthetic Vendor Proposal PDF Generator for PropIQ Evaluation.

Generates 4 realistic fictional vendor proposal PDFs for controlled procurement evaluation:
1. Northstar Systems (Strongest candidate, 99.95% SLA, 30 days, $115k/yr, auto-renewal clause)
2. Meridian Labs (Credible runner-up, $98k/yr, 45 days, 99.9% SLA, ISO 27001 pending)
3. Apex Procurement Technologies (Contradiction/risk vendor: No commitment vs 24-mo renewal; 30 days vs 60-75 days)
4. Vertex Cloud Services (Missing info vendor: Omitted SLA %, liability cap, certification evidence)
"""

import os
import fitz  # PyMuPDF


def create_proposal_pdf(filepath: str, title: str, pages_content: list):
    """Create professional multi-page PDF using PyMuPDF."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc = fitz.open()

    for page_idx, content in enumerate(pages_content):
        page = doc.new_page(width=612, height=792)  # Standard Letter size
        rect = fitz.Rect(54, 54, 558, 738)  # 0.75 in margins

        # Header
        header_text = f"{title} — Vendor Proposal (Page {page_idx + 1} of {len(pages_content)})"
        page.insert_text((54, 40), header_text, fontsize=9, color=(0.3, 0.3, 0.3))
        page.draw_line((54, 46), (558, 46), color=(0.8, 0.8, 0.8), width=0.5)

        # Content text
        page.insert_textbox(rect, content, fontsize=11, fontname="helv", color=(0.1, 0.1, 0.1), align=0)

        # Footer
        footer_text = "SYNTHETIC EVALUATION DATA — FOR PROPIQ PROCUREMENT TESTING ONLY"
        page.draw_line((54, 746), (558, 746), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text((54, 756), footer_text, fontsize=8, color=(0.5, 0.5, 0.5))

    doc.save(filepath)
    doc.close()


def generate_all_evaluation_proposals():
    target_dir = os.path.join(os.path.dirname(__file__), "proposals")
    os.makedirs(target_dir, exist_ok=True)

    # 1. Northstar Systems Proposal (5 pages)
    northstar_pages = [
        # Page 1: Executive Summary & Overview
        """NORTHSTAR SYSTEMS CORPORATION
PROPOSAL FOR ENTERPRISE VENDOR MANAGEMENT PLATFORM

1. EXECUTIVE SUMMARY
Northstar Systems is pleased to submit this proposal for our Enterprise Vendor Management SaaS Platform. Designed for modern procurement and supplier management teams, Northstar offers end-to-end vendor onboarding, performance tracking, requirement compliance, and automated risk monitoring.

Our platform delivers 99.95% availability, complete data isolation, and comprehensive API integrations.

Key Proposal Highlights:
- Annual Subscription Fee: $115,000 USD
- Implementation Timeline: 30 days guaranteed deployment
- Service Level Agreement: 99.95% uptime SLA with financial credits
- Payment Terms: Net 30 days
- Security Compliance: SOC 2 Type II certified and ISO 27001 certified""",

        # Page 2: Implementation & Deployment Timeline
        """2. IMPLEMENTATION & DEPLOYMENT TIMELINE

Northstar Systems provides a structured 30-day onboarding timeline led by a dedicated implementation manager.

Phase 1: Kickoff & Environment Setup (Days 1–5)
Initial tenant provision, single sign-on (SSO) configuration, and data model mapping.

Phase 2: Data Migration & Integration (Days 6–15)
Migration of existing supplier master records and ERP data connection. Total active setup duration is 720 hours (30 calendar days).

Phase 3: User Training & Acceptance Testing (Days 16–25)
Role-based administrator and buyer training workshops.

Phase 4: Production Go-Live (Day 30)
Full enterprise deployment and transition to dedicated 24/7 account support.""",

        # Page 3: Service Level Agreement & Support
        """3. SERVICE LEVEL AGREEMENT (SLA) & SUPPORT SERVICES

3.1 Availability Commitment
Northstar Systems guarantees a monthly Service Level Agreement (SLA) uptime of 99.95% for all core production services, excluding scheduled maintenance windows.

3.2 SLA Downtime Credits
If monthly availability falls below 99.95%, Customer shall receive SLA service credits calculated as follows:
- 99.50% to 99.94%: 10% credit of monthly fee
- 99.00% to 99.49%: 25% credit of monthly fee
- Below 99.00%: 50% credit of monthly fee

3.3 Support Tier & Availability
Northstar includes 24/7 critical incident response support for all Tier 1 infrastructure severity issues, with maximum 15-minute initial response SLA.""",

        # Page 4: Security, Compliance & Data Ownership
        """4. SECURITY, COMPLIANCE & DATA OWNERSHIP

4.1 Security Certifications
Northstar Systems maintains current SOC 2 Type II audit compliance and ISO 27001 certification. Independent audit reports are provided annually to customers.

4.2 Data Ownership & Privacy
Customer retains sole and exclusive ownership of all uploaded procurement data, supplier records, and contract documents. Northstar acquires no right, title, or interest in customer data.

4.3 Warranty & Service Assurance
Northstar provides a 12-month service assurance warranty guaranteeing that the software will perform in material conformity with system documentation.""",

        # Page 5: Commercial Terms, Renewal & Liability
        """5. COMMERCIAL TERMS, RENEWAL & LIABILITY

5.1 Pricing & Payment Terms
Annual Subscription Fee: $115,000 USD billed annually in advance. Payment terms are Net 30 days from invoice date.

5.2 Contract Renewal & Termination
The initial subscription term is 12 months. This agreement will automatically renew for successive 12-month periods unless either party provides written notice of non-renewal at least 60 days prior to the end of the current term. Customer may terminate for convenience with 30 days written notice.

5.3 Limitation of Liability
Northstar's total aggregate liability arising out of or related to this agreement shall not exceed total fees paid by Customer in the preceding 12 months.""",
    ]
    create_proposal_pdf(os.path.join(target_dir, "northstar_systems_proposal.pdf"), "Northstar Systems", northstar_pages)

    # 2. Meridian Labs Proposal (5 pages)
    meridian_pages = [
        # Page 1: Executive Summary
        """MERIDIAN LABS INC.
PROPOSAL FOR ENTERPRISE VENDOR MANAGEMENT PLATFORM

1. EXECUTIVE SUMMARY
Meridian Labs offers a high-performance, cost-effective Vendor Management Platform tailored for mid-market and enterprise procurement organizations.

Our platform delivers intuitive supplier scorecards, automated compliance checking, and seamless contract repository management.

Key Proposal Highlights:
- Annual Subscription Fee: $98,000 USD
- Implementation Timeline: 45 days
- Service Level Agreement: 99.9% uptime SLA
- Payment Terms: Net 45 days
- Security Compliance: SOC 2 Type II certified (ISO 27001 status pending)""",

        # Page 2: Implementation & Deployment
        """2. IMPLEMENTATION & ONBOARDING

Meridian Labs follows a standard 45-day implementation methodology:

Week 1–2: Configuration and schema mapping.
Week 3–4: Supplier data import and ERP connector setup.
Week 5–6: User acceptance testing and user onboarding.

Total deployment duration is 45 calendar days. Accelerated 30-day implementation is available for an additional professional services fee.""",

        # Page 3: Service Level Agreement & Support
        """3. SERVICE LEVEL AGREEMENT & SUPPORT

3.1 Availability Commitment
Meridian Labs guarantees 99.9% uptime SLA availability during business operation hours.

3.2 Support Availability
24/7 technical support is included for all severity 1 system outages via phone and web portal.""",

        # Page 4: Security & Compliance
        """4. SECURITY & COMPLIANCE

4.1 SOC 2 Type II Compliance
Meridian Labs maintains an active SOC 2 Type II compliance audit report.

4.2 ISO 27001 Status
Meridian Labs is currently undergoing ISO 27001 compliance audit preparation. Formal certification is pending completion in Q4.""",

        # Page 5: Commercial Terms & Renewal
        """5. COMMERCIAL TERMS & RENEWAL

5.1 Pricing & Payment
Annual Fee: $98,000 USD. Payment terms are Net 45 days.

5.2 Contract Renewal & Termination
Subscription term is 12 months. Contract does not renew automatically; renewal requires explicit bilateral written amendment. Customer may terminate for convenience with 60 days notice.

5.3 Warranty & Liability
12-month software functionality warranty. Aggregate liability cap is limited to 12 months of paid contract fees.""",
    ]
    create_proposal_pdf(os.path.join(target_dir, "meridian_labs_proposal.pdf"), "Meridian Labs", meridian_pages)

    # 3. Apex Procurement Technologies Proposal (5 pages)
    apex_pages = [
        # Page 1: Executive Summary (CONTRADICTION STATEMENT A)
        """APEX PROCUREMENT TECHNOLOGIES
PROPOSAL FOR ENTERPRISE VENDOR MANAGEMENT PLATFORM

1. EXECUTIVE SUMMARY
Apex Procurement Technologies delivers an enterprise-grade vendor intelligence platform. We pride ourselves on transparent, flexible commercial terms.

No long-term commitment is required for our flexible enterprise procurement package.

Key Proposal Highlights:
- Annual Subscription Fee: $105,000 USD
- Implementation Timeline: 30 days
- Service Level Agreement: 99.9% uptime SLA
- Payment Terms: Net 30 days
- Security Compliance: SOC 2 Type II certified""",

        # Page 2: Implementation Overview (CONTRADICTION STATEMENT A)
        """2. IMPLEMENTATION OVERVIEW

Apex guarantees a rapid 30-day implementation timeline for standard enterprise configurations, allowing your procurement team to achieve value within one month of contract signing.""",

        # Page 3: Statement of Work (CONTRADICTION STATEMENT B)
        """3. STATEMENT OF WORK & DEPLOYMENT SCHEDULE

Detailed Statement of Work (SOW) deployment activities:
Phase 1: Initial Discovery (15 days)
Phase 2: Custom Data Integration (30 days)
Phase 3: Testing & Go-Live (15 to 30 days)

Estimated total deployment duration is 60 to 75 days depending on customer custom backend integration requirements.""",

        # Page 4: Support & Security
        """4. SUPPORT & SECURITY

Apex provides SOC 2 Type II compliance. Standard technical support is available Monday through Friday 8 AM to 8 PM EST. 24/7 support is available only under our Premium Platinum tier.""",

        # Page 5: Commercial Terms & Renewal (CONTRADICTION STATEMENT B)
        """5. COMMERCIAL TERMS & RENEWAL

5.1 Pricing
Annual Subscription Fee: $105,000 USD. Payment terms: Net 30 days.

5.2 Auto-Renewal Clause
The agreement automatically renews for an additional 24-month term unless written cancellation notice is provided at least 120 days before renewal.

5.3 Limitation of Liability
Liability cap is set at 6 months of paid contract fees.""",
    ]
    create_proposal_pdf(os.path.join(target_dir, "apex_procurement_proposal.pdf"), "Apex Procurement Technologies", apex_pages)

    # 4. Vertex Cloud Services Proposal (5 pages)
    vertex_pages = [
        # Page 1: Executive Summary
        """VERTEX CLOUD SERVICES
PROPOSAL FOR ENTERPRISE VENDOR MANAGEMENT PLATFORM

1. EXECUTIVE SUMMARY
Vertex Cloud Services offers a scalable cloud vendor management system designed to streamline vendor evaluation and compliance tracking.

Key Proposal Highlights:
- Annual Subscription Fee: $120,000 USD
- Implementation Timeline: 30 days
- Payment Terms: Net 30 days""",

        # Page 2: Product Features & Architecture
        """2. PRODUCT FEATURES & ARCHITECTURE

Vertex provides vendor risk mapping, contract metadata indexing, and automated approval workflows built on microservice cloud architecture.""",

        # Page 3: Implementation & Services
        """3. IMPLEMENTATION & SERVICES

Vertex offers a standard 30-day deployment plan including data import templates and administrator configuration workshops.""",

        # Page 4: Support & Maintenance
        """4. SUPPORT & MAINTENANCE

Vertex provides online documentation and helpdesk email support during standard business hours.""",

        # Page 5: Commercial & General Terms
        """5. COMMERCIAL & GENERAL TERMS

Annual Subscription Fee: $120,000 USD. Payment terms: Net 30 days.

General Terms:
Contract duration is 12 months. All software is provided on an 'as-is' basis.""",
    ]
    create_proposal_pdf(os.path.join(target_dir, "vertex_cloud_services_proposal.pdf"), "Vertex Cloud Services", vertex_pages)

    print("Successfully generated 4 synthetic evaluation proposal PDFs in evaluation/proposals/")


if __name__ == "__main__":
    generate_all_evaluation_proposals()
