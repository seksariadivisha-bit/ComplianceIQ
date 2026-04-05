from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import re
from typing import Any


TURNOVER_LAKHS_BY_RANGE = {
    "unknown": 0,
    "under_40L": 30,
    "40L_1Cr": 70,
    "1Cr_10Cr": 500,
    "10Cr_100Cr": 5000,
    "100Cr_500Cr": 25000,
    "above_500Cr": 75000,
}

TURNOVER_RANGE_BOUNDS = {
    "unknown": (0, 9999999),
    "under_40L": (0, 40),
    "40L_1Cr": (40, 100),
    "1Cr_10Cr": (100, 1000),
    "10Cr_100Cr": (1000, 10000),
    "100Cr_500Cr": (10000, 50000),
    "above_500Cr": (50000, 9999999),
}

EMPLOYEE_COUNT_BY_RANGE = {
    "unknown": 0,
    "1_10": 10,
    "11_50": 50,
    "51_200": 200,
    "201_500": 500,
    "above_500": 800,
}

EMPLOYEE_RANGE_BOUNDS = {
    "unknown": (0, 999999),
    "1_10": (1, 10),
    "11_50": (11, 50),
    "51_200": (51, 200),
    "201_500": (201, 500),
    "above_500": (501, 999999),
}

INACTIVE_SCHEME_TEMPLATE_IDS = {
    "abry",
}

SECTOR_BUCKETS = {
    "technology": "technology",
    "technology_software": "technology",
    "technology_saas": "technology",
    "technology_hardware": "technology",
    "it_services": "technology",
    "bpo_kpo": "technology",
    "food_manufacturing": "food_processing",
    "food_processing": "food_processing",
    "food_retail": "food_processing",
    "restaurants_hospitality": "hospitality",
    "pharma_manufacturing": "healthcare",
    "pharma_distribution": "healthcare",
    "medical_devices": "healthcare",
    "hospitals_clinics": "healthcare",
    "diagnostic_labs": "healthcare",
    "healthcare": "healthcare",
    "fintech": "fintech",
    "nbfc": "fintech",
    "banking": "fintech",
    "insurance": "fintech",
    "investment_advisory": "fintech",
    "stockbroking": "fintech",
    "manufacturing": "manufacturing",
    "manufacturing_auto": "manufacturing",
    "manufacturing_electronics": "manufacturing",
    "manufacturing_chemicals": "manufacturing",
    "manufacturing_textiles": "manufacturing",
    "manufacturing_steel_metal": "manufacturing",
    "manufacturing_cement": "manufacturing",
    "manufacturing_plastic": "manufacturing",
    "manufacturing_garments": "manufacturing",
    "manufacturing_leather": "manufacturing",
    "manufacturing_paper": "manufacturing",
    "retail": "retail",
    "retail_ecommerce": "retail",
    "retail_offline": "retail",
    "marketplace_platform": "retail",
    "real_estate": "real_estate",
    "real_estate_developer": "real_estate",
    "real_estate_agent": "real_estate",
    "construction": "construction",
    "construction_infrastructure": "construction",
    "logistics": "logistics",
    "logistics_transport": "logistics",
    "warehousing": "logistics",
    "courier": "logistics",
    "edtech": "education",
    "education": "education",
    "education_school": "education",
    "education_college": "education",
    "education_edtech": "education",
    "coaching": "education",
    "agriculture": "agriculture",
    "agriculture_farming": "agriculture",
    "agritech": "agriculture",
    "food_agri_processing": "food_processing",
    "energy": "energy",
    "energy_solar": "energy",
    "energy_conventional": "energy",
    "mining": "energy",
    "media": "media",
    "media_entertainment": "media",
    "gaming": "media",
    "ott": "media",
    "legal_professional": "professional_services",
    "ca_cs_firm": "professional_services",
    "consulting": "professional_services",
    "ngo_csr": "ngo",
    "social_enterprise": "ngo",
    "export": "export",
    "export_trading": "export",
    "import_trading": "export",
    "tourism_hotels": "hospitality",
    "travel_agency": "hospitality",
    "hospitality": "hospitality",
    "telecom": "telecom",
    "isp": "telecom",
    "other": "other",
}

POLLUTION_CATEGORY_BY_SECTOR = {
    "technology": "white",
    "technology_software": "white",
    "technology_saas": "white",
    "technology_hardware": "orange",
    "it_services": "white",
    "bpo_kpo": "white",
    "food_manufacturing": "orange",
    "food_processing": "orange",
    "food_retail": "green",
    "restaurants_hospitality": "green",
    "pharma_manufacturing": "red",
    "pharma_distribution": "orange",
    "medical_devices": "orange",
    "hospitals_clinics": "orange",
    "diagnostic_labs": "orange",
    "fintech": "white",
    "nbfc": "white",
    "banking": "white",
    "insurance": "white",
    "investment_advisory": "white",
    "stockbroking": "white",
    "manufacturing": "orange",
    "manufacturing_auto": "orange",
    "manufacturing_electronics": "orange",
    "manufacturing_chemicals": "red",
    "manufacturing_textiles": "orange",
    "manufacturing_steel_metal": "red",
    "manufacturing_cement": "red",
    "manufacturing_plastic": "orange",
    "manufacturing_garments": "green",
    "manufacturing_leather": "orange",
    "manufacturing_paper": "orange",
    "retail": "white",
    "retail_ecommerce": "white",
    "retail_offline": "white",
    "marketplace_platform": "white",
    "real_estate_developer": "orange",
    "construction_infrastructure": "red",
    "logistics_transport": "green",
    "warehousing": "green",
    "courier": "green",
    "education_school": "white",
    "education_college": "white",
    "education_edtech": "white",
    "coaching": "white",
    "agriculture_farming": "green",
    "agritech": "green",
    "food_agri_processing": "orange",
    "energy_solar": "orange",
    "energy_conventional": "red",
    "mining": "red",
    "media_entertainment": "white",
    "gaming": "white",
    "ott": "white",
    "legal_professional": "white",
    "ca_cs_firm": "white",
    "consulting": "white",
    "ngo_csr": "white",
    "social_enterprise": "white",
    "export_trading": "white",
    "import_trading": "white",
    "tourism_hotels": "green",
    "travel_agency": "white",
    "telecom": "orange",
    "isp": "white",
    "other": "white",
}

FOOD_SECTORS = {"food_processing", "food_manufacturing", "food_retail", "food_agri_processing"}
MANUFACTURING_SECTORS = {
    "manufacturing",
    "manufacturing_auto",
    "manufacturing_electronics",
    "manufacturing_chemicals",
    "manufacturing_textiles",
    "manufacturing_steel_metal",
    "manufacturing_cement",
    "manufacturing_plastic",
    "manufacturing_garments",
    "manufacturing_leather",
    "manufacturing_paper",
    "food_manufacturing",
    "food_processing",
    "pharma_manufacturing",
    "medical_devices",
}
HEALTHCARE_SECTORS = {"healthcare", "pharma_manufacturing", "pharma_distribution", "medical_devices", "hospitals_clinics", "diagnostic_labs"}
FINANCIAL_SECTORS = {"fintech", "nbfc", "banking", "insurance", "investment_advisory", "stockbroking"}
REAL_ESTATE_SECTORS = {"real_estate", "real_estate_developer", "real_estate_agent"}
IT_SECTORS = {"technology", "technology_software", "technology_saas", "technology_hardware", "it_services", "bpo_kpo", "education_edtech"}
EDUCATION_SECTORS = {"education", "education_school", "education_college", "education_edtech", "coaching"}
HOSPITALITY_SECTORS = {"hospitality", "restaurants_hospitality", "tourism_hotels", "travel_agency"}
CONSTRUCTION_SECTORS = {"construction", "construction_infrastructure", "real_estate_developer"}
EXPORT_SECTORS = {"export", "export_trading", "import_trading"}
ECOMMERCE_SECTORS = {"retail_ecommerce", "marketplace_platform"}
PROFESSIONAL_SERVICE_SECTORS = {"legal_professional", "ca_cs_firm", "consulting"}


def normalize_sector_key(value: Any) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return lowered or "other"


def sector_bucket(value: Any) -> str:
    sector_key = normalize_sector_key(value)
    return SECTOR_BUCKETS.get(sector_key, sector_key)


def pollution_category(value: Any) -> str:
    sector_key = normalize_sector_key(value)
    if sector_key in POLLUTION_CATEGORY_BY_SECTOR:
        return POLLUTION_CATEGORY_BY_SECTOR[sector_key]
    return POLLUTION_CATEGORY_BY_SECTOR.get(sector_bucket(sector_key), "white")


def company_trigger_profile(company: dict[str, Any]) -> dict[str, Any]:
    sector_key = normalize_sector_key(company.get("sector", "other"))
    current_sector = effective_company_sector(company)
    current_sector_key = normalize_sector_key(current_sector)
    current_bucket = sector_bucket(current_sector_key)
    employee_count = company_employee_count(company)
    turnover_lakhs = company_turnover_lakhs(company)
    gstin = str(company.get("gstin", "") or "").strip()

    return {
        "sector_key": current_sector_key,
        "sector_bucket": current_bucket,
        "sector_display": current_sector_key,
        "pollution_category": pollution_category(current_sector_key),
        "employee_count": employee_count,
        "turnover_lakhs": turnover_lakhs,
        "company_age_years": company_age_years(company),
        "has_gstin": True if gstin else company.get("has_gstin"),
        "requires_tds": company.get("deducts_tds"),
        "is_msme": company.get("is_msme"),
        "is_startup_india": company.get("is_startup_india"),
        "is_dpiit": company.get("is_dpiit"),
        "is_export_oriented": company.get("is_export_oriented"),
        "has_foreign_investment": company.get("has_foreign_investment"),
        "is_listed": company.get("is_listed"),
        "women_led": company.get("women_led"),
        "has_scst_founder": company.get("has_scst_founder"),
        "has_factory_operations": company.get("has_factory_operations"),
        "handles_food_products": company.get("handles_food_products") if company.get("handles_food_products") is not None else (current_sector_key in FOOD_SECTORS or current_bucket == "food_processing"),
        "has_rd_collaboration": company.get("has_rd_collaboration"),
        "has_new_hires": company.get("has_new_hires"),
        "uses_contract_labour": company.get("uses_contract_labour"),
        "uses_interstate_migrant_workers": company.get("uses_interstate_migrant_workers"),
        "serves_defence_sector": company.get("serves_defence_sector"),
        "controlled_items_exposure": company.get("controlled_items_exposure"),
        "generates_hazardous_waste": company.get("generates_hazardous_waste"),
        "has_warehouse": company.get("has_warehouse"),
        "has_cold_chain": company.get("has_cold_chain"),
        "has_primary_processing": company.get("has_primary_processing"),
        "has_b2b_receivables": company.get("has_b2b_receivables"),
        "has_patent_activity": company.get("has_patent_activity"),
        "regulated_financial_entity": company.get("regulated_financial_entity"),
        "has_healthcare_facility": company.get("has_healthcare_facility"),
        "has_diagnostic_lab": company.get("has_diagnostic_lab"),
        "project_based_operations": company.get("project_based_operations"),
        "greenfield_for_promoter": company.get("greenfield_for_promoter"),
        "raw_sector": sector_key,
    }

