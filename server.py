from __future__ import annotations

import copy
import json
import mimetypes
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from engine import (
    SCHEMES_CATALOG,
    build_obligations,
    build_scheme_opportunities,
    build_schemes,
    compute_metrics,
    discover_company_profile,
    enrich_company_runtime,
    evaluate_scheme,
    evaluate_scheme_review,
    scheme_display_metadata,
    sync_obligation_statuses,
    validate_company_payload,
)
from company_discovery import build_website_context, looks_like_website
from official_sources import (
    active_official_sources,
    build_identifier_questions,
    build_verification_plan,
    rank_company_myscheme_matches,
    refresh_source_health,
    sync_myscheme_catalog,
)

UTC = timezone.utc

# ── SETUP ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get("DB_PATH", str(ROOT / "db" / "complianceiq.sqlite3")))
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5001))

# Suppress load_dotenv getcwd error in sandbox
try:
    dotenv.load_dotenv()
except Exception:
    pass

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
CORS(app)

sessions: dict[str, dict] = {}  # session_id -> inferred profile dict

UNKNOWN_FLAG_FIELDS = {
    "has_gstin",
    "is_export_oriented",
    "has_foreign_investment",
    "is_listed",
    "deducts_tds",
    "has_factory_operations",
    "handles_food_products",
    "has_rd_collaboration",
    "has_new_hires",
    "women_led",
    "has_scst_founder",
    "uses_contract_labour",
    "uses_interstate_migrant_workers",
    "serves_defence_sector",
    "controlled_items_exposure",
    "generates_hazardous_waste",
    "has_warehouse",
    "has_cold_chain",
    "has_primary_processing",
    "has_b2b_receivables",
    "has_patent_activity",
    "regulated_financial_entity",
    "has_healthcare_facility",
    "has_diagnostic_lab",
    "project_based_operations",
    "greenfield_for_promoter",
}


# ── DATABASE HELPERS ──────────────────────────────────────────────────────────

def db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def now_iso():
    return datetime.now(UTC).isoformat()


def bool_int(value):
    return 1 if value else 0


def row_value(row, key, default=None):
    return row[key] if key in row.keys() else default


def ensure_columns(connection, table, definitions):
    existing = {r["name"] for r in connection.execute(f"pragma table_info({table})").fetchall()}
    for defn in definitions:
        col = defn.split()[0]
        if col not in existing:
            try:
                connection.execute(f"alter table {table} add column {defn}")
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
            existing.add(col)


def normalize_company_lookup(name):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def normalize_domain_lookup(value):
    return str(value or "").strip().lower().removeprefix("www.")


