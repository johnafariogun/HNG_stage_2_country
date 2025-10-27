# Country Currency & Exchange API

FastAPI service that fetches country data and exchange rates, caches them in MySQL, and exposes CRUD endpoints.

Setup

1. Create a Python virtual environment and install dependencies:

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt

2. Copy and edit `.env.example` to `.env` and set your MySQL credentials.

3. Create the MySQL database specified in `.env` (default: `country_cache`).

4. Run the app with uvicorn:

   .\.venv\Scripts\Activate.ps1; uvicorn country_service.main:app --host 0.0.0.0 --port 8000 --reload

Endpoints

- POST /countries/refresh — fetch countries and exchange rates and cache in DB
- GET /countries — list cached countries; supports ?region=& ?currency=& ?sort=gdp_desc
- GET /countries/{name} — get single country by name
- DELETE /countries/{name} — delete a country by name
- GET /status — shows total countries and last refresh timestamp
- GET /countries/image — serve generated summary image (cache/summary.png)

Notes

- The refresh process fetches data first and only updates the DB if external fetches succeed.
- Summary image is saved to `cache/summary.png`.
