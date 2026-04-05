from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import date, datetime, timezone
UTC = timezone.utc
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from engine import normalize_sector_key, sector_bucket


OFFICIAL_SOURCES = [
    {
        "source_id": "mca_master_data",
        "name": "MCA Company / LLP Master Data",
        "owner": "Ministry of Corporate Affairs",
        "domain": "mca.gov.in",
        "category": "company_registry",
        "source_url": "https://www.mca.gov.in/",
        "access_mode": "portal_with_manual_step",
        "identifier_fields": ["company_name", "cin", "llpin"],
        "industries": ["all"],
        "description": "Official company and LLP master data source used for incorporation and registry details.",
        "notes": "Use CIN or LLPIN wherever possible. Public access exists, but the live workflow is portal-based rather than a stable open API.",
    },
    {
        "source_id": "gst_taxpayer_search",
        "name": "GST Taxpayer Search",
        "owner": "GSTN / Government of India",
        "domain": "tutorial.gst.gov.in",
        "category": "tax_registration",
        "source_url": "https://tutorial.gst.gov.in/userguide/taxpayersdashboard/Search_Taxpayer_manual.htm",
        "access_mode": "portal_with_captcha",
        "identifier_fields": ["gstin"],
        "industries": ["all"],
        "description": "Official GST taxpayer search and filing visibility for registered taxpayers.",
        "notes": "The public GST workflow requires GSTIN and a captcha; login reveals additional business profile fields.",
    },
    {
        "source_id": "udyam_verification",
        "name": "Udyam Registration Verification",
        "owner": "Ministry of MSME",
        "domain": "udyamregistration.gov.in",
        "category": "msme_registry",
        "source_url": "https://udyamregistration.gov.in/Udyam_Verify.aspx",
        "access_mode": "portal_with_captcha",
        "identifier_fields": ["udyam_number"],
        "industries": ["all"],
        "description": "Official MSME / Udyam verification source.",
        "notes": "Requires a valid Udyam number and captcha. Use it to verify MSME status rather than relying on self-declaration.",
    },
    {
        "source_id": "startup_india_recognition",
        "name": "Startup India Recognition / 80-IAC Validation",
        "owner": "Startup India / DPIIT",
        "domain": "startupindia.gov.in",
        "category": "startup_registry",
        "source_url": "https://www.startupindia.gov.in/content/sih/en/startupgov/validate-startup-recognition.html",
        "access_mode": "public_validation",
        "identifier_fields": ["dpiit_certificate_number", "company_name", "cin", "pan"],
        "industries": ["technology", "education", "fintech", "healthcare", "other"],
        "description": "Official Startup India recognition and tax-exemption validation page.",
        "notes": "Best used with a certificate number; entity name can also be used in the validation workflow.",
    },
    {
        "source_id": "myscheme",
        "name": "myScheme",
        "owner": "Digital India Corporation / MeitY",
        "domain": "myscheme.gov.in",
        "category": "scheme_discovery",
        "source_url": "https://www.myscheme.gov.in/",
        "access_mode": "public_web",
        "identifier_fields": ["state", "sector", "entity_type", "annual_turnover", "employee_count"],
        "industries": ["all"],
        "description": "National platform for official scheme discovery and eligibility guidance.",
        "notes": "Use for scheme discovery and application routing. Scheme details live here and should be preferred over stale local copies.",
    },
    {
        "source_id": "dpiit_industrial_license_services",
        "name": "DPIIT Industrial License Services",
        "owner": "Department for Promotion of Industry and Internal Trade",
        "domain": "services.dpiit.gov.in",
        "category": "industrial_licensing",
        "source_url": "https://services.dpiit.gov.in/lms/ilServices",
        "access_mode": "portal_with_manual_step",
        "identifier_fields": ["company_name", "cin"],
        "industries": ["manufacturing", "technology"],
        "profile_tags": ["defence", "manufacturing"],
        "description": "Official industrial-licensing route for compulsorily licensable items, including defence-sector products under the IDR Act and Arms Act pathways.",
        "notes": "Use when the business manufactures defence items, aerospace systems, UAVs, or other licensable products. DPIIT's G2B portal is the official industrial-licence route.",
    },
    {
        "source_id": "drdo_tdf_official",
        "name": "DRDO Technology Development Fund",
        "owner": "DRDO / Ministry of Defence",
        "domain": "drdo.gov.in",
        "category": "sectoral_grants",
        "source_url": "https://www.drdo.gov.in/drdo/node/2967",
        "access_mode": "public_web",
        "identifier_fields": ["company_name", "cin"],
        "industries": ["manufacturing", "technology"],
        "profile_tags": ["defence", "manufacturing", "technology"],
        "description": "Official DRDO source for the Technology Development Fund and related defence-industry innovation support.",
        "notes": "Best used for defence and aerospace suppliers, especially where innovation, subsystem development, or prototyping support is being assessed.",
    },
    {
        "source_id": "invest_telangana_tsipass",
        "name": "Invest Telangana / TS-iPASS",
        "owner": "Department of Industries & Commerce, Government of Telangana",
        "domain": "invest.telangana.gov.in",
        "category": "state_industrial_clearances",
        "source_url": "https://invest.telangana.gov.in/",
        "access_mode": "public_web",
        "identifier_fields": ["company_name", "cin", "state"],
        "industries": ["manufacturing", "technology", "food_processing", "logistics", "construction"],
        "profile_tags": ["manufacturing", "defence", "food_processing"],
        "states": ["Telangana"],
        "description": "Official Telangana investor platform covering focus sectors such as Aerospace & Defence and the TS-iPASS single-window clearance route.",
        "notes": "Use for Telangana-based industrial projects to map plant approvals, self-certification routes, and state industrial support.",
    },
    {
        "source_id": "fssai_licensing",
        "name": "FSSAI FoSCoS Licensing",
        "owner": "Food Safety and Standards Authority of India",
        "domain": "fssai.gov.in",
        "category": "sectoral_licensing",
        "source_url": "https://www.fssai.gov.in/cms/licensing.php",
        "access_mode": "public_web",
        "identifier_fields": ["sector", "annual_turnover", "fssai_license_number"],
        "industries": ["food_processing", "retail", "logistics"],
        "description": "Official source for food licensing and FoSCoS eligibility guidance.",
        "notes": "Food businesses should be validated here; FoSCoS is the official pan-India IT platform for food-business licensing.",
    },
    {
        "source_id": "fssai_license_verify",
        "name": "FSSAI License Verification",
        "owner": "Food Safety and Standards Authority of India",
        "domain": "ams.fssai.gov.in",
        "category": "sectoral_verification",
        "source_url": "https://ams.fssai.gov.in/verifyLicence",
        "access_mode": "public_validation",
        "identifier_fields": ["fssai_license_number"],
        "industries": ["food_processing", "retail", "logistics"],
        "description": "Official FSSAI license-verification page.",
        "notes": "Use when the company provides a license number and sector indicates food-related operations.",
    },
    {
        "source_id": "epfo_establishment_search",
        "name": "EPFO Establishment Search",
        "owner": "Employees' Provident Fund Organisation",
        "domain": "unifiedportal-emp.epfindia.gov.in",
        "category": "labour_registry",
        "source_url": "https://unifiedportal-emp.epfindia.gov.in/publicPortal/no-auth/misReport/home/loadEstSearchHome",
        "access_mode": "portal_with_captcha",
        "identifier_fields": ["company_name", "epfo_establishment_code", "pan"],
        "industries": ["all"],
        "description": "Official EPFO establishment search.",
        "notes": "Useful for EPF-covered establishments. Requires captcha, so plan for a human-in-the-loop verification step.",
    },
    {
        "source_id": "esic_employer_search",
        "name": "ESIC Employer Search",
        "owner": "Employees' State Insurance Corporation",
        "domain": "portal.esic.gov.in",
        "category": "labour_registry",
        "source_url": "https://portal.esic.gov.in/EmployerSearch",
        "access_mode": "portal_with_captcha",
        "identifier_fields": ["company_name", "esic_employer_code", "state"],
        "industries": ["all"],
        "description": "Official ESIC employer lookup.",
        "notes": "Use for ESI-covered establishments and jurisdiction-aware verification.",
    },
    {
        "source_id": "labour_gazette",
        "name": "Ministry of Labour Gazette Notifications",
        "owner": "Ministry of Labour & Employment",
        "domain": "labour.gov.in",
        "category": "regulatory_updates",
        "source_url": "https://labour.gov.in/mainsecretariatdivisions/gazette-notifications",
        "access_mode": "public_web",
        "identifier_fields": ["sector", "state", "employee_count"],
        "industries": ["all"],
        "description": "Official labour gazette notifications source.",
        "notes": "Use this as a canonical source for labour-rule updates and exemptions instead of stale local assumptions.",
    },
    {
        "source_id": "indiacode",
        "name": "India Code",
        "owner": "Legislative Department / Government of India",
        "domain": "indiacode.nic.in",
        "category": "primary_law",
        "source_url": "https://www.indiacode.nic.in/",
        "access_mode": "public_web",
        "identifier_fields": ["act_name", "ministry", "sector"],
        "industries": ["all"],
        "description": "Official primary-law source for Acts, Rules, Regulations, Notifications and related legal texts.",
        "notes": "Use India Code as the canonical text source for central Acts and related subordinate legislation when available there.",
    },
    {
        "source_id": "dgft_export_schemes",
        "name": "DGFT Export Promotion Schemes",
        "owner": "Directorate General of Foreign Trade",
        "domain": "dgft.gov.in",
        "category": "export_schemes",
        "source_url": "https://www.dgft.gov.in/CP/?opt=highlights-on-export-promotion-schemes",
        "access_mode": "public_web",
        "identifier_fields": ["iec_number", "is_export_oriented", "sector"],
        "industries": ["export", "manufacturing", "technology", "other"],
        "description": "Official DGFT source for export-promotion scheme highlights.",
        "notes": "Use for export-oriented companies and cross-check with myScheme where overlap exists.",
    },
    {
        "source_id": "data_gov_in",
        "name": "Open Government Data Platform India",
        "owner": "NIC / MeitY",
        "domain": "data.gov.in",
        "category": "open_data_api",
        "source_url": "https://www.data.gov.in/help",
        "access_mode": "api_key_or_public_web",
        "identifier_fields": ["api_key"],
        "industries": ["all"],
        "description": "Official open-data and API catalog for government datasets.",
        "notes": "Use for official datasets where a ministry publishes machine-readable APIs. Many feeds require an API key generated on the portal.",
    },
]

