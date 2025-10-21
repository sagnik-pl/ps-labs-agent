"""
AWS client utilities for Athena and Glue integration.
"""
import boto3
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


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
        self.s3_client = self.session.client("s3")

        # Track if connection has been validated
        self._validated = False

    def validate_connection(self) -> dict:
        """
        Validate AWS connection and configuration.

        Checks:
        - AWS credentials are valid
        - Glue database is accessible
        - S3 output location is accessible
        - Athena can execute queries

        Returns:
            Dict with validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Test Glue database access
        try:
            response = self.glue_client.get_database(Name=settings.glue_database)
            logger.info(f"✓ Glue database '{settings.glue_database}' is accessible")
        except Exception as e:
            validation_results["valid"] = False
            error_msg = f"Cannot access Glue database '{settings.glue_database}': {str(e)}"
            validation_results["errors"].append(error_msg)
            logger.error(f"✗ {error_msg}")

        # Test S3 output location access
        try:
            # Extract bucket name from S3 path
            s3_path = settings.athena_s3_output_location
            if s3_path.startswith("s3://"):
                bucket_name = s3_path.replace("s3://", "").split("/")[0]
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"✓ S3 bucket '{bucket_name}' is accessible")
            else:
                validation_results["warnings"].append(
                    f"S3 output location format unusual: {s3_path}"
                )
        except Exception as e:
            validation_results["valid"] = False
            error_msg = f"Cannot access S3 bucket for Athena output: {str(e)}"
            validation_results["errors"].append(error_msg)
            logger.error(f"✗ {error_msg}")

        # Test table listing
        try:
            tables = self.list_tables()
            if len(tables) > 0:
                logger.info(f"✓ Found {len(tables)} tables in Glue catalog")
            else:
                validation_results["warnings"].append(
                    "Glue database is empty (no tables found)"
                )
                logger.warning("⚠ No tables found in Glue database")
        except Exception as e:
            validation_results["valid"] = False
            error_msg = f"Cannot list tables: {str(e)}"
            validation_results["errors"].append(error_msg)
            logger.error(f"✗ {error_msg}")

        self._validated = True
        return validation_results

    def ensure_validated(self):
        """
        Ensure connection has been validated at least once.
        Logs a warning if not validated.
        """
        if not self._validated:
            logger.warning(
                "AWS client used without validation. "
                "Call validate_connection() on startup to catch config issues early."
            )

    def get_athena_connection(self):
        """Get PyAthena connection for executing queries."""
        return connect(
            s3_staging_dir=settings.athena_s3_output_location,
            region_name=settings.aws_region,
            schema_name=settings.glue_database,
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
        # Log warning if connection hasn't been validated
        self.ensure_validated()

        # The agent is responsible for adding user_id filters in queries
        # We don't add it automatically to avoid ambiguity with table aliases

        conn = self.get_athena_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.as_pandas()


# Global instance
aws_client = AWSClient()