OBLIGATIONS_CATALOG = [
    {
        "template_id": "gstr1-monthly",
        "name": "GSTR-1 Monthly Return",
        "category": "gst",
        "frequency": "monthly",
        "due_day": 11,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "requires_gstin": True,
        "min_turnover_lakhs": 500,
        "penalty_per_day": 100,
        "description": "Statement of outward supplies for taxpayers above the QRMP threshold.",
    },
    {
        "template_id": "gstr3b-monthly",
        "name": "GSTR-3B Monthly Return",
        "category": "gst",
        "frequency": "monthly",
        "due_day": 20,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "requires_gstin": True,
        "penalty_per_day": 50,
        "description": "Monthly GST summary return for liability and input credits.",
    },
    {
        "template_id": "gstr1-quarterly",
        "name": "GSTR-1 Quarterly Return",
        "category": "gst",
        "frequency": "quarterly",
        "due_day": 13,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "requires_gstin": True,
        "max_turnover_lakhs": 500,
        "penalty_per_day": 50,
        "description": "QRMP outward supply return for smaller taxpayers.",
    },
    {
        "template_id": "gstr9-annual",
        "name": "GSTR-9 Annual Return",
        "category": "gst",
        "frequency": "annual",
        "due_month": 12,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "requires_gstin": True,
        "penalty_per_day": 200,
        "description": "Annual GST return for registered taxpayers where applicable.",
    },
    {
        "template_id": "gstr9c-review",
        "name": "GSTR-9C / GST Reconciliation Review",
        "category": "gst",
        "frequency": "annual",
        "due_month": 12,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "requires_gstin": True,
        "min_turnover_lakhs": 500,
        "penalty_per_day": 500,
        "description": "Annual GST reconciliation and supporting working-paper review for larger taxpayers.",
    },
    {
        "template_id": "einvoicing-review",
        "name": "e-Invoicing Compliance Review",
        "category": "gst",
        "frequency": "monthly",
        "due_day": 5,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "requires_gstin": True,
        "min_turnover_lakhs": 500,
        "penalty_per_day": 1000,
        "description": "Review whether e-invoicing applies and whether IRN generation, invoice-series controls, and ERP setup are compliant.",
    },
    {
        "template_id": "tds-payment",
        "name": "TDS Deposit",
        "category": "tds",
        "frequency": "monthly",
        "due_day": 7,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd", "proprietorship"],
        "penalty_per_day": 500,
        "description": "Monthly TDS deposit and challan review for deductors.",
    },
    {
        "template_id": "tds-q1",
        "name": "TDS Return Q1",
        "category": "tds",
        "frequency": "annual",
        "due_month": 7,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "public_ltd"],
        "penalty_per_day": 200,
        "description": "Quarter 1 TDS filing.",
    },
    {
        "template_id": "tds-q2",
        "name": "TDS Return Q2",
        "category": "tds",
        "frequency": "annual",
        "due_month": 10,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "public_ltd"],
        "penalty_per_day": 200,
        "description": "Quarter 2 TDS filing.",
    },
    {
        "template_id": "tds-q3",
        "name": "TDS Return Q3",
        "category": "tds",
        "frequency": "annual",
        "due_month": 1,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "public_ltd", "partnership", "proprietorship"],
        "penalty_per_day": 200,
        "description": "Quarter 3 TDS filing.",
    },
    {
        "template_id": "tds-q4",
        "name": "TDS Return Q4",
        "category": "tds",
        "frequency": "annual",
        "due_month": 5,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "public_ltd", "partnership", "proprietorship"],
        "penalty_per_day": 200,
        "description": "Quarter 4 TDS filing.",
    },
    {
        "template_id": "advance-tax-june",
        "name": "Advance Tax Installment 1",
        "category": "tax",
        "frequency": "annual",
        "due_month": 6,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "min_turnover_lakhs": 40,
        "penalty_per_day": 200,
        "description": "Advance tax payment review for the June installment.",
    },
    {
        "template_id": "advance-tax-september",
        "name": "Advance Tax Installment 2",
        "category": "tax",
        "frequency": "annual",
        "due_month": 9,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "min_turnover_lakhs": 40,
        "penalty_per_day": 200,
        "description": "Advance tax payment review for the September installment.",
    },
    {
        "template_id": "advance-tax-december",
        "name": "Advance Tax Installment 3",
        "category": "tax",
        "frequency": "annual",
        "due_month": 12,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "min_turnover_lakhs": 40,
        "penalty_per_day": 200,
        "description": "Advance tax payment review for the December installment.",
    },
    {
        "template_id": "advance-tax-march",
        "name": "Advance Tax Installment 4",
        "category": "tax",
        "frequency": "annual",
        "due_month": 3,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "min_turnover_lakhs": 40,
        "penalty_per_day": 200,
        "description": "Advance tax payment review for the March installment.",
    },
    {
        "template_id": "tax-audit-review",
        "name": "Tax Audit Review",
        "category": "tax",
        "frequency": "annual",
        "due_month": 9,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "min_turnover_lakhs": 100,
        "penalty_per_day": 1000,
        "description": "Tax-audit applicability and Form 3CD review for businesses above the audit threshold.",
    },
    {
        "template_id": "pf-monthly",
        "name": "PF Monthly Contribution",
        "category": "labour",
        "frequency": "monthly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 20,
        "penalty_per_day": 500,
        "description": "Monthly EPF contribution for establishments with 20+ employees.",
    },
    {
        "template_id": "esi-monthly",
        "name": "ESI Monthly Contribution",
        "category": "labour",
        "frequency": "monthly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 10,
        "penalty_per_day": 300,
        "description": "Monthly ESI contribution for covered establishments.",
    },
    {
        "template_id": "aoc4",
        "name": "MCA Form AOC-4",
        "category": "roc",
        "frequency": "annual",
        "due_month": 10,
        "due_day": 29,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "penalty_per_day": 100,
        "description": "Annual filing of financial statements with MCA.",
    },
    {
        "template_id": "mgt7",
        "name": "MCA Form MGT-7",
        "category": "roc",
        "frequency": "annual",
        "due_month": 11,
        "due_day": 29,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "penalty_per_day": 100,
        "description": "Annual return filing with MCA.",
    },
    {
        "template_id": "itr-company",
        "name": "Income Tax Return - Company",
        "category": "tax",
        "frequency": "annual",
        "due_month": 10,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "penalty_per_day": 1000,
        "description": "Annual income tax return for companies.",
    },
    {
        "template_id": "profession-tax",
        "name": "Professional Tax",
        "category": "labour",
        "frequency": "annual",
        "due_month": 6,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "states": ["Maharashtra", "Karnataka", "Tamil Nadu", "West Bengal"],
        "penalty_per_day": 50,
        "description": "State-level professional tax in notified states.",
    },
    {
        "template_id": "labour-welfare",
        "name": "Labour Welfare Fund",
        "category": "labour",
        "frequency": "annual",
        "due_month": 12,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 5,
        "penalty_per_day": 75,
        "description": "Annual labour welfare contribution where applicable.",
    },
    {
        "template_id": "shops-establishment-review",
        "name": "Shops & Establishments Compliance Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "min_employees": 1,
        "exclude_factory_like": True,
        "penalty_per_day": 150,
        "description": "Review state Shops & Establishments registration, notice display, leave, weekly-off, and workplace-condition rules. Exposure varies by state, so confirm the state-specific labour department requirements.",
    },
    {
        "template_id": "minimum-wage-review",
        "name": "Minimum Wage & Wage-Payment Review",
        "category": "labour",
        "frequency": "monthly",
        "due_day": 10,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "min_employees": 1,
        "penalty_per_day": 300,
        "description": "Verify that state-notified minimum wages, VDA revisions, wage periods, and wage-payment timelines are being followed. This is a recurring labour-risk check rather than a one-time filing.",
    },
    {
        "template_id": "working-hours-review",
        "name": "Working Hours, Weekly-Off & Overtime Review",
        "category": "labour",
        "frequency": "monthly",
        "due_day": 12,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "min_employees": 1,
        "penalty_per_day": 300,
        "description": "Review attendance, shift rosters, overtime practices, weekly-off compliance, and register maintenance. This is especially important for retail, logistics, food, and operational teams.",
    },
    {
        "template_id": "fssai-renewal",
        "name": "FSSAI License Renewal",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 9,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "sectors": ["food_processing"],
        "requires_flags": ["handles_food_products"],
        "penalty_per_day": 100,
        "description": "Annual FSSAI renewal for food businesses.",
    },
    {
        "template_id": "environment-clearance",
        "name": "Pollution Control Consent & Environmental Approvals Review",
        "category": "environmental",
        "frequency": "annual",
        "due_month": 8,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["manufacturing"],
        "requires_factory_like": True,
        "penalty_per_day": 1000,
        "description": "Review Consent to Establish / Operate, pollution-control board filings, emissions or discharge conditions, and other plant-level environmental approvals for manufacturing sites.",
    },
    {
        "template_id": "factory-license-review",
        "name": "Factory Licence & Occupier / Manager Compliance Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["manufacturing"],
        "requires_factory_like": True,
        "min_employees": 10,
        "penalty_per_day": 1000,
        "description": "Review factory registration or licence status, occupier and manager filings, approved plans, worker thresholds, and state factory-inspectorate obligations for the plant.",
    },
    {
        "template_id": "defence-industrial-licence-review",
        "name": "Defence Industrial Licence & Controlled Items Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["manufacturing", "technology"],
        "requires_flags": ["serves_defence_sector"],
        "penalty_per_day": 1500,
        "description": "Review whether current products or assemblies fall under compulsorily licensable defence items, whether the industrial licence scope is correct, and whether progress / amendment obligations need attention before production or scale-up.",
    },
    {
        "template_id": "defence-site-security-review",
        "name": "Licensed Defence Site Security & Restricted Data Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 25,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["manufacturing", "technology"],
        "requires_flags": ["serves_defence_sector"],
        "penalty_per_day": 1000,
        "description": "Review plant security controls, restricted drawings or data handling, vendor and visitor access, and any site-side commitments that usually sit alongside licensed defence manufacturing.",
    },
    {
        "template_id": "posh-report",
        "name": "POSH Annual Report",
        "category": "labour",
        "frequency": "annual",
        "due_month": 3,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 10,
        "penalty_per_day": 100,
        "description": "Annual POSH reporting for covered establishments.",
    },
    {
        "template_id": "gratuity-readiness",
        "name": "Gratuity Eligibility & Funding Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "min_employees": 10,
        "penalty_per_day": 250,
        "description": "Check gratuity applicability, service records, and funding readiness for establishments with 10 or more workers.",
    },
    {
        "template_id": "maternity-benefit-review",
        "name": "Maternity Benefit Compliance Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "min_employees": 10,
        "penalty_per_day": 250,
        "description": "Review maternity-benefit coverage, leave, and policy readiness for establishments with 10 or more persons, subject to ESI overlap and state applicability.",
    },
    {
        "template_id": "bonus-review",
        "name": "Bonus Act Eligibility Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 11,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 20,
        "penalty_per_day": 250,
        "description": "Review Payment of Bonus Act applicability, eligible employee population, and payout readiness for establishments with 20 or more workers.",
    },
    {
        "template_id": "factory-safety-review",
        "name": "Factory Safety, Health & Welfare Audit",
        "category": "labour",
        "frequency": "quarterly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 10,
        "requires_factory_like": True,
        "penalty_per_day": 1000,
        "description": "Review health, safety, welfare, notice-display, accident reporting, PPE, and worker-condition controls for factory or plant operations.",
    },
    {
        "template_id": "standing-orders-review",
        "name": "Industrial Standing Orders & Shift Rules Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["manufacturing"],
        "requires_factory_like": True,
        "min_employees": 100,
        "penalty_per_day": 500,
        "description": "Review standing orders, shift classifications, suspension and misconduct procedures, and worker-rule communication for larger industrial establishments.",
    },
    {
        "template_id": "apprenticeship-review",
        "name": "Apprenticeship & Skill Training Compliance Review",
        "category": "labour",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 25,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["manufacturing"],
        "requires_factory_like": True,
        "min_employees": 30,
        "penalty_per_day": 400,
        "description": "Review apprenticeship, trainee intake, designated trade obligations, and training records where industrial operations are large enough to trigger them.",
    },
    {
        "template_id": "contract-labour-review",
        "name": "Contract Labour Compliance Review",
        "category": "labour",
        "frequency": "quarterly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 20,
        "requires_flags": ["uses_contract_labour"],
        "penalty_per_day": 600,
        "description": "Review contract-labour registration, contractor licensing, registers, and prohibited-process exposure where contract labour is used at scale.",
    },
    {
        "template_id": "interstate-migrant-review",
        "name": "Inter-State Migrant Worker Compliance Review",
        "category": "labour",
        "frequency": "quarterly",
        "due_day": 18,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "min_employees": 5,
        "requires_flags": ["uses_interstate_migrant_workers"],
        "penalty_per_day": 600,
        "description": "Review passbooks, displacement allowance, travel allowance, accommodation, and record-keeping if inter-state migrant workers are engaged.",
    },
    {
        "template_id": "llp-form-8",
        "name": "LLP Form 8 (Statement of Accounts)",
        "category": "roc",
        "frequency": "annual",
        "due_month": 10,
        "due_day": 30,
        "entity_types": ["llp"],
        "penalty_per_day": 100,
        "description": "Annual LLP statement of accounts and solvency filing.",
    },
    {
        "template_id": "llp-form-11",
        "name": "LLP Form 11 (Annual Return)",
        "category": "roc",
        "frequency": "annual",
        "due_month": 5,
        "due_day": 30,
        "entity_types": ["llp"],
        "penalty_per_day": 100,
        "description": "Annual LLP return filing.",
    },
    {
        "template_id": "board-meetings-review",
        "name": "Board Meetings & Governance Calendar Review",
        "category": "roc",
        "frequency": "quarterly",
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "opc"],
        "penalty_per_day": 250,
        "description": "Review board-meeting cadence, agenda packs, minutes, and governance calendar obligations under the Companies Act.",
    },
    {
        "template_id": "agm-review",
        "name": "Annual General Meeting Readiness Review",
        "category": "roc",
        "frequency": "annual",
        "due_month": 9,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "penalty_per_day": 1000,
        "description": "Review AGM timeline, notices, directors' report, and related annual governance tasks.",
    },
    {
        "template_id": "statutory-registers-review",
        "name": "Statutory Registers & Minutes Review",
        "category": "roc",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd", "opc"],
        "penalty_per_day": 500,
        "description": "Review statutory registers, share records, director records, and minutes book maintenance.",
    },
    {
        "template_id": "msme-1-review",
        "name": "MSME-1 Vendor Disclosure Review",
        "category": "roc",
        "frequency": "quarterly",
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "min_turnover_lakhs": 100,
        "penalty_per_day": 250,
        "description": "Review half-yearly MSME vendor payment disclosures where purchases from MSME suppliers create reporting obligations.",
    },
    {
        "template_id": "csr-review",
        "name": "CSR Spend & Reporting Review",
        "category": "roc",
        "frequency": "annual",
        "due_month": 9,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "min_turnover_lakhs": 100000,
        "penalty_per_day": 1000,
        "description": "Review CSR applicability, committee composition, spend tracking, and board-report disclosure for large companies.",
    },
    {
        "template_id": "brsr-review",
        "name": "BRSR / ESG Reporting Review",
        "category": "roc",
        "frequency": "annual",
        "due_month": 7,
        "due_day": 31,
        "entity_types": ["public_ltd"],
        "requires_listed": True,
        "penalty_per_day": 1000,
        "description": "Review BRSR and sustainability disclosure readiness for listed entities where SEBI requirements apply.",
    },
    {
        "template_id": "internal-audit-review",
        "name": "Internal Audit Applicability Review",
        "category": "roc",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "min_turnover_lakhs": 20000,
        "penalty_per_day": 500,
        "description": "Review whether internal audit becomes mandatory based on turnover, borrowings, or listed status.",
    },
    {
        "template_id": "fssai-annual-return",
        "name": "FSSAI Annual Return",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 5,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "sectors": ["food_processing"],
        "requires_flags": ["handles_food_products"],
        "penalty_per_day": 100,
        "description": "Annual return for licensed food businesses where FSSAI return obligations apply.",
    },
    {
        "template_id": "food-labelling-review",
        "name": "Food Packaging, Labelling & Traceability Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "sectors": ["food_processing"],
        "penalty_per_day": 300,
        "description": "Review food packaging, labelling, allergen, batch traceability, and consumer-information compliance.",
    },
    {
        "template_id": "drug-licence-review",
        "name": "Drug Licence Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "sectors": ["healthcare", "pharma_manufacturing", "pharma_distribution"],
        "penalty_per_day": 1000,
        "description": "Review drug-manufacturing or drug-distribution licence status and state-drug-controller obligations.",
    },
    {
        "template_id": "cdsco-review",
        "name": "CDSCO / Medical Device Registration Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 25,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd"],
        "sectors": ["healthcare", "medical_devices"],
        "penalty_per_day": 1000,
        "description": "Review CDSCO registrations, import licences, product approvals, and device-specific compliance for regulated products.",
    },
    {
        "template_id": "clinical-establishment-review",
        "name": "Clinical Establishment Registration Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 25,
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "sectors": ["healthcare", "hospitals_clinics", "diagnostic_labs"],
        "requires_flags": ["has_healthcare_facility"],
        "penalty_per_day": 500,
        "description": "Review state clinical-establishment registration, renewals, and facility-level operational permissions.",
    },
    {
        "template_id": "biomedical-waste-review",
        "name": "Biomedical Waste Authorisation Review",
        "category": "environmental",
        "frequency": "annual",
        "due_month": 6,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "llp", "partnership", "public_ltd", "proprietorship"],
        "sectors": ["healthcare", "hospitals_clinics", "diagnostic_labs"],
        "requires_flags": ["has_healthcare_facility"],
        "penalty_per_day": 800,
        "description": "Review biomedical-waste authorisation, disposal contracts, manifests, and waste records for healthcare facilities.",
    },
    {
        "template_id": "rbi-registration-review",
        "name": "RBI / Financial Regulator Registration Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership"],
        "sectors": ["fintech", "nbfc", "banking", "insurance", "investment_advisory", "stockbroking"],
        "requires_flags": ["regulated_financial_entity"],
        "penalty_per_day": 1500,
        "description": "Review whether the entity's regulated activities need RBI, SEBI, or IRDAI registration and whether the current approval scope is correct.",
    },
    {
        "template_id": "financial-returns-review",
        "name": "Quarterly Financial Regulator Returns Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership"],
        "sectors": ["fintech", "nbfc", "banking", "insurance", "investment_advisory", "stockbroking"],
        "requires_flags": ["regulated_financial_entity"],
        "penalty_per_day": 1200,
        "description": "Review RBI / SEBI / IRDAI periodic returns, prudential statements, and supervisory reporting where applicable.",
    },
    {
        "template_id": "kyc-aml-review",
        "name": "KYC / AML Policy & Monitoring Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 25,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership"],
        "sectors": ["fintech", "nbfc", "banking", "insurance", "investment_advisory", "stockbroking"],
        "requires_flags": ["regulated_financial_entity"],
        "penalty_per_day": 1200,
        "description": "Review KYC, AML, sanctions, suspicious-transaction, and policy-governance controls for regulated financial businesses.",
    },
    {
        "template_id": "pmla-review",
        "name": "PMLA / FIU Reporting Review",
        "category": "sectoral",
        "frequency": "monthly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership"],
        "sectors": ["fintech", "nbfc", "banking", "insurance", "investment_advisory", "stockbroking"],
        "requires_flags": ["regulated_financial_entity"],
        "penalty_per_day": 1500,
        "description": "Review suspicious transaction reporting, FIU workflows, and PMLA record-keeping where applicable.",
    },
    {
        "template_id": "financial-cyber-review",
        "name": "Financial Cybersecurity Framework Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 6,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership"],
        "sectors": ["fintech", "nbfc", "banking", "insurance", "investment_advisory", "stockbroking"],
        "requires_flags": ["regulated_financial_entity"],
        "penalty_per_day": 1000,
        "description": "Review regulator-mandated cybersecurity, incident response, audit, and resilience controls for financial entities.",
    },
    {
        "template_id": "rera-registration-review",
        "name": "RERA Registration Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sectors": ["real_estate", "real_estate_developer"],
        "requires_flags": ["project_based_operations"],
        "penalty_per_day": 1500,
        "description": "Review whether ongoing real-estate projects require RERA registration and whether project-level compliance is being followed.",
    },
    {
        "template_id": "rera-quarterly-review",
        "name": "RERA Quarterly Update Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sectors": ["real_estate", "real_estate_developer"],
        "requires_flags": ["project_based_operations"],
        "penalty_per_day": 1000,
        "description": "Review project-level quarterly RERA updates, escrow, and progress disclosures.",
    },
    {
        "template_id": "dpdp-review",
        "name": "DPDP Privacy & Consent Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["technology", "education", "retail", "healthcare", "fintech", "media", "professional_services"],
        "penalty_per_day": 1000,
        "description": "Review privacy notice, consent, data-processing, and grievance controls under the Digital Personal Data Protection framework.",
    },
    {
        "template_id": "cert-in-review",
        "name": "CERT-In Incident Reporting Readiness Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["technology", "education", "retail", "fintech", "media", "telecom"],
        "penalty_per_day": 1000,
        "description": "Review incident logging, clock synchronisation, retention, and 6-hour CERT-In reporting readiness for digital businesses.",
    },
    {
        "template_id": "stpi-review",
        "name": "STPI / SEZ Unit Compliance Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 6,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership"],
        "sector_groups": ["technology", "education"],
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 800,
        "description": "Review STPI / SEZ unit registration, export records, and periodic reporting where the software business operates under these regimes.",
    },
    {
        "template_id": "softex-review",
        "name": "SOFTEX / Software Export Reporting Review",
        "category": "sectoral",
        "frequency": "monthly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["technology", "education"],
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 500,
        "description": "Review SOFTEX and related software-export reporting for IT or SaaS exporters where applicable.",
    },
    {
        "template_id": "education-affiliation-review",
        "name": "Education Affiliation / Recognition Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["trust", "society", "section_8", "pvt_ltd", "public_ltd"],
        "sector_groups": ["education"],
        "penalty_per_day": 500,
        "description": "Review affiliation, recognition, or board-level approvals for schools and education institutions.",
    },
    {
        "template_id": "aicte-ugc-review",
        "name": "AICTE / UGC Approval Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 30,
        "entity_types": ["trust", "society", "section_8", "pvt_ltd", "public_ltd"],
        "sectors": ["education_college"],
        "penalty_per_day": 1000,
        "description": "Review AICTE / UGC approval, intake permissions, and annual institution reporting where applicable.",
    },
    {
        "template_id": "hotel-fire-review",
        "name": "Hospitality Fire NOC & Property Safety Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["hospitality"],
        "penalty_per_day": 1000,
        "description": "Review fire NOC, guest-safety, occupancy, and local operating permits for hotels and hospitality properties.",
    },
    {
        "template_id": "liquor-licence-review",
        "name": "Liquor Licence Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["hospitality"],
        "penalty_per_day": 1500,
        "description": "Review excise, serving, and liquor-licence permissions where the hospitality business serves alcohol.",
    },
    {
        "template_id": "cform-review",
        "name": "Foreign Guest C-Form / FRRO Readiness Review",
        "category": "sectoral",
        "frequency": "monthly",
        "due_day": 10,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["hospitality"],
        "penalty_per_day": 500,
        "description": "Review C-Form, foreign-guest reporting, and hospitality record-keeping where foreign nationals are hosted.",
    },
    {
        "template_id": "bocw-review",
        "name": "BOCW Registration Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["construction"],
        "penalty_per_day": 1200,
        "description": "Review BOCW registration, labour-board registration, and project-level worker-welfare obligations for construction businesses.",
    },
    {
        "template_id": "bocw-cess-review",
        "name": "BOCW Cess Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sector_groups": ["construction"],
        "penalty_per_day": 1200,
        "description": "Review building and construction workers welfare cess computation and deposit for eligible projects.",
    },
    {
        "template_id": "iec-review",
        "name": "Import Export Code Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 300,
        "description": "Review IEC status, DGFT profile updates, and entity-export readiness.",
    },
    {
        "template_id": "dgft-review",
        "name": "DGFT Export Compliance Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 500,
        "description": "Review DGFT profile, incentive claims, shipping-document discipline, and export-program registrations.",
    },
    {
        "template_id": "lut-review",
        "name": "GST LUT / Export Tax Review",
        "category": "gst",
        "frequency": "annual",
        "due_month": 3,
        "due_day": 31,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "requires_gstin": True,
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 500,
        "description": "Review LUT, export-without-payment-of-tax setup, and GST refund readiness for exporters.",
    },
    {
        "template_id": "fema-export-review",
        "name": "FEMA Export Proceeds Review",
        "category": "sectoral",
        "frequency": "monthly",
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 800,
        "description": "Review export proceeds realisation timelines, bank documentation, and FEMA discipline for export invoices.",
    },
    {
        "template_id": "rcmc-review",
        "name": "RCMC / Export Council Membership Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "requires_flags": ["is_export_oriented"],
        "penalty_per_day": 300,
        "description": "Review RCMC and relevant export-promotion-council registrations where goods categories require them.",
    },
    {
        "template_id": "marketplace-tcs-review",
        "name": "Marketplace TCS Review",
        "category": "gst",
        "frequency": "monthly",
        "due_day": 10,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sectors": ["marketplace_platform"],
        "requires_gstin": True,
        "penalty_per_day": 500,
        "description": "Review e-commerce operator TCS collection, deposit, and reconciliation where the business runs a marketplace.",
    },
    {
        "template_id": "ecommerce-rules-review",
        "name": "Consumer Protection (E-Commerce) Rules Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sectors": ["retail_ecommerce", "marketplace_platform"],
        "penalty_per_day": 400,
        "description": "Review e-commerce disclosures, grievance, seller information, and consumer-protection rule obligations.",
    },
    {
        "template_id": "fdi-fc-gpr-review",
        "name": "FDI Reporting / FC-GPR Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 4,
        "due_day": 20,
        "entity_types": ["pvt_ltd", "public_ltd", "llp"],
        "requires_foreign_investment": True,
        "penalty_per_day": 1500,
        "description": "Review foreign-investment reporting, FC-GPR / FC-TRS workflows, and downstream FEMA obligations.",
    },
    {
        "template_id": "fla-return-review",
        "name": "Foreign Liabilities & Assets Return Review",
        "category": "sectoral",
        "frequency": "annual",
        "due_month": 7,
        "due_day": 15,
        "entity_types": ["pvt_ltd", "public_ltd", "llp"],
        "requires_foreign_investment": True,
        "penalty_per_day": 1000,
        "description": "Review RBI annual FLA return applicability and filing readiness for entities with foreign investment or overseas assets/liabilities.",
    },
    {
        "template_id": "sebi-lodr-review",
        "name": "SEBI LODR Quarterly Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 45,
        "entity_types": ["public_ltd"],
        "requires_listed": True,
        "penalty_per_day": 1500,
        "description": "Review listed-company quarterly financial results and SEBI LODR disclosure readiness.",
    },
    {
        "template_id": "shareholding-pattern-review",
        "name": "Shareholding Pattern & Governance Disclosure Review",
        "category": "sectoral",
        "frequency": "quarterly",
        "due_day": 21,
        "entity_types": ["public_ltd"],
        "requires_listed": True,
        "penalty_per_day": 1000,
        "description": "Review listed-company shareholding pattern, RPT, and governance disclosure readiness.",
    },
    {
        "template_id": "director-kyc",
        "name": "Director KYC",
        "category": "roc",
        "frequency": "annual",
        "due_month": 9,
        "due_day": 30,
        "entity_types": ["pvt_ltd", "public_ltd"],
        "penalty_per_day": 0,
        "description": "DIR-3 KYC for directors.",
    },
]

