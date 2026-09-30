Build a full-stack web application named **CompareBuy**.

Purpose:
Help Indonesian consumers compare and choose technology products using a curated gadget catalog, detailed specifications, community review summaries, warranty information, marketplace prices, personalized recommendations, and side-by-side comparisons. The application supports smartphones, laptops, tablets, TWS/audio devices, and smartwatches.

The current source has a Next.js frontend and FastAPI backend. Product information is presently held in backend Python memory and mirrored in frontend fallback data; there is no database, user account, authentication, or product administration. The database in this specification is the proposed persistent design for completing the application, not a claim about the current implementation.

Use this stack:

* Frontend: Next.js 14 App Router + React 18 + JavaScript/JSX
* Styling: Tailwind CSS 3
* Icons: Lucide React
* Backend: Python 3.12+ + FastAPI
* Validation and API schemas: Pydantic 2
* Database: PostgreSQL
* ORM and migrations: SQLAlchemy 2.x + Alembic (to be added for database integration)
* API style: REST API returning JSON
* HTTP client and marketplace parsing: HTTPX + BeautifulSoup4
* Frontend deployment: Vercel
* Backend deployment: Render using the existing Dockerfile or Python runtime configuration
* Local frontend-to-backend URL: `NEXT_PUBLIC_API_URL`
* Backend configuration: `.env.example`, including `ALLOWED_ORIGINS` and `DATABASE_URL`

Code rules:

* Keep the existing separation between `frontend/` and `backend/`; a TypeScript monorepo is not required.
* Use Python `snake_case` for backend modules, functions, variables, Pydantic fields, and JSON properties. Use PascalCase for Python classes and Pydantic models.
* Use JavaScript `camelCase` for variables and functions, and PascalCase for React component names and files.
* Keep API request and response property names consistent with the existing snake_case Pydantic schemas and frontend client.
* Keep database access behind backend data-access/service boundaries; do not connect the browser directly to PostgreSQL.
* Keep the frontend fallback catalog compatible with the backend product contract, and document its relationship to the seeded catalog to prevent data drift.
* Do not add authentication or user-specific saved histories in the first version; comparison selections and theme preference remain browser-local.
* Do not add comments unless they clarify non-obvious behavior. Keep lines below 150 characters where practical.
* Validate all external input with Pydantic and return consistent HTTP status codes and useful error details.

Main entities:

1. Brand

	* `id` (primary key)
	* `name` (required, unique)
	* `created_at`
	* One Brand has many Products.

2. Product

	* `id` (primary key; preserve existing identifiers such as `sm-001`)
	* `name` (required)
	* `brand_id` (foreign key to Brand)
	* `category` (enum: `smartphone`, `laptop`, `tablet`, `tws`, `smartwatch`)
	* `price` (curated base/MSRP price in whole Indonesian rupiah)
	* `image_url`
	* `description`
	* `release_year`
	* `score_performance`, `score_camera`, `score_battery`, `score_display`
	* `score_build_quality`, `score_value`, `score_audio`, `score_software`
	* `is_active`, `created_at`, `updated_at`
	* One Product has one ProductSpecs, one ReviewSentiment, and one WarrantyInfo record; it can have many Tags, MarketplaceLinks, and MarketplacePrice snapshots.

3. ProductSpecs

	* `product_id` (primary key and foreign key to Product)
	* `specifications` (JSONB; category-specific keys such as `display`, `processor`, `ram`, `storage`, `battery`, `camera`, `os`, `weight`, `connectivity`, `screen_size`, `refresh_rate`, `resolution`, `gpu`, `water_resistance`, `driver_size`, `anc`, `codec`, `sensors`, `build_material`, and `special_features`)
	* `updated_at`
	* One-to-one with Product. JSONB preserves the existing flexible `ProductSpecs` contract without requiring nullable columns for every device category.

