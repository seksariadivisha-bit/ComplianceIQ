# ComplianceIQ Robustness Blueprint

## Purpose

This document defines what "extremely robust" should mean for ComplianceIQ before more code changes are made.

The current product already has useful pieces:
- website-based identity and legal-entity detection
- some industry-specific compliance mapping
- some scheme clause review
- official-source routing

But it is still not robust enough because:
- different companies still receive too many generic schemes and compliance items
- the intake profile is too shallow for many sector-specific decisions
- scheme and compliance logic are mixed into one broad catalog instead of being built from a source-backed coverage model
- "all compliances" and "all schemes" cannot be solved by one static list

The platform should be rebuilt around:
1. Official source families
2. A canonical company fact model
3. Progressive profiling
4. Deterministic mapping
5. Verification and confidence labels
6. Sector-specific packs

## Non-Negotiable Product Principles

- Never show a scheme just because it loosely sounds relevant.
- Never hide important compliance just to keep the UI clean.
- Never force users through a giant universal form.
- Detect first, confirm second, ask conditionally third.
- Separate current-entity truth from parent-entity truth and strategic-path opportunities.
- Distinguish "applies now" from "might apply" from "could be unlocked later".
- Use official sources as the source of truth wherever possible.
- Treat schemes and compliances as living data, not a one-time hardcoded project.

## What "Full Coverage" Actually Means

The system must cover four different universes.

### 1. Entity-Level Compliance

These apply because of the legal entity, tax registrations, turnover, listing status, ownership, or cross-border status.

Examples:
- GST
- TDS
- income tax return
- tax audit
- transfer pricing
- MCA / ROC filings
- LLP filings
- listed-company disclosures
- FEMA / FDI reporting
- CSR

### 2. Employer-Level Compliance

These apply because of headcount, payroll, type of workers, location, labour model, or state labour rules.

Examples:
- PF
- ESI
- POSH
- gratuity
- bonus
- maternity
- minimum wages
- wage payment
- working-hours / weekly-off / overtime
- Shops & Establishments
- labour welfare fund
- professional tax
- contract labour
- migrant labour

### 3. Facility- or Project-Level Compliance

These apply because the business operates a plant, site, clinic, warehouse, project, or regulated facility.

Examples:
- factory licence
- fire NOC
- CTE / CTO
- hazardous waste
- biomedical waste
- clinical establishment registration
- FSSAI licence
- drug licence
- CDSCO approvals
- RERA
- BOCW
- boiler and lift approvals
- excise-sensitive licences
- local trade licences

### 4. Schemes and Support Programs

These are not one homogeneous catalog. They break down into:
- central evergreen schemes
- state evergreen schemes
- sector-specific schemes
- regulator-specific windows
- rolling support programs
- periodic cohorts
- competitive grant programs
- strategic unlock routes

## Why a Static "Every Scheme + Every Compliance" List Is Not Enough

### Compliances

Compliance is spread across:
- central acts
- state acts and rules
- regulator circulars
- licence-specific conditions
- project-level approvals
- local body permissions
- periodic notifications

### Schemes

Scheme applicability changes because:
- schemes open and close
- ministries revise clauses
- budget windows shift
- state schemes differ
- cohorts are periodic
- the same scheme may be technically active but practically unavailable for a given company profile

So the target architecture must be:
- static where law structure is stable
- dynamic where scheme or portal status changes

## Official Source Families

The platform should treat these as source families, not just links.

### Primary Law / Legal Text
- India Code
- state labour and state commercial law portals where India Code is incomplete

### Central Registries and Validation
- MCA
- GSTN
- Udyam
- Startup India / DPIIT
- DGFT
- FSSAI FoSCoS
- CDSCO
- EPFO
- ESIC

### Financial and Market Regulators
- RBI
- SEBI
- IRDAI

### Environmental / Industrial
- CPCB
- SPCBs
- DPIIT industrial licensing
- state single-window / industrial promotion portals

### Scheme Discovery
- myScheme
- ministry-specific scheme pages
- state startup / industry / MSME portals

### Update Sources
- gazette notifications
- ministry notification pages
- regulator circular pages

## Canonical Company Fact Model

This is the backbone of the product. The system should support every field below even if not all are collected in the first user interaction.

### Identity and Scope
- brand_name
- legal_entity_name
- parent_entity_name
- operator_name
- website_url
- website_domain
- analysis_scope
  - current_entity
  - parent_entity
  - brand_unit
  - project_vehicle
  - new_entity_scenario