MYSCHEME_API_BASE = "https://api.myscheme.gov.in"
MYSCHEME_WEB_ORIGIN = "https://www.myscheme.gov.in"
MYSCHEME_API_KEY = os.environ.get("MYSCHEME_API_KEY", "tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc")
MYSCHEME_PAGE_SIZE = 100

COMPANY_SECTOR_KEYWORDS = {
    "technology": ["technology", "software", "digital", "saas", "cloud", "platform", "electronics", "patent", "ipr"],
    "manufacturing": [
        "manufacturing",
        "industrial",
        "factory",
        "plant",
        "production",
        "machinery",
        "processing unit",
        "aerospace",
        "defence",
        "defense",
        "aircraft",
        "avionics",
        "uav",
        "drone",
        "missile",
        "precision engineering",
    ],
    "retail": ["retail", "ecommerce", "e commerce", "online store", "marketplace", "consumer brand"],
    "food_processing": ["food processing", "food", "beverage", "tea", "coffee", "spice", "spices", "fssai", "processing"],
    "healthcare": ["healthcare", "medical", "pharma", "biotech", "wellness", "ayush"],
    "fintech": ["fintech", "payments", "banking", "credit", "insurance", "financial services"],
    "education": ["education", "edtech", "learning", "training", "skilling", "school", "college", "university"],
    "logistics": ["logistics", "transport", "shipping", "warehouse", "freight", "supply chain"],
    "construction": ["construction", "housing", "real estate", "builders", "infrastructure"],
    "export": ["export", "exporter", "international trade", "dgft", "iec"],
    "agriculture": ["agriculture", "agri", "plantation", "farm", "horticulture", "tea garden", "post harvest"],
    "real_estate": ["real estate", "rera", "builder", "developer", "housing project"],
    "hospitality": ["hotel", "hospitality", "tourism", "resort", "travel"],
    "telecom": ["telecom", "telecommunication", "broadband", "isp"],
    "energy": ["energy", "power", "solar", "renewable", "electricity"],
    "media": ["media", "entertainment", "content", "gaming", "broadcast"],
    "professional_services": ["consulting", "legal", "chartered accountant", "company secretary", "professional services"],
    "ngo": ["social enterprise", "ngo", "foundation", "non profit", "csr"],
    "other": ["enterprise", "business"],
}

