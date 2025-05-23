# Lovelog Backend

A FastAPI backend application for the Lovelog project with configurable CORS middleware.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create environment file:**
   Create a `.env` file in the root directory with the following configuration:
   ```env
   # CORS Configuration
   CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
   CORS_ALLOW_CREDENTIALS=true
   CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
   CORS_ALLOW_HEADERS=*

   # Application Configuration
   APP_HOST=0.0.0.0
   APP_PORT=8000
   APP_RELOAD=true
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

## Environment Variables

### CORS Configuration
- `CORS_ALLOW_ORIGINS`: Comma-separated list of allowed origins (default: localhost variants)
- `CORS_ALLOW_CREDENTIALS`: Allow credentials in CORS requests (default: true)
- `CORS_ALLOW_METHODS`: Comma-separated list of allowed HTTP methods (default: GET,POST,PUT,DELETE,OPTIONS)
- `CORS_ALLOW_HEADERS`: Comma-separated list of allowed headers (default: *)

### Application Configuration
- `APP_HOST`: Host to bind the server (default: 0.0.0.0)
- `APP_PORT`: Port to run the server (default: 8000)
- `APP_RELOAD`: Enable auto-reload in development (default: true)

## API Documentation

Once running, you can access:
- Interactive API docs: http://localhost:8000/docs
- Alternative API docs: http://localhost:8000/redoc

## Endpoints

- `GET /`: Welcome message
- `GET /items`: List all items
- `GET /items/{item_id}`: Get a specific item
- `POST /items`: Create a new item
