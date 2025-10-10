"""
Application settings loaded from environment variables.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

# DEBUG: Print all environment variables to see what Railway is providing
print("=" * 80)
print("ENVIRONMENT VARIABLES AVAILABLE:")
for key, value in os.environ.items():
    if any(x in key.upper() for x in ['AWS', 'ATHENA', 'GLUE', 'FIREBASE', 'OPENAI', 'ANTHROPIC']):
        print(f"{key} = {value[:20]}..." if len(value) > 20 else f"{key} = {value}")
print("=" * 80)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )
    # LLM Provider
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # AWS Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str

    # Athena S3 Output - Development
    athena_s3_output_location_dev: str
    glue_database_dev: str

    # Athena S3 Output - Production
    athena_s3_output_location_prod: str
    glue_database_prod: str

    # Firebase - AWS Secrets Manager
    firebase_secret_name_dev: str
    firebase_secret_name_prod: str

    # Application
    environment: str = "development"
    log_level: str = "INFO"

    @property
    def athena_s3_output_location(self) -> str:
        """Get Athena S3 output location based on environment."""
        if self.environment == "production":
            return self.athena_s3_output_location_prod
        return self.athena_s3_output_location_dev

    @property
    def glue_database(self) -> str:
        """Get Glue database name based on environment."""
        if self.environment == "production":
            return self.glue_database_prod
        return self.glue_database_dev

    @property
    def firebase_secret_name(self) -> str:
        """Get Firebase secret name based on environment."""
        if self.environment == "production":
            return self.firebase_secret_name_prod
        return self.firebase_secret_name_dev


settings = Settings()