BUSINESS_CATEGORIES = {
    "Business & Entrepreneurship",
    "Banking,Financial Services and Insurance",
}

COMPANY_SCHEME_FOR_TERMS = {
    "business",
    "enterprise",
    "startup",
    "industry",
    "industries",
    "msme",
    "company",
    "companies",
    "institution",
    "institutions",
    "organisation",
    "organization",
    "cooperative",
}

INDIVIDUAL_SCHEME_FOR_TERMS = {
    "individual",
    "family",
    "farmer",
    "farmers",
    "artisan",
    "artisans",
    "weaver",
    "weavers",
    "student",
    "students",
    "citizen",
    "citizens",
    "youth",
    "woman",
    "women",
    "beneficiary",
}

NON_COMPANY_SCHEME_KEYWORDS = [
    "khadi",
    "handloom",
    "handicraft",
    "artisan",
    "artisans",
    "weaver",
    "weavers",
    "spinner",
    "craft award",
    "pension",
    "scholarship",
    "self employment",
    "self-employment",
    "unemployed youth",
    "manual scavengers",
    "village industries",
    "ex servicemen",
    "ex-servicemen",
    "widow",
    "widows",
    "penury",
    "social defence",
    "social welfare",
    "alcoholism",
    "substance abuse",
    "rehabilitation",
]

STARTUP_PROGRAM_KEYWORDS = [
    "startup",
    "startups",
    "startup india",
    "dpiit",
    "seed fund",
    "incubator",
    "incubation",
    "fund of funds",
    "aif",
    "venture capital",
]

MSME_PROGRAM_KEYWORDS = [
    "msme",
    "mse",
    "micro small",
    "micro and small",
    "micro & small",
    "small enterprise",
    "small enterprises",
    "udyam",
]

EXPORT_PROGRAM_KEYWORDS = [
    "export",
    "exporter",
    "dgft",
    "iec",
    "international market",
    "market development assistance",
    "trade fair",
    "duty remission",
    "advance authorisation",
    "advance authorization",
]

MANUFACTURING_PROGRAM_KEYWORDS = [
    "manufacturer",
    "manufacturing",
    "factory",
    "plant",
    "machinery",
    "capital goods",
    "supporting manufacturer",
    "production line",
]

DEFENCE_PROGRAM_KEYWORDS = [
    "defence",
    "defense",
    "defence industry",
    "defense industry",
    "defence production",
    "defense production",
    "aerospace",
    "aircraft",
    "avionics",
    "uav",
    "drone",
    "missile",
    "industrial license",
    "industrial licence",
]

WOMEN_PROGRAM_KEYWORDS = ["women", "woman", "female"]

RD_PROGRAM_KEYWORDS = ["research", "r d", "innovation", "patent", "ipr", "science and technology"]

INTERMEDIARY_PROGRAM_KEYWORDS = [
    "incubator",
    "incubators",
    "fund of funds",
    "aif",
    "alternative investment fund",
    "venture capital",
]

SOCIAL_SEGMENT_KEYWORDS = [
    "scheduled caste",
    "scheduled tribe",
    "sc st",
    "transgender",
    "tea tribes",
    "adivasi",
]