SCHEMES_CATALOG = [
    {
        "template_id": "cgtmse",
        "name": "CGTMSE Credit Guarantee Scheme",
        "ministry": "Ministry of MSME",
        "scheme_type": "loan",
        "benefit_value": "Up to ₹2 Cr collateral-free credit guarantee",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Credit guarantee",
        "source_url": "https://www.cgtmse.in/",
        "requires_msme": True,
        "exclude_flags": [
            {
                "field": "regulated_financial_entity",
                "negative": "Regulated financial entities should not be treated as a standard MSME credit-guarantee fit.",
            }
        ],
    },
    {
        "template_id": "startup-tax",
        "name": "Startup India Tax Exemption",
        "ministry": "DPIIT",
        "scheme_type": "tax_benefit",
        "benefit_value": "100% income tax exemption for 3 years",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "Tax exemption",
        "source_url": "https://www.startupindia.gov.in/",
        "entity_types": ["pvt_ltd", "llp"],
        "requires_dpiit": True,
        "requires_dpiit_confirmed": True,
        "requires_identifiers": [
            {
                "field": "dpiit_certificate_number",
                "positive": "DPIIT certificate number is available for official validation.",
                "negative": "DPIIT certificate number should be confirmed before treating this tax benefit as ready.",
            }
        ],
        "max_turnover_lakhs": 10000,
        "max_company_age_years": 10,
    },
    {
        "template_id": "pli",
        "name": "PLI Scheme - Manufacturing",
        "ministry": "Ministry of Commerce",
        "scheme_type": "subsidy",
        "benefit_value": "4-6% incentive on incremental sales",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "4-6% sales incentive",
        "source_url": "https://www.makeinindia.com/production-linked-incentives-schemes",
        "entity_types": ["pvt_ltd", "public_ltd"],
        "sectors": ["manufacturing"],
        "min_turnover_lakhs": 1000,
    },
    {
        "template_id": "pmegp",
        "name": "PMEGP Capital Subsidy",
        "ministry": "Ministry of MSME",
        "scheme_type": "grant",
        "benefit_value": "15% to 35% capital subsidy",
        "max_benefit_amount": 2500000,
        "value_kind": "money",
        "value_label": "Capital subsidy",
        "source_url": "https://www.kviconline.gov.in/pmegp/",
        "entity_types": ["proprietorship", "partnership", "llp"],
        "sector_groups": ["manufacturing", "food_processing", "agriculture", "retail", "hospitality"],
        "max_turnover_lakhs": 40,
    },
    {
        "template_id": "samadhaan",
        "name": "MSME Samadhaan",
        "ministry": "Ministry of MSME",
        "scheme_type": "market_access",
        "benefit_value": "Delayed payment protection for MSMEs",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Payment protection",
        "source_url": "https://samadhaan.msme.gov.in/",
        "requires_msme": True,
        "requires_flags": [
            {
                "field": "has_b2b_receivables",
                "positive": "The business does raise B2B receivables against buyers.",
                "negative": "B2B receivables from buyers are required.",
                "strict": True,
            }
        ],
    },
    {
        "template_id": "zed",
        "name": "ZED Certification",
        "ministry": "Ministry of MSME",
        "scheme_type": "certification",
        "benefit_value": "Certification benefits and subsidy support",
        "max_benefit_amount": 200000,
        "value_kind": "money",
        "value_label": "Certification subsidy",
        "source_url": "https://zed.msme.gov.in/",
        "sectors": ["manufacturing"],
        "requires_msme": True,
    },
    {
        "template_id": "sip-eit",
        "name": "SIP-EIT Patent Subsidy",
        "ministry": "DPIIT",
        "scheme_type": "grant",
        "benefit_value": "Up to ₹15L for international patent cost support",
        "max_benefit_amount": 1500000,
        "value_kind": "money",
        "value_label": "Patent cost support",
        "source_url": "https://www.startupindia.gov.in/",
        "sector_groups": ["technology", "manufacturing", "healthcare"],
        "requires_one_of": ["is_msme", "is_startup_india"],
        "requires_flags": [
            {
                "field": "has_patent_activity",
                "positive": "Patent or patentable IP activity is confirmed.",
                "negative": "Patent filing or patentable product activity is required.",
                "strict": True,
            }
        ],
    },
    {
        "template_id": "rd-grant",
        "name": "R&D Multiplier Grants",
        "ministry": "Ministry of Science & Technology",
        "scheme_type": "r_and_d",
        "benefit_value": "Up to ₹2 Cr for industry-academia R&D collaboration",
        "max_benefit_amount": 20000000,
        "value_kind": "money",
        "value_label": "R&D grant",
        "source_url": "https://www.meity.gov.in/",
        "sectors": ["technology", "manufacturing", "healthcare"],
        "requires_flags": [
            {
                "field": "has_rd_collaboration",
                "positive": "R&D collaboration is confirmed.",
                "negative": "Formal R&D collaboration is required.",
                "strict": True,
            }
        ],
    },
    {
        "template_id": "abry",
        "name": "ABRY Employment Scheme",
        "ministry": "Ministry of Labour",
        "scheme_type": "subsidy",
        "benefit_value": "Government contribution toward EPF for eligible new hires",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "EPF support",
        "source_url": "https://www.epfindia.gov.in/",
        "min_employees": 2,
        "requires_flags": [
            {
                "field": "has_new_hires",
                "positive": "Recent qualifying hires are indicated.",
                "negative": "Recent qualifying hires are required.",
            }
        ],
    },
    {
        "template_id": "seed-fund",
        "name": "Startup India Seed Fund",
        "ministry": "DPIIT",
        "scheme_type": "grant",
        "benefit_value": "Up to ₹20L in early-stage support",
        "max_benefit_amount": 2000000,
        "value_kind": "money",
        "value_label": "Seed funding",
        "source_url": "https://www.startupindia.gov.in/",
        "entity_types": ["pvt_ltd", "llp"],
        "requires_dpiit": True,
        "requires_dpiit_confirmed": True,
        "requires_identifiers": [
            {
                "field": "dpiit_certificate_number",
                "positive": "DPIIT certificate number is available for official validation.",
                "negative": "DPIIT certificate number should be confirmed before treating this grant route as ready.",
            }
        ],
        "max_company_age_years": 2,
    },
    {
        "template_id": "treds",
        "name": "TReDS Invoice Discounting",
        "ministry": "Ministry of MSME",
        "scheme_type": "loan",
        "benefit_value": "Invoice discounting and receivables finance",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Receivables finance",
        "source_url": "https://www.treds.in/",
        "requires_msme": True,
        "requires_flags": [
            {
                "field": "has_b2b_receivables",
                "positive": "The business does raise B2B receivables against buyers.",
                "negative": "B2B receivables from corporate or institutional buyers are required.",
                "strict": True,
            }
        ],
    },
    {
        "template_id": "mai",
        "name": "MAI Export Scheme",
        "ministry": "Ministry of Commerce",
        "scheme_type": "market_access",
        "benefit_value": "Export market access and promotion support",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Market access support",
        "source_url": "https://www.dgft.gov.in/CP/?opt=highlights-on-export-promotion-schemes",
        "requires_export": True,
        "requires_identifiers": [
            {
                "field": "iec_number",
                "positive": "IEC is available for official export-route verification.",
                "negative": "IEC should be confirmed before treating export-support schemes as ready.",
            }
        ],
    },
    {
        "template_id": "aif",
        "name": "Agriculture Infrastructure Fund",
        "ministry": "Department of Agriculture & Farmers Welfare",
        "scheme_type": "loan",
        "benefit_value": "3% interest subvention on loans up to ₹2 Cr, with credit guarantee support for eligible borrowers",
        "max_benefit_amount": 600000,
        "value_kind": "estimate",
        "value_label": "Approx. ₹6L yearly interest support",
        "source_url": "https://agriinfra.dac.gov.in/",
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "sectors": ["agriculture", "food_processing"],
        "requires_any_flags": [
            {
                "field": "has_primary_processing",
                "positive": "Primary or integrated processing is indicated.",
            },
            {
                "field": "has_warehouse",
                "positive": "Warehousing or post-harvest storage infrastructure is indicated.",
            },
            {
                "field": "has_cold_chain",
                "positive": "Cold-chain infrastructure is indicated.",
            },
            {
                "field": "project_based_operations",
                "positive": "A real project-style infrastructure build is indicated.",
            },
        ],
        "requires_any_flags_prompt": "Confirm there is a real agri-infrastructure, storage, cold-chain, or processing project, not just retail or resale activity.",
        "uncertainty": "Confirm that the project involves eligible agriculture or post-harvest infrastructure, and whether the parent entity or a separate project vehicle should apply.",
    },
    {
        "template_id": "elevate",
        "name": "Karnataka Elevate",
        "ministry": "Government of Karnataka",
        "scheme_type": "grant",
        "benefit_value": "Up to ₹50L grant for Karnataka startups",
        "max_benefit_amount": 5000000,
        "value_kind": "money",
        "value_label": "Startup grant",
        "source_url": "https://startup.karnataka.gov.in/",
        "entity_types": ["pvt_ltd", "llp"],
        "states": ["Karnataka"],
        "sectors": ["technology", "edtech", "fintech", "healthcare"],
        "requires_startup_india": True,
        "max_company_age_years": 5,
    },
    {
        "template_id": "meity",
        "name": "Digital India / MeitY Grants",
        "ministry": "Ministry of Electronics & IT",
        "scheme_type": "grant",
        "benefit_value": "Various grants for software and technology startups",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "Grant support",
        "source_url": "https://www.meity.gov.in/",
        "entity_types": ["pvt_ltd"],
        "sector_groups": ["technology", "education"],
    },
    {
        "template_id": "drdo-tdf",
        "name": "DRDO Technology Development Fund",
        "ministry": "DRDO / Ministry of Defence",
        "scheme_type": "grant",
        "benefit_value": "Project cost support for defence and dual-use technology development under the official DRDO TDF route",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "Project cost support",
        "source_url": "https://drdo.gov.in/drdo/startups-support",
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship", "public_ltd"],
        "sectors": ["manufacturing", "technology"],
        "strict_requires_flags": ["serves_defence_sector"],
        "requires_one_of": ["is_msme", "is_startup_india"],
        "uncertainty": "The official route prioritises MSMEs and startups; larger companies may need a consortium, startup subsidiary, or a more specific project pathway.",
    },
    {
        "template_id": "telangana-aerospace-support",
        "name": "Telangana Aerospace & Defence Investor Support",
        "ministry": "Invest Telangana",
        "scheme_type": "market_access",
        "benefit_value": "Single-window approvals, land or infrastructure access, and customised state support for aerospace and defence investments in Telangana",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "State industrial support",
        "source_url": "https://invest.telangana.gov.in/",
        "entity_types": ["pvt_ltd", "public_ltd", "llp", "partnership", "proprietorship"],
        "states": ["Telangana"],
        "sectors": ["manufacturing", "technology"],
        "strict_requires_flags": ["serves_defence_sector"],
        "uncertainty": "Final support depends on project size, employment, land or park needs, and the exact Telangana policy route used.",
    },
    {
        "template_id": "interest-equalisation",
        "name": "Interest Equalisation Scheme",
        "ministry": "Ministry of Commerce / RBI",
        "scheme_type": "subsidy",
        "benefit_value": "3% to 5% interest subvention on eligible pre-shipment and post-shipment export credit",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "Interest support",
        "source_url": "https://www.dgft.gov.in/CP/?opt=highlights-on-export-promotion-schemes",
        "requires_export": True,
        "requires_identifiers": [
            {
                "field": "iec_number",
                "positive": "IEC is available for official export-route verification.",
                "negative": "IEC should be confirmed before treating export credit support as ready.",
            }
        ],
        "sector_groups": ["manufacturing", "food_processing", "agriculture", "export", "hospitality"],
    },
    {
        "template_id": "rodtep",
        "name": "RoDTEP",
        "ministry": "Ministry of Commerce",
        "scheme_type": "tax_benefit",
        "benefit_value": "Remission of duties and taxes on exported products at notified rates",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "Duty remission",
        "source_url": "https://www.dgft.gov.in/CP/?opt=highlights-on-export-promotion-schemes",
        "requires_export": True,
        "requires_identifiers": [
            {
                "field": "iec_number",
                "positive": "IEC is available for official export-route verification.",
                "negative": "IEC should be confirmed before treating export remission support as ready.",
            }
        ],
        "sector_groups": ["manufacturing", "food_processing", "agriculture", "export"],
    },
    {
        "template_id": "nirvik",
        "name": "NIRVIK / Export Credit Insurance Support",
        "ministry": "ECGC",
        "scheme_type": "insurance",
        "benefit_value": "Higher export credit insurance cover and lower premium support for exporters",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Insurance support",
        "source_url": "https://www.ecgc.in/",
        "requires_export": True,
        "requires_identifiers": [
            {
                "field": "iec_number",
                "positive": "IEC is available for official export-route verification.",
                "negative": "IEC should be confirmed before treating export insurance support as ready.",
            }
        ],
        "sector_groups": ["manufacturing", "food_processing", "technology", "export"],
    },
    {
        "template_id": "sidbi-msme-loans",
        "name": "SIDBI MSME Finance",
        "ministry": "SIDBI",
        "scheme_type": "loan",
        "benefit_value": "Growth capital and MSME credit support through SIDBI products",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "MSME finance",
        "source_url": "https://www.sidbi.in/",
        "requires_msme": True,
        "sector_groups": ["manufacturing", "food_processing", "technology", "healthcare", "logistics", "construction", "retail"],
    },
    {
        "template_id": "national-scst-hub",
        "name": "National SC-ST Hub",
        "ministry": "Ministry of MSME",
        "scheme_type": "market_access",
        "benefit_value": "Procurement access, vendor development, and capacity support for SC/ST-owned MSMEs",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Procurement access",
        "source_url": "https://www.scsthub.in/",
        "requires_msme": True,
        "requires_any_flags": [
            {
                "field": "has_scst_founder",
                "positive": "SC/ST founder ownership is confirmed.",
            }
        ],
        "requires_any_flags_strict": True,
    },
    {
        "template_id": "fame-india",
        "name": "FAME India",
        "ministry": "Ministry of Heavy Industries",
        "scheme_type": "subsidy",
        "benefit_value": "EV demand incentives and ecosystem support for eligible electric mobility categories",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "EV incentive",
        "source_url": "https://fame2.heavyindustries.gov.in/",
        "sector_groups": ["manufacturing", "logistics"],
        "sectors": ["manufacturing_auto", "logistics_transport"],
    },
    {
        "template_id": "textile-tufs",
        "name": "ATUFS / Textile Upgradation Support",
        "ministry": "Ministry of Textiles",
        "scheme_type": "subsidy",
        "benefit_value": "Capital subsidy and technology upgradation support for the textile sector",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "Capex subsidy",
        "source_url": "https://texmin.nic.in/",
        "sectors": ["manufacturing_textiles", "manufacturing_garments"],
    },
    {
        "template_id": "gujarat-industrial-subsidy",
        "name": "Gujarat Industrial Policy Subsidies",
        "ministry": "Government of Gujarat",
        "scheme_type": "subsidy",
        "benefit_value": "Capital and interest support under Gujarat industrial policy for eligible manufacturing projects",
        "max_benefit_amount": 0,
        "value_kind": "variable",
        "value_label": "State subsidy",
        "source_url": "https://iportal.gujarat.gov.in/",
        "states": ["Gujarat"],
        "sector_groups": ["manufacturing", "food_processing"],
    },
    {
        "template_id": "stand-up-india",
        "name": "Stand-Up India",
        "ministry": "Ministry of Finance",
        "scheme_type": "loan",
        "benefit_value": "₹10L to ₹1Cr loan support",
        "max_benefit_amount": 0,
        "value_kind": "non_cash",
        "value_label": "Loan support",
        "source_url": "https://www.standupmitra.in/",
        "entity_types": ["pvt_ltd", "llp", "partnership", "proprietorship"],
        "requires_flags": [
            {
                "field": "greenfield_for_promoter",
                "positive": "Greenfield status for the promoter is confirmed.",
                "negative": "Greenfield status is required.",
            }
        ],
        "requires_any_flags": [
            {
                "field": "women_led",
                "positive": "Women-led ownership is confirmed.",
            },
            {
                "field": "has_scst_founder",
                "positive": "SC/ST founder ownership is confirmed.",
            },
        ],
        "requires_any_flags_strict": True,
    },
]

SCHEME_TEMPLATE_INDEX = {item["template_id"]: item for item in SCHEMES_CATALOG}


def scheme_template(template_id: str) -> dict[str, Any]:
    return SCHEME_TEMPLATE_INDEX.get(template_id, {})