- entity_relationship_notes

### Legal Form
- entity_type
  - private limited
  - public limited
  - OPC
  - LLP
  - partnership
  - proprietorship
  - trust
  - society
  - section 8
  - cooperative
  - other
- listed_status
- listed_exchange_type

### Geography
- registered_state
- operating_state
- city
- multi_state_operations
- district
- industrial_area_or_sez

### Business Classification
- primary_sector
- sub_sector
- business_model
  - manufacturing
  - processing
  - services
  - software
  - trading
  - marketplace
  - contractor
  - warehousing
  - healthcare_facility
  - finance_regulated
  - education_operator
  - project_based
- operating_activity
- group_sector_hint
- nic_codes_if_available

### Scale
- employee_range
- worker_type_mix
  - permanent
  - contractual
  - migrant
  - apprentices
- turnover_range
- funding_stage
- company_age_years
- founded_year

### Registrations and Credentials
- cin
- llpin
- gstin
- tan
- pan
- udyam_number
- dpiit_certificate_number
- fssai_license_number
- iec_number
- epfo_establishment_code
- esic_employer_code
- drug_licence_number
- cdsco_registration_number
- rbi_registration_type
- sebi_registration_type
- irdai_registration_type

### Business Flags
- has_gstin
- deducts_tds
- is_msme_registered
- is_startup_india_recognised
- is_dpiit_recognised
- is_export_oriented
- imports_goods
- has_foreign_investment
- has_overseas_borrowing
- has_cross_border_data_flow

### Facility and Operations Facts
- has_factory_operations
- has_office_only_operations
- has_warehouse
- has_cold_chain
- has_clinic_or_hospital
- has_diagnostic_lab
- has_food_operations
- has_primary_processing
- has_secondary_processing
- has_standalone_processing
- has_physical_premises
- number_of_locations
- pollution_category
- generates_hazardous_waste
- uses_boilers
- requires_fire_noc
- requires_local_trade_licence

### Labour Facts
- uses_contract_labour
- uses_interstate_migrant_workers
- employee_wage_profile_low_band_present
- has_women_employees
- has_shift_operations
- has_overtime_operations

### Founder / Ownership Facts
- women_led_majority
- sc_st_promoter_majority
- founder_shareholding_threshold_confirmed
- greenfield_for_promoter
- prior_founder_scheme_usage

### Sector-Specific Facts
- serves_defence_sector
- controlled_items_exposure
- r_and_d_collaboration
- regulated_financial_entity
- real_estate_project_size
- number_of_real_estate_units
- agri_project_type
- number_of_aif_projects
- project_location_count
- export_product_category
- export_credit_usage

## Field Classification: What To Auto-Fill vs Ask

### Auto-Detect First

These should be discovered or suggested wherever possible:
- brand_name
- legal_entity_name
- parent_entity_name hints
- website
- domain
- likely entity type
- likely state
- likely sector
- possible sub-sector
- public GSTIN / CIN / FSSAI / IEC / LLPIN if exposed
- food / export / manufacturing / defence / retail signals
- whether the brand appears to sit on top of another legal entity

### Ask For Confirmation

These should be shown as "we found this, please confirm":
- legal entity when different from the entered name
- sector if detected with medium confidence
- state if inferred from GSTIN or website
- public IDs found on site
- parent / operator relationship
- current analysis scope

### Ask Only When Material

These should appear only after earlier facts make them relevant:
- GST status
- TDS deductor status
- employee range
- turnover range
- MSME / Udyam
- DPIIT / Startup India
- export yes/no
- foreign investment yes/no
- listed yes/no
- founder-route questions
- factory / project / facility questions
- sector-pack questions

## Progressive Intake Design

The product should not use one giant form. It should use five layers.

### Layer 1: Identity Detection

User input:
- company name
- or website

System detects:
- brand name
- legal entity
- parent / operator hints
- likely website
- likely sector
- likely state
- public IDs

System asks:
- Which entity are we analyzing?
- Are these detected identity details correct?

### Layer 2: Universal Trigger Questions

Ask only the few questions that unlock many rules:
- employee range
- turnover range
- GST registered?
- deducts TDS?
- MSME registered?
- DPIIT recognised?
- exports or cross-border sales?
- received foreign investment?
- listed?

This should usually be 5 to 8 inputs, not more.