COMMODITY_KEYWORDS = {
    "tea": ["tea", "tea garden", "tea plantation", "orthodox tea", "speciality tea", "specialty tea"],
    "coffee": ["coffee"],
    "spices": ["spice", "spices"],
    "oilseeds": ["oil palm", "oilseed", "oilseeds", "edible oil", "edible oils"],
    "coir": ["coir"],
    "rubber": ["rubber"],
    "piggery": ["piggery", "pig", "pork"],
    "livestock": ["livestock", "poultry", "dairy", "goat", "sheep", "cattle"],
    "fisheries": ["fisheries", "fishery", "aquaculture", "marine"],
    "handloom": ["handloom", "handicraft", "artisan", "weaver"],
}

FALSE_DEFENCE_PHRASES = ["social defence", "civil defence"]

SPECIALISED_SCHEME_KEYWORDS = {
    **COMMODITY_KEYWORDS,
    "telecom": ["telecom", "telecommunication"],
    "defence": ["defence", "defense", "military", "armed forces", "naval", "aerospace"],
    "tourism": ["tourism", "tourist", "homestay", "hospitality"],
    "textiles": ["textile", "garment", "apparel", "loom"],
    "ayush": ["ayush"],
}


def active_official_sources() -> list[dict[str, Any]]:
    return [dict(item) for item in OFFICIAL_SOURCES]


def _match_fields(company: dict[str, Any], names: list[str]) -> dict[str, Any]:
    matched: dict[str, Any] = {}
    for name in names:
        if name == "company_name":
            value = company.get("name")
        else:
            value = company.get(name)
        if value not in (None, "", False):
            matched[name] = value
    return matched


