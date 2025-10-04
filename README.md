# Photosphere Labs Agent System

Multi-agent system for actionable e-commerce insights using natural language queries.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Set up Firebase (AWS Secrets Manager):**
   - Firebase credentials are stored in AWS Secrets Manager
   - Secrets: `ps-labs-firebase-dev` and `ps-labs-firebase-prod`
   - The application automatically fetches credentials at runtime
   - Secret names configured in `.env` as `FIREBASE_SECRET_NAME_DEV` and `FIREBASE_SECRET_NAME_PROD`

4. **Configure AWS:**
   - Ensure AWS credentials have access to Athena and Glue Data Catalog
   - Set Athena output S3 bucket locations for dev and prod:
     - `ATHENA_S3_OUTPUT_LOCATION_DEV`
     - `ATHENA_S3_OUTPUT_LOCATION_PROD`
   - Set Glue database names:
     - `GLUE_DATABASE_DEV`
     - `GLUE_DATABASE_PROD`

5. **Switch environments:**
   - Set `ENVIRONMENT=development` for dev (default)
   - Set `ENVIRONMENT=production` for prod

## Usage

### CLI Interface (for testing)

```bash
# Activate virtual environment
source agent_venv/bin/activate

# Run the CLI interface
python main.py
```

### API Server

```bash
# Activate virtual environment
source agent_venv/bin/activate

# Run the FastAPI server
python api.py

# Or with uvicorn directly
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

- `POST /chat` - Send a chat message
  ```json
  {
    "user_id": "user123",
    "message": "Show me my Instagram engagement metrics",
    "conversation_id": "optional-conversation-id"
  }
  ```
- `GET /health` - Health check endpoint

## Architecture

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation.
