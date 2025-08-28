# Backend - Stock Data API

This is the backend service for the stock data application that provides stock information via Alpha Vantage API.

## Prerequisites

- Docker and Docker Compose installed
- Alpha Vantage API key in the root `.env` file

## Setup

1. Make sure you have the `.env` file in the project root with your Alpha Vantage API key:
   ```
   ALPHAVANTAGE_API_KEY=your_api_key_here
   ```

2. Run the backend service:
   ```bash
   docker-compose up --build
   ```

## API Endpoints

- `GET /api/stock/{symbol}` - Get stock data for a specific symbol
  - Example: `http://localhost:8000/api/stock/AAPL`

## Features

- Caching with TTL (60 seconds)
- Rate limit handling
- Error handling for API issues
- CORS enabled for frontend integration

## Development

The service runs on port 8000 and includes hot reload for development.
