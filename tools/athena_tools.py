"""
Tools for Athena query generation and execution.
"""
from langchain.tools import Tool
from pydantic import BaseModel, Field
from typing import Optional
from utils.aws_client import aws_client


class AthenaQueryInput(BaseModel):
    """Input schema for Athena query tool."""

    query: str = Field(description="SQL query to execute on Athena")
    user_id: str = Field(description="User ID for data isolation")


class AthenaSchemaInput(BaseModel):
    """Input schema for getting table schema."""

    table_name: str = Field(description="Name of the table to get schema for")


def execute_athena_query(query: str, user_id: str) -> str:
    """
    Execute an Athena query and return results.

    Args:
        query: SQL query to execute
        user_id: User ID for data isolation

    Returns:
        Query results as formatted string
    """
    try:
        df = aws_client.execute_query(query, user_id)

        if df.empty:
            return "No results found for the query."

        # Format results as string
        return f"Query executed successfully. Results:\n{df.to_string()}"

    except Exception as e:
        return f"Error executing query: {str(e)}"


def get_table_schema(table_name: str) -> str:
    """
    Get schema information for a table.

    Args:
        table_name: Name of the table

    Returns:
        Table schema as formatted string
    """
    try:
        schema = aws_client.get_table_schema(table_name)
        columns_info = "\n".join(
            [f"- {col['name']} ({col['type']})" for col in schema["columns"]]
        )
        return f"Table: {schema['table_name']}\nColumns:\n{columns_info}"

    except Exception as e:
        return f"Error getting schema: {str(e)}"


def list_available_tables() -> str:
    """
    List all available tables in the Glue catalog.

    Returns:
        List of table names
    """
    try:
        tables = aws_client.list_tables()
        return f"Available tables:\n" + "\n".join([f"- {t}" for t in tables])

    except Exception as e:
        return f"Error listing tables: {str(e)}"


# LangChain tools
from langchain_core.tools import StructuredTool

athena_query_tool = StructuredTool.from_function(
    func=execute_athena_query,
    name="execute_athena_query",
    description="Execute SQL query on Athena to fetch user's analytics data. Always include user_id for data isolation. Use this when you need to retrieve specific metrics or data from user's Instagram, Facebook, or Google Analytics data.",
    args_schema=AthenaQueryInput,
)

table_schema_tool = StructuredTool.from_function(
    func=get_table_schema,
    name="get_table_schema",
    description="Get the schema (column names and types) of a table from Glue Data Catalog. Use this before writing SQL queries to understand available columns.",
    args_schema=AthenaSchemaInput,
)

list_tables_tool = Tool(
    name="list_available_tables",
    description="List all available tables in the Glue Data Catalog. Use this to discover what data sources are available. Takes no arguments.",
    func=lambda x="": list_available_tables(),
)
