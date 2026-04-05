# ComplianceIQ

ComplianceIQ is a B2B SaaS concept for Indian enterprises: one product for compliance visibility and government-scheme discovery.

The original Emergent transcript you shared was helpful as a product spec, but there was no usable codebase in this repository. This repo now contains:

- A dependency-free interactive prototype in plain HTML/CSS/JS
- A production-oriented PostgreSQL/Supabase schema in [`db/schema.sql`](/Users/divi/Documents/New%20project/db/schema.sql)
- A short implementation plan for porting this into a real Next.js + Supabase app later

## What is included

- [`index.html`](/Users/divi/Documents/New%20project/index.html): landing page + onboarding + dashboard shell
- [`styles.css`](/Users/divi/Documents/New%20project/styles.css): visual system and layout
- [`app.js`](/Users/divi/Documents/New%20project/app.js): onboarding logic, compliance matching, scheme matching, dashboard calculations
- [`db/schema.sql`](/Users/divi/Documents/New%20project/db/schema.sql): normalized schema for a future production backend
- [`docs/implementation-plan.md`](/Users/divi/Documents/New%20project/docs/implementation-plan.md): what to build next when a JS toolchain is available

## Run locally

This machine does not currently have Node.js installed, so the product is intentionally built with the Python standard library plus SQLite.

1. From this folder, run:

```bash
python3 server.py
```

2. Open [http://localhost:8000](http://localhost:8000)

## Submit-ready hosting

For an application or demo submission, the normal package is:

- a stable hosted URL
- the code repository
- optionally a short Loom demo

This repo is now prepared for a quick public Render deployment:

- [`requirements.txt`](/Users/divi/Documents/New%20project/requirements.txt) installs the Python dependencies plus `gunicorn`
- [`render.yaml`](/Users/divi/Documents/New%20project/render.yaml) defines a Render web service
- `server.py` now respects a `DB_PATH` environment variable, so the hosted SQLite location can be configured

### Fastest production-ish deploy on Render

1. Push this folder to a GitHub repository.
2. In Render, choose `New +` → `Blueprint`.
3. Select the GitHub repo.
4. Render will read [`render.yaml`](/Users/divi/Documents/New%20project/render.yaml) and provision a Python web service.
5. After deploy, use the generated `onrender.com` URL in your application form.

### Why this is the right submission path

- A tunnel link is not reliable enough for an application review.
- A real hosted URL stays up after your laptop sleeps or disconnects.
- This free-path setup is suitable for a demo/application link, but its local SQLite data is ephemeral and may reset on redeploy or restart.

## Prototype features

- Landing page and guided company intake
- SQLite-backed company records
- Rule-based compliance obligation matching
- Rule-based government scheme matching with explainability
- Dashboard with risk score, burn rate, upcoming obligations, and scheme upside
- Compliance workspace with persistent status updates
- Schemes workspace with persistent application/received states
- Lightweight local API from `server.py`
- Official-source registry for MCA, GST, Udyam, Startup India, myScheme, FSSAI, DGFT, EPFO, ESIC, India Code, Labour Gazette, and data.gov.in
- Company verification plan that asks for official identifiers such as CIN, GSTIN, Udyam number, DPIIT certificate, FSSAI license number, and IEC
- Source-health refresh endpoint so the app can record whether official portals are reachable from the local environment
- Live myScheme catalog sync that caches official scheme records with close dates, ministries, categories, tags, and source URLs
- Company-specific official-scheme matching that excludes expired schemes and explains why a live official scheme appears relevant

## Important note

This is now a real local MVP with a backend database, an official-source integration layer, and a live myScheme sync. The product stores official identifiers, routes verification to official sources only, and now pulls current official scheme records into the local database. Some official systems are still captcha-driven portals or require manual verification, so coverage is honest and provenance-first rather than magical or complete-by-default.