def build_identifier_questions(company: dict[str, Any]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    entity_type = company.get("entity_type")
    sector = _effective_company_sector(company)

    if entity_type in {"pvt_ltd", "public_ltd"}:
        questions.append(
            {
                "field": "cin",
                "label": "CIN",
                "description": "Use the Corporate Identification Number to validate the company with MCA.",
            }
        )
    if entity_type == "llp":
        questions.append(
            {
                "field": "llpin",
                "label": "LLPIN",
                "description": "Use the LLPIN to validate the entity with MCA.",
            }
        )

    if company.get("is_msme") or not company.get("udyam_number"):
        questions.append(
            {
                "field": "udyam_number",
                "label": "Udyam registration number",
                "description": "Use this to verify MSME classification from the official Udyam portal.",
            }
        )

    if sector == "food_processing":
        questions.append(
            {
                "field": "fssai_license_number",
                "label": "FSSAI license number",
                "description": "Use this to verify food-business licensing on official FSSAI systems.",
            }
        )

    if company.get("is_dpiit") or company.get("is_startup_india") or entity_type in {"pvt_ltd", "llp"}:
        questions.append(
            {
                "field": "dpiit_certificate_number",
                "label": "Startup India / DPIIT certificate number",
                "description": "Use this to validate Startup India recognition and 80-IAC eligibility.",
            }
        )

    if company.get("is_export_oriented"):
        questions.append(
            {
                "field": "iec_number",
                "label": "IEC number",
                "description": "Use this for DGFT-linked export program and exporter verification workflows.",
            }
        )

    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for item in questions:
        if item["field"] in seen:
            continue
        seen.add(item["field"])
        deduped.append(item)
    return deduped


def build_verification_plan(company: dict[str, Any]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    sector = _effective_company_sector(company)
    company_state = str(company.get("state", "")).strip()
    company_tags = _company_profile_tags(company)

    for source in active_official_sources():
        if source["category"] == "tax_registration" and not company.get("gstin"):
            continue

        industries = source.get("industries", ["all"])
        if "all" not in industries and sector not in industries:
            continue

        states = source.get("states", [])
        if states and company_state not in states:
            continue

        profile_tags = set(source.get("profile_tags", []))
        if profile_tags and not (profile_tags & company_tags):
            continue

        provided = _match_fields(company, source.get("identifier_fields", []))
        required_fields = source.get("identifier_fields", [])
        missing_fields = [field for field in required_fields if field not in provided]

        status = "ready" if provided else "needs_identifiers"
        if source["access_mode"] in {"portal_with_captcha", "portal_with_manual_step"} and provided:
            status = "manual_verification_required"

        plan.append(
            {
                "source_id": source["source_id"],
                "source_name": source["name"],
                "category": source["category"],
                "source_url": source["source_url"],
                "access_mode": source["access_mode"],
                "provided_identifiers": provided,
                "missing_fields": missing_fields,
                "status": status,
                "description": source["description"],
                "notes": source["notes"],
            }
        )

    return plan


def probe_source(source: dict[str, Any], timeout_seconds: int = 10) -> dict[str, Any]:
    checked_at = datetime.now(UTC).isoformat()
    request = Request(
        source["source_url"],
        headers={
            "User-Agent": "ComplianceIQ/0.1 (+official-source-check)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            http_status = getattr(response, "status", 200)
            return {
                "source_id": source["source_id"],
                "checked_at": checked_at,
                "status": "reachable",
                "http_status": http_status,
                "status_detail": f"Official source responded with HTTP {http_status}.",
            }
    except HTTPError as exc:
        return {
            "source_id": source["source_id"],
            "checked_at": checked_at,
            "status": "http_error",
            "http_status": exc.code,
            "status_detail": f"Official source returned HTTP {exc.code}.",
        }
    except URLError as exc:
        reason = str(exc.reason)
        if "CERTIFICATE_VERIFY_FAILED" in reason:
            return {
                "source_id": source["source_id"],
                "checked_at": checked_at,
                "status": "tls_validation_failed",
                "http_status": None,
                "status_detail": f"TLS validation failed locally: {reason}",
            }
        return {
            "source_id": source["source_id"],
            "checked_at": checked_at,
            "status": "unreachable",
            "http_status": None,
            "status_detail": f"Source probe failed: {reason}",
        }


def refresh_source_health(source_ids: list[str] | None = None) -> list[dict[str, Any]]:
    allowed = set(source_ids or [])
    selected = [
        source
        for source in active_official_sources()
        if not allowed or source["source_id"] in allowed
    ]
    results: list[dict[str, Any]] = []
    for source in selected:
        result = probe_source(source)
        if source["access_mode"] in {"portal_with_captcha", "portal_with_manual_step"} and result["status"] == "reachable":
            result["status"] = "reachable_with_manual_step"
            result["status_detail"] = f"{result['status_detail']} Verification still requires an interactive portal step."
        results.append(result)
    return results


def source_catalog_json() -> str:
    return json.dumps(active_official_sources())


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_normalize_text(item) for item in value)
    return " ".join(str(value).strip().lower().split())


def _normalized_words(value: Any) -> list[str]:
    return re.findall(r"[a-z0-9]+", _normalize_text(value))


def _normalized_phrase(value: Any) -> str:
    return " ".join(_normalized_words(value))


def _contains_any(text: str, keywords: list[str]) -> bool:
    phrase_text = f" {_normalized_phrase(text)} "
    text_tokens = set(phrase_text.split())
    for keyword in keywords:
        phrase = _normalized_phrase(keyword)
        if not phrase:
            continue
        if " " in phrase:
            if f" {phrase} " in phrase_text:
                return True
            continue
        if phrase in text_tokens:
            return True
    return False


def _contains_defence_context(text: str) -> bool:
    phrase_text = f" {_normalized_phrase(text)} "
    for phrase in FALSE_DEFENCE_PHRASES:
        phrase_text = phrase_text.replace(f" {phrase} ", " ")
    return _contains_any(phrase_text, DEFENCE_PROGRAM_KEYWORDS)


def _myscheme_value_hint(text: str) -> tuple[str, str]:
    if _contains_any(text, ["interest subvention", "interest subsidy"]):
        return ("non_cash", "Interest support")
    if _contains_any(text, ["tax", "duty exemption", "tax exemption", "tax rebate"]):
        return ("non_cash", "Tax relief")
    if _contains_any(text, ["credit guarantee", "guarantee cover"]):
        return ("non_cash", "Credit guarantee")
    if _contains_any(text, ["loan", "credit", "working capital", "finance", "financial assistance"]):
        return ("non_cash", "Financing support")
    if _contains_any(text, ["market access", "export promotion", "promotion support"]):
        return ("non_cash", "Market access")
    if _contains_any(text, ["certificate", "certification", "quality mark"]):
        return ("non_cash", "Certification")
    if _contains_any(text, ["training", "capacity building", "skilling"]):
        return ("non_cash", "Capability support")
    if _contains_any(text, ["subsidy", "grant", "incentive"]):
        return ("non_cash", "Subsidy or grant")
    return ("non_cash", "Needs review")


def _effective_company_sector(company: dict[str, Any]) -> str:
    operating_activity = company.get("operating_activity", "same_as_detected")
    if operating_activity and operating_activity != "same_as_detected":
        mapped = {
            "procurement_ecommerce": "retail",
            "manufacturing_processing": "manufacturing",
            "agriculture_plantation": "agriculture",
            "services_software": "technology",
            "healthcare_services": "healthcare",
        }.get(operating_activity)
        if mapped == "manufacturing" and company.get("handles_food_products"):
            return "food_processing"
        if mapped:
            return sector_bucket(mapped)
    return sector_bucket(normalize_sector_key(company.get("sector", "other")))


def _matched_keyword_groups(text: str, mapping: dict[str, list[str]]) -> set[str]:
    matched: set[str] = set()
    for group, keywords in mapping.items():
        if group == "defence":
            if _contains_defence_context(text):
                matched.add(group)
        elif _contains_any(text, keywords):
            matched.add(group)
    return matched


def _myscheme_headers(include_json_body: bool = False) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": MYSCHEME_WEB_ORIGIN,
        "Referer": f"{MYSCHEME_WEB_ORIGIN}/",
        "User-Agent": "Mozilla/5.0 (compatible; ComplianceIQ/0.1; +official-source-sync)",
        "x-api-key": MYSCHEME_API_KEY,
    }
    if include_json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _myscheme_request(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    method: str = "GET",
    body: Any = None,
    timeout_seconds: int = 25,
) -> dict[str, Any]:
    url = f"{MYSCHEME_API_BASE}{path}"
    if params:
        clean_params = {key: value for key, value in params.items() if value not in (None, "")}
        query = urlencode(clean_params)
        if query:
            url = f"{url}?{query}"
    payload = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        method = "POST"
    request = Request(url, data=payload, headers=_myscheme_headers(body is not None), method=method)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content = response.read().decode("utf-8")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"myScheme request failed with HTTP {exc.code}: {detail[:240]}") from exc
    except URLError as exc:
        reason = str(exc.reason)
        if "CERTIFICATE_VERIFY_FAILED" in reason:
            return _myscheme_request_via_curl(url, body=body)
        raise RuntimeError(f"myScheme request failed: {exc.reason}") from exc

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("myScheme returned non-JSON content") from exc

    if parsed.get("statusCode") != 200 or parsed.get("status") != "Success":
        message = parsed.get("message") or parsed.get("errorDescription") or "Unexpected myScheme response"
        raise RuntimeError(f"myScheme request was not successful: {message}")
    return parsed


def _myscheme_request_via_curl(url: str, *, body: Any = None) -> dict[str, Any]:
    command = ["curl", "-sL", url]
    for header, value in _myscheme_headers(body is not None).items():
        command.extend(["-H", f"{header}: {value}"])
    if body is not None:
        command.extend(["--data", json.dumps(body)])
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("curl is required for the local TLS fallback but is not installed") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"myScheme curl fallback failed: {detail[:240]}") from exc

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("myScheme curl fallback returned non-JSON content") from exc

    if parsed.get("statusCode") != 200 or parsed.get("status") != "Success":
        message = parsed.get("message") or parsed.get("errorDescription") or "Unexpected myScheme response"
        raise RuntimeError(f"myScheme request was not successful: {message}")
    return parsed


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def fetch_myscheme_scheme_page(
    *,
    offset: int = 0,
    size: int = MYSCHEME_PAGE_SIZE,
    lang: str = "en",
    keyword: str = "",
    filters: list[dict[str, Any]] | None = None,
    sort: str = "multiple_sort",
) -> dict[str, Any]:
    query = json.dumps(filters) if filters else ""
    response = _myscheme_request(
        "/search/v6/schemes",
        params={
            "lang": lang,
            "q": query,
            "keyword": keyword,
            "sort": sort,
            "from": offset,
            "size": size,
        },
    )
    return response["data"]


