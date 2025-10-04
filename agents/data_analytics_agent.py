"""
Data Analytics Agent for querying user's analytics data via Athena.
"""
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.athena_tools import (
    athena_query_tool,
    table_schema_tool,
    list_tables_tool,
)
from config.settings import settings


class DataAnalyticsAgent:
    """Agent for analyzing user's data from Glue Data Catalog."""

    def __init__(self, use_anthropic: bool = False):
        """
        Initialize Data Analytics Agent.

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

        # Define tools
        self.tools = [
            list_tables_tool,
            table_schema_tool,
            athena_query_tool,
        ]

        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a Data Analytics Agent specialized in querying e-commerce analytics data.

Your role is to:
1. Understand user questions about their Instagram, Facebook, and Google Analytics data
2. Discover available tables using list_available_tables
3. Get table schemas using get_table_schema before writing queries
4. Write and execute SQL queries using execute_athena_query
5. Interpret results and provide clear, actionable insights

Important guidelines:
- ALWAYS include user_id in queries for data isolation
- Start by listing tables if you're unsure what data is available
- Check table schemas before writing SQL
- Write efficient SQL queries
- Provide context and interpretation with your results
- Focus on actionable insights, not just raw numbers

User ID: {user_id}
Conversation Context: {context}
""",
                ),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create agent
        self.agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

    def run(self, query: str, user_id: str, context: str = "") -> str:
        """
        Execute a query using the Data Analytics Agent.

        Args:
            query: User's natural language query
            user_id: User ID for data isolation
            context: Conversation context

        Returns:
            Agent's response
        """
        try:
            result = self.agent_executor.invoke(
                {
                    "input": query,
                    "user_id": user_id,
                    "context": context or "No previous context",
                }
            )
            return result["output"]

        except Exception as e:
            return f"Error processing query: {str(e)}"
