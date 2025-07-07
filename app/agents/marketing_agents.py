from typing import Iterator, List, Optional
from agno.agent import Agent, RunResponse
from agno.models.anthropic import Claude
from agno.storage.sqlite import SqliteStorage
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.crawl4ai import Crawl4aiTools
from app.agents.base_agent import BaseAgent
from app.core import settings
from agno.utils.pprint import pprint_run_response
from fastapi import UploadFile
import os

class MarketingAgent(BaseAgent):
    def __init__(self):
        self.AGENT_STORAGE = settings.AGENT_STORAGE
        print(self.AGENT_STORAGE)
        self.marketing_website_team = self._create_marketing_website_team()


    # Factory methods for creating individual agents
    def create_website_analyzer_agent(self):
        return Agent(
            name="Website Analyzer Agent",
            role="You are an expert at analyzing website structure, performance, and technical SEO elements",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze technical aspects of websites including performance, structure, and technical SEO elements",
                "Check loading speed and performance metrics",
                "Identify technical issues (broken links, redirects, etc.)",
                "Evaluate mobile responsiveness",
                "Analyze site architecture and navigation",
                "Check technical SEO elements (sitemaps, robots.txt, schema)",
                "Assess content hierarchy and information architecture",
                "Audit page metadata, headers, and structured data",
                "Create a comprehensive technical report with an overall score from 0-100",
                "Format all output in markdown",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_seo_keyword_agent(self):
        return Agent(
            name="SEO Keyword Agent",
            role="You are an expert at optimizing website content for search engines and keyword relevance",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Extract the current primary and secondary keywords being targeted",
                "Analyze keyword density, placement, and relevance in content",
                "Identify meta tags and headings that could be optimized for better search visibility",
                "Suggest 5-7 additional relevant keywords based on industry and topic",
                "Recommend natural placement opportunities for keywords in existing copy",
                "Analyze competitor websites for keyword strategies",
                "Evaluate internal linking structure for SEO optimization",
                "Create a keyword strategy with short-term and long-term recommendations",
                "Format all output in markdown with tables for keyword analysis",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_offer_analysis_agent(self):
        return Agent(
            name="Offer Analysis Agent",
            role="You are an expert at analyzing and improving product/service offers on websites",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze existing offers on the website based on Alex Hormozi's $100M Offers framework",
                "Identify the core value proposition and evaluate its clarity and appeal",
                "Check if pricing, positioning, and promises match what the market urgently wants",
                "Evaluate if the offer feels like a 'no-brainer' purchase",
                "Look for clear risk reversal, guarantees, and urgency elements",
                "Analyze the offer structure for dream outcome, transformation, and unique mechanism",
                "Identify if the offer clearly addresses objections and reduces purchasing friction",
                "Check for appropriate urgency and scarcity elements",
                "Provide specific recommendations to improve the offer structure",
                "Format all output in markdown",
                "Include specific examples of how to transform the current offers into more compelling ones",
                "Instead of making open-ended recommendations, provide clear actionable recommendations",
                "Our offer is high quality software development so that maintenance cost is low",
                "Product we develop stands the test of time",
                "Are cheaper over time because of high quality and lower technical debt",
                "Our products are built faster because we are an AI first company where we use AI frameworks in all the steps of SDLC process",
                "We are truly better faster cheaper",
                "Our heart lies in craftsmanship and we are not a bodyshop",
                "We consider ourselves tech nannies of our clients, we take care of their tech when they go out and do their business",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_audience_analysis_agent(self):
        return Agent(
            name="Audience Analysis Agent",
            role="You are an expert at identifying target audiences and their needs from website content",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze the website to identify the target audience segments",
                "Evaluate how well the website demonstrates understanding of customer needs and pain points",
                "Create audience personas based on the website content and target market",
                "Assess if the website speaks to customers in their own language and emotional state",
                "Check if the website addresses different levels of customer awareness (from unaware to most aware)",
                "Identify if copy resonates with different decision-making styles (analytical vs. emotional)",
                "Evaluate if the messaging addresses audience objections and hesitations",
                "Analyze how effectively the site segments visitors based on needs and intent",
                "Identify gaps in audience understanding and segmentation",
                "Recommend improvements to better connect with the target audience",
                "Format all output in markdown",
                "Include specific examples of how to better address audience needs and emotions",
                "Instead of making open-ended recommendations, provide clear actionable recommendations",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_copywriting_agent(self):
        return Agent(
            name="Copywriting Agent",
            role="You are an expert copywriter specializing in clear, emotional, and compelling marketing messages",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze the current copywriting and messaging on the website",
                "Don't just make recommendations - create complete new copy for all major website sections",
                "Completely rewrite headlines, subheadlines, and body copy to be more clear, emotional, and persuasive",
                "Transform features into benefits in your new copy",
                "Create messaging that triggers emotional responses and clear actions",
                "Apply the 4U framework (Useful, Urgent, Unique, Ultra-specific) to all new headlines",
                "Rewrite all CTAs to improve clarity and motivation",
                "Incorporate storytelling elements and emotional narrative in your new copy",
                "Clearly articulate the unique selling proposition throughout your new content",
                "Format all output in markdown with clear section labels that correspond to website sections",
                "Present a COMPLETE VERSION 1 of new website copy organized by page sections",
                "Use SEO friendly language and keywords in your new copy",
                "Ensure the new copy aligns with our company purpose",
                "Focus on creating copy that speaks to both technical and non-technical audiences",
                "The new copy should emphasize quality, craftsmanship, and AI-enhanced development",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_copy_variation_agent(self):
        return Agent(
            name="Copy Variation Agent",
            role="You are an expert at creating multiple distinct but effective copy variations for websites",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Take the initial new copy created by the Copywriting Agent and create 2 distinct variations",
                "VARIATION 2 should use a more technical, feature-focused approach for technically savvy audiences",
                "VARIATION 3 should use a more emotional, benefit-focused approach for non-technical audiences",
                "For each variation, create complete copy for all major website sections",
                "Include headlines, subheadlines, body copy, and CTAs in each variation",
                "Format all output in markdown with clear section labels",
                "Clearly label each variation (VARIATION 2, VARIATION 3)",
                "Ensure all variations maintain the core value proposition and align with company purpose",
                "Make the variations genuinely different in tone, structure, and approach - not just minor word changes",
                "Incorporate the insights from audience analysis and offer analysis in your variations",
                "Use SEO friendly language and keywords in all variations",
            ],
            show_tool_calls=True,
            tools=[Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_conversion_pathway_agent(self):
        return Agent(
            name="Conversion Pathway Agent",
            role="You are an expert at optimizing user journeys and conversion paths on websites",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Map the current user journey from entry to conversion point",
                "Identify friction points where copy or design may cause users to hesitate or abandon",
                "Evaluate CTAs for clarity, urgency, and value communication",
                "Assess form fields and submission processes for conversion barriers",
                "Analyze the persuasion sequence and logical flow of information",
                "Check for appropriate use of social proof and trust elements at decision points",
                "Evaluate visual hierarchy and attention guidance toward conversion goals",
                "Recommend micro-copy improvements to guide users through decision points",
                "Create a conversion funnel analysis with specific improvement recommendations",
                "Format all output in markdown with journey maps",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            tools=[Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_distribution_agent(self):
        return Agent(
            name="Distribution Strategy Agent",
            role="You are an expert at analyzing and improving traffic generation and visibility strategies",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze the website's current distribution and traffic generation strategies",
                "Evaluate social media integration, SEO setup, content shareability, and traffic sources",
                "Check for lead capture mechanisms and audience building features",
                "Assess if content is designed for platform-specific algorithms and shareability",
                "Evaluate the website's connection to existing marketing channels",
                "Check for email newsletter signup and lead nurturing paths",
                "Analyze content repurposing potential for multiple platforms",
                "Identify viral loop potential and referral mechanisms",
                "Identify gaps in the distribution strategy",
                "Recommend specific improvements to increase visibility and traffic",
                "Format all output in markdown",
                "Include specific tactics to improve distribution across owned, earned, and paid channels",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_testing_agent(self):
        return Agent(
            name="Testing & Iteration Agent",
            role="You are an expert at developing testing strategies for marketing websites",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze the website for existing testing capabilities and data collection",
                "Identify key elements that should be tested (headlines, offers, CTAs, etc.)",
                "Design specific A/B tests to improve conversion rates",
                "For each element, generate 3 alternative versions with different approaches",
                "Explain the psychological principle behind each variation",
                "Recommend which metrics should be tracked and how data should inform iterations",
                "Prioritize tests based on potential conversion impact (high/medium/low)",
                "Create a structured testing plan with priorities and expected outcomes",
                "Format all output in markdown",
                "Include specific examples of tests to run and how to implement them",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            tools=[GoogleSearchTools(), Crawl4aiTools(max_length=None)],
            stream=True,
            markdown=True,
        )

    def create_product_manager_agent(self):
        return Agent(
            name="Product Manager Agent",
            role="You are an expert product manager who can analyze and improve product offerings",
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=8096),
            instructions=[
                "Analyze all the aspects of the generated report and create a list of todos",
                "Create a markdown todo list for a set of developers",
                "Organize todos by priority (Must-Have, Should-Have, Could-Have)",
                "Group todos by area (Technical, Content, SEO, UX, etc.)",
                "ToDos should be in form of a checklist and feel free to add sub-items",
                "Todos should have clear language for someone at intern level to follow",
                "Estimate effort level for each todo (Small, Medium, Large)",
                "Create a phased implementation plan (Phase 1, 2, 3)",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            tools=[Crawl4aiTools(max_length=None), GoogleSearchTools()],
            stream=True,
            markdown=True,
        )

    def _create_marketing_website_team(self):
        return Agent(
            name="Marketing Website Optimization Team",
            team=[
                self.create_website_analyzer_agent(),
                self.create_seo_keyword_agent(),
                self.create_offer_analysis_agent(),
                self.create_audience_analysis_agent(),
                self.create_copywriting_agent(),
                self.create_copy_variation_agent(),
                self.create_conversion_pathway_agent(),
                self.create_distribution_agent(),
                self.create_testing_agent(),
                self.create_product_manager_agent()
            ],
            model=Claude(id="claude-3-7-sonnet-20250219", max_tokens=12000),
            instructions=[
                "You are a team of marketing experts who work together to analyze and optimize websites.",
                "Given a website URL, conduct a comprehensive review focused on marketing effectiveness.",
                "Each team member has specific expertise aligned with core marketing skills:",
                "1. Technical Foundation (Website Analyzer) reviews technical aspects",
                "2. Search Engine Visibility (SEO Keyword Agent) evaluates keyword strategy",
                "3. Offer Creation (Offer Analysis) evaluates the product/service offers",
                "4. Audience Understanding (Audience Analysis) evaluates target audience alignment",
                "5. Message Crafting (Copywriting) creates complete new copy for the website",
                "6. Copy Variation (Copy Variation Agent) creates multiple distinct versions of the copy",
                "7. User Journey (Conversion Pathway) analyzes the path to conversion",
                "8. Distribution (Distribution Strategy) analyzes traffic generation",
                "9. Testing & Iteration (Testing) develops a testing and optimization plan",
                "10. Implementation Planning (Product Manager) creates actionable tasks",
                "Provide a comprehensive report with actionable recommendations",
                "Include specific examples and improvements for each section",
                "Format all output in markdown with clear sections",
                "Create a separate section called NEW WEBSITE COPY with three complete variations",
                "Pass all the analysis and reports to the product manager so that clear course of action is charted for developers",
                "Create a separate section called TODOS at the end of the report to gather all the todos",
                "Instead of making open-ended recommendations, provide clear actionable steps",
            ],
            show_tool_calls=True,
            markdown=True,
            storage=SqliteStorage(table_name="marketing_website_team", db_file=self.AGENT_STORAGE),
            stream=True,
        )

    def review_marketing_website(self, url):
        print(f"Starting marketing website review for URL: {url}")
        prompt = f"""
        Please conduct a complete marketing review and optimization of the website at {url}.
        The website should be a marketing machine that generates leads and converts them into customers.
        Current Audience: CxOs, Product Managers, and Founders of startups. Pre-product, non-tech startup founders looking for software development services.
        We target people who have already been burnt by India or other outsourcing experience because quality of work stands us apart.
        We want to appeal to the people who already understand software craft, or totally non-tech audience.
        <company-purpose>
    Bring our clients' dreams to life by being their trusted engineering partners, crafting innovative software solutions.
    Challenge offshore development stereotypes by delivering exceptional quality, and proving the value of craftsmanship.
    Empower clients to deliver value quickly and frequently to their end users.
    Ensure long-term success for our clients by building reliable, sustainable, and impactful solutions.
    Raise the bar of software craft by setting a new standard for the community.
        </company-purpose>
        
        Follow this process:
        1. Analyze technical aspects of the website
        2. Evaluate SEO and keyword strategy
        3. Evaluate the offers and value propositions
        4. Assess audience understanding and segmentation
        5. Create complete new copy for the entire website (not just recommendations)
        6. Generate two additional variations of the new copy for different audience segments
        7. Analyze user journey and conversion pathways
        8. Analyze distribution and traffic strategies
        9. Develop testing and optimization strategy
        
        For the new copy, provide:
        - VARIATION 1: Balanced copy that speaks to both technical and non-technical audiences
        - VARIATION 2: Copy optimized for technical audiences (CxOs with technical background)
        - VARIATION 3: Copy optimized for non-technical audiences (Founders without technical expertise)
        
        Each variation should be complete and include all major website sections.
        
        For each area, provide:
        - Analysis of current status
        - Specific issues identified
        - Actionable recommendations with examples
        - Priority improvements that will have the biggest impact
        
        Provide a comprehensive report with all findings and improvements. Along with the three complete variations of new website copy.
        """

        try:
            print(f"Running marketing website team for URL: {url}")
            print(self.marketing_website_team)
            response_stream : Iterator[RunResponse] = self.marketing_website_team.run(prompt)
            content = ""
            for response in response_stream:
                content += response.content
            pprint_run_response(response, markdown=True)
            print("Marketing website team completed successfully.")
            return content
        except Exception as e:
            print(f"Error running marketing website team: {e}")
            return f"# Error: {e}"


    
    def run_marketing_agent(self, url: str) -> str:
        return self.review_marketing_website(url)
    
    def get_response(self, url: str, files: Optional[List[UploadFile]] = None, user_email: Optional[str] = None) -> str:
        print(f"Getting response for URL: {url}")
        response = self.run_marketing_agent(url)
        print("Response received successfully.")
        return response
