import unittest

from company_discovery import contains_defence_signal
from engine import build_obligations, build_schemes, evaluate_scheme_review, scheme_template


def obligation_ids(company):
    return {item["template_id"] for item in build_obligations(company)}


def scheme_status(company):
    return {item["template_id"]: item["status"] for item in build_schemes(company)}


class EngineArchetypeTests(unittest.TestCase):
    def test_solo_tech_freelancer_is_not_over_flagged(self):
        company = {
            "name": "Solo Dev Studio",
            "state": "Karnataka",
            "city": "Bengaluru",
            "entity_type": "proprietorship",
            "sector": "technology_saas",
            "annual_turnover": "under_40L",
            "employee_count": "1_10",
            "founded_year": 2024,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "has_gstin": False,
            "is_export_oriented": False,
        }
        obligations = obligation_ids(company)
        self.assertIn("dpdp-review", obligations)
        self.assertNotIn("pf-monthly", obligations)
        self.assertNotIn("esi-monthly", obligations)
        self.assertNotIn("posh-report", obligations)

    def test_food_startup_gets_food_and_labour_mapping(self):
        company = {
            "name": "FreshLeaf Foods",
            "state": "Maharashtra",
            "city": "Pune",
            "entity_type": "pvt_ltd",
            "sector": "food_processing",
            "annual_turnover": "1Cr_10Cr",
            "employee_count": "11_50",
            "founded_year": 2022,
            "is_msme": True,
            "is_startup_india": True,
            "is_dpiit": True,
            "has_gstin": True,
            "gstin": "27ABCDE1234F1Z5",
            "is_export_oriented": False,
            "handles_food_products": True,
            "deducts_tds": True,
        }
        obligations = obligation_ids(company)
        self.assertIn("fssai-renewal", obligations)
        self.assertIn("fssai-annual-return", obligations)
        self.assertIn("esi-monthly", obligations)
        self.assertNotIn("pf-monthly", obligations)

    def test_manufacturing_company_gets_factory_and_environment(self):
        company = {
            "name": "OrangeFab Industries",
            "state": "Gujarat",
            "city": "Ahmedabad",
            "entity_type": "pvt_ltd",
            "sector": "manufacturing_chemicals",
            "annual_turnover": "10Cr_100Cr",
            "employee_count": "51_200",
            "founded_year": 2018,
            "is_msme": True,
            "is_startup_india": False,
            "is_dpiit": False,
            "has_gstin": True,
            "gstin": "24ABCDE1234F1Z5",
            "is_export_oriented": True,
            "has_factory_operations": True,
            "uses_contract_labour": True,
        }
        obligations = obligation_ids(company)
        self.assertIn("factory-license-review", obligations)
        self.assertIn("environment-clearance", obligations)
        self.assertIn("contract-labour-review", obligations)

    def test_nbfc_with_fdi_gets_finance_and_fema_reviews(self):
        company = {
            "name": "Metro Capital NBFC",
            "state": "Maharashtra",
            "city": "Mumbai",
            "entity_type": "pvt_ltd",
            "sector": "nbfc",
            "annual_turnover": "100Cr_500Cr",
            "employee_count": "201_500",
            "founded_year": 2016,
            "is_msme": False,
            "is_startup_india": False,
            "is_dpiit": False,
            "has_gstin": True,
            "gstin": "27ABCDE1234F1Z5",
            "is_export_oriented": False,
            "deducts_tds": True,
            "has_foreign_investment": True,
        }
        obligations = obligation_ids(company)
        self.assertIn("rbi-registration-review", obligations)
        self.assertIn("pmla-review", obligations)
        self.assertIn("fla-return-review", obligations)

    def test_export_saas_startup_gets_export_and_startup_schemes(self):
        company = {
            "name": "CloudOrbit",
            "state": "Delhi",
            "city": "Delhi",
            "entity_type": "pvt_ltd",
            "sector": "technology_saas",
            "annual_turnover": "1Cr_10Cr",
            "employee_count": "51_200",
            "founded_year": 2021,
            "is_msme": True,
            "is_startup_india": True,
            "is_dpiit": True,
            "has_gstin": True,
            "gstin": "07ABCDE1234F1Z5",
            "is_export_oriented": True,
            "deducts_tds": True,
            "has_rd_collaboration": True,
        }
        obligations = obligation_ids(company)
        schemes = scheme_status(company)
        self.assertIn("softex-review", obligations)
        self.assertIn("startup-tax", schemes)
        self.assertIn("mai", schemes)
        self.assertEqual(schemes["rd-grant"], "eligible")

    def test_generic_food_msme_does_not_get_founder_patent_or_receivables_routes_by_default(self):
        company = {
            "name": "Tea Shelf",
            "state": "West Bengal",
            "city": "Kolkata",
            "entity_type": "pvt_ltd",
            "sector": "food_processing",
            "annual_turnover": "40L_1Cr",
            "employee_count": "11_50",
            "is_msme": True,
            "has_gstin": True,
            "handles_food_products": True,
        }
        schemes = scheme_status(company)
        self.assertNotIn("seed-fund", schemes)
        self.assertNotIn("startup-tax", schemes)
        self.assertNotIn("sip-eit", schemes)
        self.assertNotIn("stand-up-india", schemes)
        self.assertNotIn("national-scst-hub", schemes)
        self.assertNotIn("treds", schemes)
        self.assertNotIn("samadhaan", schemes)
        self.assertIn("aif", schemes)

    def test_receivables_routes_only_surface_when_b2b_receivables_are_real(self):
        company = {
            "name": "MetalFab Supply",
            "state": "Gujarat",
            "city": "Ahmedabad",
            "entity_type": "pvt_ltd",
            "sector": "manufacturing_steel_metal",
            "annual_turnover": "1Cr_10Cr",
            "employee_count": "11_50",
            "is_msme": True,
            "has_gstin": True,
            "has_b2b_receivables": False,
        }
        schemes = scheme_status(company)
        self.assertNotIn("treds", schemes)
        self.assertNotIn("samadhaan", schemes)

        company["has_b2b_receivables"] = True
        schemes = scheme_status(company)
        self.assertIn("treds", schemes)
        self.assertIn("samadhaan", schemes)

    def test_guided_review_blocks_aif_when_processing_is_secondary_only(self):
        company = {
            "name": "Tea Infra Projects",
            "state": "Assam",
            "city": "Dibrugarh",
            "entity_type": "pvt_ltd",
            "sector": "food_processing",
            "annual_turnover": "1Cr_10Cr",
            "employee_count": "11_50",
            "is_msme": True,
            "has_gstin": True,
            "handles_food_products": True,
            "has_primary_processing": True,
        }
        review = evaluate_scheme_review(
            company,
            scheme_template("aif"),
            {
                "aif_project_fit": "yes",
                "aif_processing_scope": "secondary_only",
                "aif_location_pattern": "single_location",
                "aif_project_count": "1_5",
            },
        )
        self.assertEqual(review["review_status"], "review_ineligible")
        self.assertTrue(any("Standalone secondary processing" in item for item in review["unmet_conditions"]))

    def test_guided_review_can_confirm_apply_ready_status_for_scheme_with_extra_conditions(self):
        company = {
            "name": "CloudOrbit",
            "state": "Delhi",
            "city": "Delhi",
            "entity_type": "pvt_ltd",
            "sector": "technology_saas",
            "annual_turnover": "1Cr_10Cr",
            "employee_count": "11_50",
            "founded_year": 2022,
            "is_msme": True,
            "is_startup_india": True,
            "is_dpiit": True,
            "has_gstin": True,
            "is_export_oriented": False,
            "dpiit_certificate_number": "",
        }
        review = evaluate_scheme_review(
            company,
            scheme_template("startup-tax"),
            {
                "entity_type_fit": "yes",
                "dpiit_ready": "yes",
                "turnover_fit": "yes",
                "dpiit_certificate_number_ready": "yes",
                "finance_ready": "yes",
                "age_fit": "yes",
            },
        )
        self.assertEqual(review["review_status"], "review_eligible")
        self.assertTrue(review["can_apply_now"])


class DiscoverySignalTests(unittest.TestCase):
    def test_storefront_defence_copy_does_not_trigger_industrial_defence(self):
        text = (
            "Cold & Defense teas help with cold and cough. "
            "The immune system benefits from herbal blends."
        )
        self.assertFalse(contains_defence_signal(text))

    def test_aerospace_manufacturing_copy_triggers_industrial_defence(self):
        text = (
            "Nucon Aerospace is a precision engineering and defence manufacturing company "
            "building components and assemblies for aerospace systems."
        )
        self.assertTrue(contains_defence_signal(text))


if __name__ == "__main__":
    unittest.main()