4. ReviewSentiment

	* `product_id` (primary key and foreign key to Product)
	* `overall_score` (community summary rating)
	* `total_reviews`
	* `pros` (JSONB array of strings)
	* `cons` (JSONB array of strings)
	* `summary`
	* `updated_at`
	* One-to-one with Product. This stores an aggregated summary, not individual review records or verified review provenance.

5. WarrantyInfo

	* `product_id` (primary key and foreign key to Product)
	* `duration_months`
	* `coverage`
	* `claim_ease` (scale 1-10)
	* `official_service_centers`
	* `score` (warranty transparency/index score, 0-100)
	* `updated_at`
	* One-to-one with Product.

6. Tag

	* `id` (primary key)
	* `name` (required, unique)
	* Many-to-many with Product through ProductTag.

7. ProductTag

	* `product_id` (foreign key to Product)
	* `tag_id` (foreign key to Tag)
	* Composite primary key: (`product_id`, `tag_id`).

8. Marketplace

	* `id` (primary key)
	* `code` (unique stable value, such as `tokopedia`, `shopee`, or `lazada`)
	* `name` (display name)
	* One Marketplace has many MarketplaceLinks and MarketplacePrice snapshots.

9. MarketplaceLink

	* `id` (primary key)
	* `product_id` (foreign key to Product)
	* `marketplace_id` (foreign key to Marketplace)
	* `url`
	* Unique constraint on (`product_id`, `marketplace_id`).

10. MarketplacePrice

	* `id` (primary key)
	* `product_id` (foreign key to Product)
	* `marketplace_id` (foreign key to Marketplace)
	* `price` (whole Indonesian rupiah)
	* `seller`
	* `url`
	* `available`
	* `source` (enum: `scraped` or `fallback`)
	* `captured_at` (timestamp with time zone)
	* Product and Marketplace each have many price snapshots. The source field distinguishes fetched data from curated fallback data.

Database rules:

* Use PostgreSQL with UTF-8 encoding. Store database timestamps in UTC and return timezone-aware ISO 8601 timestamps from the API; display them in WIB in the UI where appropriate.
* Use SQLAlchemy models and Alembic migrations. Seed the database from the curated 20-product dataset currently in `backend/app/products.py`, including specifications, sentiment summaries, warranty data, tags, and marketplace links.
* Preserve existing product IDs so browser fallback records and API records continue to refer to the same products.
* `Brand.name`, `Tag.name`, and `Marketplace.code` must be unique and non-empty.
* Product name and category are required. `Product.price` must be greater than or equal to zero; `release_year` must be a plausible positive year.
* Each Product must have exactly one ProductSpecs, ReviewSentiment, and WarrantyInfo record. Deleting a product may cascade to its dependent detail, tag association, link, and price snapshot rows.
* Product score fields and `WarrantyInfo.score` must be in the range 0-100. `ReviewSentiment.overall_score` must be in the range 0-5 and `total_reviews` must be non-negative.
* `WarrantyInfo.duration_months` and `official_service_centers` must be non-negative; `claim_ease` must be from 1 through 10.
* Marketplace prices must be positive whole rupiah values, have a valid URL and capture timestamp, and record whether they came from a live scrape or fallback.
* Enforce numeric ranges and non-negative values with PostgreSQL `CHECK` constraints as well as Pydantic validation; database constraints remain authoritative for persisted data.
* Enforce unique product-tag pairs and one marketplace link per product/marketplace. Use foreign keys to prevent orphaned records.
* Add indexes for product category, brand, price, active status, and name; index marketplace price lookups by (`product_id`, `marketplace_id`, `captured_at`). Add suitable indexes for tag filtering.
* Save price observations as append-only snapshots rather than silently overwriting prior observations. A failed scrape must not erase the latest known price. Do not label fallback data as live data in the UI or API response.
* Comparison selections, wizard input/results, and theme are not persisted to PostgreSQL in version one. Comparison and theme remain in `localStorage`; scoring is calculated per request.
* Seed and migration operations must be repeatable and must not create duplicate brands, tags, marketplaces, or products.

Backend features:

