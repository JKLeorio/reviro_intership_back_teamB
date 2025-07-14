# Reviro intership team B back project


## Requirements

- Docker (optional, but recommended)
- Python 3.8+

## Setup and Run

### 1. Clone the repository and set env

```bash
git clone git@github.com:JKLeorio/reviro_intership_back_teamB.git
cd reviro_intership_back_teamB
```
Create a .env file and pass the filled values ​​from .env.example to it

### 2. Run with Docker (recommended)

Build and start the container:

```bash
docker compose build
docker compose up
```

This will build the Docker image, run tests and migrations, and start the FastAPI server with Uvicorn.

The API will be available at:  
`http://localhost:8000`

### 3. Run locally without Docker

#### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh # Linux/macOS
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"    # Windows
```

#### Create and activate virtual environment, install dependencies

```bash
uv sync
```

#### Run tests

```bash
uv run pytest tests\
```

#### Run database migrations

```bash
uv run alembic upgrade head
```

#### Start the FastAPI server

```bash
uv run main.py
```

The API will be available at:  
`http://localhost:8000`

## Alembic commands

- To create a new migration:

```bash
uv run alembic revision --autogenerate -m "Migration message"
```

- To apply migrations:

```bash
uv run alembic upgrade head
```

## API Documentation

Once running, visit the interactive API docs at:  
`http://localhost:8000/docs` (Swagger UI)  
or  
`http://localhost:8000/redoc` (ReDoc)