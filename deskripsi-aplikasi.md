# CompareBuy

Build a full-stack web application named **CompareBuy**.

## Purpose

Help Indonesian consumers compare and choose technology products objectively. The application combines a curated gadget catalog, product specifications, review sentiment, warranty information, marketplace prices, a personalized recommendation wizard, and side-by-side comparison.

The current application supports these product categories:

* Smartphone
* Laptop
* Tablet
* TWS / audio
* Smartwatch

The current dataset contains 20 curated products stored in backend memory and mirrored by frontend fallback data. It does not currently use a database, user accounts, authentication, or persistent product administration.

## Current Stack

* Frontend: Next.js 14 App Router + React 18
* Frontend language: JavaScript with JSX
* Styling: Tailwind CSS 3
* Icons: Lucide React
* Backend: Python FastAPI
* Validation and response schemas: Pydantic 2
* HTTP client and scraper: HTTPX + BeautifulSoup4
* API style: REST API returning JSON
* Frontend deployment: Vercel-compatible Next.js application
* Backend deployment plan: Render
* Frontend deployment plan: Vercel
* Planned database: PostgreSQL
* Current database implementation: None; product data is held in Python memory

## Application Features

### 1. Landing Page

The landing page presents:

* CompareBuy branding and technology advisory positioning.
* A call-to-action to start the four-step Smart Wizard.
* A call-to-action to open the gadget catalog.
* Six feature pillars:
  * Smart Recommendation Wizard.
  * Weighted Dynamic Scoring Engine.
  * Side-by-Side Comparison Matrix.
  * Real User Sentiment Aggregator.
  * After-Sales & Warranty Index.
  * Live Marketplace Price Scraping.
* A category selector for featured products.
* A preview of curated products.
* A CTA banner to start the recommendation wizard.

### 2. Gadget Catalog

The catalog allows users to:

* Search by product name, brand, description, or tag.
* Filter by gadget category.
* Filter by brand.
* Filter by predefined budget ranges.
* Sort by recommendation score, lowest price, highest price, or name.
* Open a product detail modal.
* Add or remove a product from the comparison list.
* Use the filter panel on desktop or a mobile filter drawer on smaller screens.
* See loading placeholders and an empty state when no product matches.

The frontend first requests data from the FastAPI catalog endpoint. If the API is unavailable, it filters the local product dataset in `frontend/src/data/products.js`.

### 3. Smart Recommendation Wizard

The wizard has four steps:

1. **Choose Category**
   * Select smartphone, laptop, tablet, TWS/audio, or smartwatch.
2. **Set Budget**
   * Select a category-specific budget preset.
   * Adjust minimum and maximum budget with two range sliders.
3. **Choose Usage Scenarios**
   * Select one or more scenarios such as gaming, productivity, photography, content creation, business, student, fitness, multimedia, or casual use.
4. **Set Trade-Off Priorities**
   * Set importance from 1 to 5 for performance, camera, battery, display, build quality, and value.

The result page shows:

* The best recommendation.
* Additional ranked alternatives.
* Total recommendation score.
* Budget fit status.
* Score breakdown.
* Contextual explanation for the recommendation.
* Buttons to open product details or add products to the comparison dock.

If the backend scoring endpoint is unavailable, the frontend runs a simplified local scoring fallback.

### 4. Product Comparison

The comparison flow supports up to four products at once.

* Products can be added from product cards, the product modal, the comparison page, or the floating dock.
* The selected products are saved to `localStorage` under `comparebuy_dock`.
* The comparison matrix displays price, warranty, technical specifications, and score fields.
* The best value in each comparable row is highlighted automatically.
* Users can remove individual products or clear the entire comparison list.
* An empty state guides the user back to the catalog.

The backend accepts between two and four product IDs for a comparison request.

### 5. Product Detail Modal

Each product can be opened in a modal with four tabs:

* **Spesifikasi**: display, refresh rate, processor, RAM, storage, battery, camera, operating system, weight, connectivity, water resistance, build material, and special features.
* **User Experience & Review**: rating, review count, community summary, pros, and cons.
* **Garansi & Purna Jual**: warranty duration, claim ease, service center count, warranty coverage, and warranty index score.
* **Marketplace Live & Value**: MSRP, marketplace offers, cheapest offer, potential savings, seller, availability, and store links.