def normalize_myscheme_search_item(item: dict[str, Any], *, synced_at: str) -> dict[str, Any]:
    fields = item.get("fields") or {}
    close_date = fields.get("schemeCloseDate")
    parsed_close_date = _parse_optional_date(close_date)
    categories = [str(entry).strip() for entry in fields.get("schemeCategory", []) if str(entry).strip()]
    states = [str(entry).strip() for entry in fields.get("beneficiaryState", []) if str(entry).strip()]
    tags = [str(entry).strip() for entry in fields.get("tags", []) if str(entry).strip()]
    scheme_name = str(fields.get("schemeName", "")).strip()
    ministry = str(fields.get("nodalMinistryName", "")).strip()
    slug = str(fields.get("slug", "")).strip()
    scheme_for = str(fields.get("schemeFor", "")).strip()
    brief_description = str(fields.get("briefDescription", "")).strip()
    return {
        "source_id": "myscheme",
        "scheme_id": item.get("id") or slug,
        "slug": slug,
        "scheme_name": scheme_name,
        "scheme_short_title": str(fields.get("schemeShortTitle", "")).strip(),
        "level": str(fields.get("level", "")).strip(),
        "scheme_for": scheme_for,
        "ministry": ministry,
        "categories": categories,
        "beneficiary_states": states,
        "tags": tags,
        "brief_description": brief_description,
        "scheme_close_date": close_date or None,
        "is_expired": bool(parsed_close_date and parsed_close_date < date.today()),
        "priority": int(fields.get("priority") or 0),
        "source_url": f"{MYSCHEME_WEB_ORIGIN}/schemes/{slug}" if slug else MYSCHEME_WEB_ORIGIN,
        "synced_at": synced_at,
        "raw_json": json.dumps(item, ensure_ascii=False),
    }


def sync_myscheme_catalog(*, lang: str = "en", max_records: int | None = None) -> dict[str, Any]:
    synced_at = datetime.now(UTC).isoformat()
    offset = 0
    total = None
    items: list[dict[str, Any]] = []

    while total is None or offset < total:
        page = fetch_myscheme_scheme_page(offset=offset, size=MYSCHEME_PAGE_SIZE, lang=lang)
        if total is None:
            total = int(page.get("summary", {}).get("total") or 0)
        hits = page.get("hits", {}).get("items", [])
        if not hits:
            break

        for hit in hits:
            items.append(normalize_myscheme_search_item(hit, synced_at=synced_at))
            if max_records is not None and len(items) >= max_records:
                break

        if max_records is not None and len(items) >= max_records:
            break
        offset += len(hits)

    return {
        "source_id": "myscheme",
        "synced_at": synced_at,
        "total_available": total or len(items),
        "fetched_count": len(items),
        "items": items,
    }


def fetch_myscheme_scheme_details(slugs: list[str], *, lang: str = "en") -> list[dict[str, Any]]:
    clean_slugs = [slug for slug in slugs if slug]
    if not clean_slugs:
        return []
    response = _myscheme_request("/schemes/v6/public/schemes", body=clean_slugs)
    details = response.get("data") or []
    if lang == "en":
        return details

    selected: list[dict[str, Any]] = []
    for entry in details:
        if lang in entry:
            selected.append({"slug": entry.get("slug"), lang: entry.get(lang)})
        elif "en" in entry:
            selected.append({"slug": entry.get("slug"), "en": entry.get("en")})
    return selected


def _company_turnover_bucket(company: dict[str, Any]) -> str:
    return str(company.get("annual_turnover", "")).strip()