### Layer 3: Sector Pack

After sector confirmation, ask a short industry-specific pack.

## Sector Packs

Each sector pack should be small, high-value, and only appear when relevant.

### Food / Beverage / Tea / Coffee / Agri Processing
- Do you manufacture, process, store, or only retail?
- Do you hold an FSSAI licence?
- Is the facility owned, leased, or outsourced?
- Is there cold-chain, warehouse, or storage infrastructure?
- Is this linked to plantation / agriculture / post-harvest activity?
- Is processing primary, secondary, or integrated?
- How many project locations are involved?

### Manufacturing / Industrial
- Is there a factory / plant / industrial site?
- Approximate worker threshold at the site?
- Is power used in manufacturing?
- Any hazardous waste / emissions / discharge?
- Do you use contract labour?
- Do you use migrant labour?
- Are there multiple plants / units?

### Defence / Aerospace
- Does the business supply defence or aerospace systems, components, or controlled items?
- Are the products licensable or controlled?
- Is there a defence industrial licence already?
- Is there a security-sensitive site or restricted data exposure?
- Is the work export-linked or offset-linked?

### Technology / SaaS / IT / BPO
- Is software or IT service exported?
- Is the company in STPI / SEZ?
- Does the company collect significant personal data?
- Is there formal R&D collaboration?
- Is the entity seeking startup incentives or grant routes?

### Healthcare / Pharma / Devices
- Hospital / clinic / lab / manufacturer / distributor / device?
- Drug licence?
- CDSCO registration?
- Biomedical waste generation?
- Clinical establishment registration?

### Fintech / NBFC / Regulated Finance
- RBI regulated?
- SEBI regulated?
- IRDAI regulated?
- Lending, broking, advisory, insurance, payment aggregation, or wallet model?
- Is PMLA / KYC-AML relevant?

### Construction / Real Estate
- Project-based operations?
- Project size?
- Number of units?
- Uses contract labour?
- RERA applicability?
- BOCW applicability?

### Logistics / Warehousing / Cold Chain
- Warehouse or transport only?
- Cold chain?
- Export-linked storage?
- Contract labour?
- Hazardous storage?

### Education
- K12, higher education, coaching, edtech?
- Affiliation / approval type?
- Campus vs online-only?

### Hospitality / Restaurants / Hotels
- Restaurant, cloud kitchen, hotel, tourism operator?
- Food service?
- Liquor licence?
- Foreign guest handling?

### Chemicals / Hazardous Industries
- Category of chemical operations
- hazardous waste
- emissions or discharge
- boiler / pressure / storage conditions

## Scheme Review Layers

Not every question belongs in onboarding.

Scheme review should happen in three layers:

### Layer A: Initial Surface
Show only if:
- sector roughly matches
- entity roughly matches
- geography roughly matches
- no obvious hard blocker exists

Status options:
- likely relevant
- needs confirmation
- strategic path only

### Layer B: Hard Clause Check
Ask only the minimum scheme-specific questions needed to avoid misleading output.

Examples:
- AIF:
  - project type
  - primary vs standalone secondary processing
  - location
  - project count
- Stand-Up India:
  - majority founder category
  - greenfield status
  - shareholding threshold
  - prior use
- PLI:
  - eligible product category
  - minimum investment
  - base-year or incremental sales facts
- export schemes:
  - IEC
  - export products
  - export credit usage

### Layer C: Verification / Activation
Show:
- what proof is needed
- what official source validates it
- whether the source is live, manual, or captcha-gated

## Compliance Review Layers

Compliance should not be shown as one undifferentiated list.

### 1. Definitely Applies
Enough facts are known and the trigger is clear.

### 2. Likely Applies
Sector and scale strongly suggest it, but one factual confirmation is missing.

### 3. Needs Confirmation
The business is in a relevant lane, but a critical site / labour / registration fact is missing.

### 4. Not Applicable
Explicitly ruled out by known facts.

## Coverage by Sector Family

The engine should support at least the following sector families:
- technology / SaaS / IT services / BPO
- hardware / electronics manufacturing
- food manufacturing
- food retail / restaurants / cloud kitchens
- agri processing / tea / coffee / plantation-linked businesses
- general manufacturing
- automotive / EV
- textiles / garments
- chemicals / hazardous manufacturing
- defence / aerospace
- pharma manufacturing
- medical devices
- hospitals / clinics / diagnostic labs
- fintech
- NBFC
- banking and insurance support lanes
- real estate development
- construction / infrastructure
- logistics / warehousing / cold chain
- e-commerce / marketplace / D2C
- retail offline
- education / edtech
- hospitality / tourism / hotels
- media / entertainment / gaming
- professional services
- NGOs / trusts / societies / section 8
- cooperatives
- export merchants / importers / merchant traders
- energy / renewables / utilities