# ── INIT DB ───────────────────────────────────────────────────────────────────

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = db()
    try:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                legal_name TEXT,
                website_url TEXT,
                website_domain TEXT,
                analysis_scope TEXT,
                operating_activity TEXT,
                group_sector_hint TEXT,
                cin TEXT,
                llpin TEXT,
                gstin TEXT,
                pan TEXT,
                udyam_number TEXT,
                dpiit_certificate_number TEXT,
                fssai_license_number TEXT,
                iec_number TEXT,
                state TEXT,
                city TEXT,
                entity_type TEXT,
                sector TEXT,
                annual_turnover TEXT,
                employee_count TEXT,
                founded_year INTEGER,
                is_msme INTEGER DEFAULT 0,
                is_startup_india INTEGER DEFAULT 0,
                is_dpiit INTEGER DEFAULT 0,
                has_gstin INTEGER,
                is_export_oriented INTEGER,
                has_foreign_investment INTEGER,
                is_listed INTEGER,
                deducts_tds INTEGER,
                has_factory_operations INTEGER,
                handles_food_products INTEGER,
                has_rd_collaboration INTEGER,
                has_new_hires INTEGER,
                women_led INTEGER,
                has_scst_founder INTEGER,
                uses_contract_labour INTEGER,
                uses_interstate_migrant_workers INTEGER,
                serves_defence_sector INTEGER,
                controlled_items_exposure INTEGER,
                generates_hazardous_waste INTEGER,
                has_warehouse INTEGER,
                has_cold_chain INTEGER,
                has_primary_processing INTEGER,
                has_b2b_receivables INTEGER,
                has_patent_activity INTEGER,
                regulated_financial_entity INTEGER,
                has_healthcare_facility INTEGER,
                has_diagnostic_lab INTEGER,
                project_based_operations INTEGER,
                greenfield_for_promoter INTEGER,
                unknown_flags_json TEXT DEFAULT '[]',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS company_obligations (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                template_id TEXT,
                name TEXT,
                category TEXT,
                description TEXT,
                penalty_per_day REAL DEFAULT 0,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                filed_date TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS company_schemes (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                template_id TEXT,
                name TEXT,
                ministry TEXT,
                scheme_type TEXT,
                benefit_value TEXT,
                max_benefit_amount REAL,
                status TEXT DEFAULT 'eligible',
                reasons_json TEXT DEFAULT '[]',
                blockers_json TEXT DEFAULT '[]',
                uncertainty TEXT,
                applied_date TEXT,
                benefit_received_amount REAL,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS official_sources (
                source_id TEXT PRIMARY KEY,
                name TEXT,
                owner TEXT,
                domain TEXT,
                category TEXT,
                source_url TEXT,
                access_mode TEXT,
                identifier_fields_json TEXT DEFAULT '[]',
                industries_json TEXT DEFAULT '[]',
                description TEXT,
                notes TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS official_source_checks (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES official_sources(source_id) ON DELETE CASCADE,
                checked_at TEXT,
                status TEXT,
                http_status INTEGER,
                status_detail TEXT
            );

            CREATE TABLE IF NOT EXISTS official_scheme_cache (
                scheme_id TEXT PRIMARY KEY,
                source_id TEXT,
                slug TEXT,
                scheme_name TEXT,
                scheme_short_title TEXT,
                level TEXT,
                scheme_for TEXT,
                ministry TEXT,
                categories_json TEXT DEFAULT '[]',
                beneficiary_states_json TEXT DEFAULT '[]',
                tags_json TEXT DEFAULT '[]',
                brief_description TEXT,
                scheme_close_date TEXT,
                is_expired INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 0,
                source_url TEXT,
                raw_json TEXT,
                synced_at TEXT
            );
        """)

        # Migration: add any missing columns
        ensure_columns(con, "companies", [
            "analysis_scope TEXT",
            "operating_activity TEXT",
            "group_sector_hint TEXT",
            "llpin TEXT",
            "udyam_number TEXT",
            "dpiit_certificate_number TEXT",
            "fssai_license_number TEXT",
            "iec_number TEXT",
            "unknown_flags_json TEXT DEFAULT '[]'",
            "controlled_items_exposure INTEGER",
            "generates_hazardous_waste INTEGER",
            "has_warehouse INTEGER",
            "has_cold_chain INTEGER",
            "has_primary_processing INTEGER",
            "has_b2b_receivables INTEGER",
            "has_patent_activity INTEGER",
            "regulated_financial_entity INTEGER",
            "has_healthcare_facility INTEGER",
            "has_diagnostic_lab INTEGER",
            "project_based_operations INTEGER",
            "greenfield_for_promoter INTEGER",
        ])
        ensure_columns(con, "company_schemes", [
            "uncertainty TEXT",
            "benefit_received_amount REAL",
        ])

        con.commit()
        _seed_official_sources(con)
        con.commit()
    finally:
        con.close()


def _seed_official_sources(con):
    sources = active_official_sources()
    for src in sources:
        existing = con.execute(
            "SELECT source_id FROM official_sources WHERE source_id = ?",
            (src["source_id"],),
        ).fetchone()
        if not existing:
            con.execute(
                """INSERT INTO official_sources
                   (source_id, name, owner, domain, category, source_url, access_mode,
                    identifier_fields_json, industries_json, description, notes, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    src["source_id"],
                    src.get("name", ""),
                    src.get("owner", ""),
                    src.get("domain", ""),
                    src.get("category", ""),
                    src.get("source_url", ""),
                    src.get("access_mode", ""),
                    json.dumps(src.get("identifier_fields", [])),
                    json.dumps(src.get("industries", [])),
                    src.get("description", ""),
                    src.get("notes", ""),
                    now_iso(),
                ),
            )


# ── ROW_TO_COMPANY ─────────────────────────────────────────────────────────────

def row_to_company(row) -> dict:
    unknown_flags: set[str] = set()
    try:
        raw = row_value(row, "unknown_flags_json", "[]")
        unknown_flags = set(json.loads(raw or "[]"))
    except Exception:
        pass

    def flag(field):
        if field in unknown_flags:
            return None
        val = row_value(row, field)
        if val is None:
            return None
        return bool(val)

    company = {
        "id": row_value(row, "id"),
        "name": row_value(row, "name", ""),
        "legal_name": row_value(row, "legal_name"),
        "website_url": row_value(row, "website_url"),
        "website_domain": row_value(row, "website_domain"),
        "analysis_scope": row_value(row, "analysis_scope"),
        "operating_activity": row_value(row, "operating_activity"),
        "group_sector_hint": row_value(row, "group_sector_hint"),
        "cin": row_value(row, "cin"),
        "llpin": row_value(row, "llpin"),
        "gstin": row_value(row, "gstin"),
        "pan": row_value(row, "pan"),
        "udyam_number": row_value(row, "udyam_number"),
        "dpiit_certificate_number": row_value(row, "dpiit_certificate_number"),
        "fssai_license_number": row_value(row, "fssai_license_number"),
        "iec_number": row_value(row, "iec_number"),
        "state": row_value(row, "state", ""),
        "city": row_value(row, "city", ""),
        "entity_type": row_value(row, "entity_type", "other"),
        "sector": row_value(row, "sector", "other"),
        "annual_turnover": row_value(row, "annual_turnover", "under_40L"),
        "employee_count": row_value(row, "employee_count", "1_10"),
        "founded_year": row_value(row, "founded_year"),
        "is_msme": bool(row_value(row, "is_msme", 0)),
        "is_startup_india": bool(row_value(row, "is_startup_india", 0)),
        "is_dpiit": bool(row_value(row, "is_dpiit", 0)),
        # Unknown-flaggable boolean fields
        "has_gstin": flag("has_gstin"),
        "is_export_oriented": flag("is_export_oriented"),
        "has_foreign_investment": flag("has_foreign_investment"),
        "is_listed": flag("is_listed"),
        "deducts_tds": flag("deducts_tds"),
        "has_factory_operations": flag("has_factory_operations"),
        "handles_food_products": flag("handles_food_products"),
        "has_rd_collaboration": flag("has_rd_collaboration"),
        "has_new_hires": flag("has_new_hires"),
        "women_led": flag("women_led"),
        "has_scst_founder": flag("has_scst_founder"),
        "uses_contract_labour": flag("uses_contract_labour"),
        "uses_interstate_migrant_workers": flag("uses_interstate_migrant_workers"),
        "serves_defence_sector": flag("serves_defence_sector"),
        "controlled_items_exposure": flag("controlled_items_exposure"),
        "generates_hazardous_waste": flag("generates_hazardous_waste"),
        "has_warehouse": flag("has_warehouse"),
        "has_cold_chain": flag("has_cold_chain"),
        "has_primary_processing": flag("has_primary_processing"),
        "has_b2b_receivables": flag("has_b2b_receivables"),
        "has_patent_activity": flag("has_patent_activity"),
        "regulated_financial_entity": flag("regulated_financial_entity"),
        "has_healthcare_facility": flag("has_healthcare_facility"),
        "has_diagnostic_lab": flag("has_diagnostic_lab"),
        "project_based_operations": flag("project_based_operations"),
        "greenfield_for_promoter": flag("greenfield_for_promoter"),
        "unknown_flags": list(unknown_flags),
        "created_at": row_value(row, "created_at"),
        "updated_at": row_value(row, "updated_at"),
    }

    company = enrich_company_runtime(company)
    return company


# ── CRUD FUNCTIONS ─────────────────────────────────────────────────────────────

def list_companies() -> list[dict]:
    con = db()
    try:
        rows = con.execute("SELECT * FROM companies ORDER BY created_at DESC").fetchall()
        result = []
        for row in rows:
            c = row_to_company(row)
            obligations = _load_obligations_for_company(con, c["id"])
            schemes = _load_schemes_for_company(con, c["id"])
            c["metrics"] = compute_metrics(c, obligations, schemes)
            result.append(c)
        return result
    finally:
        con.close()


def get_company(company_id: str) -> dict:
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            raise KeyError(f"Company {company_id} not found")
        c = row_to_company(row)
        obligations = _load_obligations_for_company(con, company_id)
        schemes = _load_schemes_for_company(con, company_id)
        c["metrics"] = compute_metrics(c, obligations, schemes)
        c["verification_plan"] = build_verification_plan(c)
        return c
    finally:
        con.close()


def _load_obligations_for_company(con, company_id: str) -> list[dict]:
    rows = con.execute(
        "SELECT * FROM company_obligations WHERE company_id = ?", (company_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def _load_schemes_for_company(con, company_id: str) -> list[dict]:
    rows = con.execute(
        "SELECT * FROM company_schemes WHERE company_id = ?", (company_id,)
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["reasons"] = json.loads(d.pop("reasons_json", "[]") or "[]")
        except Exception:
            d["reasons"] = []
        try:
            d["blockers"] = json.loads(d.pop("blockers_json", "[]") or "[]")
        except Exception:
            d["blockers"] = []
        result.append(d)
    return result


def find_existing_company(
    name: str,
    legal_name: str | None,
    website_domain: str | None,
    analysis_scope: str | None,
    operating_activity: str | None,
    sector: str | None,
    state: str | None,
) -> dict | None:
    con = db()
    try:
        # Try domain match first
        if website_domain:
            norm_domain = normalize_domain_lookup(website_domain)
            row = con.execute(
                "SELECT * FROM companies WHERE website_domain = ?", (norm_domain,)
            ).fetchone()
            if row:
                return row_to_company(row)

        # Try normalized name match
        if name:
            norm_name = normalize_company_lookup(name)
            rows = con.execute("SELECT * FROM companies").fetchall()
            for row in rows:
                stored_name = normalize_company_lookup(row_value(row, "name", ""))
                stored_legal = normalize_company_lookup(row_value(row, "legal_name", "") or "")
                if stored_name == norm_name or (legal_name and stored_legal == normalize_company_lookup(legal_name)):
                    return row_to_company(row)

        return None
    finally:
        con.close()


def create_company(payload: dict) -> dict:
    validated = validate_company_payload(payload)

    website_domain = None
    website_url = validated.get("website_url") or payload.get("website_url")
    if website_url:
        website_domain = normalize_domain_lookup(
            re.sub(r"https?://", "", website_url).split("/")[0]
        )

    existing = find_existing_company(
        name=validated.get("name", ""),
        legal_name=validated.get("legal_name"),
        website_domain=website_domain,
        analysis_scope=validated.get("analysis_scope"),
        operating_activity=validated.get("operating_activity"),
        sector=validated.get("sector"),
        state=validated.get("state"),
    )
    if existing:
        return existing

    company_id = str(uuid.uuid4())
    ts = now_iso()

    unknown_flags = set(payload.get("unknown_flags", []))
    for field in UNKNOWN_FLAG_FIELDS:
        if validated.get(field) is None:
            unknown_flags.add(field)
    unknown_flags_json = json.dumps(list(unknown_flags))

    def flag_val(field):
        if field in unknown_flags:
            return 0
        val = validated.get(field)
        if val is None:
            return 0
        return bool_int(val)

    con = db()
    try:
        values = (
            company_id,
            validated.get("name", ""),
            validated.get("legal_name"),
            website_url,
            website_domain,
            validated.get("analysis_scope"),
            validated.get("operating_activity"),
            validated.get("group_sector_hint"),
            validated.get("cin"),
            validated.get("llpin"),
            validated.get("gstin"),
            validated.get("pan"),
            validated.get("udyam_number"),
            validated.get("dpiit_certificate_number"),
            validated.get("fssai_license_number"),
            validated.get("iec_number"),
            validated.get("state", ""),
            validated.get("city", ""),
            validated.get("entity_type", "other"),
            validated.get("sector", "other"),
            validated.get("annual_turnover", "under_40L"),
            validated.get("employee_count", "1_10"),
            validated.get("founded_year"),
            bool_int(validated.get("is_msme", False)),
            bool_int(validated.get("is_startup_india", False)),
            bool_int(validated.get("is_dpiit", False)),
            flag_val("has_gstin"),
            flag_val("is_export_oriented"),
            flag_val("has_foreign_investment"),
            flag_val("is_listed"),
            flag_val("deducts_tds"),
            flag_val("has_factory_operations"),
            flag_val("handles_food_products"),
            flag_val("has_rd_collaboration"),
            flag_val("has_new_hires"),
            flag_val("women_led"),
            flag_val("has_scst_founder"),
            flag_val("uses_contract_labour"),
            flag_val("uses_interstate_migrant_workers"),
            flag_val("serves_defence_sector"),
            flag_val("controlled_items_exposure"),
            flag_val("generates_hazardous_waste"),
            flag_val("has_warehouse"),
            flag_val("has_cold_chain"),
            flag_val("has_primary_processing"),
            flag_val("has_b2b_receivables"),
            flag_val("has_patent_activity"),
            flag_val("regulated_financial_entity"),
            flag_val("has_healthcare_facility"),
            flag_val("has_diagnostic_lab"),
            flag_val("project_based_operations"),
            flag_val("greenfield_for_promoter"),
            unknown_flags_json,
            ts,
            ts,
        )
        placeholders = ",".join(["?"] * len(values))
        con.execute(
            f"""INSERT INTO companies (
                id, name, legal_name, website_url, website_domain,
                analysis_scope, operating_activity, group_sector_hint,
                cin, llpin, gstin, pan, udyam_number, dpiit_certificate_number,
                fssai_license_number, iec_number,
                state, city, entity_type, sector, annual_turnover, employee_count,
                founded_year, is_msme, is_startup_india, is_dpiit,
                has_gstin, is_export_oriented, has_foreign_investment, is_listed,
                deducts_tds, has_factory_operations, handles_food_products,
                has_rd_collaboration, has_new_hires, women_led, has_scst_founder,
                uses_contract_labour, uses_interstate_migrant_workers, serves_defence_sector,
                controlled_items_exposure, generates_hazardous_waste, has_warehouse,
                has_cold_chain, has_primary_processing, has_b2b_receivables, has_patent_activity,
                regulated_financial_entity,
                has_healthcare_facility, has_diagnostic_lab, project_based_operations,
                greenfield_for_promoter,
                unknown_flags_json, created_at, updated_at
            ) VALUES ({placeholders})""",
            values,
        )

        company_row = con.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        company = row_to_company(company_row)

        # Build and persist obligations
        obligations = build_obligations(company)
        for obl in obligations:
            obl_id = str(uuid.uuid4())
            con.execute(
                """INSERT INTO company_obligations
                   (id, company_id, template_id, name, category, description,
                    penalty_per_day, due_date, status, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    obl_id,
                    company_id,
                    obl.get("template_id", ""),
                    obl.get("name", ""),
                    obl.get("category", ""),
                    obl.get("description", ""),
                    obl.get("penalty_per_day", 0),
                    obl.get("due_date", ""),
                    obl.get("status", "pending"),
                    ts,
                    ts,
                ),
            )

        # Build and persist schemes
        schemes = build_schemes(company)
        for sch in schemes:
            sch_id = str(uuid.uuid4())
            display = scheme_display_metadata(sch.get("template_id", ""))
            con.execute(
                """INSERT INTO company_schemes
                   (id, company_id, template_id, name, ministry, scheme_type,
                    benefit_value, max_benefit_amount, status, reasons_json,
                    blockers_json, uncertainty, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    sch_id,
                    company_id,
                    sch.get("template_id", ""),
                    sch.get("name", ""),
                    sch.get("ministry", ""),
                    sch.get("scheme_type", ""),
                    display.get("value_label", sch.get("benefit_value", "")),
                    display.get("max_benefit_amount"),
                    sch.get("status", "eligible"),
                    json.dumps(sch.get("reasons", [])),
                    json.dumps(sch.get("blockers", [])),
                    sch.get("uncertainty", ""),
                    ts,
                    ts,
                ),
            )

        con.commit()
        return company
    finally:
        con.close()


def list_obligations(company_id: str, status: str | None = None) -> list[dict]:
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            raise KeyError(f"Company {company_id} not found")
        company = row_to_company(row)
    finally:
        con.close()

    # Sync with current engine output
    fresh = build_obligations(company)
    persist_synced_obligations(company_id, fresh)

    con = db()
    try:
        rows = con.execute(
            "SELECT * FROM company_obligations WHERE company_id = ?", (company_id,)
        ).fetchall()
        obligations = [dict(r) for r in rows]
    finally:
        con.close()

    obligations = sync_obligation_statuses(obligations)

    if status:
        obligations = [o for o in obligations if o.get("status") == status]

    obligations.sort(key=lambda o: o.get("due_date") or "9999-12-31")
    return obligations


def persist_synced_obligations(company_id: str, fresh_obligations: list[dict] | None = None):
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            return
        company = row_to_company(row)

        if fresh_obligations is None:
            fresh_obligations = build_obligations(company)

        existing_rows = con.execute(
            "SELECT * FROM company_obligations WHERE company_id = ?", (company_id,)
        ).fetchall()
        existing_by_template: dict[str, dict] = {}
        for r in existing_rows:
            tid = r["template_id"]
            if tid:
                existing_by_template[tid] = dict(r)

        ts = now_iso()
        for obl in fresh_obligations:
            tid = obl.get("template_id", "")
            if tid and tid in existing_by_template:
                # Update metadata but preserve user-set status
                existing = existing_by_template[tid]
                new_status = existing.get("status", "pending")
                con.execute(
                    """UPDATE company_obligations
                       SET name=?, category=?, description=?, penalty_per_day=?,
                           due_date=?, status=?, updated_at=?
                       WHERE id=?""",
                    (
                        obl.get("name", ""),
                        obl.get("category", ""),
                        obl.get("description", ""),
                        obl.get("penalty_per_day", 0),
                        obl.get("due_date", ""),
                        new_status,
                        ts,
                        existing["id"],
                    ),
                )
            elif tid:
                obl_id = str(uuid.uuid4())
                con.execute(
                    """INSERT INTO company_obligations
                       (id, company_id, template_id, name, category, description,
                        penalty_per_day, due_date, status, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        obl_id,
                        company_id,
                        tid,
                        obl.get("name", ""),
                        obl.get("category", ""),
                        obl.get("description", ""),
                        obl.get("penalty_per_day", 0),
                        obl.get("due_date", ""),
                        obl.get("status", "pending"),
                        ts,
                        ts,
                    ),
                )

        con.commit()
    finally:
        con.close()


def list_schemes(company_id: str, status: str | None = None) -> list[dict]:
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            raise KeyError(f"Company {company_id} not found")
        company = row_to_company(row)
    finally:
        con.close()

    # Sync: evaluate all engine schemes and upsert
    fresh = build_schemes(company)
    ts = now_iso()

    con = db()
    try:
        existing_rows = con.execute(
            "SELECT * FROM company_schemes WHERE company_id = ?", (company_id,)
        ).fetchall()
        existing_by_template: dict[str, dict] = {}
        for r in existing_rows:
            tid = r["template_id"]
            if tid:
                existing_by_template[tid] = dict(r)

        for sch in fresh:
            tid = sch.get("template_id", "")
            display = scheme_display_metadata(tid)
            if tid and tid in existing_by_template:
                existing = existing_by_template[tid]
                user_status = existing.get("status", sch.get("status", "eligible"))
                # Only update engine-derived fields; preserve user workflow status
                if user_status in ("eligible", "ineligible", "maybe"):
                    user_status = sch.get("status", user_status)
                con.execute(
                    """UPDATE company_schemes
                       SET name=?, ministry=?, scheme_type=?, benefit_value=?,
                           max_benefit_amount=?, status=?, reasons_json=?,
                           blockers_json=?, uncertainty=?, updated_at=?
                       WHERE id=?""",
                    (
                        sch.get("name", ""),
                        sch.get("ministry", ""),
                        sch.get("scheme_type", ""),
                        display.get("value_label", sch.get("benefit_value", "")),
                        display.get("max_benefit_amount"),
                        user_status,
                        json.dumps(sch.get("reasons", [])),
                        json.dumps(sch.get("blockers", [])),
                        sch.get("uncertainty", ""),
                        ts,
                        existing["id"],
                    ),
                )
            elif tid:
                sch_id = str(uuid.uuid4())
                con.execute(
                    """INSERT INTO company_schemes
                       (id, company_id, template_id, name, ministry, scheme_type,
                        benefit_value, max_benefit_amount, status, reasons_json,
                        blockers_json, uncertainty, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        sch_id,
                        company_id,
                        tid,
                        sch.get("name", ""),
                        sch.get("ministry", ""),
                        sch.get("scheme_type", ""),
                        display.get("value_label", sch.get("benefit_value", "")),
                        display.get("max_benefit_amount"),
                        sch.get("status", "eligible"),
                        json.dumps(sch.get("reasons", [])),
                        json.dumps(sch.get("blockers", [])),
                        sch.get("uncertainty", ""),
                        ts,
                        ts,
                    ),
                )

        con.commit()

        rows = con.execute(
            "SELECT * FROM company_schemes WHERE company_id = ?", (company_id,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["reasons"] = json.loads(d.pop("reasons_json", "[]") or "[]")
            except Exception:
                d["reasons"] = []
            try:
                d["blockers"] = json.loads(d.pop("blockers_json", "[]") or "[]")
            except Exception:
                d["blockers"] = []
            display = scheme_display_metadata(d.get("template_id", ""))
            d.update(display)
            template = next((item for item in SCHEMES_CATALOG if item["template_id"] == d.get("template_id")), None)
            if template:
                evaluated = evaluate_scheme(company, template)
                d["review_clauses"] = evaluated.get("review_clauses", [])
                d["review_questions"] = evaluated.get("review_questions", [])
                d["hard_blockers"] = evaluated.get("hard_blockers", [])
                d["soft_checks"] = evaluated.get("soft_checks", [])
            result.append(d)
    finally:
        con.close()

    if status:
        result = [s for s in result if s.get("status") == status]

    return result


def update_obligation_status(company_id: str, obligation_id: str, action: str) -> dict:
    con = db()
    try:
        row = con.execute(
            "SELECT * FROM company_obligations WHERE id = ? AND company_id = ?",
            (obligation_id, company_id),
        ).fetchone()
        if not row:
            raise KeyError(f"Obligation {obligation_id} not found for company {company_id}")

        ts = now_iso()
        if action == "filed":
            new_status = "filed"
            filed_date = ts[:10]
            con.execute(
                "UPDATE company_obligations SET status=?, filed_date=?, updated_at=? WHERE id=?",
                (new_status, filed_date, ts, obligation_id),
            )
        elif action == "reopen":
            new_status = "pending"
            con.execute(
                "UPDATE company_obligations SET status=?, filed_date=NULL, updated_at=? WHERE id=?",
                (new_status, ts, obligation_id),
            )
        else:
            raise ValueError(f"Unknown action: {action}")

        con.commit()
        updated = con.execute(
            "SELECT * FROM company_obligations WHERE id = ?", (obligation_id,)
        ).fetchone()
        return dict(updated)
    finally:
        con.close()


def update_scheme_status(company_id: str, scheme_id: str, action: str) -> dict:
    con = db()
    try:
        row = con.execute(
            "SELECT * FROM company_schemes WHERE id = ? AND company_id = ?",
            (scheme_id, company_id),
        ).fetchone()
        if not row:
            raise KeyError(f"Scheme {scheme_id} not found for company {company_id}")

        ts = now_iso()
        if action == "apply":
            con.execute(
                "UPDATE company_schemes SET status='applied', applied_date=?, updated_at=? WHERE id=?",
                (ts[:10], ts, scheme_id),
            )
        elif action == "receive":
            con.execute(
                "UPDATE company_schemes SET status='received', updated_at=? WHERE id=?",
                (ts, scheme_id),
            )
        elif action == "reopen":
            con.execute(
                "UPDATE company_schemes SET status='eligible', applied_date=NULL, updated_at=? WHERE id=?",
                (ts, scheme_id),
            )
        else:
            raise ValueError(f"Unknown action: {action}")

        con.commit()
        updated = con.execute(
            "SELECT * FROM company_schemes WHERE id = ?", (scheme_id,)
        ).fetchone()
        d = dict(updated)
        try:
            d["reasons"] = json.loads(d.pop("reasons_json", "[]") or "[]")
        except Exception:
            d["reasons"] = []
        try:
            d["blockers"] = json.loads(d.pop("blockers_json", "[]") or "[]")
        except Exception:
            d["blockers"] = []
        return d
    finally:
        con.close()


def reset_data():
    con = db()
    try:
        con.execute("DELETE FROM company_obligations")
        con.execute("DELETE FROM company_schemes")
        con.execute("DELETE FROM official_source_checks")
        con.execute("DELETE FROM companies")
        con.commit()
    finally:
        con.close()


def list_official_sources() -> list[dict]:
    con = db()
    try:
        rows = con.execute("SELECT * FROM official_sources ORDER BY name").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["identifier_fields"] = json.loads(d.pop("identifier_fields_json", "[]") or "[]")
            except Exception:
                d["identifier_fields"] = []
            try:
                d["industries"] = json.loads(d.pop("industries_json", "[]") or "[]")
            except Exception:
                d["industries"] = []
            # Attach latest check
            check = con.execute(
                "SELECT * FROM official_source_checks WHERE source_id = ? ORDER BY checked_at DESC LIMIT 1",
                (d["source_id"],),
            ).fetchone()
            d["latest_check"] = dict(check) if check else None
            result.append(d)
        return result
    finally:
        con.close()


def record_official_source_checks(checks: list[dict]):
    con = db()
    try:
        ts = now_iso()
        for check in checks:
            check_id = str(uuid.uuid4())
            con.execute(
                """INSERT INTO official_source_checks
                   (id, source_id, checked_at, status, http_status, status_detail)
                   VALUES (?,?,?,?,?,?)""",
                (
                    check_id,
                    check.get("source_id", ""),
                    check.get("checked_at", ts),
                    check.get("status", ""),
                    check.get("http_status"),
                    check.get("status_detail", ""),
                ),
            )
        con.commit()
    finally:
        con.close()


def get_company_verification_plan(company_id: str) -> list[dict]:
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            raise KeyError(f"Company {company_id} not found")
        company = row_to_company(row)
    finally:
        con.close()
    return build_verification_plan(company)


def list_official_scheme_cache(
    source_id: str | None = None,
    include_expired: bool = False,
    limit: int = 50,
) -> list[dict]:
    con = db()
    try:
        query = "SELECT * FROM official_scheme_cache WHERE 1=1"
        params: list = []
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        if not include_expired:
            query += " AND (is_expired = 0 OR is_expired IS NULL)"
        query += " ORDER BY priority DESC, synced_at DESC LIMIT ?"
        params.append(limit)

        rows = con.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            for json_field in ("categories_json", "beneficiary_states_json", "tags_json"):
                key = json_field.replace("_json", "s") if json_field != "beneficiary_states_json" else "beneficiary_states"
                raw_key = json_field
                # map categories_json -> categories, beneficiary_states_json -> beneficiary_states, tags_json -> tags
                mapped = {
                    "categories_json": "categories",
                    "beneficiary_states_json": "beneficiary_states",
                    "tags_json": "tags",
                }[json_field]
                try:
                    d[mapped] = json.loads(d.pop(json_field, "[]") or "[]")
                except Exception:
                    d[mapped] = []
            try:
                d["raw"] = json.loads(d.pop("raw_json", "{}") or "{}")
            except Exception:
                d["raw"] = {}
            result.append(d)
        return result
    finally:
        con.close()


def store_official_scheme_cache(items: list[dict]):
    con = db()
    try:
        ts = now_iso()
        for item in items:
            scheme_id = item.get("scheme_id") or str(uuid.uuid4())
            con.execute(
                """INSERT INTO official_scheme_cache
                   (scheme_id, source_id, slug, scheme_name, scheme_short_title, level,
                    scheme_for, ministry, categories_json, beneficiary_states_json,
                    tags_json, brief_description, scheme_close_date, is_expired,
                    priority, source_url, raw_json, synced_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(scheme_id) DO UPDATE SET
                       slug=excluded.slug,
                       scheme_name=excluded.scheme_name,
                       scheme_short_title=excluded.scheme_short_title,
                       level=excluded.level,
                       scheme_for=excluded.scheme_for,
                       ministry=excluded.ministry,
                       categories_json=excluded.categories_json,
                       beneficiary_states_json=excluded.beneficiary_states_json,
                       tags_json=excluded.tags_json,
                       brief_description=excluded.brief_description,
                       scheme_close_date=excluded.scheme_close_date,
                       is_expired=excluded.is_expired,
                       priority=excluded.priority,
                       source_url=excluded.source_url,
                       raw_json=excluded.raw_json,
                       synced_at=excluded.synced_at""",
                (
                    scheme_id,
                    item.get("source_id", "myscheme"),
                    item.get("slug", ""),
                    item.get("scheme_name", ""),
                    item.get("scheme_short_title", ""),
                    item.get("level", ""),
                    item.get("scheme_for", ""),
                    item.get("ministry", ""),
                    json.dumps(item.get("categories", [])),
                    json.dumps(item.get("beneficiary_states", [])),
                    json.dumps(item.get("tags", [])),
                    item.get("brief_description", ""),
                    item.get("scheme_close_date"),
                    bool_int(item.get("is_expired", False)),
                    item.get("priority", 0),
                    item.get("source_url", ""),
                    json.dumps(item.get("raw", {})),
                    ts,
                ),
            )
        con.commit()
    finally:
        con.close()


def sync_official_scheme_catalog(source_id: str) -> dict:
    if source_id != "myscheme":
        raise ValueError(f"Sync not supported for source: {source_id}")
    result = sync_myscheme_catalog()
    items = result.get("schemes", [])
    if items:
        store_official_scheme_cache(items)
    return {
        "source_id": source_id,
        "synced": len(items),
        "summary": result.get("summary", {}),
    }


def list_company_official_schemes(company_id: str, limit: int = 12) -> list[dict]:
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            raise KeyError(f"Company {company_id} not found")
        company = row_to_company(row)
    finally:
        con.close()

    matches, _meta = _rank_official_schemes_for_company(company, limit=limit)
    return matches


def list_company_scheme_opportunities(company_id: str, limit: int = 6) -> list[dict]:
    con = db()
    try:
        row = con.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        if not row:
            raise KeyError(f"Company {company_id} not found")
        company = row_to_company(row)
    finally:
        con.close()
    return build_scheme_opportunities(company, limit=limit)


# ── SESSION HELPERS ────────────────────────────────────────────────────────────

def _rank_official_schemes_for_company(company: dict, limit: int = 12) -> tuple[list[dict], dict[str, object]]:
    cached = list_official_scheme_cache(source_id="myscheme", include_expired=False, limit=500)
    if not cached:
        return [], {"matched_total": 0, "cached_total": 0, "last_synced_at": None}

    all_matches = rank_company_myscheme_matches(company, cached, limit=max(limit, len(cached)))
    last_synced_at = max((item.get("synced_at") for item in cached if item.get("synced_at")), default=None)
    meta = {
        "matched_total": len(all_matches),
        "cached_total": len(cached),
        "last_synced_at": last_synced_at,
    }
    return all_matches[:limit], meta


def _build_analysis_focus(
    company: dict,
    obligations: list[dict],
    schemes: list[dict],
    verification_plan: list[dict],
    official_scheme_matches: list[dict],
    official_scheme_meta: dict[str, object],
    scheme_opportunities: list[dict],
) -> dict[str, object]:
    what_adds_value: list[str] = []
    next_actions: list[str] = []
    summary_parts: list[str] = []

    scope = str(company.get("analysis_scope", "current_entity")).strip()
    company_name = str(company.get("name", "")).strip() or "This company"
    legal_name = str(company.get("legal_name", "")).strip()
    group_sector_hint = str(company.get("group_sector_hint", "")).strip()
    operating_activity = str(company.get("operating_activity", "")).strip()

    open_schemes = [item for item in schemes if item.get("status") in {"eligible", "maybe"}]
    operational_obligations = [item for item in obligations if item.get("category") not in {"gst", "tax", "tds"}]
    tax_obligations = [item for item in obligations if item.get("category") in {"gst", "tax", "tds"}]
    overdue_obligations = [item for item in obligations if item.get("status") == "overdue"]
    ready_checks = [item for item in verification_plan if item.get("status") == "ready"]
    manual_checks = [item for item in verification_plan if item.get("status") == "manual_verification_required"]
    missing_identifier_labels = [
        item["label"]
        for item in build_identifier_questions(company)
        if not company.get(item["field"])
    ]

    if scope == "brand_unit" and legal_name and legal_name.lower() != company_name.lower():
        what_adds_value.append(
            f"The platform is separating the brand '{company_name}' from the legal entity '{legal_name}', so parent-entity opportunities are not mixed into the brand-unit recommendation set."
        )
        summary_parts.append("Brand and legal-entity reasoning is active.")
    elif group_sector_hint:
        what_adds_value.append(
            f"The platform is keeping the current entity separate from parent-group {group_sector_hint.replace('_', ' ')} signals, which reduces false company-level scheme matches."
        )
        summary_parts.append("Parent-group signals are being handled separately.")

    if company.get("has_factory_operations") or operating_activity == "manufacturing_processing":
        what_adds_value.append(
            "Industrial and factory-level compliance mapping is switched on, so labour, safety, environmental, and plant-side obligations are being considered together rather than flattened into generic business compliance."
        )
        summary_parts.append("Industrial operating logic is active.")

    if tax_obligations and operational_obligations:
        what_adds_value.append(
            "GST and tax are being separated from operational compliance, which keeps plant, labour, and sector reviews readable instead of burying them under filing noise."
        )

    if open_schemes:
        what_adds_value.append(
            f"{len(open_schemes)} mapped schemes already look relevant for the current profile before counting live official-source leads."
        )
        summary_parts.append(f"{len(open_schemes)} mapped schemes are already in play.")

    if official_scheme_matches:
        what_adds_value.append(
            f"Live official-catalog ranking surfaced {len(official_scheme_matches)} additional leads from {official_scheme_meta.get('cached_total', 0)} cached official schemes, so the platform is not limited to the local curated catalogue."
        )
        summary_parts.append("Official-source scheme discovery is contributing additional leads.")

    if verification_plan:
        what_adds_value.append(
            f"The official verification path is tailored to this profile: {len(ready_checks)} source(s) are ready now and {len(manual_checks)} require a human portal or captcha step."
        )
        summary_parts.append("Official verification routing is available.")

    if scheme_opportunities:
        what_adds_value.append(
            f"{len(scheme_opportunities)} strategic-path opportunities are being kept separate from immediately usable schemes, so structural unlocks do not get mistaken for current eligibility."
        )
        summary_parts.append("Strategic unlocks are being shown separately.")

    if missing_identifier_labels:
        preview = ", ".join(missing_identifier_labels[:2])
        suffix = " and more" if len(missing_identifier_labels) > 2 else ""
        next_actions.append(f"Confirm official identifiers like {preview}{suffix} to tighten verification and reduce scheme uncertainty.")

    if open_schemes:
        top_scheme = open_schemes[0]
        next_actions.append(f"Open guided review for {top_scheme['name']} first; it is one of the strongest currently-usable scheme leads.")
    elif official_scheme_matches:
        top_official = official_scheme_matches[0]
        next_actions.append(f"Review the official-source lead '{top_official.get('scheme_name', 'top official lead')}' before treating it as a real opportunity.")

    if overdue_obligations:
        next_item = overdue_obligations[0]
        next_actions.append(f"Resolve overdue item '{next_item['name']}' first to reduce immediate penalty exposure.")
    elif operational_obligations:
        next_item = operational_obligations[0]
        next_actions.append(f"Check the next operational obligation, '{next_item['name']}', so compliance risk does not build quietly.")

    if scheme_opportunities:
        unlock = scheme_opportunities[0]
        unlock_action = (unlock.get("unlock_actions") or ["Review the structural change needed before treating this as available."])[0]
        next_actions.append(f"For strategic upside, start with '{unlock['name']}': {unlock_action}")

    if not summary_parts:
        summary_parts.append("The platform is combining company mapping, official verification, and scheme logic into one review flow.")

    return {
        "summary": " ".join(summary_parts[:3]),
        "what_adds_value": what_adds_value[:5],
        "next_actions": next_actions[:4],
    }


def _build_company_analysis_bundle(
    company: dict,
    *,
    obligations: list[dict] | None = None,
    schemes: list[dict] | None = None,
    include_official_matches: bool = True,
    official_limit: int = 12,
    opportunity_limit: int = 6,
) -> dict[str, object]:
    current_obligations = sync_obligation_statuses(
        copy.deepcopy(obligations if obligations is not None else build_obligations(company))
    )
    current_schemes = copy.deepcopy(schemes if schemes is not None else build_schemes(company))
    verification_plan = build_verification_plan(company)
    identifier_questions = build_identifier_questions(company)
    scheme_opportunities = build_scheme_opportunities(company, limit=opportunity_limit)

    if include_official_matches:
        official_scheme_matches, official_scheme_meta = _rank_official_schemes_for_company(company, limit=official_limit)
    else:
        official_scheme_matches, official_scheme_meta = [], {
            "matched_total": 0,
            "cached_total": 0,
            "last_synced_at": None,
        }

    return {
        "obligations": current_obligations,
        "schemes": current_schemes,
        "metrics": compute_metrics(company, current_obligations, current_schemes),
        "verification": {
            "identifier_questions": identifier_questions,
            "verification_plan": verification_plan,
        },
        "official_scheme_matches": official_scheme_matches,
        "official_scheme_meta": official_scheme_meta,
        "scheme_opportunities": scheme_opportunities,
        "analysis_focus": _build_analysis_focus(
            company,
            current_obligations,
            current_schemes,
            verification_plan,
            official_scheme_matches,
            official_scheme_meta,
            scheme_opportunities,
        ),
    }

def _fill_required_defaults(inferred: dict) -> dict:
    defaults = {
        "state": "",
        "city": "",
        "entity_type": "other",
        "sector": "other",
        "annual_turnover": "unknown",
        "employee_count": "unknown",
    }
    result = dict(inferred)
    for field, default in defaults.items():
        if result.get(field) in (None, ""):
            result[field] = default
    return result


def _build_confirmations(inferred: dict, company_name: str, website_context: dict | None) -> list[dict]:
    confirmations = []

    legal_name = inferred.get("legal_name", "")
    if legal_name and legal_name.lower() != company_name.lower():
        confirmations.append({
            "type": "entity_clarification",
            "message": f"We found a legal entity: {legal_name}",
            "detail": f"'{company_name}' appears to operate under '{legal_name}'",
            "field": "legal_name",
            "suggested_value": legal_name,
        })

    if website_context:
        ids = website_context.get("identifier_candidates", {})
        if ids.get("gstin"):
            confirmations.append({
                "type": "id_suggestion",
                "message": f"GSTIN found: {ids['gstin']}",
                "detail": "We found this on your website. Is this correct?",
                "field": "gstin",
                "suggested_value": ids["gstin"],
            })
        if ids.get("cin"):
            confirmations.append({
                "type": "id_suggestion",
                "message": f"CIN found: {ids['cin']}",
                "detail": "We found this on your website. Is this correct?",
                "field": "cin",
                "suggested_value": ids["cin"],
            })
        if ids.get("fssai_license_number"):
            confirmations.append({
                "type": "id_suggestion",
                "message": f"FSSAI licence found: {ids['fssai_license_number']}",
                "detail": "We found this on your website. Is this correct?",
                "field": "fssai_license_number",
                "suggested_value": ids["fssai_license_number"],
            })

    sector = inferred.get("sector", "")
    if sector and sector not in ("other", ""):
        confirmations.append({
            "type": "sector_confirmation",
            "message": f"Business sector: {sector.replace('_', ' ').title()}",
            "detail": "We inferred this from your company details. Correct?",
            "field": "sector",
            "suggested_value": sector,
        })

    return confirmations


def _build_eligibility_explanation(evaluated: dict) -> str:
    status = evaluated["status"]
    reasons = evaluated.get("reasons", [])
    blockers = evaluated.get("blockers", [])
    uncertainty = evaluated.get("uncertainty", "")

    if status == "eligible":
        base = "You appear to meet all criteria for this scheme."
        if reasons:
            base += f" {reasons[0]}"
        return base
    elif status == "maybe":
        base = "You likely qualify, but a few details need confirmation."
        if uncertainty:
            base += f" {uncertainty}"
        return base
    elif blockers:
        return f"Does not qualify: {'; '.join(blockers[:2])}"
    return "Does not qualify based on current profile."


def _get_activation_steps(scheme: dict) -> list[str]:
    steps_map: dict[str, list[str]] = {
        "cgtmse": [
            "Contact your bank's MSME desk and request a CGTMSE-backed loan",
            "Provide your Udyam registration certificate",
            "Bank files the guarantee request with CGTMSE",
            "Annual guarantee fee paid by bank (may be partially passed to you)",
        ],
        "startup_india_tax_exemption": [
            "Ensure you have an active DPIIT recognition certificate",
            "File Form 80-IAC with your Income Tax Return",
            "Get certification from the Inter-Ministerial Board (IMB) — apply via startupindia.gov.in",
            "Claim exemption for any 3 consecutive years of your choice within 10 years",
        ],
        "aif": [
            "Identify your agri-infrastructure project (cold storage, warehouse, processing unit)",
            "Apply at agriinfra.dac.gov.in",
            "Select a lending institution (most nationalised banks, RRBs, cooperative banks)",
            "Submit project proposal with location details",
            "Receive sanction — 3% interest subvention credited automatically",
        ],
        "startup_india_seed_fund": [
            "Find a DPIIT-approved incubator in your sector at startupindia.gov.in",
            "Apply to the incubator with your startup pitch",
            "Incubator evaluates and selects startups",
            "If selected, funds disbursed in tranches",
        ],
        "standup_india": [
            "Visit standupmitra.in",
            "Register with your SC/ST or woman entrepreneur credentials",
            "Prepare a business plan for your greenfield project",
            "Contact a participating bank branch",
            "Loan processed with concessional terms",
        ],
        "pmegp": [
            "Apply online at kviconline.gov.in",
            "Select the appropriate category (general / SC/ST/OBC/women)",
            "Prepare detailed project report for the new enterprise",
            "Loan sanctioned via participating bank; subsidy adjusted automatically",
        ],
        "zed_certification": [
            "Register at zed.msme.gov.in",
            "Select a QCI-empanelled assessment body",
            "Undergo factory assessment",
            "Receive ZED rating (Bronze / Silver / Gold / Diamond)",
            "Subsidy on certification fee credited via DBT",
        ],
    }
    template_id = scheme.get("template_id", "")
    return steps_map.get(template_id, [
        f"Visit the official scheme page: {scheme.get('source_url', '')}",
        "Prepare the required documents listed below",
        "Submit application and track status",
    ])


def _mapped_scheme_review_payload(company: dict, scheme_row: dict, scheme_template: dict, answers: dict | None = None) -> dict:
    review = evaluate_scheme_review(company, scheme_template, answers or {})
    display = scheme_display_metadata(scheme_template.get("template_id", ""))
    return {
        "scheme_id": scheme_row["id"],
        "template_id": scheme_template.get("template_id", ""),
        "scheme_name": scheme_template.get("name", scheme_row.get("name", "")),
        "current_status": scheme_row.get("status", review.get("status", "maybe")),
        "benefit_value": display["value_label"],
        "max_benefit_amount": display["max_benefit_amount"],
        "value_kind": display["value_kind"],
        "source_url": display["source_url"],
        "questions": review.get("review_questions", []),
        "clauses": review.get("review_clauses", []),
        "matched_conditions": review.get("matched_conditions", []),
        "unmet_conditions": review.get("unmet_conditions", []),
        "remaining_checks": review.get("remaining_checks", []),
        "review_status": review.get("review_status", "review_needs_confirmation"),
        "review_verdict": review.get("review_verdict", "Still needs confirmation before applying"),
        "review_tone": review.get("review_tone", "warning"),
        "review_message": review.get("review_message", ""),
        "can_apply_now": bool(review.get("can_apply_now")),
        "activation_steps": _get_activation_steps(scheme_template),
        "uncertainty": review.get("uncertainty", ""),
    }


# ── FLASK ROUTES ───────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.route("/api/companies", methods=["GET"])
def api_list_companies():
    try:
        return jsonify({"companies": list_companies()})
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies", methods=["POST"])
def api_create_company():
    try:
        payload = request.get_json(silent=True) or {}
        company = create_company(payload)
        return jsonify({"company": company}), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>", methods=["GET"])
def api_get_company(company_id: str):
    try:
        persist_synced_obligations(company_id)
        company = get_company(company_id)
        obligations = list_obligations(company_id)
        schemes = list_schemes(company_id)
        analysis_bundle = _build_company_analysis_bundle(
            company,
            obligations=obligations,
            schemes=schemes,
            include_official_matches=True,
        )
        company_with_metrics = dict(company)
        company_with_metrics["metrics"] = analysis_bundle["metrics"]
        company_with_metrics["analysis_focus"] = analysis_bundle["analysis_focus"]
        return jsonify({"company": company_with_metrics})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/obligations", methods=["GET"])
def api_list_obligations(company_id: str):
    try:
        status = request.args.get("status") or None
        obligations = list_obligations(company_id, status=status)
        return jsonify({"obligations": obligations})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/schemes", methods=["GET"])
def api_list_schemes(company_id: str):
    try:
        status = request.args.get("status") or None
        schemes = list_schemes(company_id, status=status)
        return jsonify({"schemes": schemes})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/verification-plan", methods=["GET"])
def api_verification_plan(company_id: str):
    try:
        company = get_company(company_id)
        analysis_bundle = _build_company_analysis_bundle(
            company,
            obligations=list_obligations(company_id),
            schemes=list_schemes(company_id),
            include_official_matches=False,
        )
        return jsonify(analysis_bundle["verification"])
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/official-schemes", methods=["GET"])
def api_company_official_schemes(company_id: str):
    try:
        limit = int(request.args.get("limit", 12))
        company = get_company(company_id)
        official_matches, official_meta = _rank_official_schemes_for_company(company, limit=limit)
        return jsonify({
            "schemes": official_matches,
            **official_meta,
        })
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/scheme-opportunities", methods=["GET"])
def api_company_scheme_opportunities(company_id: str):
    try:
        limit = int(request.args.get("limit", 6))
        opportunities = list_company_scheme_opportunities(company_id, limit=limit)
        return jsonify({"opportunities": opportunities})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/obligations/<obligation_id>/filed", methods=["POST"])
def api_obligation_filed(company_id: str, obligation_id: str):
    try:
        updated = update_obligation_status(company_id, obligation_id, "filed")
        return jsonify({"obligation": updated})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/obligations/<obligation_id>/reopen", methods=["POST"])
def api_obligation_reopen(company_id: str, obligation_id: str):
    try:
        updated = update_obligation_status(company_id, obligation_id, "reopen")
        return jsonify({"obligation": updated})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/schemes/<scheme_id>/apply", methods=["POST"])
def api_scheme_apply(company_id: str, scheme_id: str):
    try:
        updated = update_scheme_status(company_id, scheme_id, "apply")
        return jsonify({"scheme": updated})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/schemes/<scheme_id>/receive", methods=["POST"])
def api_scheme_receive(company_id: str, scheme_id: str):
    try:
        updated = update_scheme_status(company_id, scheme_id, "receive")
        return jsonify({"scheme": updated})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/schemes/<scheme_id>/reopen", methods=["POST"])
def api_scheme_reopen(company_id: str, scheme_id: str):
    try:
        updated = update_scheme_status(company_id, scheme_id, "reopen")
        return jsonify({"scheme": updated})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/companies/<company_id>/schemes/<scheme_id>/review", methods=["POST"])
def api_company_scheme_review(company_id: str, scheme_id: str):
    try:
        company = get_company(company_id)
        con = db()
        try:
            row = con.execute(
                "SELECT * FROM company_schemes WHERE id = ? AND company_id = ?",
                (scheme_id, company_id),
            ).fetchone()
        finally:
            con.close()
        if not row:
            raise KeyError(f"Scheme {scheme_id} not found for company {company_id}")

        scheme_row = dict(row)
        scheme_template = next(
            (item for item in SCHEMES_CATALOG if item["template_id"] == scheme_row.get("template_id")),
            None,
        )
        if not scheme_template:
            raise KeyError(f"Scheme template {scheme_row.get('template_id')} not found")

        data = request.get_json(silent=True) or {}
        answers = data.get("answers", {}) or {}
        return jsonify(_mapped_scheme_review_payload(company, scheme_row, scheme_template, answers))
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/official-sources", methods=["GET"])
def api_official_sources():
    try:
        return jsonify({"sources": list_official_sources()})
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/official-sources/refresh", methods=["POST"])
def api_official_sources_refresh():
    try:
        data = request.get_json(silent=True) or {}
        source_ids = data.get("source_ids") or None
        checks = refresh_source_health(source_ids=source_ids)
        record_official_source_checks(checks)
        return jsonify({"checks": checks, "sources": list_official_sources()})
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/official-schemes", methods=["GET"])
def api_official_schemes():
    try:
        source_id = request.args.get("source_id") or None
        include_expired = request.args.get("include_expired", "false").lower() == "true"
        limit = int(request.args.get("limit", 50))
        schemes = list_official_scheme_cache(
            source_id=source_id, include_expired=include_expired, limit=limit
        )
        return jsonify({"schemes": schemes})
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/official-schemes/sync", methods=["POST"])
def api_official_schemes_sync():
    try:
        data = request.get_json(silent=True) or {}
        source_id = data.get("source_id", "myscheme")
        summary = sync_official_scheme_catalog(source_id)
        return jsonify(summary)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/reset", methods=["POST"])
def api_reset():
    try:
        reset_data()
        return jsonify({"ok": True})
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/discover-company", methods=["POST"])
def api_discover_company():
    try:
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        website = str(payload.get("website", "")).strip()

        if not website and looks_like_website(name):
            website, name = name, ""

        website_context = None
        if website or name:
            try:
                website_context = build_website_context(name=name, website=website)
            except Exception:
                pass

        discovery = discover_company_profile(name, website_context=website_context)

        # Enrich with official identifier questions and website summary
        inferred = discovery.get("inferred", {})
        discovery["official_identifier_questions"] = build_identifier_questions(inferred)
        if website_context:
            discovery["website_summary"] = {
                "url": website_context.get("url", website),
                "detected_name": website_context.get("detected_name"),
                "description": website_context.get("description"),
            }

        # Check for existing company match
        website_domain = None
        if website:
            website_domain = normalize_domain_lookup(
                re.sub(r"https?://", "", website).split("/")[0]
            )
        existing = find_existing_company(
            name=name,
            legal_name=inferred.get("legal_name"),
            website_domain=website_domain,
            analysis_scope=inferred.get("analysis_scope"),
            operating_activity=inferred.get("operating_activity"),
            sector=inferred.get("sector"),
            state=inferred.get("state"),
        )
        if existing:
            discovery["existing_company_id"] = existing["id"]

        return jsonify({"discovery": discovery})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except sqlite3.Error as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": f"Discovery failed: {exc.__class__.__name__}: {exc}"}), 500


# ── SESSION-BASED ENDPOINTS ────────────────────────────────────────────────────

@app.route("/api/discover", methods=["POST"])
def discover():
    """Step 1: User enters company name + optional website. Returns detected profile + questionnaire."""
    data = request.get_json(silent=True) or {}
    company_name = str(data.get("company_name", "") or "").strip()
    website_url = str(data.get("website_url", "") or "").strip() or None

    if not company_name and not website_url:
        return jsonify({"error": "Company name is required"}), 400

    website_context: dict | None = None
    effective_url = website_url or (company_name if looks_like_website(company_name) else None)
    effective_name = (
        company_name if website_url else (company_name if not looks_like_website(company_name) else "")
    )
    if effective_url or effective_name:
        try:
            website_context = build_website_context(
                name=effective_name or "",
                website=effective_url or "",
            )
        except Exception:
            website_context = None

    try:
        discovery = discover_company_profile(company_name, website_context=website_context)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Discovery failed: {exc.__class__.__name__}"}), 500

    inferred = discovery["inferred"]
    questions = discovery.get("follow_up_questions", [])
    notes = discovery.get("notes", [])

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "company_name": company_name,
        "inferred": inferred,
        "website_context": website_context,
        "answers": {},
    }

    confirmations = _build_confirmations(inferred, company_name, website_context)

    return jsonify({
        "session_id": session_id,
        "profile": inferred,
        "questions": questions,
        "confirmations": confirmations,
        "detection_summary": {
            "match_type": discovery.get("match_type", ""),
            "confidence": discovery.get("confidence", ""),
            "notes": notes,
            "detected": [
                f"{k}: {v}"
                for k, v in inferred.items()
                if v and k in {
                    "legal_name", "gstin", "cin", "sector", "state",
                    "entity_type", "website_domain",
                }
            ],
        },
    })


@app.route("/api/questionnaire/submit", methods=["POST"])
def submit_questionnaire():
    """Step 2: User answers questionnaire. Returns updated profile + full obligation/scheme results."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    answers = data.get("answers", {})
    confirmations = data.get("confirmations", {})

    if not session_id or session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    session = sessions[session_id]
    inferred = dict(session["inferred"])

    for field, value in (confirmations or {}).items():
        if value not in (None, ""):
            inferred[field] = value

    for field, value in (answers or {}).items():
        if value is not None:
            inferred[field] = value

    inferred = _fill_required_defaults(inferred)
    inferred = enrich_company_runtime(inferred)
    analysis_bundle = _build_company_analysis_bundle(inferred, include_official_matches=True)

    sessions[session_id]["inferred"] = inferred
    sessions[session_id]["answers"] = answers

    return jsonify({
        "session_id": session_id,
        "profile": inferred,
        "results": {
            "obligations": analysis_bundle["obligations"],
            "schemes": analysis_bundle["schemes"],
            "opportunities": analysis_bundle["scheme_opportunities"],
            "metrics": analysis_bundle["metrics"],
            "verification": analysis_bundle["verification"],
            "official_scheme_matches": analysis_bundle["official_scheme_matches"],
            "official_scheme_meta": analysis_bundle["official_scheme_meta"],
            "analysis_focus": analysis_bundle["analysis_focus"],
        },
    })


@app.route("/api/scheme/<scheme_id>/review", methods=["POST"])
def scheme_review(scheme_id: str):
    """Step 3: Deep review of a specific scheme within a session."""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    answers = data.get("answers", {})

    if not session_id or session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    scheme = next((s for s in SCHEMES_CATALOG if s["template_id"] == scheme_id), None)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404

    profile = sessions[session_id]["inferred"]
    payload = _mapped_scheme_review_payload(
        profile,
        {"id": scheme_id, "status": evaluate_scheme(profile, scheme)["status"], "name": scheme["name"]},
        scheme,
        answers,
    )
    payload["stage"] = "questions" if not answers else "verdict"
    payload["eligibility_status"] = payload["review_status"]
    payload["eligibility_explanation"] = payload["review_message"]
    return jsonify(payload)


@app.route("/api/session/<session_id>/profile", methods=["GET"])
def get_session_profile(session_id: str):
    if session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(sessions[session_id]["inferred"])


@app.route("/api/schemes", methods=["GET"])
def list_schemes_catalog():
    """Return the full scheme catalogue (names and IDs only)."""
    return jsonify({
        "schemes": [
            {
                "template_id": s["template_id"],
                "name": s["name"],
                "ministry": s.get("ministry", ""),
                "scheme_type": s.get("scheme_type", ""),
                "benefit_value": s.get("benefit_value", ""),
                **scheme_display_metadata(s["template_id"]),
            }
            for s in SCHEMES_CATALOG
        ]
    })


# ── STATIC FILE SERVING ────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    f = ROOT / "index.html"
    if f.exists():
        return send_from_directory(str(ROOT), "index.html")
    return jsonify({"status": "ok"})


@app.route("/<path:path>")
def serve_static(path):
    f = ROOT / path
    if f.is_file():
        return send_from_directory(str(ROOT), path)
    return jsonify({"error": "Not found"}), 404


# ── MODULE-LEVEL INIT (for gunicorn / direct import) ──────────────────────────

try:
    init_db()
except Exception:
    pass


# ── ENTRYPOINT ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print(f"ComplianceIQ running on http://localhost:{PORT}")
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=PORT, host=HOST)