### 6. Theme and Layout

The shared application layout includes:

* Responsive sticky navigation bar.
* Indonesian interface labels.
* Dark mode and light mode.
* Theme preference persisted in `localStorage` under `comparebuy_theme`.
* Floating comparison dock.
* Global product detail modal.
* Responsive footer.
* Loading, empty, hover, and transition states.

## Data Models

The main Pydantic product model is `Product` in `backend/app/models.py`.

### Product

* `id`
* `name`
* `brand`
* `category`
* `price`
* `image`
* `description`
* `specs`
* `review_sentiment`
* `warranty`
* `marketplace_links`
* `tags`
* `release_year`
* `score_performance`
* `score_camera`
* `score_battery`
* `score_display`
* `score_build_quality`
* `score_value`
* `score_audio`
* `score_software`

### ProductSpecs

The flexible specification object may contain:

* `display`
* `processor`
* `ram`
* `storage`
* `battery`
* `camera`
* `os`
* `weight`
* `connectivity`
* `screen_size`
* `refresh_rate`
* `resolution`
* `gpu`
* `water_resistance`
* `driver_size`
* `anc`
* `codec`
* `sensors`
* `build_material`
* `special_features`

### ReviewSentiment

* `overall_score`
* `total_reviews`
* `pros`
* `cons`
* `summary`

### WarrantyInfo

* `duration_months`
* `coverage`
* `claim_ease`
* `official_service_centers`
* `score`

### MarketplacePrice

* `marketplace`
* `price`
* `url`
* `seller`
* `available`

## Recommendation Algorithm

The scoring engine is implemented in `backend/app/scoring.py` using weighted Multi-Criteria Decision Analysis (MCDA).

### Scoring dimensions

* Performance
* Camera
* Battery
* Display
* Build quality
* Value for money
* Audio
* Software and updates

### Scoring flow

1. Filter products by the selected category.
2. Read user priority values, defaulting an unspecified dimension to `3`.
3. Add scenario-specific boosts.
4. Normalize all weights so their total is `1.0`.
5. Calculate the weighted product score.
6. Apply a budget modifier:
   * Within budget: `+5`.
   * Below the minimum budget: `+2`.
   * Above the maximum budget by up to 20%: `-5`.
   * Above the maximum budget by more than 20%: `-15`.
7. Generate a contextual `why_this_product` explanation from the three strongest weighted dimensions.
8. Sort products by final score in descending order and assign ranks.

The backend supports scenario boosts for gaming, productivity, photography, social media, content creation, business, student, fitness, multimedia, and casual use.

## Marketplace Price Scraping

The price service is implemented in `backend/app/scraper.py`.

* It attempts to read search results from Tokopedia, Shopee, and Lazada.
* Requests run concurrently with `asyncio.gather()`.
* HTTP requests use HTTPX with browser-like headers and a timeout.
* HTML is parsed with BeautifulSoup4.
* If a marketplace cannot be scraped, the service uses curated fallback prices.
* Fallback prices receive a small random variation.
* Results are sorted from the lowest price to the highest price.
* The response includes the marketplace, price, seller, availability, URL, and update time.

The price result is therefore not guaranteed to be a fully live result; it may contain fallback data when marketplace pages are dynamic, blocked, or unavailable.

## REST API Routes

### Service

* `GET /` - Return service name, version, health status, and documentation path.
* `GET /health` - Return the backend health status.

### Catalog

* `GET /api/products` - List products with search, category, brand, price, tag, sorting, and pagination query parameters.
* `GET /api/products/{product_id}` - Return one product by ID.
* `GET /api/brands` - Return unique brands.
* `GET /api/tags` - Return unique tags.
* `GET /api/categories` - Return available product categories.

Supported catalog query parameters:

* `search`
* `category`
* `brand`
* `min_price`
* `max_price`
* `tags`
* `sort_by`: `score`, `price_asc`, `price_desc`, or `name`
* `page`
* `per_page`

### Recommendations

* `POST /api/score` - Calculate ranked recommendations from category, budget, scenarios, and priorities.

### Comparison

* `POST /api/compare` - Compare two to four products and return specification highlights.

### Marketplace Prices

* `GET /api/prices/{product_id}` - Fetch marketplace prices with fallback handling.

## API Response Models