def _company_employee_bucket(company: dict[str, Any]) -> str:
    return str(company.get("employee_count", "")).strip()


def _is_established_company(company: dict[str, Any]) -> bool:
    current_year = datetime.now(UTC).year
    founded_year = int(company.get("founded_year") or current_year)
    age = max(current_year - founded_year, 0)
    turnover_bucket = _company_turnover_bucket(company)
    employee_bucket = _company_employee_bucket(company)
    if turnover_bucket not in {"", "under_40L"}:
        return True
    if employee_bucket not in {"", "1_10"}:
        return True
    return age >= 2


def _scheme_for_terms(scheme: dict[str, Any]) -> set[str]:
    raw = _normalized_phrase(scheme.get("scheme_for")).replace("/", " ")
    return {term for term in raw.split() if term}


def _exclude_non_company_scheme(company: dict[str, Any], scheme: dict[str, Any], text: str) -> bool:
    scheme_for_terms = _scheme_for_terms(scheme)
    established = _is_established_company(company)
    analysis_scope = str(company.get("analysis_scope", "current_entity")).strip()

    if scheme_for_terms & INDIVIDUAL_SCHEME_FOR_TERMS:
        if analysis_scope != "new_entity_scenario":
            return True
        if established:
            return True

    if _contains_any(text, NON_COMPANY_SCHEME_KEYWORDS):
        if analysis_scope != "new_entity_scenario":
            return True
        if established:
            return True

    return False


def _company_profile_tags(company: dict[str, Any]) -> set[str]:
    identity_text = " ".join(
        [
            str(company.get("name", "")),
            str(company.get("legal_name", "")),
            str(company.get("website_domain", "")),
            str(company.get("website_url", "")),
            str(company.get("sector", "")),
            str(company.get("operating_activity", "")),
        ]
    )
    tags = _matched_keyword_groups(identity_text, SPECIALISED_SCHEME_KEYWORDS)
    tags.add(_effective_company_sector(company))
    if company.get("handles_food_products"):
        tags.add("food_processing")
    if company.get("has_factory_operations") or str(company.get("operating_activity", "")).strip() == "manufacturing_processing":
        tags.add("manufacturing")
    if company.get("serves_defence_sector"):
        tags.add("defence")
    if str(company.get("operating_activity", "")).strip() == "procurement_ecommerce":
        tags.add("retail")
        tags.add("ecommerce")
    if str(company.get("group_sector_hint", "")).strip():
        tags.add(f"parent_{company['group_sector_hint']}")
    return tags


def _has_conflicting_specialised_focus(text: str, company_tags: set[str]) -> bool:
    matched_groups = _matched_keyword_groups(text, SPECIALISED_SCHEME_KEYWORDS)
    if not matched_groups:
        return False
    return any(group not in company_tags for group in matched_groups)


def _missing_current_company_gate(company: dict[str, Any], text: str) -> str:
    analysis_scope = str(company.get("analysis_scope", "current_entity")).strip()
    operating_activity = str(company.get("operating_activity", "same_as_detected")).strip()
    current_sector = _effective_company_sector(company)

    if _contains_any(text, STARTUP_PROGRAM_KEYWORDS) and not (company.get("is_startup_india") or company.get("is_dpiit")):
        if analysis_scope != "new_entity_scenario":
            return "startup"

    if _contains_any(text, MSME_PROGRAM_KEYWORDS) and not company.get("is_msme"):
        return "msme"

    if _contains_any(text, EXPORT_PROGRAM_KEYWORDS) and not company.get("is_export_oriented"):
        return "export"

    if _contains_any(text, WOMEN_PROGRAM_KEYWORDS) and not company.get("women_led"):
        return "women"

    if _contains_defence_context(text) and not company.get("serves_defence_sector"):
        return "defence"

    if _contains_any(text, INTERMEDIARY_PROGRAM_KEYWORDS):
        return "intermediary"

    if _contains_any(text, SOCIAL_SEGMENT_KEYWORDS):
        if company.get("has_scst_founder"):
            return ""
        return "social_segment"

    if _contains_any(text, RD_PROGRAM_KEYWORDS) and not company.get("has_rd_collaboration"):
        if current_sector not in {"technology", "manufacturing", "healthcare", "education", "fintech"}:
            return "r_and_d"

    if _contains_any(text, MANUFACTURING_PROGRAM_KEYWORDS):
        if current_sector not in {"manufacturing", "food_processing"}:
            return "manufacturing"
        if analysis_scope == "brand_unit" and operating_activity in {"same_as_detected", "procurement_ecommerce"} and not company.get("has_factory_operations"):
            return "manufacturing"

    return ""


