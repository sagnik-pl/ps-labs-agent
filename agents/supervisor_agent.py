"""
Supervisor Agent that routes queries to specialized agents.
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from typing import Literal, Dict, Any
from agents.data_analytics_agent import DataAnalyticsAgent
from config.settings import settings
import json


class SupervisorAgent:
    """Supervisor agent that routes queries to specialized agents."""

    def __init__(self, use_anthropic: bool = True):
        """
        Initialize Supervisor Agent.

        Args:
            use_anthropic: If True, use Claude; otherwise use OpenAI GPT-4
        """
        # Select LLM provider
        if use_anthropic:
            self.llm = ChatAnthropic(
                model="claude-3-sonnet-20240229",
                anthropic_api_key=settings.anthropic_api_key,
                temperature=0,
            )
        else:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                openai_api_key=settings.openai_api_key,
                temperature=0,
            )

        # Initialize specialized agents
        self.agents = {
            "data_analytics": DataAnalyticsAgent(use_anthropic=use_anthropic),
            # Future agents will be added here:
            # "competitor_intelligence": CompetitorIntelligenceAgent(),
            # "creative": CreativeAgent(),
            # "financial_analyst": FinancialAnalystAgent(),
            # "media_planner": MediaPlannerAgent(),
            # "sentiment_analyst": SentimentAnalystAgent(),
        }

        # Routing prompt
        self.routing_prompt = ChatPromptTemplate.from_template(
            """You are a Supervisor Agent that routes user queries to specialized agents.

Available agents:
1. data_analytics - Queries user's own analytics data (Instagram, Facebook, Google Analytics) from Glue Data Catalog
2. competitor_intelligence - (Coming soon) Researches competitors, web scraping, Meta Ads Library
3. creative - (Coming soon) Generates ad creatives and images
4. financial_analyst - (Coming soon) P&L analysis, profitability calculations
5. media_planner - (Coming soon) Budget optimization, media planning
6. sentiment_analyst - (Coming soon) Brand sentiment analysis from web

User Query: {query}
Conversation Context: {context}

Analyze the query and determine which agent(s) should handle it.
Respond with ONLY a JSON object in this format:
{{
    "primary_agent": "agent_name",
    "reasoning": "brief explanation",
    "requires_multiple_agents": false
}}

For now, route all data queries to "data_analytics". Route other queries to "data_analytics" with a message that those features are coming soon.
"""
        )

    def route_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Determine which agent should handle the query.

        Args:
            query: User's query
            context: Conversation context

        Returns:
            Dict with routing decision
        """
        try:
            prompt = self.routing_prompt.format(query=query, context=context)
            response = self.llm.invoke(prompt)

            # Extract JSON from response
            content = response.content

            # Try to parse JSON
            try:
                routing_decision = json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, default to data_analytics
                routing_decision = {
                    "primary_agent": "data_analytics",
                    "reasoning": "Default routing",
                    "requires_multiple_agents": False,
                }

            return routing_decision

        except Exception as e:
            # Default fallback
            return {
                "primary_agent": "data_analytics",
                "reasoning": f"Error in routing: {str(e)}",
                "requires_multiple_agents": False,
            }

    def process_query(
        self, query: str, user_id: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        Process user query by routing to appropriate agent(s).

        Args:
            query: User's natural language query
            user_id: User ID for data isolation
            context: Conversation context

        Returns:
            Dict with response and metadata
        """
        # Route the query
        routing_decision = self.route_query(query, context)
        primary_agent = routing_decision["primary_agent"]

        # Check if agent is available
        if primary_agent not in self.agents:
            return {
                "response": f"The {primary_agent} agent is coming soon. Currently, only data analytics queries are supported.",
                "agent_used": None,
                "routing_decision": routing_decision,
            }

        # Execute with the appropriate agent
        try:
            agent = self.agents[primary_agent]
            response = agent.run(query, user_id, context)

            return {
                "response": response,
                "agent_used": primary_agent,
                "routing_decision": routing_decision,
            }

        except Exception as e:
            return {
                "response": f"Error processing query: {str(e)}",
                "agent_used": primary_agent,
                "routing_decision": routing_decision,
                "error": str(e),
            }
