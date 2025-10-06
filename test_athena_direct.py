"""Test Athena access directly"""
import boto3
from config.settings import settings

# Create Athena client
client = boto3.client(
    'athena',
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key
)

# Try a simple query
try:
    response = client.start_query_execution(
        QueryString='SELECT 1',
        QueryExecutionContext={
            'Database': settings.glue_database
        },
        ResultConfiguration={
            'OutputLocation': settings.athena_s3_output_location,
        }
    )
    print(f"✅ Query started successfully!")
    print(f"Query ID: {response['QueryExecutionId']}")
except Exception as e:
    print(f"❌ Error: {e}")