1. Product Catalog

	* List and return product details from PostgreSQL after database integration; initially, the current in-memory curated catalog is the data source.
	* Support search by name, brand, description, and tags; filter by category, brand, price range, and tags; sort by score, ascending/descending price, or name; and paginate results.
	* Return the available categories, brands, and tags for filter controls.
	* Return a clear not-found response for an unknown product.

2. Smart Recommendation and MCDA Scoring

	* Accept category, minimum and maximum budget, one or more usage scenarios, and priority weights from 1 to 5.
	* Support the existing scenarios: gaming, productivity, photography, social media, content creation, business, student, fitness, multimedia, and casual.
	* Score the eight dimensions: performance, camera, battery, display, build quality, value, audio, and software.
	* Default unspecified priority weights to 3, apply scenario boosts, normalize weights, apply the existing budget modifiers (+5 within, +2 below, -5 up to 20% above, -15 more than 20% above), rank results, and return a contextual explanation and score breakdown.
	* Do not persist wizard input or recommendation results in version one.

3. Side-by-Side Comparison

	* Accept 2-4 distinct product IDs and return product data plus comparable specification, score, price, and warranty highlights.
	* Highlight the best value when a comparison rule can determine one. Lower weight and lower price are better; higher score dimensions and warranty index are better.
	* Reject requests outside the 2-4 product limit and return not found when any requested product does not exist.

4. Marketplace Price Collection

	* Attempt concurrent price reads from Tokopedia, Shopee, and Lazada using HTTPX, bounded timeouts, and HTML parsing.
	* Use curated fallback prices for marketplaces that fail or do not expose parseable results. Return sorted offers, seller, URL, availability, source, and update time.
	* Persist collected offers as MarketplacePrice snapshots after database integration; do not update product MSRP from marketplace observations.
	* Handle network failures, timeouts, blocked or changed markup, invalid price text, and missing fallback data without failing the whole application.
	* Respect marketplace terms and rate limits. Explain in API/UI responses when a result is fallback or stale; do not promise that every result is live.

5. Service and Configuration

	* Provide root service information, a health endpoint, and FastAPI OpenAPI documentation.
	* Configure CORS from `ALLOWED_ORIGINS` for the local frontend and deployed frontend.
	* Read database configuration from `DATABASE_URL` after PostgreSQL integration; never commit secrets.
	* Return useful validation and service errors without exposing stack traces or credentials.

Frontend pages:

1. Home (`/`)

	* Present CompareBuy and its gadget-advisory purpose, links to the wizard and catalog, six feature highlights, featured products with category selection, and a wizard call to action.

2. Gadget Catalog (`/catalog`)

	* Load the catalog through the API and use `frontend/src/data/products.js` as a fallback when the API is unavailable.
	* Provide instant search, category/brand/budget filters, sorting, product cards, loading placeholders, and an empty state.
	* Open a product detail modal and let users add/remove products from the comparison dock.
	* Provide a desktop filter panel and mobile filter drawer.

3. Smart Recommendation Wizard (`/wizard`)

	* Provide four steps: category, budget, usage scenarios, and trade-off priorities.
	* Show ranked recommendations, total score, score breakdown, budget fit, and the `why_this_product` explanation.
	* Allow users to open product details or add a recommendation to the comparison dock; provide a reset action and loading/error states.
	* Use the backend scoring endpoint with a simplified client-side fallback when unavailable.

4. Product Comparison (`/compare`)

	* Compare up to four products in a side-by-side matrix, with automatic highlights for best comparable values.
	* Allow adding/removing products and clearing the comparison list. Persist the list in `localStorage` under `comparebuy_dock`.
	* Provide an empty state that links back to the catalog.

5. Shared Product Detail Modal

	* Provide four tabs: technical specifications, user experience/review sentiment, warranty/after-sales, and marketplace prices/value.
	* Show the product image, brand, category, curated price, and a comparison action. Support mobile tab navigation and modal scrolling.

UI requirements:

