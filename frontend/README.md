# RabbitHole Frontend

React frontend for the RabbitHole research paper discovery tool.

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Flask backend running on `http://localhost:5000` (see main project README)

## Setup

### Install dependencies

```bash
npm install
```

## Development

### Run development server

```bash
npm run dev
```

The app will be available at `http://localhost:5173` (or the next available port).

The Vite dev server is configured to proxy API requests to the Flask backend at `http://localhost:5000`.

### Make sure the backend is running

Before using the frontend, ensure the Flask backend is running:

1. **Start Redis** (required for API calls):

   ```bash
   docker compose up -d redis
   ```

2. **Start Flask backend** (choose one):
   - **Option A: Using Docker**:
     ```bash
     docker compose up -d web
     ```
   - **Option B: Run locally** (What I did):

     ```bash
     # Set environment variables in .env file in the root path
     REDIS_CACHE_URL="redis://localhost:6379/2"
     CELERY_BROKER_URL="redis://localhost:6379/0"
     CELERY_RESULT_BACKEND="redis://localhost:6379/1"

     # Run Flask
     python run.py
     ```

## Build

### Build for production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Linting

### Lint code

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable React components
│   ├── pages/           # Page components (HomePage, ResultsPage)
│   ├── types/           # TypeScript type definitions
│   ├── assets/          # Static assets (images, etc.)
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── public/              # Public static files
├── dist/                # Production build output
└── vite.config.ts       # Vite configuration
```
