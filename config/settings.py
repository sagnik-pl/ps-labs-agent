"""
Application settings loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # LLM Provider
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # AWS Configuration
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

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

    class Config:
        env_file = ".env"
        case_sensitive = False

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
