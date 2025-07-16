# SaaS Backend - AI-Powered Content Management System

This project is a FastAPI backend that provides AI-powered content generation, WordPress integration, and automated outline creation for blog posts. It includes semantic keyword generation, competitor analysis, and automated content workflow management.

## Features
- **User Registration & Login**: Secure user management with hashed passwords and JWT authentication.
- **WordPress Account Management**: Connect, update, test, and delete multiple WordPress accounts per user.
- **Content Job Management**: Create and list content jobs with AI-powered processing.
- **AI-Powered Outline Generation**: Automated outline creation using semantic keywords and competitor analysis.
- **Semantic Keyword Generation**: AI-driven keyword research and SEO optimization.
- **Competitor Analysis**: Automated competitor URL scraping and keyword extraction.
- **WordPress API Integration**: Validates credentials and fetches site info using the WordPress REST API.
- **CORS Enabled**: Allows cross-origin requests for frontend integration.

## Project Structure
```
backend/
├── app/
│   ├── main.py                # Main FastAPI application
│   ├── auth.py                # Authentication utilities
│   ├── database.py            # Database session and models
│   ├── models.py              # SQLAlchemy models
│   ├── outline_generation.py  # AI-powered outline generation script
│   └── blog-AI/               # AI content generation modules
│       ├── main.py            # Blog-AI CLI entry point
│       ├── README.md          # Blog-AI documentation
│       ├── docs/              # Documentation files
│       └── src/               # Source code modules
│           ├── automation/    # Content automation
│           ├── competitor_analysis/ # Competitor scraping
│           ├── seo/           # SEO and keyword generation
│           ├── outline/       # Outline generation
│           ├── blog_sections/ # Blog section generators
│           ├── text_generation/ # Core text generation
│           └── testing/       # Test scripts
├── index.html                 # Landing page
├── pyproject.toml             # Project dependencies (uv)
├── uv.lock                    # Dependency lock file
├── requirements.txt           # Pip requirements
└── README.md                  # Project documentation
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- OpenAI API key
- PostgreSQL database
- WordPress sites with Application Passwords

### Installation
1. **Clone the repository**
2. **Install dependencies using uv** (recommended):
   ```sh
   uv sync
   ```
   Or using pip:
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (create a `.env` file):
   ```env
   SECRET_KEY=your_secret_key_here
   ALGORITHM=HS256
   DATABASE_URL=postgresql://username:password@localhost/database_name
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Set up the database**:
   ```sh
   # Create tables (if not already done)
   python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
   ```

5. **Run the server**:
   ```sh
   uv run fastapi dev app/main.py
   ```

### Running the Outline Generation Script
To process pending content jobs and generate outlines:
```sh
cd app
python outline_generation.py
```

## API Overview

### Authentication
- `POST /register` — Register a new user
- `POST /login` — Login and receive JWT token

### Content Jobs
- `GET /my-jobs` — List all jobs for the current user
- `POST /create-job` — Create a new content job (requires JWT)

### WordPress Account Management
- `POST /wordpress/connect` — Connect a new WordPress account
- `GET /wordpress/accounts` — List all connected WordPress accounts
- `PUT /wordpress/accounts/{account_id}` — Update a WordPress account
- `DELETE /wordpress/accounts/{account_id}` — Delete a WordPress account
- `POST /wordpress/test/{account_id}` — Test connection to a WordPress account
- `GET /wordpress/sites` — Get info about all connected WordPress sites

### Health & Static
- `GET /health` — Health check (database connection)
- `GET /` — Serve landing page (`index.html`)

## Authentication
All protected endpoints require a Bearer JWT token in the `Authorization` header:
```
Authorization: Bearer <token>
```
Obtain the token via the `/login` endpoint.

## Models
- **User**: username, password (hashed), name, email (optional), role
- **WordPressCredentials**: siteUrl, username, applicationPassword, userId
- **ContentJob**: title, main_keyword, related_keywords, article_word_count, article_length, competitor URLs, status, outline, etc.

## Error Handling
- Returns appropriate HTTP status codes and error messages for authentication, validation, and server errors.
- Logs errors and stack traces for debugging.

## Notes
- Ensure your database is set up and models are migrated before running the server.
- Application passwords are required for WordPress REST API access.
- CORS is enabled for all origins by default (adjust as needed for production).

## License
MIT (or specify your license)

---
Feel free to extend this documentation as your project evolves!