The backend defines these response and request schemas:

* `CatalogResponse`
* `WizardInput`
* `ScoreBreakdown`
* `ScoredProduct`
* `ScoringResponse`
* `CompareRequest`
* `SpecHighlight`
* `CompareResponse`
* `PriceResponse`

## Project Structure

```text
Rekayasa Perangkat Lunak/
  README.md
  format-jawaban.md
  perbaikan.md
  deskripsi-aplikasi.md
  backend/
    Dockerfile
    Procfile
    railway.json (legacy deployment configuration)
    requirements.txt
    test_api.py
    .env.example
    app/
      __init__.py
      main.py
      models.py
      products.py
      scoring.py
      scraper.py
      routers/
        __init__.py
        catalog.py
        compare.py
        prices.py
        scoring.py
  frontend/
    package.json
    package-lock.json
    next.config.js
    tailwind.config.js
    postcss.config.js
    jsconfig.json
    .env.example
    src/
      app/
        layout.js
        page.js
        globals.css
        catalog/page.js
        compare/page.js
        wizard/page.js
      components/
        catalog/
          FilterPanel.js
          ProductCard.js
          SearchBar.js
        compare/
          ComparisonMatrix.js
        layout/
          FloatingDock.js
          Footer.js
          Navbar.js
        product/
          ProductModal.js
          TabReviews.js
          TabSpecs.js
          TabValue.js
          TabWarranty.js
        ui/
          PriceTag.js
          ScoreBadge.js
          ThemeToggle.js
        wizard/
          StepBudget.js
          StepCategory.js
          StepPriority.js
          StepScenario.js
          WizardResults.js
      context/
        CompareContext.js
        ThemeContext.js
      data/products.js
      lib/api.js
```

## Environment Configuration

### Backend

For the planned PostgreSQL integration and Render deployment, configure the backend environment variables as follows:

```env
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/comparebuy
```

`DATABASE_URL` is the planned PostgreSQL connection string. The current FastAPI code does not read this variable yet because product data is still stored in memory.

### Frontend

Copy `frontend/.env.example` to `frontend/.env.local` and configure:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Installation and Startup

### Backend

```bash
cd backend
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

* API: `http://localhost:8000`
* Swagger UI: `http://localhost:8000/docs`
* ReDoc: `http://localhost:8000/redoc`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`.

Available frontend scripts:

* `npm run dev` - Start the Next.js development server.
* `npm run build` - Build the production application.
* `npm run start` - Start the production application after building.
* `npm run lint` - Run the configured Next.js lint command.

## Docker and Deployment Plan

The backend includes a multi-stage Dockerfile based on Python 3.12 slim. It installs dependencies in a build stage, copies the installed packages into the runtime image, exposes port `8000`, and provides a `/health` container health check. This image can be used by Render for backend deployment.

Target deployment:

* **Database: PostgreSQL** hosted by a managed PostgreSQL provider or Render PostgreSQL.
* **Backend: Render**, using the `backend` directory, Dockerfile or Python build configuration, and Uvicorn as the start command.
* **Frontend: Vercel**, using the `frontend` directory and `NEXT_PUBLIC_API_URL` pointing to the deployed Render backend.
* **CORS:** Set the backend `ALLOWED_ORIGINS` value to include the local frontend URL and the production Vercel URL.

Recommended Render backend settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

The existing `railway.json` is retained in the repository as a legacy deployment configuration and is not the target deployment platform.

## Verification

Run the backend API smoke test from the `backend` directory:

```bash
python test_api.py
```

The test verifies:

* Health check.
* Catalog loading.
* Recommendation scoring.
* Product comparison.
* Marketplace price response and fallback data.

## Current Limitations

* Product data is in-memory and resets when the backend restarts.
* PostgreSQL integration is planned but is not implemented in the current code.
* There is no ORM, migration, seed script, or CRUD administration.
* There is no authentication or user profile system.
* The marketplace service uses static fallback prices with random variation when scraping fails.
* Backend and frontend product datasets are similar but not perfectly identical.
* Backend scoring uses eight dimensions, while the frontend fallback uses six dimensions.
* Product image URLs are external in the frontend seed data and local `/images/...` paths in the backend seed data; image availability depends on the active data source.
* The frontend is JavaScript/JSX, not TypeScript.
