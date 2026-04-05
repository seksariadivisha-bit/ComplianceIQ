# Implementation Plan

## Why this repo starts as a static prototype

The local environment currently has Python 3 available but no `node`, `npm`, `pnpm`, `yarn`, or frontend framework toolchain. Rather than leave you with only notes, this repo includes a working prototype that can be served with `python3 -m http.server`.

## Recommended production path

1. Install Node.js
2. Bootstrap a Next.js app with TypeScript
3. Use [`db/schema.sql`](/Users/divi/Documents/New%20project/db/schema.sql) as the starting point for Supabase migrations
4. Port the matching logic from [`app.js`](/Users/divi/Documents/New%20project/app.js) into:
   - server actions
   - typed utility modules
   - background jobs for alerts and recalculations
5. Replace `localStorage` with:
   - Supabase Auth
   - Postgres tables
   - row-level security policies

## Suggested MVP build order

1. Auth and tenant setup
2. Company onboarding
3. Compliance obligation catalog + matching
4. Company compliance workspace
5. Scheme catalog + explainable matching
6. Dashboard metrics and alerts
7. Admin content management
8. Payments and subscriptions

## Product corrections from the Emergent transcript

- The transcript mixed a Python/Mongo backend with a React frontend, while the product brief recommends Next.js + Supabase. The schema in this repo aligns to the latter.
- The earlier output had incomplete routing and partial page creation. This prototype keeps the UX coherent in one place.
- The matching engine here is deterministic and explainable, which is critical for a compliance product.
