"""
Application settings loaded from environment variables.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    # LLM Provider
    openai_api_key: Optional[str] = Field(default=None, env='OPENAI_API_KEY')
    anthropic_api_key: Optional[str] = Field(default=None, env='ANTHROPIC_API_KEY')

    # AWS Configuration
    aws_access_key_id: str = Field(env='AWS_ACCESS_KEY_ID')
    aws_secret_access_key: str = Field(env='AWS_SECRET_ACCESS_KEY')
    aws_region: str = Field(env='AWS_REGION')

    # Athena S3 Output - Development
    athena_s3_output_location_dev: str = Field(env='ATHENA_S3_OUTPUT_LOCATION_DEV')
    glue_database_dev: str = Field(env='GLUE_DATABASE_DEV')

    # Athena S3 Output - Production
    athena_s3_output_location_prod: str = Field(env='ATHENA_S3_OUTPUT_LOCATION_PROD')
    glue_database_prod: str = Field(env='GLUE_DATABASE_PROD')

    # Firebase - AWS Secrets Manager
    firebase_secret_name_dev: str = Field(env='FIREBASE_SECRET_NAME_DEV')
    firebase_secret_name_prod: str = Field(env='FIREBASE_SECRET_NAME_PROD')

    # Application
    environment: str = Field(default="development", env='ENVIRONMENT')
    log_level: str = Field(default="INFO", env='LOG_LEVEL')

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
