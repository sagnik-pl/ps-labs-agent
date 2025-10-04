"""
AWS client utilities for Athena and Glue integration.
"""
import boto3
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor
from config.settings import settings


class AWSClient:
    """AWS client for Athena queries and Glue catalog access."""

    def __init__(self):
        self.session = boto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self.athena_client = self.session.client("athena")
        self.glue_client = self.session.client("glue")

    def get_athena_connection(self):
        """Get PyAthena connection for executing queries."""
        return connect(
            s3_staging_dir=settings.athena_s3_output_location,
            region_name=settings.aws_region,
            cursor_class=PandasCursor,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def list_tables(self, database: str = None) -> list[str]:
        """List all tables in the Glue catalog."""
        db = database or settings.glue_database
        response = self.glue_client.get_tables(DatabaseName=db)
        return [table["Name"] for table in response.get("TableList", [])]

    def get_table_schema(self, table_name: str, database: str = None) -> dict:
        """Get schema information for a specific table."""
        db = database or settings.glue_database
        response = self.glue_client.get_table(DatabaseName=db, Name=table_name)
        table = response["Table"]

        columns = [
            {"name": col["Name"], "type": col["Type"]}
            for col in table["StorageDescriptor"]["Columns"]
        ]

        return {"table_name": table_name, "columns": columns}

    def execute_query(self, query: str, user_id: str = None):
        """Execute Athena query and return results as pandas DataFrame."""
        # Add user_id filter if provided for data isolation
        if user_id and "WHERE" not in query.upper():
            query = f"{query} WHERE user_id = '{user_id}'"
        elif user_id:
            query = query.replace("WHERE", f"WHERE user_id = '{user_id}' AND")

        conn = self.get_athena_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.as_pandas()


# Global instance
aws_client = AWSClient()