def title_case_flag(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def scheme_display_metadata(template_id: str) -> dict[str, Any]:
    template = scheme_template(template_id)
    amount = template.get("max_benefit_amount", 0) or 0
    value_kind = template.get("value_kind") or ("money" if amount else "non_cash")
    value_label = template.get("value_label") or template.get("benefit_value", "")
    return {
        "max_benefit_amount": amount,
        "value_kind": value_kind,
        "value_label": value_label,
        "source_url": template.get("source_url", ""),
    }


def format_lakhs_text(value: Any) -> str:
    amount = float(value or 0)
    if amount >= 100:
        crores = amount / 100
        if crores.is_integer():
            return f"₹{int(crores)} Cr"
        return f"₹{crores:.1f} Cr"
    if amount >= 1:
        if amount.is_integer():
            return f"₹{int(amount)} L"
        return f"₹{amount:.1f} L"
    rupees = int(round(amount * 100000))
    return f"₹{rupees:,}"


def humanize_entity_types(entity_types: list[str]) -> str:
    return ", ".join(value.replace("_", " ") for value in entity_types)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def select_question(
    key: str,
    label: str,
    options: list[list[str]],
    *,
    blocking_values: list[str] | None = None,
    uncertain_values: list[str] | None = None,
    blocking_message: str = "",
    warning_message: str = "",
    success_message: str = "",
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "options": options,
        "blocking_values": blocking_values or [],
        "uncertain_values": uncertain_values or [],
        "blocking_message": blocking_message,
        "warning_message": warning_message,
        "success_message": success_message,
    }


def yes_no_unsure_question(
    key: str,
    label: str,
    *,
    blocking_message: str,
    warning_message: str,
    success_message: str,
) -> dict[str, Any]:
    return select_question(
        key,
        label,
        [["unsure", "Not sure yet"], ["yes", "Yes"], ["no", "No"]],
        blocking_values=["no"],
        uncertain_values=["unsure"],
        blocking_message=blocking_message,
        warning_message=warning_message,
        success_message=success_message,
    )


def scheme_review_clauses(scheme: dict[str, Any]) -> list[str]:
    clauses: list[str] = []

    if scheme.get("scheme_type") == "loan":
        clauses.append("This is a financing route, so the loan ceiling is not the same as direct monetary gain.")
    if scheme.get("entity_types"):
        clauses.append(f"Eligible applicant structures include {humanize_entity_types(scheme['entity_types'])}.")
    if scheme.get("states"):
        clauses.append(f"This route is limited to entities operating in {', '.join(scheme['states'])}.")
    if scheme.get("requires_msme"):
        clauses.append("MSME / Udyam registration is required.")
    if scheme.get("requires_startup_india"):
        clauses.append("Startup India recognition is required.")
    if scheme.get("requires_dpiit"):
        clauses.append("DPIIT recognition is required.")
    if scheme.get("requires_export"):
        clauses.append("The route is intended for exporters or export-linked businesses.")
    if scheme.get("requires_one_of"):
        readable = []
        for key in scheme["requires_one_of"]:
            if key == "is_msme":
                readable.append("MSME registration")
            elif key == "is_startup_india":
                readable.append("Startup India recognition")
            elif key == "is_dpiit":
                readable.append("DPIIT recognition")
        if readable:
            clauses.append(f"At least one of these credentials is needed: {', '.join(readable)}.")
    if scheme.get("min_turnover_lakhs") is not None:
        clauses.append(f"Turnover needs to clear at least {format_lakhs_text(scheme['min_turnover_lakhs'])}.")
    if scheme.get("max_turnover_lakhs") is not None:
        clauses.append(f"Turnover generally needs to stay within {format_lakhs_text(scheme['max_turnover_lakhs'])}.")
    if scheme.get("max_company_age_years") is not None:
        clauses.append(f"The applying entity should usually be within {scheme['max_company_age_years']} years of age.")
    for flag in scheme.get("requires_flags", []):
        field = flag.get("field")
        if field == "has_rd_collaboration":
            clauses.append("A formal R&D or academic collaboration is part of the route.")
        elif field == "has_new_hires":
            clauses.append("The value depends on qualifying new hires actually being on payroll.")
        elif field == "serves_defence_sector":
            clauses.append("The applicant needs a real defence or aerospace product/program fit.")
    for field in scheme.get("strict_requires_flags", []):
        if field == "serves_defence_sector":
            clauses.append("The route is only relevant if the entity genuinely serves defence or aerospace manufacturing.")

    if scheme.get("template_id") == "aif":
        clauses.extend(
            [
                "3% interest subvention applies only up to ₹2 Cr of loan value, for a maximum of 7 years.",
                "Multiple projects at one location still share an overall ₹2 Cr cap at that location.",
                "Projects in different locations can each be considered separately, provided each location is distinct.",
                "For private-sector applicants such as agri-entrepreneurs and start-ups, the scheme caps the count at 25 projects.",
                "Standalone secondary processing is not eligible under the official guideline.",
                "For tea, coffee, and cocoa, eligible primary processing includes withering, rolling, fermentation, drying, sorting, packaging, and tea bags.",
            ]
        )

    deduped: list[str] = []
    seen: set[str] = set()
    for clause in clauses:
        if clause in seen:
            continue
        seen.add(clause)
        deduped.append(clause)
    return deduped


def scheme_review_questions(scheme: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []

    if scheme.get("entity_types"):
        questions.append(
            yes_no_unsure_question(
                "entity_type_fit",
                f"Will the applicant use an allowed entity type for this scheme ({humanize_entity_types(scheme['entity_types'])})?",
                blocking_message="The applicant structure does not fit this scheme route.",
                warning_message="Entity structure still needs confirmation before this scheme should be treated as usable.",
                success_message="The applicant structure looks aligned to the scheme.",
            )
        )

    if scheme.get("states"):
        questions.append(
            yes_no_unsure_question(
                "state_fit",
                f"Is the applying entity actually based or operating in {', '.join(scheme['states'])}?",
                blocking_message="The current entity does not satisfy the scheme's state condition.",
                warning_message="State fit still needs confirmation before this scheme should be treated as usable.",
                success_message="The state condition appears to be satisfied.",
            )
        )

    if scheme.get("requires_msme"):
        questions.append(
            yes_no_unsure_question(
                "msme_ready",
                "Does the applying entity hold valid MSME / Udyam registration?",
                blocking_message="MSME registration is required for this scheme.",
                warning_message="MSME registration still needs confirmation.",
                success_message="MSME registration appears available for this route.",
            )
        )

    if scheme.get("requires_startup_india"):
        questions.append(
            yes_no_unsure_question(
                "startup_india_ready",
                "Does the applying entity hold Startup India recognition?",
                blocking_message="Startup India recognition is required for this scheme.",
                warning_message="Startup India recognition still needs confirmation.",
                success_message="Startup India recognition appears available for this route.",
            )
        )

    if scheme.get("requires_dpiit"):
        questions.append(
            yes_no_unsure_question(
                "dpiit_ready",
                "Does the applying entity hold DPIIT recognition?",
                blocking_message="DPIIT recognition is required for this scheme.",
                warning_message="DPIIT recognition still needs confirmation.",
                success_message="DPIIT recognition appears available for this route.",
            )
        )

    if scheme.get("requires_export"):
        questions.append(
            yes_no_unsure_question(
                "export_ready",
                "Is the applying entity genuinely export-oriented for this scheme route?",
                blocking_message="This route needs real export activity.",
                warning_message="Export activity still needs confirmation.",
                success_message="Export orientation looks aligned to the scheme.",
            )
        )

    if scheme.get("requires_one_of"):
        questions.append(
            select_question(
                "credential_path",
                "Does the applying entity meet at least one of the required startup or MSME credential paths?",
                [
                    ["unsure", "Not sure yet"],
                    ["yes", "Yes"],
                    ["no", "No"],
                ],
                blocking_values=["no"],
                uncertain_values=["unsure"],
                blocking_message="The applicant does not appear to satisfy any of the required credential paths.",
                warning_message="The required credential path still needs confirmation.",
                success_message="At least one qualifying credential path appears available.",
            )
        )

    if scheme.get("max_company_age_years") is not None:
        questions.append(
            yes_no_unsure_question(
                "age_fit",
                f"Will the applying entity stay within the scheme's age limit of {scheme['max_company_age_years']} years?",
                blocking_message="The entity appears too old for this scheme route.",
                warning_message="Entity age fit still needs confirmation.",
                success_message="Entity age appears to fit the scheme ceiling.",
            )
        )

    if scheme.get("min_turnover_lakhs") is not None or scheme.get("max_turnover_lakhs") is not None:
        threshold_bits: list[str] = []
        if scheme.get("min_turnover_lakhs") is not None:
            threshold_bits.append(f"above {format_lakhs_text(scheme['min_turnover_lakhs'])}")
        if scheme.get("max_turnover_lakhs") is not None:
            threshold_bits.append(f"within {format_lakhs_text(scheme['max_turnover_lakhs'])}")
        questions.append(
            yes_no_unsure_question(
                "turnover_fit",
                f"Does the applying entity's turnover fit the scheme threshold ({' and '.join(threshold_bits)})?",
                blocking_message="The entity turnover does not fit the scheme threshold.",
                warning_message="Turnover fit still needs confirmation.",
                success_message="Turnover appears aligned to the scheme threshold.",
            )
        )

    founder_fields = {flag.get("field") for flag in scheme.get("requires_any_flags", [])}
    if founder_fields.intersection({"women_led", "has_scst_founder"}):
        questions.append(
            select_question(
                "founder_route",
                "Does the applicant qualify through a women-led or SC/ST founder route?",
                [
                    ["unsure", "Not sure yet"],
                    ["women", "Women-led route"],
                    ["scst", "SC/ST founder route"],
                    ["both", "Both"],
                    ["neither", "Neither"],
                ],
                blocking_values=["neither"],
                uncertain_values=["unsure"],
                blocking_message="The founder-route condition is not satisfied on the current answer.",
                warning_message="The founder-route condition still needs confirmation.",
                success_message="A qualifying founder route appears available.",
            )
        )

    for flag in scheme.get("requires_flags", []):
        field = flag.get("field")
        if field == "has_rd_collaboration":
            questions.append(
                yes_no_unsure_question(
                    "rd_collaboration_ready",
                    "Is there a formal R&D or academic collaboration that can support this application?",
                    blocking_message="A formal R&D collaboration is required here.",
                    warning_message="The R&D collaboration route still needs confirmation.",
                    success_message="The R&D collaboration route appears available.",
                )
            )
        elif field == "has_new_hires":
            questions.append(
                yes_no_unsure_question(
                    "new_hires_ready",
                    "Are there qualifying new hires on payroll for this scheme period?",
                    blocking_message="This route depends on qualifying new hires.",
                    warning_message="The new-hire condition still needs confirmation.",
                    success_message="Qualifying new hires appear to be present.",
                )
            )
        elif field == "greenfield_for_promoter":
            questions.append(
                yes_no_unsure_question(
                    "greenfield_ready",
                    "Is this genuinely a greenfield business for the promoter using the founder-route scheme?",
                    blocking_message="This route is not available if the promoter is not genuinely using it for a greenfield business.",
                    warning_message="Greenfield status still needs confirmation.",
                    success_message="Greenfield status appears aligned to the scheme.",
                )
            )
        elif field == "has_patent_activity":
            questions.append(
                yes_no_unsure_question(
                    "patent_activity_ready",
                    "Is there a real patent filing, prosecution, or patentable product-development track behind this application?",
                    blocking_message="Patent-led activity is required for this route.",
                    warning_message="Patent-led activity still needs confirmation.",
                    success_message="Patent-led activity appears aligned to the scheme.",
                )
            )
        elif field == "has_b2b_receivables":
            questions.append(
                yes_no_unsure_question(
                    "b2b_receivables_ready",
                    "Does the applicant actually raise B2B invoices to buyers and carry receivables against them?",
                    blocking_message="B2B receivables are required for this route.",
                    warning_message="B2B receivables still need confirmation.",
                    success_message="B2B receivables appear aligned to the scheme.",
                )
            )
        elif field == "controlled_items_exposure":
            questions.append(
                yes_no_unsure_question(
                    "controlled_items_ready",
                    "Do the relevant products or assemblies appear controlled, licensable, or security-sensitive for this route?",
                    blocking_message="This route should not be treated as relevant if the products do not fit the controlled-items condition.",
                    warning_message="Controlled-items exposure still needs confirmation.",
                    success_message="Controlled-items exposure appears directionally aligned.",
                )
            )

    for identifier in scheme.get("requires_identifiers", []):
        questions.append(
            yes_no_unsure_question(
                f"{identifier['field']}_ready",
                f"Is the required identifier available for official validation ({identifier['field'].replace('_', ' ')})?",
                blocking_message=identifier["negative"],
                warning_message=identifier["negative"],
                success_message=identifier["positive"],
            )
        )

    for field in scheme.get("strict_requires_flags", []):
        if field == "serves_defence_sector":
            questions.append(
                yes_no_unsure_question(
                    "defence_fit",
                    "Does the entity genuinely manufacture or supply defence or aerospace products, systems, or components relevant to this route?",
                    blocking_message="The company does not appear to fit the defence or aerospace requirement.",
                    warning_message="The defence or aerospace fit still needs confirmation.",
                    success_message="The defence or aerospace fit appears credible.",
                )
            )

    if scheme.get("scheme_type") == "tax_benefit":
        questions.append(
            select_question(
                "finance_ready",
                "Are financial statements and a CA-led review available for this tax-benefit route?",
                [["partial", "Partially"], ["yes", "Yes"], ["no", "No"]],
                blocking_values=["no"],
                uncertain_values=["partial"],
                blocking_message="The tax-benefit route should not be treated as usable without finance and CA review.",
                warning_message="Finance or CA review is still incomplete.",
                success_message="Finance and CA review readiness looks good.",
            )
        )

    if scheme.get("template_id") == "aif":
        questions.extend(
            [
                select_question(
                    "aif_project_fit",
                    "Does the project clearly fit an eligible AIF use case such as post-harvest management, storage, logistics, viable farming assets, or qualifying tea/coffee/cocoa processing?",
                    [["unsure", "Not sure yet"], ["yes", "Yes"], ["no", "No or mostly unrelated infrastructure"]],
                    blocking_values=["no"],
                    uncertain_values=["unsure"],
                    blocking_message="The current project does not read like eligible agriculture infrastructure.",
                    warning_message="Project fit still needs confirmation.",
                    success_message="Project scope appears directionally aligned to AIF.",
                ),
                select_question(
                    "aif_processing_scope",
                    "If processing is involved, is it primary processing or integrated primary + secondary, rather than standalone secondary processing?",
                    [
                        ["unsure", "Not sure yet"],
                        ["primary_or_integrated", "Primary or integrated primary + secondary"],
                        ["secondary_only", "Standalone secondary processing only"],
                        ["not_processing", "Processing is not the main project type"],
                    ],
                    blocking_values=["secondary_only"],
                    uncertain_values=["unsure"],
                    blocking_message="Standalone secondary processing is not eligible under the AIF guideline.",
                    warning_message="Processing classification still needs confirmation.",
                    success_message="The processing structure appears compatible with the official guideline.",
                ),
                select_question(
                    "aif_location_pattern",
                    "How is the project being structured across locations?",
                    [
                        ["unsure", "Not sure yet"],
                        ["single_location", "Single location or multiple assets in one location"],
                        ["different_locations", "Different project locations"],
                        ["apmc_multi_type", "APMC with different infrastructure types in the market area"],
                    ],
                    uncertain_values=["unsure"],
                    warning_message="Location structure still needs confirmation because it changes the usable cap.",
                    success_message="The location structure has been clarified.",
                ),
                select_question(
                    "aif_project_count",
                    "After this project, how many AIF projects would this private-sector applicant have in total?",
                    [
                        ["unsure", "Not sure yet"],
                        ["1_5", "1 to 5"],
                        ["6_25", "6 to 25"],
                        ["over_25", "More than 25"],
                    ],
                    blocking_values=["over_25"],
                    uncertain_values=["unsure"],
                    blocking_message="The private-sector applicant appears above the 25-project cap.",
                    warning_message="Project-count cap still needs confirmation.",
                    success_message="Project count appears to stay within the private-sector cap.",
                ),
            ]
        )

    deduped: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for question in questions:
        key = question["key"]
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(question)
    return deduped


def contextual_scheme_review_questions(company: dict[str, Any], scheme: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    if company.get("analysis_scope") == "brand_unit" and (
        company.get("group_sector_hint") or company.get("legal_name")
    ):
        questions.append(
            select_question(
                "correct_entity",
                "Which entity should actually apply for this scheme?",
                [
                    ["brand", "Current brand or business unit"],
                    ["parent", "Parent or legal entity"],
                    ["separate", "Separate new entity scenario"],
                    ["unsure", "Not sure yet"],
                ],
                uncertain_values=["unsure"],
                warning_message="Entity scope still needs confirmation before the scheme should be treated as application-ready.",
                success_message="The application entity has been clarified.",
            )
        )
    questions.extend(scheme_review_questions(scheme))
    deduped: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for question in questions:
        key = question["key"]
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(question)
    return deduped


def _review_answer_to_bool(answer: Any) -> bool | None:
    if answer in (True, "yes", "true", "Yes", "TRUE"):
        return True
    if answer in (False, "no", "false", "No", "FALSE"):
        return False
    return None


def _apply_review_answers_to_company(company: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    updated = deepcopy(company)

    mapping = {
        "msme_ready": "is_msme",
        "startup_india_ready": "is_startup_india",
        "dpiit_ready": "is_dpiit",
        "export_ready": "is_export_oriented",
        "rd_collaboration_ready": "has_rd_collaboration",
        "new_hires_ready": "has_new_hires",
        "greenfield_ready": "greenfield_for_promoter",
        "patent_activity_ready": "has_patent_activity",
        "b2b_receivables_ready": "has_b2b_receivables",
        "controlled_items_ready": "controlled_items_exposure",
        "defence_fit": "serves_defence_sector",
    }

    for answer_key, company_field in mapping.items():
        value = _review_answer_to_bool(answers.get(answer_key))
        if value is not None:
            updated[company_field] = value

    founder_route = answers.get("founder_route")
    if founder_route == "women":
        updated["women_led"] = True
        updated["has_scst_founder"] = False
    elif founder_route == "scst":
        updated["women_led"] = False
        updated["has_scst_founder"] = True
    elif founder_route == "both":
        updated["women_led"] = True
        updated["has_scst_founder"] = True
    elif founder_route == "neither":
        updated["women_led"] = False
        updated["has_scst_founder"] = False

    processing_scope = answers.get("aif_processing_scope")
    if processing_scope == "primary_or_integrated":
        updated["has_primary_processing"] = True
    elif processing_scope == "secondary_only":
        updated["has_primary_processing"] = False

    for identifier in OPTIONAL_IDENTIFIER_FIELDS:
        answer_key = f"{identifier}_ready"
        if answers.get(answer_key) == "yes" and not updated.get(identifier):
            updated[identifier] = "__review_confirmed__"
        elif answers.get(answer_key) == "no":
            updated[identifier] = ""

    return enrich_company_runtime(updated)


def _review_resolution_targets(scheme: dict[str, Any], question_key: str) -> list[str]:
    targets: list[str] = []
    if question_key == "entity_type_fit":
        targets.append("Entity type does not match.")
    elif question_key == "state_fit":
        targets.append("State is not covered.")
    elif question_key == "credential_path":
        targets.extend(
            [
                "Needs one qualifying startup/MSME credential.",
                "A qualifying startup/MSME credential still needs confirmation.",
            ]
        )
    elif question_key == "age_fit":
        targets.extend(
            [
                "Company age exceeds the limit.",
                "Company age still needs confirmation.",
            ]
        )
    elif question_key == "turnover_fit":
        targets.extend(
            [
                "Turnover is below the minimum threshold.",
                "Turnover exceeds the scheme ceiling.",
            ]
        )
    elif question_key == "msme_ready":
        targets.extend(
            [
                "MSME registration required.",
                "MSME registration status needs confirmation.",
            ]
        )
    elif question_key == "startup_india_ready":
        targets.extend(
            [
                "Startup India recognition required.",
                "Startup India recognition status needs confirmation.",
            ]
        )
    elif question_key == "dpiit_ready":
        targets.extend(
            [
                "DPIIT recognition required.",
                "DPIIT recognition status needs confirmation.",
            ]
        )
    elif question_key == "export_ready":
        targets.extend(
            [
                "Export activity required.",
                "Export activity still needs confirmation.",
            ]
        )
    elif question_key == "founder_route":
        targets.append(
            scheme.get("requires_any_flags_prompt")
            or "Confirm at least one of the scheme-specific qualifying paths before treating this as ready."
        )
    elif question_key == "finance_ready":
        targets.extend(
            [
                "The tax-benefit route should not be treated as usable without finance and CA review.",
                "Finance or CA review is still incomplete.",
            ]
        )
    elif question_key == "aif_project_fit":
        targets.extend(
            [
                "The current project does not read like eligible agriculture infrastructure.",
                "Project fit still needs confirmation.",
            ]
        )
    elif question_key == "aif_processing_scope":
        targets.extend(
            [
                "Standalone secondary processing is not eligible under the AIF guideline.",
                "Processing classification still needs confirmation.",
            ]
        )
    elif question_key == "aif_project_count":
        targets.extend(
            [
                "The private-sector applicant appears above the 25-project cap.",
                "Project-count cap still needs confirmation.",
            ]
        )

    for identifier in scheme.get("requires_identifiers", []):
        if question_key == f"{identifier['field']}_ready":
            targets.append(identifier["negative"])

    return targets


def _assess_review_questions(
    scheme: dict[str, Any],
    questions: list[dict[str, Any]],
    answers: dict[str, Any],
) -> dict[str, list[str]]:
    hard_blockers: list[str] = []
    warnings: list[str] = []
    successes: list[str] = []
    missing: list[str] = []
    resolved_targets: list[str] = []

    for question in questions:
        answer = answers.get(question["key"])
        if answer in (None, ""):
            missing.append(f"{question['label']} still needs confirmation.")
            continue
        if answer in question.get("blocking_values", []):
            message = question.get("blocking_message") or f"{question['label']} is not satisfied."
            hard_blockers.append(message)
            continue
        if answer in question.get("uncertain_values", []):
            message = question.get("warning_message") or f"{question['label']} still needs confirmation."
            warnings.append(message)
            continue
        if question.get("success_message"):
            successes.append(question["success_message"])
        resolved_targets.extend(_review_resolution_targets(scheme, question["key"]))

    return {
        "hard_blockers": dedupe_preserve_order(hard_blockers),
        "warnings": dedupe_preserve_order(warnings),
        "successes": dedupe_preserve_order(successes),
        "missing": dedupe_preserve_order(missing),
        "resolved_targets": dedupe_preserve_order(resolved_targets),
    }


def _aif_review_adjustments(answers: dict[str, Any]) -> dict[str, list[str]]:
    warnings: list[str] = []
    successes: list[str] = []
    location_pattern = answers.get("aif_location_pattern")
    if location_pattern == "single_location":
        warnings.append("AIF can still work here, but multiple projects at one location share one overall ₹2 Cr interest-subvention cap at that location.")
    elif location_pattern == "different_locations":
        successes.append("Different project locations can materially improve usable AIF economics if each site is genuinely distinct.")
    elif location_pattern == "apmc_multi_type":
        warnings.append("The multi-infrastructure, same-market-area exception is mainly framed for APMCs, so confirm the applicant route carefully.")
    return {
        "warnings": dedupe_preserve_order(warnings),
        "successes": dedupe_preserve_order(successes),
    }


def evaluate_scheme_review(company: dict[str, Any], scheme: dict[str, Any], answers: dict[str, Any] | None = None) -> dict[str, Any]:
    review_answers = {
        str(key): value
        for key, value in (answers or {}).items()
        if value not in (None, "")
    }
    review_company = _apply_review_answers_to_company(company, review_answers)
    base = evaluate_scheme(review_company, scheme)
    questions = contextual_scheme_review_questions(review_company, scheme)
    assessment = _assess_review_questions(scheme, questions, review_answers)

    hard_blockers = list(base.get("hard_blockers", []))
    soft_checks = list(base.get("soft_checks", []))
    reasons = list(base.get("reasons", []))

    if assessment["resolved_targets"]:
        hard_blockers = [item for item in hard_blockers if item not in assessment["resolved_targets"]]
        soft_checks = [item for item in soft_checks if item not in assessment["resolved_targets"]]

    hard_blockers.extend(assessment["hard_blockers"])
    soft_checks.extend(assessment["warnings"])
    reasons.extend(assessment["successes"])

    if scheme.get("template_id") == "aif":
        aif_adjustments = _aif_review_adjustments(review_answers)
        soft_checks.extend(aif_adjustments["warnings"])
        reasons.extend(aif_adjustments["successes"])

    entity_scope = review_answers.get("correct_entity")
    if entity_scope == "parent":
        review_status = "better_for_parent_entity"
        verdict = "Better aligned to the parent or legal entity"
        tone = "warning"
        message = "The scheme may still be valid, but it looks better aligned to the parent or legal entity than to the currently assessed brand unit."
    elif entity_scope == "separate":
        review_status = "better_for_separate_entity"
        verdict = "Better suited to a separate entity setup"
        tone = "warning"
        message = "This route looks more credible in a separate-entity scenario than under the currently assessed entity."
    elif hard_blockers:
        review_status = "review_ineligible"
        verdict = "Not apply-ready on the current answers"
        tone = "danger"
        message = hard_blockers[0]
    elif assessment["missing"] or soft_checks or base.get("uncertainty"):
        review_status = "review_needs_confirmation"
        verdict = "Still needs confirmation before applying"
        tone = "warning"
        if assessment["missing"]:
            message = assessment["missing"][0]
        elif soft_checks:
            message = soft_checks[0]
        else:
            message = base.get("uncertainty", "") or "A few conditions still need confirmation."
    else:
        review_status = "review_eligible"
        verdict = "Looks apply-ready now"
        tone = "success"
        message = "On the current company facts plus guided-review answers, this scheme looks application-ready."

    remaining_checks = []
    remaining_checks.extend(assessment["missing"])
    remaining_checks.extend(soft_checks)
    if base.get("uncertainty"):
        remaining_checks.append(base["uncertainty"])

    return {
        **base,
        "review_status": review_status,
        "review_verdict": verdict,
        "review_tone": tone,
        "review_message": message,
        "matched_conditions": dedupe_preserve_order(reasons),
        "unmet_conditions": dedupe_preserve_order(hard_blockers),
        "remaining_checks": dedupe_preserve_order(remaining_checks),
        "review_questions": questions,
        "review_answers": review_answers,
        "can_apply_now": review_status == "review_eligible",
    }

COMPANY_DIRECTORY = [
    {
        "aliases": ["infosys", "infosys ltd", "infosys limited"],
        "profile": {
            "name": "Infosys",
            "state": "Karnataka",
            "city": "Bengaluru",
            "entity_type": "public_ltd",
            "sector": "technology",
            "annual_turnover": "above_500Cr",
            "employee_count": "above_500",
            "founded_year": 1981,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "is_export_oriented": True,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "high",
    },
    {
        "aliases": ["zoho", "zoho corp", "zoho corporation"],
        "profile": {
            "name": "Zoho",
            "state": "Tamil Nadu",
            "city": "Chennai",
            "entity_type": "pvt_ltd",
            "sector": "technology",
            "annual_turnover": "100Cr_500Cr",
            "employee_count": "above_500",
            "founded_year": 1996,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "is_export_oriented": True,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "high",
    },
    {
        "aliases": ["zerodha"],
        "profile": {
            "name": "Zerodha",
            "state": "Karnataka",
            "city": "Bengaluru",
            "entity_type": "pvt_ltd",
            "sector": "fintech",
            "annual_turnover": "100Cr_500Cr",
            "employee_count": "201_500",
            "founded_year": 2010,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "is_export_oriented": False,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "high",
    },
    {
        "aliases": ["biocon"],
        "profile": {
            "name": "Biocon",
            "state": "Karnataka",
            "city": "Bengaluru",
            "entity_type": "public_ltd",
            "sector": "healthcare",
            "annual_turnover": "above_500Cr",
            "employee_count": "above_500",
            "founded_year": 1978,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "is_export_oriented": True,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "high",
    },
    {
        "aliases": ["ather", "ather energy"],
        "profile": {
            "name": "Ather Energy",
            "state": "Karnataka",
            "city": "Bengaluru",
            "entity_type": "pvt_ltd",
            "sector": "manufacturing",
            "annual_turnover": "10Cr_100Cr",
            "employee_count": "201_500",
            "founded_year": 2013,
            "is_msme": False,
            "is_startup_india": True,
            "is_dpiit": True,
            "is_export_oriented": False,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "high",
    },
    {
        "aliases": ["nykaa"],
        "profile": {
            "name": "Nykaa",
            "state": "Maharashtra",
            "city": "Mumbai",
            "entity_type": "public_ltd",
            "sector": "retail",
            "annual_turnover": "above_500Cr",
            "employee_count": "above_500",
            "founded_year": 2012,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "is_export_oriented": False,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "high",
    },
    {
        "aliases": ["keyshelf", "key shelf", "keyshell"],
        "profile": {
            "name": "KeyShelf",
            "state": "Karnataka",
            "city": "Bengaluru",
            "entity_type": "pvt_ltd",
            "sector": "technology",
            "annual_turnover": "1Cr_10Cr",
            "employee_count": "11_50",
            "founded_year": 2022,
            "is_msme": True,
            "is_startup_india": True,
            "is_dpiit": True,
            "is_export_oriented": False,
        },
        "notes": ["Matched against the local company intelligence directory."],
        "confidence": "medium",
    },
]

SECTOR_KEYWORDS = {
    "technology_saas": [
        "tech",
        "software",
        "labs",
        "digital",
        "systems",
        "data",
        "cloud",
        "ai",
        "saas",
        "platform",
        "analytics",
        "automation",
    ],
    "it_services": ["it services", "it consulting", "managed services", "outsourcing", "integration services"],
    "bpo_kpo": ["bpo", "kpo", "process outsourcing", "call center", "back office"],
    "manufacturing": [
        "manufacturing",
        "industries",
        "steel",
        "motors",
        "auto",
        "energy",
        "factory",
        "industrial",
        "plant",
        "production",
        "electronics",
        "equipment",
        "aerospace",
        "defence",
        "defense",
        "aviation",
        "avionics",
        "aircraft",
        "drone",
        "uav",
        "missile",
        "precision engineering",
        "fabrication",
        "machining",
    ],
    "manufacturing_electronics": ["electronics", "pcb", "semiconductor", "ems", "electronic manufacturing"],
    "manufacturing_textiles": ["textile", "textiles", "apparel", "garment", "loom", "weaving"],
    "manufacturing_chemicals": ["chemicals", "chemical", "speciality chemical", "bulk drug"],
    "pharma_manufacturing": ["pharma", "pharmaceutical", "bulk drugs", "formulations"],
    "medical_devices": ["medical device", "medical devices", "diagnostic equipment", "implant"],
    "retail_ecommerce": [
        "retail",
        "stores",
        "fashion",
        "mart",
        "shop",
        "store",
        "ecommerce",
        "online store",
        "gifting",
        "wholesale",
        "consumer brand",
    ],
    "marketplace_platform": ["marketplace", "seller platform", "multi-vendor", "aggregator", "merchant platform"],
    "food_processing": [
        "foods",
        "food",
        "kitchen",
        "beverage",
        "beverages",
        "dairy",
        "snacks",
        "tea",
        "coffee",
        "chai",
        "brew",
        "herbal",
        "loose leaf",
        "packed food",
        "spices",
        "bakery",
    ],
    "hospitals_clinics": ["hospital", "clinic", "care", "medical center", "healthcare", "clinical"],
    "diagnostic_labs": ["diagnostic", "pathology", "radiology", "lab", "laboratory"],
    "fintech": ["fintech", "payments", "lending", "wallet", "neo bank"],
    "nbfc": ["nbfc", "microfinance", "vehicle finance", "housing finance"],
    "banking": ["bank", "banking"],
    "insurance": ["insurance", "insurtech", "brokerage"],
    "investment_advisory": ["investment advisory", "wealth", "asset management", "pms", "aif"],
    "stockbroking": ["broking", "broker", "stock broking", "trading platform"],
    "education_edtech": ["edtech", "learning", "upskilling", "skilling"],
    "education_school": ["school", "schools", "cbse", "icse", "academy"],
    "education_college": ["college", "university", "institute", "campus"],
    "logistics_transport": ["logistics", "supply", "shipping", "freight", "delivery", "transport", "fleet"],
    "warehousing": ["warehouse", "warehousing", "cold chain"],
    "construction_infrastructure": ["infra", "construction", "builders", "cement", "realty", "contracting", "epc"],
    "real_estate_developer": ["real estate", "developer", "developers", "realty"],
    "export_trading": ["exports", "export", "trading", "global", "international shipping", "worldwide shipping"],
    "agriculture_farming": ["agro", "farm", "agri", "estate", "plantation", "horticulture"],
    "agritech": ["agritech", "farm tech", "agri-tech"],
    "tourism_hotels": ["hotel", "resort", "hospitality", "homestay"],
    "travel_agency": ["travel", "tour", "tourism", "booking"],
    "telecom": ["telecom", "telecommunications", "carrier"],
    "isp": ["internet service provider", "broadband", "isp"],
    "energy_solar": ["solar", "renewable", "photovoltaic"],
    "energy_conventional": ["power plant", "thermal", "oil", "gas", "energy"],
    "legal_professional": ["legal", "law firm", "advocates"],
    "ca_cs_firm": ["chartered accountant", "ca firm", "company secretary", "cs firm"],
    "consulting": ["consulting", "advisory", "consultants"],
    "ngo_csr": ["foundation", "ngo", "non profit", "csr"],
    "media_entertainment": ["media", "entertainment", "studio", "production house"],
    "gaming": ["gaming", "game studio"],
}

LEGAL_SUFFIX_TOKENS = {
    "private",
    "pvt",
    "public",
    "limited",
    "ltd",
    "llp",
    "corporation",
    "corp",
    "company",
    "co",
    "inc",
    "incorporated",
}

DEFENCE_KEYWORDS = {
    "defence",
    "defense",
    "aerospace",
    "aviation",
    "avionics",
    "military",
    "armed",
    "naval",
    "aircraft",
    "drone",
    "uav",
    "missile",
    "munition",
    "ordnance",
}

FACTORY_INDICATOR_KEYWORDS = {
    "manufacturing",
    "factory",
    "plant",
    "production",
    "assembly",
    "fabrication",
    "machining",
    "industrial",
    "workshop",
    "facility",
    "aerospace",
    "defence",
    "defense",
}

REQUIRED_COMPANY_FIELDS = [
    "name",
    "state",
    "city",
    "entity_type",
    "sector",
    "annual_turnover",
    "employee_count",
    "founded_year",
]

OPTIONAL_IDENTIFIER_FIELDS = [
    "cin",
    "llpin",
    "gstin",
    "pan",
    "udyam_number",
    "dpiit_certificate_number",
    "fssai_license_number",
    "iec_number",
]

OPTIONAL_PROFILE_FIELDS = [
    "legal_name",
    "website_url",
    "website_domain",
    "analysis_scope",
    "operating_activity",
    "group_sector_hint",
]

OPERATING_ACTIVITY_TO_SECTOR = {
    "procurement_ecommerce": "retail",
    "manufacturing_processing": "manufacturing",
    "agriculture_plantation": "agriculture",
    "services_software": "technology",
    "healthcare_services": "healthcare",
}


def inferred_sector_pack(profile: dict[str, Any]) -> str:
    triggers = company_trigger_profile(profile)
    sector_key = triggers["sector_key"]
    sector_group = triggers["sector_bucket"]
    identity_text = " ".join(
        str(profile.get(field, "") or "")
        for field in ["name", "legal_name", "website_domain", "website_url", "group_sector_hint"]
    ).lower()
    defence_hint = any(keyword in identity_text for keyword in DEFENCE_KEYWORDS)

    if sector_group in {"manufacturing", "food_processing"} and (triggers["serves_defence_sector"] or defence_hint):
        return "manufacturing_defence"
    if sector_group in {"food_processing", "agriculture"} or sector_key in {"food_retail", "food_manufacturing"}:
        return "food_agri"
    if sector_group == "manufacturing":
        return "manufacturing"
    if sector_group == "healthcare":
        return "healthcare"
    if sector_group == "fintech":
        return "finance"
    if sector_group in {"construction", "real_estate"}:
        return "construction_real_estate"
    if sector_group == "logistics":
        return "logistics"
    if sector_group == "technology":
        return "technology"
    return "general"


def _question(field: str, label: str, description: str, priority: int, section: str) -> dict[str, Any]:
    return {
        "field": field,
        "label": label,
        "description": description,
        "priority": priority,
        "section": section,
    }


def follow_up_questions_for_profile(profile: dict[str, Any]) -> list[dict[str, str]]:
    profile = enrich_company_runtime(dict(profile))
    questions: list[dict[str, str]] = []
    entity_type = profile.get("entity_type")
    triggers = company_trigger_profile(profile)
    sector_pack = inferred_sector_pack(profile)

    if profile.get("has_gstin") is None and not profile.get("gstin"):
        questions.append(_question(
            "has_gstin",
            "Is the operating entity registered under GST?",
            "This is the gate for GST returns, e-invoicing, and several tax-linked obligations.",
            1,
            "universal",
        ))

    if entity_type in {"pvt_ltd", "public_ltd", "llp", "partnership", "opc"} and profile.get("deducts_tds") is None:
        questions.append(_question(
            "deducts_tds",
            "Does this company deduct TDS?",
            "This decides whether quarterly TDS return obligations should be created.",
            2,
            "universal",
        ))

    if profile.get("is_export_oriented") is None:
        questions.append(_question(
            "is_export_oriented",
            "Does the company export or sell cross-border?",
            "This changes DGFT-linked opportunities, export-support schemes, and some sector-specific approvals.",
            3,
            "universal",
        ))

    if profile.get("is_msme") is True and profile.get("has_b2b_receivables") is None:
        questions.append(_question(
            "has_b2b_receivables",
            "Does the business raise B2B invoices to companies, distributors, institutions, or government buyers?",
            "This decides whether receivables tools like TReDS and delayed-payment routes such as Samadhaan are genuinely relevant.",
            3,
            "universal",
        ))

    if profile.get("women_led") is None:
        questions.append(_question(
            "women_led",
            "Is the business women-led with majority ownership?",
            "This affects founder-route credit and support schemes.",
            4,
            "founder",
        ))

    if profile.get("has_scst_founder") is None:
        questions.append(_question(
            "has_scst_founder",
            "Is the business majority-owned or controlled by an SC/ST founder?",
            "This affects founder-route procurement and credit schemes.",
            5,
            "founder",
        ))

    if (
        (profile.get("women_led") is True or profile.get("has_scst_founder") is True)
        and profile.get("greenfield_for_promoter") is None
    ):
        questions.append(_question(
            "greenfield_for_promoter",
            "If using a founder-route scheme, would this be a genuinely greenfield business for that promoter?",
            "This is a critical clause for routes like Stand-Up India and should not be assumed.",
            6,
            "founder",
        ))

    if entity_type in {"pvt_ltd", "public_ltd", "opc"} and profile.get("is_listed") is None:
        questions.append(_question(
            "is_listed",
            "Is the company listed on a stock exchange or SME platform?",
            "This changes SEBI / LODR, BRSR, and governance obligations.",
            7,
            "universal",
        ))

    if entity_type in {"pvt_ltd", "public_ltd", "llp"} and profile.get("has_foreign_investment") is None and company_turnover_lakhs(profile) >= 40:
        questions.append(_question(
            "has_foreign_investment",
            "Has the company received foreign investment, overseas loans, or other FEMA-linked funding?",
            "This changes FEMA reporting, FLA return, and foreign-capital compliance.",
            8,
            "universal",
        ))

    if sector_pack == "food_agri":
        if profile.get("handles_food_products") is None:
            questions.append(_question(
                "handles_food_products",
                "Does the business manufacture, process, store, or sell regulated food products?",
                "This changes FSSAI, food-labelling, and scheme relevance for food or tea businesses.",
                9,
                "sector_food_agri",
            ))
        if profile.get("has_primary_processing") is None:
            questions.append(_question(
                "has_primary_processing",
                "Does the business do primary or integrated processing instead of only resale or standalone secondary processing?",
                "This materially changes agri-processing schemes such as AIF and some food-processing routes.",
                10,
                "sector_food_agri",
            ))
        if profile.get("has_warehouse") is None:
            questions.append(_question(
                "has_warehouse",
                "Does the business operate warehouses, storage sites, or post-harvest infrastructure?",
                "This changes storage-linked compliance and agri-infrastructure scheme relevance.",
                11,
                "sector_food_agri",
            ))
        if profile.get("has_cold_chain") is None:
            questions.append(_question(
                "has_cold_chain",
                "Does the business operate cold-chain or temperature-controlled infrastructure?",
                "This changes cold-chain-linked schemes and facility obligations.",
                12,
                "sector_food_agri",
            ))
        if profile.get("has_factory_operations") is None:
            questions.append(_question(
                "has_factory_operations",
                "Does the business operate a processing unit, plant, or industrial food facility?",
                "This affects plant, environmental, fire-safety, and facility-linked compliance.",
                13,
                "sector_food_agri",
            ))

    if sector_pack in {"manufacturing", "manufacturing_defence"}:
        if profile.get("has_factory_operations") is None:
            questions.append(_question(
                "has_factory_operations",
                "Does the company operate a factory, plant, workshop, or industrial site?",
                "This affects factory, plant, environmental, fire-safety, and premises-linked compliance.",
                9,
                "sector_manufacturing",
            ))
        if profile.get("generates_hazardous_waste") is None:
            questions.append(_question(
                "generates_hazardous_waste",
                "Do operations generate hazardous waste, emissions, effluents, solvents, or regulated scrap?",
                "This changes pollution-control and hazardous-waste obligations.",
                10,
                "sector_manufacturing",
            ))
        if profile.get("uses_contract_labour") is None:
            questions.append(_question(
                "uses_contract_labour",
                "Does the business rely on contract labour?",
                "This decides whether contract-labour registration, licensing, and register reviews should be flagged.",
                11,
                "sector_manufacturing",
            ))
        if profile.get("uses_interstate_migrant_workers") is None:
            questions.append(_question(
                "uses_interstate_migrant_workers",
                "Are inter-state migrant workers engaged?",
                "This changes labour-condition, allowance, and record-keeping obligations under migrant-worker rules.",
                12,
                "sector_manufacturing",
            ))
        if sector_pack == "manufacturing_defence" and profile.get("serves_defence_sector") is None:
            questions.append(_question(
                "serves_defence_sector",
                "Does the business manufacture or supply aerospace / defence systems, components, or controlled products?",
                "This changes industrial-licence, defence-industry support, and sector-specific opportunity mapping.",
                13,
                "sector_manufacturing",
            ))
        if (profile.get("serves_defence_sector") is True or sector_pack == "manufacturing_defence") and profile.get("controlled_items_exposure") is None:
            questions.append(_question(
                "controlled_items_exposure",
                "Are any of the products or assemblies potentially controlled, licensable, or security-sensitive?",
                "This tightens defence-manufacturing compliance and scheme relevance.",
                14,
                "sector_manufacturing",
            ))

    if sector_pack == "technology" and profile.get("has_rd_collaboration") is None:
        questions.append(_question(
            "has_rd_collaboration",
            "Is there a formal R&D or academic collaboration?",
            "This changes eligibility for R&D grant programs.",
            9,
            "sector_technology",
        ))
    if sector_pack in {"technology", "manufacturing", "healthcare"} and profile.get("has_patent_activity") is None:
        questions.append(_question(
            "has_patent_activity",
            "Is the business filing patents, prosecuting IP, or funding patentable product development?",
            "This is the real gate for patent-cost support routes; we should not show them just because the company is an MSME or startup.",
            10,
            "sector_technology" if sector_pack == "technology" else "sector_manufacturing" if sector_pack == "manufacturing" else "sector_healthcare",
        ))

    if sector_pack == "healthcare":
        if profile.get("has_healthcare_facility") is None:
            questions.append(_question(
                "has_healthcare_facility",
                "Does the business operate a clinic, hospital, medical facility, or healthcare site?",
                "This changes clinical-establishment, facility, and biomedical-waste compliance.",
                9,
                "sector_healthcare",
            ))
        if profile.get("has_diagnostic_lab") is None:
            questions.append(_question(
                "has_diagnostic_lab",
                "Does the business operate a diagnostic or pathology lab?",
                "This changes healthcare-facility and biomedical-waste obligations.",
                10,
                "sector_healthcare",
            ))
        if profile.get("generates_hazardous_waste") is None:
            questions.append(_question(
                "generates_hazardous_waste",
                "Do medical or lab operations generate biomedical or hazardous waste?",
                "This changes waste-authorisation and disposal obligations.",
                11,
                "sector_healthcare",
            ))

    if sector_pack == "finance" and profile.get("regulated_financial_entity") is None:
        questions.append(_question(
            "regulated_financial_entity",
            "Is the company actually carrying a regulated financial activity requiring RBI, SEBI, or IRDAI oversight?",
            "This separates true regulated-finance compliance from generic fintech software or enablement businesses.",
            9,
            "sector_finance",
        ))

    if sector_pack == "construction_real_estate":
        if profile.get("project_based_operations") is None:
            questions.append(_question(
                "project_based_operations",
                "Does the business run project-based construction or real-estate operations?",
                "This changes project-level compliance such as RERA and BOCW.",
                9,
                "sector_construction",
            ))
        if profile.get("uses_contract_labour") is None:
            questions.append(_question(
                "uses_contract_labour",
                "Does the business rely on contract labour?",
                "This changes contract-labour and site-worker obligations.",
                10,
                "sector_construction",
            ))
        if profile.get("uses_interstate_migrant_workers") is None:
            questions.append(_question(
                "uses_interstate_migrant_workers",
                "Are inter-state migrant workers engaged on projects or sites?",
                "This changes site-worker allowances and record-keeping obligations.",
                11,
                "sector_construction",
            ))

    if sector_pack == "logistics":
        if profile.get("has_warehouse") is None:
            questions.append(_question(
                "has_warehouse",
                "Does the business operate warehouses or storage infrastructure?",
                "This changes warehousing, site, and logistics-linked rule mapping.",
                9,
                "sector_logistics",
            ))
        if profile.get("has_cold_chain") is None:
            questions.append(_question(
                "has_cold_chain",
                "Is any cold-chain or temperature-controlled infrastructure involved?",
                "This changes food/logistics support schemes and some operating obligations.",
                10,
                "sector_logistics",
            ))
        if profile.get("uses_contract_labour") is None:
            questions.append(_question(
                "uses_contract_labour",
                "Does the business rely on contract labour?",
                "This changes labour licensing and register obligations.",
                11,
                "sector_logistics",
            ))

    questions.sort(key=lambda item: (item.get("priority", 99), item["label"]))
    return questions[:14]


def company_turnover_lakhs(company: dict[str, Any]) -> int:
    return TURNOVER_LAKHS_BY_RANGE.get(company.get("annual_turnover"), 0)


def company_employee_count(company: dict[str, Any]) -> int:
    return EMPLOYEE_COUNT_BY_RANGE.get(company.get("employee_count"), 0)


def company_turnover_bounds(company: dict[str, Any]) -> tuple[int, int]:
    return TURNOVER_RANGE_BOUNDS.get(company.get("annual_turnover"), (0, 0))


def company_employee_bounds(company: dict[str, Any]) -> tuple[int, int]:
    return EMPLOYEE_RANGE_BOUNDS.get(company.get("employee_count"), (0, 0))


def definitely_meets_minimum(bounds: tuple[int, int], threshold: int) -> bool:
    lower, _ = bounds
    return lower >= threshold


def definitely_meets_maximum(bounds: tuple[int, int], threshold: int) -> bool:
    _, upper = bounds
    return upper <= threshold


def company_age_years(company: dict[str, Any]) -> int | None:
    founded_year = company.get("founded_year")
    if founded_year in (None, "", 0):
        return None
    return datetime.now().year - int(founded_year)


def _start_of_day(value: datetime) -> datetime:
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def next_due_date(rule: dict[str, Any]) -> str:
    now = datetime.now()
    if rule["frequency"] == "monthly":
      due = datetime(now.year, now.month, rule["due_day"])
      if due < _start_of_day(now):
          if now.month == 12:
              due = datetime(now.year + 1, 1, rule["due_day"])
          else:
              due = datetime(now.year, now.month + 1, rule["due_day"])
      return due.date().isoformat()

    if rule["frequency"] == "quarterly":
        quarter_dates = [
            datetime(now.year, 4, rule["due_day"]),
            datetime(now.year, 7, rule["due_day"]),
            datetime(now.year, 10, rule["due_day"]),
            datetime(now.year + 1, 1, rule["due_day"]),
        ]
        due = next((item for item in quarter_dates if item >= _start_of_day(now)), quarter_dates[0])
        return due.date().isoformat()

    due = datetime(now.year, rule.get("due_month", 1), rule["due_day"])
    if due < _start_of_day(now):
        due = datetime(now.year + 1, rule.get("due_month", 1), rule["due_day"])
    return due.date().isoformat()


def optional_bool_value(value: Any) -> bool | None:
    if value in (None, "", "unknown", "null"):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    lowered = str(value).strip().lower()
    if lowered in {"true", "yes", "1", "on"}:
        return True
    if lowered in {"false", "no", "0", "off"}:
        return False
    return None


def validate_company_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = {}
    for field in REQUIRED_COMPANY_FIELDS:
        value = payload.get(field)
        if value in (None, ""):
            raise ValueError(f"Missing required field: {field}")
        normalized[field] = value

    normalized["name"] = str(normalized["name"]).strip()
    normalized["state"] = str(normalized["state"]).strip()
    normalized["city"] = str(normalized["city"]).strip()
    normalized["entity_type"] = str(normalized["entity_type"]).strip()
    normalized["sector"] = normalize_sector_key(normalized["sector"])
    normalized["annual_turnover"] = str(normalized["annual_turnover"]).strip()
    normalized["employee_count"] = str(normalized["employee_count"]).strip()
    normalized["founded_year"] = int(normalized["founded_year"])
    normalized["is_msme"] = bool(payload.get("is_msme", False))
    normalized["is_startup_india"] = bool(payload.get("is_startup_india", False))
    normalized["is_dpiit"] = bool(payload.get("is_dpiit", False))
    normalized["has_gstin"] = optional_bool_value(payload.get("has_gstin"))
    normalized["is_export_oriented"] = optional_bool_value(payload.get("is_export_oriented"))
    normalized["has_foreign_investment"] = optional_bool_value(payload.get("has_foreign_investment"))
    normalized["is_listed"] = optional_bool_value(payload.get("is_listed"))
    for field in OPTIONAL_IDENTIFIER_FIELDS:
        normalized[field] = str(payload.get(field, "") or "").strip()
    for field in OPTIONAL_PROFILE_FIELDS:
        normalized[field] = str(payload.get(field, "") or "").strip()
    normalized["deducts_tds"] = optional_bool_value(payload.get("deducts_tds"))
    normalized["has_factory_operations"] = optional_bool_value(payload.get("has_factory_operations"))
    normalized["handles_food_products"] = optional_bool_value(payload.get("handles_food_products"))
    normalized["has_rd_collaboration"] = optional_bool_value(payload.get("has_rd_collaboration"))
    normalized["has_new_hires"] = optional_bool_value(payload.get("has_new_hires"))
    normalized["women_led"] = optional_bool_value(payload.get("women_led"))
    normalized["has_scst_founder"] = optional_bool_value(payload.get("has_scst_founder"))
    normalized["uses_contract_labour"] = optional_bool_value(payload.get("uses_contract_labour"))
    normalized["uses_interstate_migrant_workers"] = optional_bool_value(payload.get("uses_interstate_migrant_workers"))
    normalized["serves_defence_sector"] = optional_bool_value(payload.get("serves_defence_sector"))
    normalized["controlled_items_exposure"] = optional_bool_value(payload.get("controlled_items_exposure"))
    normalized["generates_hazardous_waste"] = optional_bool_value(payload.get("generates_hazardous_waste"))
    normalized["has_warehouse"] = optional_bool_value(payload.get("has_warehouse"))
    normalized["has_cold_chain"] = optional_bool_value(payload.get("has_cold_chain"))
    normalized["has_primary_processing"] = optional_bool_value(payload.get("has_primary_processing"))
    normalized["has_b2b_receivables"] = optional_bool_value(payload.get("has_b2b_receivables"))
    normalized["has_patent_activity"] = optional_bool_value(payload.get("has_patent_activity"))
    normalized["regulated_financial_entity"] = optional_bool_value(payload.get("regulated_financial_entity"))
    normalized["has_healthcare_facility"] = optional_bool_value(payload.get("has_healthcare_facility"))
    normalized["has_diagnostic_lab"] = optional_bool_value(payload.get("has_diagnostic_lab"))
    normalized["project_based_operations"] = optional_bool_value(payload.get("project_based_operations"))
    normalized["greenfield_for_promoter"] = optional_bool_value(payload.get("greenfield_for_promoter"))

    current_year = datetime.now().year
    if normalized["founded_year"] < 1900 or normalized["founded_year"] > current_year:
        raise ValueError("Founded year is out of range")

    cin = normalized["cin"].upper()
    if cin and not re.fullmatch(r"[A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}", cin):
        raise ValueError("CIN format looks invalid")
    normalized["cin"] = cin

    llpin = normalized["llpin"].upper()
    if llpin and not re.fullmatch(r"[A-Z]{3}-\d{4}", llpin):
        raise ValueError("LLPIN format looks invalid")
    normalized["llpin"] = llpin

    gstin = normalized["gstin"].upper()
    if gstin and not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]", gstin):
        raise ValueError("GSTIN format looks invalid")
    normalized["gstin"] = gstin
    if normalized["gstin"]:
        normalized["has_gstin"] = True

    pan = normalized["pan"].upper()
    if pan and not re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", pan):
        raise ValueError("PAN format looks invalid")
    normalized["pan"] = pan

    if normalized["website_url"] and "://" not in normalized["website_url"]:
        normalized["website_url"] = f"https://{normalized['website_url']}"
    if normalized["website_url"] and not normalized["website_domain"]:
        domain_match = re.match(r"https?://(?:www\.)?([^/]+)", normalized["website_url"], re.IGNORECASE)
        if domain_match:
            normalized["website_domain"] = domain_match.group(1)
    normalized["website_domain"] = str(normalized["website_domain"]).strip().lower().removeprefix("www.")
    normalized["analysis_scope"] = normalized["analysis_scope"] or "current_entity"
    normalized["operating_activity"] = normalized["operating_activity"] or "same_as_detected"

    return enrich_company_runtime(normalized)


def normalize_company_name(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in name)
    return " ".join(cleaned.split())


def normalize_company_core(name: str) -> str:
    normalized = normalize_company_name(name)
    tokens = [token for token in normalized.split() if token not in LEGAL_SUFFIX_TOKENS]
    return " ".join(tokens) if tokens else normalized


def matches_directory_entry(candidate_name: str, entry: dict[str, Any]) -> bool:
    candidate = normalize_company_name(candidate_name)
    candidate_core = normalize_company_core(candidate_name)

    alias_names = [normalize_company_name(alias) for alias in entry["aliases"]]
    alias_cores = [normalize_company_core(alias) for alias in entry["aliases"]]

    if candidate in alias_names or candidate in alias_cores:
        return True
    if candidate_core and (candidate_core in alias_names or candidate_core in alias_cores):
        return True

    if candidate_core:
        candidate_tokens = candidate_core.split()
        for alias_core in alias_cores:
            if not alias_core:
                continue
            if candidate_core == alias_core:
                return True
            if candidate_core.startswith(alias_core + " ") or alias_core.startswith(candidate_core + " "):
                return True

            alias_tokens = alias_core.split()
            if candidate_tokens and alias_tokens:
                overlap = len(set(candidate_tokens) & set(alias_tokens))
                if overlap == min(len(candidate_tokens), len(alias_tokens)) and overlap >= 2:
                    return True

    return False


def infer_sector_from_name(name: str) -> str | None:
    normalized = normalize_company_name(name)
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return sector
    return None


def infer_sector_from_text(text: str) -> str | None:
    normalized = normalize_company_name(text)
    scores: dict[str, int] = {}
    for sector, keywords in SECTOR_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score:
            scores[sector] = score
    if not scores:
        return None
    return max(scores.items(), key=lambda item: item[1])[0]


def effective_company_sector(company: dict[str, Any]) -> str:
    operating_activity = company.get("operating_activity", "same_as_detected")
    sector = normalize_sector_key(company.get("sector", ""))

    if operating_activity != "same_as_detected":
        mapped_sector = OPERATING_ACTIVITY_TO_SECTOR.get(operating_activity)
        if mapped_sector == "manufacturing" and company.get("handles_food_products"):
            return "food_processing"
        if mapped_sector:
            return mapped_sector
    return sector


def _identity_text(company: dict[str, Any]) -> str:
    return normalize_company_name(
        " ".join(
            [
                str(company.get("name", "")),
                str(company.get("legal_name", "")),
                str(company.get("website_domain", "")),
                str(company.get("website_url", "")),
                str(company.get("sector", "")),
                str(company.get("operating_activity", "")),
            ]
        )
    )


def enrich_company_runtime(company: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(company)
    identity_text = _identity_text(enriched)
    resolved_sector = effective_company_sector(enriched)
    resolved_bucket = sector_bucket(resolved_sector)
    employee_count = company_employee_count(enriched)

    if resolved_bucket in {"manufacturing", "food_processing"} and sector_bucket(enriched.get("sector")) in {"technology", "other"}:
        enriched["sector"] = resolved_sector

    if not enriched.get("serves_defence_sector") and any(keyword in identity_text for keyword in DEFENCE_KEYWORDS):
        enriched["serves_defence_sector"] = True

    if not enriched.get("has_factory_operations"):
        factory_like = enriched.get("operating_activity") == "manufacturing_processing" and (
            any(keyword in identity_text for keyword in FACTORY_INDICATOR_KEYWORDS)
            or enriched.get("serves_defence_sector")
            or employee_count >= 200
        )
        if factory_like:
            enriched["has_factory_operations"] = True

    if enriched.get("handles_food_products") is None and (resolved_sector in FOOD_SECTORS or resolved_bucket == "food_processing"):
        enriched["handles_food_products"] = True

    if enriched.get("has_primary_processing") is None and (
        resolved_sector in {"food_processing", "food_manufacturing", "agriculture", "food_agri_processing"}
        or (resolved_bucket == "food_processing" and enriched.get("operating_activity") == "manufacturing_processing")
    ):
        enriched["has_primary_processing"] = True

    if enriched.get("has_warehouse") is None and resolved_sector in {"warehousing", "logistics", "logistics_transport"}:
        enriched["has_warehouse"] = True

    if enriched.get("has_patent_activity") is None and enriched.get("has_rd_collaboration") is True:
        enriched["has_patent_activity"] = True

    if enriched.get("regulated_financial_entity") is None and resolved_sector in {"nbfc", "banking", "insurance", "investment_advisory", "stockbroking"}:
        enriched["regulated_financial_entity"] = True

    if enriched.get("has_healthcare_facility") is None and resolved_sector in {"hospitals_clinics", "diagnostic_labs"}:
        enriched["has_healthcare_facility"] = True

    if enriched.get("has_diagnostic_lab") is None and resolved_sector == "diagnostic_labs":
        enriched["has_diagnostic_lab"] = True

    if enriched.get("project_based_operations") is None and resolved_bucket in {"construction", "real_estate"}:
        enriched["project_based_operations"] = True

    if enriched.get("generates_hazardous_waste") is None and resolved_sector in {"manufacturing_chemicals", "pharma_manufacturing"}:
        enriched["generates_hazardous_waste"] = True

    if enriched.get("has_gstin") is None and enriched.get("gstin"):
        enriched["has_gstin"] = True

    return enriched


def infer_entity_type_from_name(name: str) -> str | None:
    lowered = name.lower()
    if "llp" in lowered:
        return "llp"
    if "limited" in lowered or "ltd" in lowered:
        return "public_ltd" if "public" in lowered else "pvt_ltd"
    if "private" in lowered or "pvt" in lowered:
        return "pvt_ltd"
    if "partners" in lowered or "partnership" in lowered:
        return "partnership"
    return None


def apply_website_context(inferred: dict[str, Any], website_context: dict[str, Any] | None, notes: list[str]) -> None:
    if not website_context:
        return

    if website_context.get("brand_name") and not inferred.get("name"):
        inferred["name"] = website_context["brand_name"]
    if website_context.get("legal_name"):
        inferred["legal_name"] = website_context["legal_name"]
        if not inferred.get("entity_type"):
            entity_type = infer_entity_type_from_name(website_context["legal_name"])
            if entity_type:
                inferred["entity_type"] = entity_type
    if website_context.get("operator_name") and not inferred.get("operator_name"):
        inferred["operator_name"] = website_context["operator_name"]
    if website_context.get("website_url"):
        inferred["website_url"] = website_context["website_url"]
    if website_context.get("website_domain"):
        inferred["website_domain"] = website_context["website_domain"]
    for field, value in (website_context.get("identifier_candidates") or {}).items():
        if value and not inferred.get(field):
            inferred[field] = value

    search_text = website_context.get("search_text", "")
    title = website_context.get("title", "")
    meta_description = website_context.get("meta_description", "")
    combined_text = " ".join(part for part in [search_text, title, meta_description] if part)
    sector = infer_sector_from_text(combined_text)
    if sector and not inferred.get("sector"):
        inferred["sector"] = sector
        notes.append(f"Website signals suggest the business operates in {sector.replace('_', ' ')}.")

    if website_context.get("operating_activity_hint") and not inferred.get("operating_activity"):
        inferred["operating_activity"] = website_context["operating_activity_hint"]

    if website_context.get("defence_signal"):
        inferred["serves_defence_sector"] = True
        notes.append("The website signals aerospace or defence relevance, so sector-specific industrial routes are switched on.")

    if website_context.get("factory_signal") and inferred.get("has_factory_operations") is None:
        inferred["has_factory_operations"] = True
        notes.append("The website mentions plant or manufacturing facility signals, so factory-level compliance reviews are switched on.")

    if website_context.get("warehouse_signal") and inferred.get("has_warehouse") is None:
        inferred["has_warehouse"] = True
        notes.append("The website mentions warehouse or storage infrastructure signals.")

    if website_context.get("cold_chain_signal") and inferred.get("has_cold_chain") is None:
        inferred["has_cold_chain"] = True
        notes.append("The website mentions cold-chain or temperature-controlled infrastructure.")

    if website_context.get("healthcare_facility_signal") and inferred.get("has_healthcare_facility") is None:
        inferred["has_healthcare_facility"] = True
        notes.append("The website suggests a real healthcare facility, not just a generic health business.")

    if website_context.get("diagnostic_lab_signal") and inferred.get("has_diagnostic_lab") is None:
        inferred["has_diagnostic_lab"] = True
        notes.append("The website suggests diagnostic or pathology lab operations.")

    if website_context.get("regulated_finance_signal") and inferred.get("regulated_financial_entity") is None:
        inferred["regulated_financial_entity"] = True
        notes.append("The website suggests a regulated financial-activity route rather than generic fintech software only.")

    if website_context.get("primary_processing_signal") and inferred.get("has_primary_processing") is None:
        inferred["has_primary_processing"] = True
        notes.append("The website suggests primary or post-harvest processing rather than pure resale.")

    if website_context.get("b2b_receivables_signal") and inferred.get("has_b2b_receivables") is None:
        inferred["has_b2b_receivables"] = True
        notes.append("The website suggests wholesale, enterprise, or distributor-led invoicing rather than purely consumer sales.")

    if website_context.get("patent_signal") and inferred.get("has_patent_activity") is None:
        inferred["has_patent_activity"] = True
        notes.append("The website suggests patent or IP-led product development, which is relevant for patent-support routes.")

    inferred_sector_bucket = sector_bucket(inferred.get("sector", "other"))
    if inferred.get("operating_activity") == "manufacturing_processing" and inferred_sector_bucket in {"technology", "other"}:
        inferred["sector"] = "manufacturing"
        notes.append("The website suggests a manufacturing-led operating model, so the compliance and scheme engine is treating this as industrial/manufacturing activity.")

    if (
        website_context.get("brand_name")
        and website_context.get("legal_name")
        and normalize_company_core(website_context["brand_name"]) != normalize_company_core(website_context["legal_name"])
        and not inferred.get("analysis_scope")
    ):
        inferred["analysis_scope"] = "brand_unit"
        notes.append("The public site looks like a customer-facing brand that sits on top of a separate legal entity.")

    if sector_bucket(inferred.get("sector", "")) == "food_processing" and any(
        phrase in normalize_company_name(combined_text)
        for phrase in ["tea", "coffee", "herbal", "beverage", "online tea store", "food"]
    ):
        inferred["handles_food_products"] = True
        notes.append("The website indicates food or beverage products, so FSSAI-linked logic is switched on.")

    if any(phrase in normalize_company_name(combined_text) for phrase in ["export", "international shipping", "worldwide shipping", "global shipping"]):
        inferred["is_export_oriented"] = True
        notes.append("The website mentions export or international shipping signals.")

    if any(phrase in normalize_company_name(combined_text) for phrase in ["tea estate", "tea estates", "plantation", "planter", "estate", "upper assam"]):
        inferred["group_sector_hint"] = "agriculture"
        notes.append("The website also suggests plantation or agricultural group operations in the parent entity.")

    if (website_context.get("identifier_candidates") or {}) and not any(
        "official identifiers were found" in note.lower() for note in notes
    ):
        notes.append("Some official identifiers were detected on public pages and have been prefilled for confirmation.")

    pages_fetched = website_context.get("pages_fetched") or []
    if pages_fetched:
        notes.append(f"Website discovery checked {len(pages_fetched)} public page(s) from {website_context.get('website_domain', 'the company domain')}.")


def discover_company_profile(name: str, website_context: dict[str, Any] | None = None) -> dict[str, Any]:
    website_brand = website_context.get("brand_name", "") if website_context else ""
    website_legal = website_context.get("legal_name", "") if website_context else ""
    query_value = name or website_brand or website_legal
    candidate = normalize_company_name(query_value)
    if not candidate:
        raise ValueError("Company name or website is required for discovery")

    for entry in COMPANY_DIRECTORY:
        candidate_names = [value for value in [name, website_brand, website_legal] if value]
        if any(matches_directory_entry(candidate_name, entry) for candidate_name in candidate_names):
            inferred = deepcopy(entry["profile"])
            notes = list(entry["notes"])
            apply_website_context(inferred, website_context, notes)
            inferred = enrich_company_runtime(inferred)
            missing_fields = [
                field
                for field in ["is_msme", "is_startup_india", "is_dpiit", "is_export_oriented"]
                if inferred.get(field) is None
            ]
            if candidate != normalize_company_name(inferred["name"]):
                notes.append("Matched against the local company intelligence directory after normalizing legal suffixes or close name variants.")
            if website_context and website_context.get("legal_name"):
                notes.append(f"Website indicates the legal entity may be {website_context['legal_name']}.")
            return {
                "query": query_value,
                "match_type": "directory",
                "confidence": entry["confidence"],
                "inferred": inferred,
                "notes": notes,
                "missing_fields": missing_fields,
                "follow_up_questions": follow_up_questions_for_profile(inferred),
            }

    sector = infer_sector_from_name(query_value)
    entity_type = infer_entity_type_from_name(query_value)
    inferred = {
        "name": website_brand or " ".join(part.capitalize() for part in candidate.split()),
    }
    if sector:
        inferred["sector"] = sector
    if entity_type:
        inferred["entity_type"] = entity_type

    notes = [
        "No exact company match found in the local intelligence directory.",
        "The platform inferred what it could from the company name and now needs follow-up inputs.",
    ]
    apply_website_context(inferred, website_context, notes)
    inferred = enrich_company_runtime(inferred)

    tracked_fields = [
        "entity_type",
        "sector",
        "state",
        "city",
        "annual_turnover",
        "employee_count",
        "founded_year",
        "is_msme",
        "is_startup_india",
        "is_dpiit",
        "is_export_oriented",
    ]
    missing_fields = [field for field in tracked_fields if field not in inferred]
    if inferred.get("legal_name"):
        notes.append(f"The company website points to the legal entity {inferred['legal_name']}.")
    elif inferred.get("operator_name"):
        notes.append(f"The company website points to the operating or parent brand {inferred['operator_name']}.")
    detected_sector = inferred.get("sector")
    detected_entity_type = inferred.get("entity_type")
    if detected_sector:
        notes.append(f"Likely sector detected: {detected_sector.replace('_', ' ')}.")
    if detected_entity_type:
        notes.append(f"Likely entity type detected: {detected_entity_type.replace('_', ' ')}.")

    match_type = "website" if website_context else "heuristic"
    if website_context and website_context.get("source") == "guessed_website":
        notes.append("The website was inferred from the company name and should be verified if it looks wrong.")

    return {
        "query": query_value,
        "match_type": match_type,
        "confidence": "low" if not inferred.get("sector") and not inferred.get("entity_type") else ("high" if website_context and inferred.get("legal_name") else "medium"),
        "inferred": inferred,
        "notes": notes,
        "missing_fields": missing_fields,
        "follow_up_questions": follow_up_questions_for_profile(inferred),
    }


def obligation_matches_company(company: dict[str, Any], rule: dict[str, Any]) -> bool:
    triggers = company_trigger_profile(company)
    turnover_bounds = company_turnover_bounds(company)
    employee_bounds = company_employee_bounds(company)
    company_sector = triggers["sector_key"]
    company_sector_bucket = triggers["sector_bucket"]
    company_activity = str(company.get("operating_activity", "")).strip()
    factory_like = bool(triggers["has_factory_operations"]) or company_activity == "manufacturing_processing"
    if rule.get("entity_types") and company["entity_type"] not in rule["entity_types"]:
        return False
    allowed_sector_keys = {normalize_sector_key(value) for value in rule.get("sectors", [])}
    allowed_sector_groups = {sector_bucket(value) for value in rule.get("sector_groups", [])}
    if allowed_sector_keys and company_sector not in allowed_sector_keys and company_sector_bucket not in allowed_sector_keys:
        return False
    if allowed_sector_groups and company_sector_bucket not in allowed_sector_groups:
        return False
    if rule.get("states") and company["state"] not in rule["states"]:
        return False
    if rule.get("min_turnover_lakhs") and not definitely_meets_minimum(turnover_bounds, rule["min_turnover_lakhs"]):
        return False
    if rule.get("max_turnover_lakhs") and not definitely_meets_maximum(turnover_bounds, rule["max_turnover_lakhs"]):
        return False
    if rule.get("min_employees") and not definitely_meets_minimum(employee_bounds, rule["min_employees"]):
        return False
    if rule.get("max_employees") and not definitely_meets_maximum(employee_bounds, rule["max_employees"]):
        return False
    if rule.get("requires_gstin") and triggers["has_gstin"] is not True:
        return False
    if rule.get("requires_listed") and triggers["is_listed"] is not True:
        return False
    if rule.get("requires_foreign_investment") and triggers["has_foreign_investment"] is not True:
        return False
    if rule.get("pollution_categories") and triggers["pollution_category"] not in rule["pollution_categories"]:
        return False
    for flag in rule.get("requires_flags", []):
        if not company.get(flag, False):
            return False
    for flag in rule.get("exclude_flags", []):
        if company.get(flag, False):
            return False
    if rule.get("exclude_factory_like") and factory_like:
        return False
    if rule.get("requires_factory_like") and not factory_like:
        return False
    if rule["template_id"].startswith("tds-") and triggers["requires_tds"] is not True:
        return False
    if rule["template_id"].startswith("fssai-") and triggers["handles_food_products"] is not True:
        return False
    return True


def build_obligations(company: dict[str, Any]) -> list[dict[str, Any]]:
    company = enrich_company_runtime(dict(company))
    obligations = []
    for rule in OBLIGATIONS_CATALOG:
        if not obligation_matches_company(company, rule):
            continue
        due_date = next_due_date(rule)
        obligations.append(
            {
                "template_id": rule["template_id"],
                "name": rule["name"],
                "category": rule["category"],
                "description": rule["description"],
                "penalty_per_day": rule.get("penalty_per_day", 0),
                "due_date": due_date,
                "status": "overdue" if days_until(due_date) < 0 else "pending",
                "filed_date": None,
            }
        )
    obligations.sort(key=lambda item: item["due_date"])
    return obligations


def evaluate_scheme(company: dict[str, Any], scheme: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    blockers: list[str] = []
    soft_checks: list[str] = []
    triggers = company_trigger_profile(company)
    turnover_bounds = company_turnover_bounds(company)
    employee_bounds = company_employee_bounds(company)
    company_sector = triggers["sector_key"]
    company_sector_bucket = triggers["sector_bucket"]
    group_sector_hint = company.get("group_sector_hint", "")
    group_sector_match = False

    if scheme.get("entity_types") and company["entity_type"] not in scheme["entity_types"]:
        blockers.append("Entity type does not match.")
    elif scheme.get("entity_types"):
        reasons.append(f"Entity type matches {company['entity_type'].replace('_', ' ')}.")

    allowed_sector_keys = {normalize_sector_key(value) for value in scheme.get("sectors", [])}
    allowed_sector_groups = {sector_bucket(value) for value in scheme.get("sector_groups", [])}
    sector_match = True
    if allowed_sector_keys and company_sector not in allowed_sector_keys and company_sector_bucket not in allowed_sector_keys:
        sector_match = False
    if allowed_sector_groups and company_sector_bucket not in allowed_sector_groups:
        sector_match = False

    if (allowed_sector_keys or allowed_sector_groups) and not sector_match:
        group_sector_bucket = sector_bucket(group_sector_hint)
        if group_sector_hint and (group_sector_hint in allowed_sector_keys or group_sector_bucket in allowed_sector_groups or group_sector_bucket in allowed_sector_keys):
            group_sector_match = True
            reasons.append(f"Parent or group operations also suggest {group_sector_hint.replace('_', ' ')} relevance.")
        else:
            blockers.append("Sector is outside this scheme focus.")
    elif allowed_sector_keys or allowed_sector_groups:
        reasons.append(f"Sector match: {company_sector_bucket.replace('_', ' ')}.")

    if scheme.get("states") and company["state"] not in scheme["states"]:
        blockers.append("State is not covered.")
    elif scheme.get("states"):
        reasons.append(f"State match: {company['state']}.")

    if scheme.get("min_turnover_lakhs") and not definitely_meets_minimum(turnover_bounds, scheme["min_turnover_lakhs"]):
        blockers.append("Turnover is below the minimum threshold.")
    elif scheme.get("min_turnover_lakhs"):
        reasons.append("Turnover clears the minimum threshold.")

    if scheme.get("max_turnover_lakhs") and not definitely_meets_maximum(turnover_bounds, scheme["max_turnover_lakhs"]):
        blockers.append("Turnover exceeds the scheme ceiling.")
    elif scheme.get("max_turnover_lakhs"):
        reasons.append("Turnover fits the scheme ceiling.")

    if scheme.get("min_employees") and not definitely_meets_minimum(employee_bounds, scheme["min_employees"]):
        blockers.append("Employee count is below the minimum threshold.")
    elif scheme.get("min_employees"):
        reasons.append("Employee count clears the minimum threshold.")

    if scheme.get("max_employees") and not definitely_meets_maximum(employee_bounds, scheme["max_employees"]):
        blockers.append("Employee count exceeds the scheme ceiling.")
    elif scheme.get("max_employees"):
        reasons.append("Employee count fits the scheme ceiling.")

    if scheme.get("max_company_age_years") is not None:
        if triggers["company_age_years"] is None:
            soft_checks.append("Company age still needs confirmation.")
        elif triggers["company_age_years"] > scheme["max_company_age_years"]:
            blockers.append("Company age exceeds the limit.")
        else:
            reasons.append(f"Company age is within {scheme['max_company_age_years']} years.")

    if scheme.get("requires_msme"):
        if triggers["is_msme"] is True:
            reasons.append("MSME registration present.")
        elif triggers["is_msme"] is None:
            soft_checks.append("MSME registration status needs confirmation.")
        else:
            blockers.append("MSME registration required.")
    if scheme.get("requires_startup_india"):
        if triggers["is_startup_india"] is True:
            reasons.append("Startup India recognition present.")
        elif triggers["is_startup_india"] is None:
            soft_checks.append("Startup India recognition status needs confirmation.")
        else:
            blockers.append("Startup India recognition required.")
    if scheme.get("requires_dpiit"):
        if triggers["is_dpiit"] is True:
            reasons.append("DPIIT recognition present.")
        elif triggers["is_dpiit"] is None:
            if scheme.get("requires_dpiit_confirmed"):
                blockers.append("DPIIT recognition required.")
            else:
                soft_checks.append("DPIIT recognition status needs confirmation.")
        else:
            blockers.append("DPIIT recognition required.")
    if scheme.get("requires_export"):
        if triggers["is_export_oriented"] is True:
            reasons.append("Export orientation confirmed.")
        elif triggers["is_export_oriented"] is None:
            soft_checks.append("Export activity still needs confirmation.")
        else:
            blockers.append("Export activity required.")

    if scheme.get("requires_foreign_investment"):
        if triggers["has_foreign_investment"] is True:
            reasons.append("Foreign investment or FEMA-linked funding is confirmed.")
        elif triggers["has_foreign_investment"] is None:
            soft_checks.append("Foreign investment or FEMA-linked funding status needs confirmation.")
        else:
            blockers.append("Foreign investment or FEMA-linked funding required.")

    if scheme.get("requires_listed"):
        if triggers["is_listed"] is True:
            reasons.append("Listed-company status is confirmed.")
        elif triggers["is_listed"] is None:
            soft_checks.append("Listed-company status needs confirmation.")
        else:
            blockers.append("Listed-company status required.")

    if scheme.get("requires_one_of"):
        if any(company.get(key, False) is True for key in scheme["requires_one_of"]):
            reasons.append("At least one startup/MSME credential is present.")
        elif any(company.get(key) is None for key in scheme["requires_one_of"]):
            soft_checks.append("A qualifying startup/MSME credential still needs confirmation.")
        else:
            blockers.append("Needs one qualifying startup/MSME credential.")

    if scheme.get("requires_any_flags"):
        any_path = False
        for flag in scheme["requires_any_flags"]:
            if company.get(flag["field"], False):
                reasons.append(flag["positive"])
                any_path = True
        if not any_path:
            message = (
                scheme.get("requires_any_flags_prompt")
                or "Confirm at least one of the scheme-specific qualifying paths before treating this as ready."
            )
            if scheme.get("requires_any_flags_strict"):
                blockers.append(message)
            else:
                soft_checks.append(message)

    for flag in scheme.get("requires_flags", []):
        if company.get(flag["field"], False) is True:
            reasons.append(flag["positive"])
        elif company.get(flag["field"]) is None:
            if flag.get("strict"):
                blockers.append(flag["negative"])
            else:
                soft_checks.append(flag["negative"].replace(" required.", " needs confirmation."))
        else:
            blockers.append(flag["negative"])

    for identifier in scheme.get("requires_identifiers", []):
        if company.get(identifier["field"]):
            reasons.append(identifier["positive"])
        else:
            soft_checks.append(identifier["negative"])

    for flag in scheme.get("exclude_flags", []):
        if company.get(flag["field"], False):
            blockers.append(flag["negative"])

    for field in scheme.get("strict_requires_flags", []):
        if company.get(field) is True:
            reasons.append(f"{title_case_flag(field)} is confirmed.")
        else:
            blockers.append(f"{title_case_flag(field)} is required.")

    if blockers:
        status = "ineligible"
    elif soft_checks or scheme.get("uncertainty") or group_sector_match:
        status = "maybe"
    else:
        status = "eligible"

    uncertainty_parts = [scheme.get("uncertainty", "").strip()]
    if group_sector_match:
        uncertainty_parts.append("This looks more naturally aligned to the parent or group operations, so confirm which entity should apply before treating it as a direct brand-level opportunity.")
    uncertainty = " ".join(part for part in uncertainty_parts if part).strip()
    display = scheme_display_metadata(scheme["template_id"])
    review_clauses = scheme_review_clauses(scheme)
    review_questions = scheme_review_questions(scheme)

    return {
        "template_id": scheme["template_id"],
        "name": scheme["name"],
        "ministry": scheme["ministry"],
        "scheme_type": scheme["scheme_type"],
        "benefit_value": scheme["benefit_value"],
        "max_benefit_amount": display["max_benefit_amount"],
        "value_kind": display["value_kind"],
        "value_label": display["value_label"],
        "source_url": display["source_url"],
        "status": status,
        "reasons": reasons,
        "hard_blockers": blockers,
        "soft_checks": soft_checks,
        "blockers": blockers + soft_checks,
        "uncertainty": uncertainty,
        "review_clauses": review_clauses,
        "review_questions": review_questions,
        "applied_date": None,
        "benefit_received_amount": 0,
    }


def build_schemes(company: dict[str, Any]) -> list[dict[str, Any]]:
    company = enrich_company_runtime(dict(company))
    schemes = []
    for scheme in SCHEMES_CATALOG:
        if scheme["template_id"] in INACTIVE_SCHEME_TEMPLATE_IDS:
            continue
        evaluated = evaluate_scheme(company, scheme)
        if evaluated["status"] == "ineligible":
            continue
        schemes.append(evaluated)
    schemes.sort(key=lambda item: item["max_benefit_amount"], reverse=True)
    return schemes


def scheme_unlock_actions(company: dict[str, Any], scheme: dict[str, Any], evaluated: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    triggers = company_trigger_profile(company)
    current_age = company_age_years(company)

    if scheme.get("requires_msme") and not company.get("is_msme"):
        actions.append("Check whether the assessed entity genuinely qualifies for Udyam/MSME registration; that can unlock MSME-linked credit and subsidy programs.")

    if scheme.get("requires_dpiit") and not company.get("is_dpiit"):
        if company.get("analysis_scope") != "new_entity_scenario" and (
            (current_age is not None and current_age > (scheme.get("max_company_age_years") or 999))
            or (
                scheme.get("max_turnover_lakhs") is not None
                and company_turnover_lakhs(company) > scheme["max_turnover_lakhs"]
            )
        ):
            actions.append("If this opportunity matters, model a genuine new-entity scenario; many DPIIT-linked benefits fit a younger startup vehicle rather than the parent entity.")
        else:
            actions.append("If the entity genuinely qualifies, complete Startup India / DPIIT recognition before treating this as available.")

    if scheme.get("requires_startup_india") and not company.get("is_startup_india"):
        actions.append("Only treat this as unlockable if the entity can genuinely obtain Startup India recognition.")

    if scheme.get("requires_export") and not company.get("is_export_oriented"):
        actions.append("If the business will export, obtain IEC and route the export line through the entity being evaluated.")

    for flag in scheme.get("requires_flags", []):
        if company.get(flag["field"], False):
            continue
        if flag["field"] == "has_rd_collaboration":
            actions.append("Formalize the R&D or academic collaboration before treating this as eligible.")
        elif flag["field"] == "has_new_hires":
            actions.append("This becomes relevant once qualifying new hires are actually on payroll.")
        elif flag["field"] == "serves_defence_sector":
            actions.append("Treat this as relevant only if the entity genuinely manufactures or supplies defence or aerospace systems, components, or controlled products.")
        elif flag["field"] == "greenfield_for_promoter":
            actions.append("Only treat this as available if the promoter route is genuinely greenfield for that borrower, not an expansion or repeat venture in the same line.")
        elif flag["field"] == "regulated_financial_entity":
            actions.append("Only switch on regulated-finance compliance and scheme logic if the entity itself carries a licensed or regulated financial activity.")

    for field in scheme.get("strict_requires_flags", []):
        if company.get(field):
            continue
        if field == "serves_defence_sector":
            actions.append("Treat this as relevant only if the entity genuinely manufactures or supplies defence or aerospace systems, components, or controlled products.")

    if scheme.get("requires_any_flags") and not any(company.get(flag["field"], False) for flag in scheme["requires_any_flags"]):
        actions.append(
            scheme.get("requires_any_flags_prompt")
            or "Confirm whether the applicant actually qualifies through at least one of the scheme-specific routes before treating this as available."
        )

    for identifier in scheme.get("requires_identifiers", []):
        if company.get(identifier["field"]):
            continue
        if identifier["field"] == "iec_number":
            actions.append("Get or confirm the IEC before treating export-linked schemes as ready for this entity.")
        elif identifier["field"] == "dpiit_certificate_number":
            actions.append("Confirm the DPIIT certificate number before treating startup tax or grant routes as application-ready.")

    if scheme.get("states") and company.get("state") not in scheme["states"]:
        actions.append(f"This is state-specific. It becomes relevant only if the applying entity is based or operating in {', '.join(scheme['states'])}.")

    group_sector_hint = company.get("group_sector_hint", "")
    allowed_sector_keys = {normalize_sector_key(value) for value in scheme.get("sectors", [])}
    allowed_sector_groups = {sector_bucket(value) for value in scheme.get("sector_groups", [])}
    company_sector = triggers["sector_key"]
    company_sector_bucket = triggers["sector_bucket"]
    if (
        (allowed_sector_keys and company_sector not in allowed_sector_keys and company_sector_bucket not in allowed_sector_keys)
        or (allowed_sector_groups and company_sector_bucket not in allowed_sector_groups)
    ):
        group_sector_bucket = sector_bucket(group_sector_hint)
        if group_sector_hint and (group_sector_hint in allowed_sector_keys or group_sector_bucket in allowed_sector_groups or group_sector_bucket in allowed_sector_keys):
            actions.append("Assess the parent or legal entity separately; this looks closer to the group's operating activity than to the current brand-unit scope.")
        elif company.get("analysis_scope") != "new_entity_scenario":
            actions.append("If this scheme matters strategically, compare it against a separate-entity scenario aligned to the required business line.")

    if scheme.get("max_company_age_years") is not None and current_age is not None and current_age > scheme["max_company_age_years"]:
        actions.append("This usually fits a younger entity. Only compare it against a real newco or spinout scenario if that structure is genuinely being considered.")

    if scheme.get("max_turnover_lakhs") is not None and company_turnover_lakhs(company) > scheme["max_turnover_lakhs"]:
        actions.append("This generally fits a smaller entity. Compare against a different entity or unit only if the business structure would actually support that.")

    deduped: list[str] = []
    seen: set[str] = set()
    for action in actions:
        if action in seen:
            continue
        seen.add(action)
        deduped.append(action)
    return deduped


def should_surface_unlockable_scheme(company: dict[str, Any], scheme: dict[str, Any], evaluated: dict[str, Any]) -> bool:
    blockers = set(evaluated.get("blockers", []))
    if not blockers:
        return False

    analysis_scope = company.get("analysis_scope", "current_entity")
    structural_blockers = {
        blocker
        for blocker in blockers
        if blocker
        in {
            "Entity type does not match.",
            "Sector is outside this scheme focus.",
            "State is not covered.",
            "Turnover is below the minimum threshold.",
            "Turnover exceeds the scheme ceiling.",
            "Company age exceeds the limit.",
        }
    }

    if analysis_scope != "new_entity_scenario":
        if "State is not covered." in structural_blockers:
            return False
        if "Entity type does not match." in structural_blockers:
            return False
        if "Sector is outside this scheme focus." in structural_blockers:
            group_sector_hint = company.get("group_sector_hint", "")
            scheme_sectors = {normalize_sector_key(item) for item in scheme.get("sectors", [])}
            scheme_sector_groups = {sector_bucket(item) for item in scheme.get("sector_groups", [])}
            group_sector_bucket = sector_bucket(group_sector_hint)
            if not group_sector_hint or (
                group_sector_hint not in scheme_sectors
                and group_sector_bucket not in scheme_sectors
                and group_sector_bucket not in scheme_sector_groups
            ):
                return False
        if "Company age exceeds the limit." in structural_blockers and (
            scheme.get("requires_dpiit") or scheme.get("requires_startup_india")
        ):
            return False
        if len(structural_blockers) > 1:
            return False

    if scheme.get("requires_startup_india") and analysis_scope != "new_entity_scenario":
        return False
    if scheme.get("requires_dpiit") and analysis_scope != "new_entity_scenario":
        return False

    if (
        scheme.get("requires_flags")
        and any(flag.get("field") == "has_rd_collaboration" for flag in scheme.get("requires_flags", []))
        and "Sector is outside this scheme focus." in blockers
    ):
        return False

    return True


def build_scheme_opportunities(company: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    company = enrich_company_runtime(dict(company))
    opportunities = []
    for scheme in SCHEMES_CATALOG:
        if scheme["template_id"] in INACTIVE_SCHEME_TEMPLATE_IDS:
            continue
        evaluated = evaluate_scheme(company, scheme)
        if evaluated["status"] != "ineligible":
            continue
        unlock_actions = scheme_unlock_actions(company, scheme, evaluated)
        if not unlock_actions:
            continue
        if not should_surface_unlockable_scheme(company, scheme, evaluated):
            continue
        opportunities.append(
            {
                "template_id": scheme["template_id"],
                "name": scheme["name"],
                "ministry": scheme["ministry"],
                "scheme_type": scheme["scheme_type"],
                "benefit_value": evaluated["benefit_value"],
                "max_benefit_amount": evaluated["max_benefit_amount"],
                "value_kind": evaluated["value_kind"],
                "value_label": evaluated["value_label"],
                "source_url": evaluated["source_url"],
                "status": "unlockable",
                "reasons": evaluated["reasons"],
                "blockers": evaluated["blockers"],
                "unlock_actions": unlock_actions,
                "uncertainty": evaluated["uncertainty"],
                "review_clauses": evaluated["review_clauses"],
                "review_questions": evaluated["review_questions"],
            }
        )

    opportunities.sort(
        key=lambda item: (
            len(item["unlock_actions"]),
            -item["max_benefit_amount"],
            item["name"],
        )
    )
    return opportunities[:limit]


def days_until(date_string: str) -> int:
    target = _start_of_day(datetime.fromisoformat(date_string))
    today = _start_of_day(datetime.now())
    return (target - today).days


def sync_obligation_statuses(obligations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    synced = []
    for item in obligations:
        next_item = deepcopy(item)
        if next_item["status"] != "filed":
            next_item["status"] = "overdue" if days_until(next_item["due_date"]) < 0 else "pending"
        synced.append(next_item)
    return synced


def compute_metrics(company: dict[str, Any], obligations: list[dict[str, Any]], schemes: list[dict[str, Any]]) -> dict[str, Any]:
    current_obligations = sync_obligation_statuses(obligations)
    overdue = [item for item in current_obligations if item["status"] == "overdue"]
    pending = [item for item in current_obligations if item["status"] == "pending"]
    filed = [item for item in current_obligations if item["status"] == "filed"]
    upcoming = [item for item in pending if days_until(item["due_date"]) <= 7]
    open_schemes = [item for item in schemes if item["status"] in {"eligible", "maybe"}]
    applied_schemes = [item for item in schemes if item["status"] == "applied"]
    received_schemes = [item for item in schemes if item["status"] == "received"]

    risk_score = 100 - (len(overdue) * 15) - (len(upcoming) * 5)
    risk_score = max(risk_score, 0)
    burn_rate = sum(item.get("penalty_per_day", 0) for item in overdue)
    annual_burn_estimate = burn_rate * 365
    potential = sum(item.get("max_benefit_amount", 0) for item in open_schemes)
    applied_value = sum(item.get("max_benefit_amount", 0) for item in applied_schemes)
    received_value = sum(item.get("benefit_received_amount", 0) for item in received_schemes)

    return {
        "risk_score": risk_score,
        "burn_rate": burn_rate,
        "annual_burn_estimate": annual_burn_estimate,
        "overdue_count": len(overdue),
        "pending_count": len(pending),
        "filed_count": len(filed),
        "upcoming_count": len(upcoming),
        "open_scheme_count": len(open_schemes),
        "applied_scheme_count": len(applied_schemes),
        "applied_value": applied_value,
        "received_value": received_value,
        "potential": potential,
        "total_value_at_stake": annual_burn_estimate + potential,
    }