* Use Indonesian for application labels, buttons, messages, and validation text.
* Provide a responsive layout for desktop and mobile, including sticky navigation, footer, floating comparison dock, and global product modal.
* Support dark and light themes. Persist the theme in `localStorage` under `comparebuy_theme`, and respect system preference when no preference has been saved.
* Limit comparison to four distinct products and clearly communicate the limit.
* Format prices as Indonesian rupiah. Display review score/count, warranty details, marketplace seller/availability, and whether marketplace prices are scraped or fallback data.
* Include loading, empty, error, active/selected, and disabled states for data-driven controls.
* Ensure keyboard-accessible controls, labels for icon-only buttons, visible focus states, semantic headings, and useful image alternative text.
* Avoid charts in the first version; emphasize catalog cards, structured specification tables, score badges, and comparison highlights.

Required API routes:

* `GET /` - Return service name, version, health status, and docs path.
* `GET /health` - Return backend health status.
* `GET /api/products` - List/filter/sort/paginate products. Query parameters: `search`, `category`, `brand`, `min_price`, `max_price`, `tags` (comma-separated), `sort_by` (`score`, `price_asc`, `price_desc`, `name`), `page`, and `per_page`.
* `GET /api/products/{product_id}` - Return one product.
* `GET /api/brands` - Return available brands.
* `GET /api/tags` - Return available tags.
* `GET /api/categories` - Return supported product categories.
* `POST /api/score` - Accept wizard preferences and return ranked scoring results.
* `POST /api/compare` - Accept 2-4 product IDs and return products and comparison highlights.
* `GET /api/prices/{product_id}` - Collect marketplace prices with fallback handling and return their source/update time.

Deliverables:

* Complete Next.js frontend and FastAPI backend source code.
* PostgreSQL schema implemented with SQLAlchemy, Alembic migrations, and repeatable seed data for the curated catalog.
* `.env.example` files documenting frontend API URL and backend CORS/database configuration without real secrets.
* README covering prerequisites, local setup, database startup/configuration, migrations, seeding, frontend/backend startup, API documentation, testing, and Vercel/Render deployment.
* Backend API smoke tests for health, catalog, scoring, comparison, and marketplace price fallback; add database tests for constraints and persistence when the database integration is implemented.
* Ensure the frontend builds and the backend starts; verify the catalog, wizard, comparison, and price flows with both normal API responses and documented fallback behavior.

Project structure:

```text
Rekayasa Perangkat Lunak/
  README.md
  requirement-revisi.md
  backend/
	 Dockerfile
	 Procfile
	 railway.json
	 requirements.txt
	 test_api.py
	 .env.example
	 migrations/                 # Alembic migrations (to be added)
	 app/
		__init__.py
		main.py
		models.py                 # Pydantic API schemas
		products.py               # Current curated seed/fallback catalog
		scoring.py
		scraper.py
		db.py                     # Database engine/session (to be added)
		entities/                 # SQLAlchemy database entities (to be added)
		repositories/             # Database queries (to be added)
		routers/
		  __init__.py
		  catalog.py
		  compare.py
		  prices.py
		  scoring.py
	 seed.py                     # Repeatable PostgreSQL seed command (to be added)
  frontend/
	 package.json
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
		  compare/
		  layout/
		  product/
		  ui/
		  wizard/
		context/
		  CompareContext.js
		  ThemeContext.js
		data/products.js
		lib/api.js
```

Shared package requirements:

* A cross-language TypeScript shared package is not required because the current backend is Python and the frontend is JavaScript. Keep the existing `frontend/` and `backend/` project layout.
* Treat the Pydantic schemas in `backend/app/models.py` and the FastAPI OpenAPI document as the canonical API contract. Keep frontend request/response handling in `frontend/src/lib/api.js` aligned with that contract.
* Do not maintain duplicate business scoring or database definitions in the frontend. The frontend fallback may provide degraded behavior while offline, but must remain compatible with the API product shape and must not be treated as the persistent source of truth.
* If shared API artifacts are introduced later, generate or validate them from OpenAPI rather than copying model definitions by hand. Keep database entities private to the backend; expose only validated API schemas.
