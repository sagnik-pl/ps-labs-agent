"""
Application settings loaded from environment variables.
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import logging

# Set up logging for configuration
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Log environment configuration (for debugging)
env = os.getenv('ENVIRONMENT', 'development')
logger.info(f"Initializing settings for environment: {env}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
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
    cors_origins: str = "http://localhost:3000"

    # Encryption Configuration (End-to-End Encryption for Chat Messages)
    encryption_enabled: bool = Field(default=False, description="Enable message encryption")
    kms_key_id: Optional[str] = Field(default=None, description="AWS KMS key ID for envelope encryption")

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

    def validate_configuration(self) -> dict:
        """
        Validate that all required configuration is present and valid.

        Returns:
            Dict with validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        # Check AWS credentials
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            validation_results["valid"] = False
            validation_results["errors"].append(
                "AWS credentials not set (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"
            )

        if not self.aws_region:
            validation_results["valid"] = False
            validation_results["errors"].append("AWS region not set (AWS_REGION)")

        # Check LLM API keys
        if not self.openai_api_key and not self.anthropic_api_key:
            validation_results["warnings"].append(
                "No LLM API keys set (OPENAI_API_KEY or ANTHROPIC_API_KEY)"
            )

        # Check Athena/Glue configuration
        if not self.glue_database:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"Glue database not configured for environment '{self.environment}'"
            )

        if not self.athena_s3_output_location:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"Athena S3 output location not configured for environment '{self.environment}'"
            )

        # Check Firebase configuration
        if not self.firebase_secret_name:
            validation_results["valid"] = False
            validation_results["errors"].append(
                f"Firebase secret name not configured for environment '{self.environment}'"
            )

        # Log results
        if validation_results["valid"]:
            logger.info("✓ Configuration validation passed")
            if validation_results["warnings"]:
                for warning in validation_results["warnings"]:
                    logger.warning(f"⚠ {warning}")
        else:
            logger.error("✗ Configuration validation failed:")
            for error in validation_results["errors"]:
                logger.error(f"  - {error}")

        return validation_results


settings = Settings()

# Validate configuration on startup (but don't fail - just log)
config_validation = settings.validate_configuration()
if not config_validation["valid"]:
    logger.warning(
        "Configuration has errors. Application may not function correctly. "
        "Please check environment variables."
    )
