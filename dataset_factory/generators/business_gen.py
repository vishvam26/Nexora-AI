import random
from typing import List, Dict, Any
from pathlib import Path
from dataset_factory.generators.base_generator import BaseGenerator

class BusinessGenerator(BaseGenerator):
    """
    Generates the Business dataset (business.jsonl) containing 2,000+ conversations.
    """

    def generate(self) -> List[Dict[str, Any]]:
        conversations = []
        random.seed(46)

        industries = [
            "SaaS", "E-commerce", "EdTech", "FinTech", "HealthTech", "PropTech",
            "AdTech", "LogisticsTech", "CleanTech", "BioTech", "InsurTech", "HRTech"
        ]
        
        audiences = [
            "small businesses", "freelancers", "enterprise developers", "high school students", 
            "real estate agents", "healthcare clinics", "independent merchants", "non-profit organizations",
            "content creators", "university professors"
        ]
        
        channels = [
            "SEO and content marketing", "Google Ads and PPC", "viral product loops", "direct enterprise cold outreach",
            "influencer partnerships", "developer advocate community", "affiliate marketing programs", "industry trade shows"
        ]
        
        revenue_models = [
            "monthly subscription", "usage-based pricing", "freemium model", "commission per transaction",
            "tiered annual licensing", "marketplace listing fee"
        ]

        prd_features = [
            ("User Authentication & RBAC", "Allows users to sign up, log in, reset password, and assign roles to control access."),
            ("Real-Time Analytics Dashboard", "Provides real-time updates of business events, sales metrics, and logs."),
            ("AI-Powered Auto-Responder", "Drafts answers to user support queries automatically leveraging RAG data."),
            ("Automated Invoice Billing", "Generates recurring monthly invoices and processes payments via Stripe integration."),
            ("Customizable Reporting Module", "Enables users to export PDF and CSV reports on daily operational KPIs."),
            ("Team Collaboration Invites", "Allows organization owners to invite team members via email with role configuration."),
            ("Third-party Webhook Integrations", "Sends HTTP POST payloads to external endpoints on key system events."),
            ("Data Import/Export wizard", "Supports uploading CSV files to seed database records with validation reports."),
            ("MFA Secure Verification", "Requires users to configure authenticator apps for multi-factor login checks."),
            ("Audit Logging Service", "Records all critical database write operations in a tamper-evident audit history.")
        ]

        # Generate 2,050 conversations
        for i in range(2050):
            ind = industries[i % len(industries)]
            aud = audiences[i % len(audiences)]
            chan = channels[i % len(channels)]
            rev = revenue_models[i % len(revenue_models)]
            feature_title, feature_desc = prd_features[i % len(prd_features)]

            scenario_type = i % 4
            
            if scenario_type == 0:
                # Startup advice
                prompt = f"How should I structure a {ind} startup business plan targeting {aud} using a {rev} revenue model? (Case {i+1})"
                response = (
                    f"### Startup Business Plan: {ind} for {aud}\n\n"
                    f"To build a successful business in this segment, structure your plan into five core pillars:\n\n"
                    f"1. **Value Proposition:** Solve a specific pain point for {aud} with a tailormade {ind} platform.\n"
                    f"2. **Revenue Model:** Implement a **{rev}** strategy to ensure steady cash flow.\n"
                    f"3. **Go-To-Market (GTM):** Focus initially on {chan} to acquire your first customers.\n"
                    f"4. **Product Roadmap:** Build a simple MVP highlighting one core feature, then scale up.\n"
                    f"5. **Unit Economics:** Target a customer lifetime value (LTV) to customer acquisition cost (CAC) ratio of > 3:1."
                )
                user2 = "What is the biggest operational risk for this model?"
                assistant2 = (
                    f"The biggest risk for a **{rev}** model targeting **{aud}** is **churn rate**. "
                    f"Since barrier to exit is low, you must focus heavily on customer success, onboarding tutorials, and regular product value additions."
                )
            elif scenario_type == 1:
                # PRD writing
                prompt = f"Write a Product Requirements Document (PRD) section for a new feature: '{feature_title}' (Spec variant {i+1})."
                response = (
                    f"# PRD Section: {feature_title}\n\n"
                    f"## 1. Overview\n"
                    f"{feature_desc} This specification details the requirement path {i+1}.\n\n"
                    f"## 2. User Stories\n"
                    f"- **As a user**, I want to access the feature securely so my credentials are safe.\n"
                    f"- **As an admin**, I want to see detailed audits of actions performed.\n\n"
                    f"## 3. Functional Requirements\n"
                    f"- The component must load in under 200ms.\n"
                    f"- Standard validation filters must verify inputs on the client side."
                )
                user2 = "Can you outline the KPIs for this feature?"
                assistant2 = (
                    f"### Success Metrics (KPIs) for {feature_title}\n\n"
                    f"- **Adoption Rate:** Percentage of active users accessing this feature within the first 30 days.\n"
                    f"- **Error Rate:** Percentage of failed transactions (target < 0.1%).\n"
                    f"- **Task Completion Time:** Average time taken by a user to complete the flow."
                )
            elif scenario_type == 2:
                # Marketing strategies
                prompt = f"Design a marketing funnel to acquire users for our {ind} software targeting {aud} (Campaign {i+1})."
                response = (
                    f"### Marketing Funnel Design\n\n"
                    f"Here is a 4-step acquisition funnel:\n\n"
                    f"- **Top of Funnel (Awareness):** Use **{chan}** to drive initial traffic to blog posts.\n"
                    f"- **Middle of Funnel (Consideration):** Offer a free tool or template in exchange for an email address.\n"
                    f"- **Bottom of Funnel (Conversion):** Send a targeted email sequence offering a free 14-day trial.\n"
                    f"- **Retention:** Use in-app messaging, support docs, and webinars to ensure activation."
                )
                user2 = "How do we measure success at the consideration phase?"
                assistant2 = (
                    f"At the consideration stage, measure the **opt-in conversion rate** "
                    f"and the **cost per lead (CPL)**. "
                    f"Keep optimization tests running on your landing page copy to maximize conversions."
                )
            else:
                # Customer support script
                prompt = f"Draft a customer support response for a customer whose {ind} subscription payment was double-charged (Ticket {i+1})."
                response = (
                    f"Subject: Important update regarding your {ind} invoice #{random.randint(1000,9999)}\n\n"
                    f"Dear Customer,\n\n"
                    f"Thank you for reaching out to us. I sincerely apologize for the inconvenience caused by the duplicate charge on your account.\n\n"
                    f"I have verified the transaction logs and confirmed the double charge. I have already initiated a refund for the duplicate amount of ${random.randint(20,99)}.00. The funds should credit back in 3-5 business days.\n\n"
                    f"Best regards,\n"
                    f"Customer Support Team"
                )
                user2 = "What internal check should we perform to make sure this doesn't happen again?"
                assistant2 = (
                    f"Internally, you should implement **idempotency keys** on your payment API requests. "
                    f"This ensures that if a client sends duplicate payment submissions due to network retries, "
                    f"the processor recognizes the unique transaction ID and only charges the customer once."
                )

            conv = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response},
                    {"role": "user", "content": user2},
                    {"role": "assistant", "content": assistant2}
                ]
            }
            conversations.append(conv)

        print(f"Generated {len(conversations)} business conversations.")
        return conversations