def rank_company_myscheme_matches(company: dict[str, Any], schemes: list[dict[str, Any]], *, limit: int = 12) -> list[dict[str, Any]]:
    company_state = str(company.get("state", "")).strip()
    company_sector = _effective_company_sector(company)
    analysis_scope = str(company.get("analysis_scope", "current_entity")).strip()
    company_tags = _company_profile_tags(company)
    company_text_flags = {
        "msme": bool(company.get("is_msme")),
        "startup": bool(company.get("is_startup_india") or company.get("is_dpiit")),
        "export": bool(company.get("is_export_oriented")),
        "women_led": bool(company.get("women_led")),
        "rd": bool(company.get("has_rd_collaboration")),
    }

    matches: list[dict[str, Any]] = []
    for scheme in schemes:
        if scheme.get("is_expired"):
            continue

        states = scheme.get("beneficiary_states") or []
        if states and "All" not in states and company_state and company_state not in states:
            continue

        categories = scheme.get("categories") or []
        tags = scheme.get("tags") or []
        text = " ".join(
            [
                _normalize_text(scheme.get("scheme_name")),
                _normalize_text(scheme.get("brief_description")),
                _normalize_text(scheme.get("scheme_for")),
                _normalize_text(scheme.get("ministry")),
                _normalize_text(categories),
                _normalize_text(tags),
            ]
        )

        if _exclude_non_company_scheme(company, scheme, text):
            continue

        if _has_conflicting_specialised_focus(text, company_tags):
            continue

        missing_gate = _missing_current_company_gate(company, text)
        if missing_gate:
            continue

        score = 0
        reasons: list[str] = []
        strong_signals = 0

        matched_categories = [category for category in categories if category in BUSINESS_CATEGORIES]
        if matched_categories:
            score += 2
            reasons.append(f"Official category match: {', '.join(matched_categories)}.")

        if _contains_any(text, ["business", "entrepreneur", "enterprise", "startup", "industry", "industrial"]):
            score += 1
            reasons.append("Scheme language indicates a business-facing program.")

        scheme_for_terms = _scheme_for_terms(scheme)
        if scheme_for_terms & COMPANY_SCHEME_FOR_TERMS:
            score += 2
            reasons.append("Official listing appears to address a business entity or enterprise.")

        sector_keywords = COMPANY_SECTOR_KEYWORDS.get(company_sector, COMPANY_SECTOR_KEYWORDS["other"])
        if _contains_any(text, sector_keywords):
            score += 4
            strong_signals += 1
            reasons.append(f"Sector signal found for {company_sector.replace('_', ' ')}.")

        matched_commodities = _matched_keyword_groups(text, COMMODITY_KEYWORDS)
        if matched_commodities:
            direct_commodities = sorted(matched_commodities & company_tags)
            if direct_commodities:
                score += 4
                strong_signals += 1
                reasons.append(f"Direct business-line signal found for {', '.join(direct_commodities)}.")

        matched_specialised = _matched_keyword_groups(text, SPECIALISED_SCHEME_KEYWORDS)
        direct_specialised = sorted((matched_specialised & company_tags) - matched_commodities)
        if direct_specialised:
            score += 4
            strong_signals += 1
            reasons.append(f"Specialised sector signal found for {', '.join(direct_specialised)}.")

        if company_text_flags["msme"] and _contains_any(text, ["msme", "micro, small", "micro small", "udyam"]):
            score += 3
            strong_signals += 1
            reasons.append("MSME-specific language matches the company's MSME flag.")

        if company_text_flags["startup"] and _contains_any(text, ["startup", "innovation", "seed", "incubation"]):
            score += 3
            strong_signals += 1
            reasons.append("Startup-oriented language matches the company's startup profile.")

        if company_text_flags["export"] and _contains_any(text, ["export", "exporter", "trade", "commerce", "international"]):
            score += 3
            strong_signals += 1
            reasons.append("Export-oriented language matches the company's export profile.")

        if company_text_flags["women_led"] and _contains_any(text, ["women", "woman", "female"]):
            score += 2
            strong_signals += 1
            reasons.append("Women-led preference appears relevant for this official scheme.")

        if company_text_flags["rd"] and _contains_any(text, ["research", "r&d", "science", "technology development", "ipr", "patent"]):
            score += 2
            strong_signals += 1
            reasons.append("R&D or innovation language matches the company's collaboration profile.")

        if company.get("serves_defence_sector") and _contains_defence_context(text):
            score += 3
            strong_signals += 1
            reasons.append("Defence or aerospace language matches the company's operating profile.")

        if states and company_state and company_state in states and "All" not in states:
            score += 2
            if matched_commodities or _contains_any(text, sector_keywords):
                strong_signals += 1
            reasons.append(f"State eligibility includes {company_state}.")

        minimum_score = 5 if analysis_scope == "new_entity_scenario" else 6
        minimum_strong_signals = 1 if analysis_scope == "new_entity_scenario" else 2
        if score < minimum_score or strong_signals < minimum_strong_signals:
            continue

        uncertainty = ""
        if _normalize_text(scheme.get("scheme_for")) == "individual":
            uncertainty = "Official listing is framed for individuals or founders, so human review is still needed before treating it as a company-level opportunity."
        if analysis_scope == "brand_unit" and _contains_any(text, ["plant", "machinery", "factory", "plantation", "farmer producer"]):
            extra = "This may still sit more naturally with the legal entity or parent operation than with the customer-facing brand unit."
            uncertainty = f"{uncertainty} {extra}".strip() if uncertainty else extra

        value_kind, value_label = _myscheme_value_hint(text)

        matches.append(
            {
                **scheme,
                "relevance_score": score,
                "reasons": reasons,
                "uncertainty": uncertainty,
                "value_kind": value_kind,
                "value_label": value_label,
            }
        )

    matches.sort(
        key=lambda item: (
            item.get("is_expired", False),
            -int(item.get("relevance_score", 0)),
            item.get("scheme_close_date") or "9999-12-31",
            item.get("scheme_name") or "",
        )
    )
    return matches[:limit]