## Compliance Family Buckets

The catalog should be restructured into families rather than one flat list.

### Universal Tax and Corporate
- GST
- TDS
- income tax
- ROC / MCA
- LLP
- CSR
- listed company / SEBI
- FEMA / FDI

### Labour and Employment
- PF
- ESI
- gratuity
- bonus
- maternity
- POSH
- wage and hours
- Shops & Establishments
- welfare fund
- professional tax
- contract labour
- migrant labour
- standing orders
- apprentices

### Facility and Industrial
- factory licence
- fire
- plant safety
- boiler / pressure vessel
- electrical safety if relevant
- environmental approvals
- hazardous waste
- local trade / factory permits

### Sectoral
- food
- pharma / devices
- healthcare facility
- real estate / project
- construction worker cess
- export / DGFT
- defence / controlled items
- hospitality licences
- education approvals
- financial-sector licences

## Scheme Family Buckets

The catalog should be split into:

### Universal Business Support
- MSME finance
- receivables finance
- credit guarantee
- procurement access

### Startup and Innovation
- DPIIT tax
- seed fund
- angel-tax exemption
- startup state grants
- R&D collaboration grants

### Industrial and Manufacturing
- PLI family
- state industrial subsidies
- ZED
- technology upgradation
- capex-linked programs

### Agri / Food / Rural
- AIF
- food processing incentives
- agri infra and storage support
- cluster and co-operative routes

### Export
- DGFT-linked programs
- remission / equalisation / insurance
- export market access

### Founder-Route
- Stand-Up India
- SC/ST MSME support
- women-led enterprise routes

### State-Specific
- state startup policies
- state industrial policies
- state investor support routes

### Sector-Regulator Specific
- defence innovation or industrial support
- health / medtech support
- EV / mobility support
- textile / garment support

## What the Current App Is Missing Most

### Missing high-value facts
- exact analysis scope
- richer sector subtyping
- facility / project details
- founder shareholding threshold confirmation
- regulated-finance status
- project/location-specific facts for scheme clauses
- payroll nuance for labour laws
- sector-specific licence status

### Missing logic structure
- sector packs
- confidence levels
- apply / likely / confirm / strategic labels
- better separation between entity, employer, facility, and project compliance
- stronger scheme gating before display

## Recommended Rebuild Order

### Phase 1: Coverage Blueprint and Source Map
- Build the source-family registry
- Build sector coverage matrix
- Build company fact model
- Build field classification matrix

### Phase 2: Canonical Data Layer
- Refactor compliance catalog into regulator / family buckets
- Refactor schemes into official-source-backed families
- Store proof requirements and confidence rules

### Phase 3: Intake Engine
- Identity detection
- confirmation layer
- universal trigger pack
- sector packs
- scheme deep-review packs

### Phase 4: Mapping Engine
- compliance status states
- scheme status states
- strategic path handling
- entity / parent / newco path comparison

### Phase 5: Verification Layer
- source-specific verification plan
- manual / captcha / live checks
- proof requirements on each result

### Phase 6: UI
- show only what matters
- no generic flooding
- progressive deep review
- confidence and proof language

## Practical Product Rules

- If the system does not know a critical fact, it should not pretend.
- If a compliance item depends on a site fact, ask a site question.
- If a scheme depends on a project clause, ask the project question before showing a strong recommendation.
- If a result belongs more naturally to the parent entity or another vehicle, say that clearly.
- If a result is only strategic, keep it in a separate strategic section.
- If a fact can be verified from an official source, route the user to that verification path.

## Recommended Immediate Next Deliverable

Before more product changes, the next implementation artifact should be a structured matrix with one row per field:
- field name
- why it matters
- which compliance families it affects
- which scheme families it affects
- can auto-detect?
- can verify officially?
- ask in universal pack?
- ask in which sector pack?
- ask only in deep review?

That matrix should drive:
- discovery
- questionnaire
- mapping
- verification
- UI explanations

Without that matrix, the product will keep drifting back toward generic results.
