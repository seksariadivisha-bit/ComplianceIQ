(function () {
  const state = {
    mode: "landing",
    onboardingStep: 1,
    activeView: "schemes",
    complianceFilter: "all",
    schemeFilter: "all",
    companies: [],
    activeCompanyId: null,
    company: null,
    obligations: [],
    schemes: [],
    officialSources: [],
    verificationPlan: null,
    officialSchemeMatches: [],
    officialSchemeMeta: { matchedTotal: 0, cachedTotal: 0, lastSyncedAt: null },
    schemeOpportunities: [],
    detectedOfficialIds: {},
    toast: null,
    reviewStep: 1,
    reviewAnswers: {},
    reviewAssessment: null,
    reviewLoading: false,
    selectedOfficialSchemeId: null,
    selectedOpportunityId: null,
    applicationSchemeId: null,
    applicationSchemeSource: null,
    loading: false,
    saving: false,
    onboardingBusy: false,
    onboardingMessage: "",
    error: "",
    draftCompany: defaultDraftCompany(),
    discovery: null,
    selectedSchemeId: null,
  };

  const TAX_CATEGORIES = new Set(["gst", "tds", "tax"]);

  const states = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
  ];

  const sectors = [
    "technology",
    "technology_software",
    "technology_saas",
    "technology_hardware",
    "it_services",
    "bpo_kpo",
    "manufacturing",
    "food_manufacturing",
    "food_processing",
    "retail",
    "food_retail",
    "restaurants_hospitality",
    "healthcare",
    "pharma_manufacturing",
    "pharma_distribution",
    "medical_devices",
    "hospitals_clinics",
    "diagnostic_labs",
    "fintech",
    "nbfc",
    "banking",
    "insurance",
    "investment_advisory",
    "stockbroking",
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
    "real_estate",
    "retail_ecommerce",
    "retail_offline",
    "marketplace_platform",
    "real_estate_developer",
    "real_estate_agent",
    "construction",
    "construction_infrastructure",
    "logistics",
    "logistics_transport",
    "warehousing",
    "courier",
    "education",
    "education_school",
    "education_college",
    "education_edtech",
    "coaching",
    "agriculture",
    "agriculture_farming",
    "agritech",
    "food_agri_processing",
    "energy",
    "energy_solar",
    "energy_conventional",
    "mining",
    "media",
    "media_entertainment",
    "gaming",
    "ott",
    "professional_services",
    "legal_professional",
    "ca_cs_firm",
    "consulting",
    "ngo",
    "ngo_csr",
    "social_enterprise",
    "export",
    "export_trading",
    "import_trading",
    "hospitality",
    "tourism_hotels",
    "travel_agency",
    "telecom",
    "isp",
    "other",
  ];

  const sectorBuckets = {
    technology: "technology",
    technology_software: "technology",
    technology_saas: "technology",
    technology_hardware: "technology",
    it_services: "technology",
    bpo_kpo: "technology",
    manufacturing: "manufacturing",
    food_manufacturing: "food_processing",
    food_processing: "food_processing",
    retail: "retail",
    food_retail: "food_processing",
    restaurants_hospitality: "hospitality",
    healthcare: "healthcare",
    pharma_manufacturing: "healthcare",
    pharma_distribution: "healthcare",
    medical_devices: "healthcare",
    hospitals_clinics: "healthcare",
    diagnostic_labs: "healthcare",
    fintech: "fintech",
    nbfc: "fintech",
    banking: "fintech",
    insurance: "fintech",
    investment_advisory: "fintech",
    stockbroking: "fintech",
    real_estate: "real_estate",
    manufacturing_auto: "manufacturing",
    manufacturing_electronics: "manufacturing",
    manufacturing_chemicals: "manufacturing",
    manufacturing_textiles: "manufacturing",
    manufacturing_steel_metal: "manufacturing",
    manufacturing_cement: "manufacturing",
    manufacturing_plastic: "manufacturing",
    manufacturing_garments: "manufacturing",
    manufacturing_leather: "manufacturing",
    manufacturing_paper: "manufacturing",
    retail_ecommerce: "retail",
    retail_offline: "retail",
    marketplace_platform: "retail",
    real_estate_developer: "real_estate",
    real_estate_agent: "real_estate",
    construction: "construction",
    construction_infrastructure: "construction",
    logistics: "logistics",
    logistics_transport: "logistics",
    warehousing: "logistics",
    courier: "logistics",
    education: "education",
    education_school: "education",
    education_college: "education",
    education_edtech: "education",
    coaching: "education",
    agriculture_farming: "agriculture",
    agritech: "agriculture",
    food_agri_processing: "food_processing",
    energy: "energy",
    energy_solar: "energy",
    energy_conventional: "energy",
    mining: "energy",
    media: "media",
    media_entertainment: "media",
    gaming: "media",
    ott: "media",
    professional_services: "professional_services",
    legal_professional: "professional_services",
    ca_cs_firm: "professional_services",
    consulting: "professional_services",
    ngo: "ngo",
    ngo_csr: "ngo",
    social_enterprise: "ngo",
    export: "export",
    export_trading: "export",
    import_trading: "export",
    hospitality: "hospitality",
    tourism_hotels: "hospitality",
    travel_agency: "hospitality",
    telecom: "telecom",
    telecom: "telecom",
    isp: "telecom",
  };

  const api = {
    async request(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || "Request failed");
      }
      return payload;
    },
    getCompanies() {
      return this.request("/api/companies");
    },
    getOfficialSources() {
      return this.request("/api/official-sources");
    },
    syncOfficialSchemes() {
      return this.request("/api/official-schemes/sync", {
        method: "POST",
        body: JSON.stringify({ source_id: "myscheme" }),
      });
    },
    refreshOfficialSources() {
      return this.request("/api/official-sources/refresh", {
        method: "POST",
        body: JSON.stringify({}),
      });
    },
    discoverCompany(payload) {
      return this.request("/api/discover-company", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    getCompany(companyId) {
      return this.request(`/api/companies/${companyId}`);
    },
    getVerificationPlan(companyId) {
      return this.request(`/api/companies/${companyId}/verification-plan`);
    },
    getCompanyOfficialSchemes(companyId) {
      return this.request(`/api/companies/${companyId}/official-schemes?limit=12`);
    },
    getCompanySchemeOpportunities(companyId) {
      return this.request(`/api/companies/${companyId}/scheme-opportunities?limit=8`);
    },
    getObligations(companyId) {
      const query = state.complianceFilter === "all" ? "" : `?status=${encodeURIComponent(state.complianceFilter)}`;
      return this.request(`/api/companies/${companyId}/obligations${query}`);
    },
    getSchemes(companyId) {
      const query = state.schemeFilter === "all" ? "" : `?status=${encodeURIComponent(state.schemeFilter)}`;
      return this.request(`/api/companies/${companyId}/schemes${query}`);
    },
    createCompany(payload) {
      return this.request("/api/companies", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },
    obligationAction(companyId, obligationId, action) {
      return this.request(`/api/companies/${companyId}/obligations/${obligationId}/${action}`, { method: "POST" });
    },
    schemeAction(companyId, schemeId, action) {
      return this.request(`/api/companies/${companyId}/schemes/${schemeId}/${action}`, { method: "POST" });
    },
    reviewMappedScheme(companyId, schemeId, answers = {}) {
      return this.request(`/api/companies/${companyId}/schemes/${schemeId}/review`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
    },
    reset() {
      return this.request("/api/reset", { method: "POST" });
    },
  };

  function defaultDraftCompany() {
    return {
      name: "",
      legal_name: "",
      website_url: "",
      website_domain: "",
      analysis_scope: "current_entity",
      operating_activity: "same_as_detected",
      group_sector_hint: "",
      state: "",
      city: "",
      entity_type: "",
      sector: "",
      annual_turnover: "",
      employee_count: "",
      founded_year: new Date().getFullYear() - 5,
      is_msme: false,
      is_startup_india: false,
      is_dpiit: false,
      has_gstin: null,
      is_export_oriented: null,
      has_foreign_investment: null,
      is_listed: null,
      cin: "",
      llpin: "",
      gstin: "",
      pan: "",
      udyam_number: "",
      dpiit_certificate_number: "",
      fssai_license_number: "",
      iec_number: "",
      deducts_tds: null,
      has_factory_operations: null,
      handles_food_products: null,
      has_rd_collaboration: null,
      has_new_hires: null,
      women_led: null,
      has_scst_founder: null,
      uses_contract_labour: null,
      uses_interstate_migrant_workers: null,
      serves_defence_sector: null,
      controlled_items_exposure: null,
      generates_hazardous_waste: null,
      has_warehouse: null,
      has_cold_chain: null,
      has_primary_processing: null,
      has_b2b_receivables: null,
      has_patent_activity: null,
      regulated_financial_entity: null,
      has_healthcare_facility: null,
      has_diagnostic_lab: null,
      project_based_operations: null,
      greenfield_for_promoter: null,
    };
  }

  function titleCase(value) {
    return String(value || "")
      .replace(/_/g, " ")
      .replace(/\bnbfc\b/gi, "NBFC")
      .replace(/\bisp\b/gi, "ISP")
      .replace(/\bit\b/gi, "IT")
      .replace(/\bca\b/gi, "CA")
      .replace(/\bcs\b/gi, "CS")
      .replace(/\b\w/g, (match) => match.toUpperCase());
  }

  function normalizeSector(value) {
    return String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "") || "other";
  }

  function sectorBucketName(value) {
    const key = normalizeSector(value);
    return sectorBuckets[key] || key;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function looksLikeWebsiteInput(value) {
    const candidate = String(value || "").trim();
    return /^https?:\/\//i.test(candidate) || (/^[\w.-]+\.[a-z]{2,}(\/.*)?$/i.test(candidate) && !candidate.includes(" "));
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value || 0);
  }

  function numericValue(value) {
    const amount = Number(value || 0);
    return Number.isFinite(amount) ? amount : 0;
  }

  function schemeValueDetails(item) {
    const amount = numericValue(item?.max_benefit_amount);
    const kind = String(item?.value_kind || (amount > 0 ? "money" : "non_cash")).trim();
    const label = String(item?.value_label || "").trim();

    if (amount > 0) {
      const primary = kind === "estimate" ? `Approx. ${formatCurrency(amount)}` : formatCurrency(amount);
      const secondary = label && label !== primary ? label : "";
      return {
        amount,
        kind,
        label,
        primary,
        secondary,
        isMoney: true,
      };
    }

    const primary =
      label ||
      (kind === "variable"
        ? "Variable benefit"
        : kind === "non_cash"
          ? "Non-cash benefit"
          : "Needs review");

    return {
      amount,
      kind,
      label,
      primary,
      secondary: kind === "variable" && !label ? "Official listing does not publish a fixed monetary amount." : "",
      isMoney: false,
    };
  }

  function renderSchemeValuePill(item) {
    const value = schemeValueDetails(item);
    const financial = schemeFinancialSummary(item);
    const useFinancialPrimary =
      !value.isMoney && ["Financial access", "Monetary gain", "Potential upside"].includes(financial.title);
    const primary = useFinancialPrimary ? financial.primary : value.primary;
    const secondary = useFinancialPrimary ? financial.secondary : value.secondary;
    const numericLike = /₹|\d/.test(primary);
    return `
      <div class="value-stack">
        <span class="value-pill ${value.isMoney || numericLike ? "mono" : "descriptor"}">${escapeHtml(primary)}</span>
        ${secondary ? `<small class="value-note">${escapeHtml(secondary)}</small>` : ""}
      </div>
    `;
  }

  function schemeValueNarrative(item) {
    return schemeFinancialSummary(item).primary;
  }

  function extractCurrencyPhrases(text) {
    const matches = String(text || "").match(/₹\s?\d[\d,.]*(?:\s?(?:L|Lakh|Lakhs|Cr|Crore|Crores))?/gi) || [];
    return Array.from(new Set(matches.map((match) => match.replace(/\s+/g, " ").trim())));
  }

  function schemeFinancialSummary(item) {
    const value = schemeValueDetails(item);
    const benefitText = `${item?.benefit_value || ""} ${item?.value_label || ""} ${item?.name || ""}`;
    const currencyPhrases = extractCurrencyPhrases(benefitText);

    if (value.isMoney) {
      return {
        title: "Potential value",
        primary: value.primary,
        secondary: value.secondary || "Direct monetary upside before final official verification.",
        tone: "money",
      };
    }

    if (item?.scheme_type === "loan" || /loan|credit|finance|financial assistance/i.test(benefitText)) {
      const rangeText =
        currencyPhrases.length >= 2
          ? `${currencyPhrases[0]} to ${currencyPhrases[1]}`
          : currencyPhrases[0] || value.primary;
      return {
        title: "Financial access",
        primary: rangeText,
        secondary: "Financing access, not direct savings.",
        tone: "descriptor",
      };
    }

    if (/epf|abry/i.test(benefitText)) {
      return {
        title: "Monetary gain",
        primary: "Needs payroll data",
        secondary: "Requires wage levels and number of eligible hires to estimate the support amount.",
        tone: "descriptor",
      };
    }

    if (value.kind === "variable") {
      return {
        title: "Potential upside",
        primary: currencyPhrases[0] || value.primary,
        secondary: currencyPhrases[0] ? value.primary : "Depends on actual company data and official eligibility.",
        tone: "descriptor",
      };
    }

    return {
      title: item?.scheme_type === "market_access" ? "Business value" : "Value format",
      primary: value.primary,
      secondary: value.secondary || "Official source does not publish a fixed monetary amount.",
      tone: "descriptor",
    };
  }

  function renderFinancialSummary(item) {
    const financial = schemeFinancialSummary(item);
    return `
      <div class="scheme-summary">
        <strong>${escapeHtml(financial.title)}</strong>
        <p class="${financial.tone === "money" || /₹|\d/.test(financial.primary) ? "mono" : ""}">${escapeHtml(financial.primary)}</p>
        ${financial.secondary ? `<p class="muted">${escapeHtml(financial.secondary)}</p>` : ""}
      </div>
    `;
  }

  function formatDate(value) {
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(new Date(value));
  }

  function daysUntil(value) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(value);
    due.setHours(0, 0, 0, 0);
    return Math.round((due.getTime() - today.getTime()) / 86400000);
  }

  function scopeLabel(value) {
    const labels = {
      current_entity: "Current legal entity",
      brand_unit: "Brand or business unit",
      new_entity_scenario: "Separate new entity",
    };
    return labels[value] || titleCase(value);
  }

  function activityLabel(value) {
    const labels = {
      same_as_detected: "Use detected business line",
      procurement_ecommerce: "Procurement and ecommerce brand",
      manufacturing_processing: "Manufacturing or processing entity",
      agriculture_plantation: "Agriculture or plantation business",
      services_software: "Services or software business",
      healthcare_services: "Healthcare services business",
    };
    return labels[value] || titleCase(value);
  }

  function effectiveSector(company) {
    if (!company) return "";
    if (company.operating_activity && company.operating_activity !== "same_as_detected") {
      const mapping = {
        procurement_ecommerce: "retail_ecommerce",
        manufacturing_processing: "manufacturing_electronics",
        agriculture_plantation: "agriculture",
        services_software: "technology_saas",
        healthcare_services: "hospitals_clinics",
      };
      const mapped = mapping[company.operating_activity];
      if (mapped && sectorBucketName(mapped) === "manufacturing" && company.handles_food_products) return "food_processing";
      if (mapped) return mapped;
    }
    return normalizeSector(company.sector);
  }

  function inferredSectorPack(company) {
    const sector = effectiveSector(company) || company.sector;
    const bucket = sectorBucketName(sector);
    const identityText = `${company.name || ""} ${company.legal_name || ""} ${company.website_domain || ""} ${company.website_url || ""} ${company.group_sector_hint || ""}`.toLowerCase();
    const defenceHint = /defence|defense|aerospace|aviation|avionics|aircraft|drone|uav|missile/.test(identityText);

    if ((bucket === "manufacturing" || bucket === "food_processing") && (company.serves_defence_sector === true || defenceHint)) {
      return "manufacturing_defence";
    }
    if (["food_processing", "agriculture"].includes(bucket) || ["food_retail", "food_manufacturing"].includes(normalizeSector(sector))) {
      return "food_agri";
    }
    if (bucket === "manufacturing") return "manufacturing";
    if (bucket === "healthcare") return "healthcare";
    if (bucket === "fintech") return "finance";
    if (["construction", "real_estate"].includes(bucket)) return "construction_real_estate";
    if (bucket === "logistics") return "logistics";
    if (bucket === "technology") return "technology";
    return "general";
  }

  function isTaxCategory(category) {
    return TAX_CATEGORIES.has(String(category || "").toLowerCase());
  }

  function operationalObligations() {
    return state.obligations.filter((item) => !isTaxCategory(item.category));
  }

  function taxObligations() {
    return state.obligations.filter((item) => isTaxCategory(item.category));
  }

  function obligationExposure(item) {
    const perDay = Number(item.penalty_per_day || 0);
    const delta = daysUntil(item.due_date);
    if (item.status === "overdue") {
      return perDay * Math.max(Math.abs(delta), 1);
    }
    return perDay;
  }

  function badge(label, tone) {
    return `<span class="badge ${tone}">${escapeHtml(label)}</span>`;
  }

  function statusTone(status) {
    if (["eligible", "filed", "received"].includes(status)) return "success";
    if (["overdue"].includes(status)) return "danger";
    if (["pending", "maybe"].includes(status)) return "warning";
    if (["applied"].includes(status)) return "info";
    return "neutral";
  }

  function metricCard(label, value, foot) {
    const iconMap = {
      "Risk score": "shield",
      "Applicable obligations": "company",
      "Untapped scheme value": "rupee",
      "Value already in motion": "scheme",
      "Open now": "scheme",
      "Applied": "official",
      "Realized": "rupee",
      "Strategic upside": "spark",
    };
    return `
      <article class="metric-card">
        <span class="metric-kicker">${iconBadge(iconMap[label] || "spark", "soft")}${escapeHtml(label)}</span>
        <div class="metric-value mono">${escapeHtml(value)}</div>
        <div class="metric-foot">${escapeHtml(foot)}</div>
      </article>
    `;
  }

  function iconGlyph(name) {
    const glyphs = {
      company: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 20h16"/><path d="M6 20V8l6-4 6 4v12"/><path d="M9 12h.01"/><path d="M15 12h.01"/><path d="M9 16h.01"/><path d="M15 16h.01"/></svg>',
      shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l7 3v6c0 4.5-2.6 7.8-7 9-4.4-1.2-7-4.5-7-9V6l7-3z"/><path d="M9.5 12.5l1.7 1.7 3.6-4"/></svg>',
      rupee: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 6h9"/><path d="M6 10h9"/><path d="M6 6c3 0 5 1.8 5 4s-2 4-5 4h2l6 6"/></svg>',
      spark: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/></svg>',
      scheme: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 7h14"/><path d="M5 12h10"/><path d="M5 17h8"/><path d="M17 15l2 2 3-4"/></svg>',
      official: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l7 4v5c0 4.2-2.6 7.5-7 9-4.4-1.5-7-4.8-7-9V7l7-4z"/><path d="M9 11h6"/><path d="M9 15h4"/></svg>',
    };
    return glyphs[name] || glyphs.spark;
  }

  function iconBadge(name, tone = "brand") {
    return `<span class="icon-badge ${tone}">${iconGlyph(name)}</span>`;
  }

  function summaryItem(label, value, detail = "") {
    return `
      <div class="summary-item">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value || "To confirm")}</strong>
        ${detail ? `<small>${escapeHtml(detail)}</small>` : ""}
      </div>
    `;
  }

  async function bootstrap() {
    state.loading = true;
    render();
    try {
      await loadOfficialSources(false);
      await loadCompanies(false);
      state.mode = "landing";
    } catch (error) {
      state.error = error.message;
    } finally {
      state.loading = false;
      render();
    }
  }

  async function loadOfficialSources(showLoader = true) {
    if (showLoader) {
      state.loading = true;
      render();
    }
    try {
      const payload = await api.getOfficialSources();
      state.officialSources = payload.sources || [];
      state.error = "";
    } catch (error) {
      state.error = error.message;
    } finally {
      if (showLoader) {
        state.loading = false;
        render();
      }
    }
  }

  async function loadCompanies(keepLoading = true) {
    if (keepLoading) {
      state.loading = true;
      render();
    }
    const payload = await api.getCompanies();
    state.companies = [...(payload.companies || [])].sort((left, right) => {
      const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
      const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
      return rightTime - leftTime;
    });
    if (state.activeCompanyId && !state.companies.some((item) => item.id === state.activeCompanyId)) {
      state.activeCompanyId = state.companies[0] ? state.companies[0].id : null;
    }
    if (keepLoading) {
      state.loading = false;
      render();
    }
  }

  async function loadWorkspace(companyId, showLoader = true) {
    if (!companyId) return;
    if (showLoader) {
      state.loading = true;
      render();
    }
    try {
      state.activeCompanyId = companyId;
      const [companyPayload, obligationsPayload, schemesPayload, verificationPayload, officialSchemesPayload, opportunityPayload] = await Promise.all([
        api.getCompany(companyId),
        api.getObligations(companyId),
        api.getSchemes(companyId),
        api.getVerificationPlan(companyId),
        api.getCompanyOfficialSchemes(companyId),
        api.getCompanySchemeOpportunities(companyId),
      ]);
      state.company = companyPayload.company;
      state.obligations = obligationsPayload.obligations || [];
      state.schemes = schemesPayload.schemes || [];
      state.verificationPlan = verificationPayload;
      state.officialSchemeMatches = officialSchemesPayload.schemes || [];
      state.schemeOpportunities = opportunityPayload.opportunities || [];
      if (!state.schemes.some((item) => item.id === state.selectedSchemeId)) {
        state.selectedSchemeId = null;
      }
      if (!state.schemeOpportunities.some((item) => item.template_id === state.selectedOpportunityId)) {
        state.selectedOpportunityId = null;
      }
      state.officialSchemeMeta = {
        matchedTotal: officialSchemesPayload.matched_total || 0,
        cachedTotal: officialSchemesPayload.cached_total || 0,
        lastSyncedAt: officialSchemesPayload.last_synced_at || null,
      };
      if (!state.officialSchemeMatches.some((item) => item.scheme_id === state.selectedOfficialSchemeId)) {
        state.selectedOfficialSchemeId = null;
      }
      if (state.applicationSchemeSource === "mapped" && !state.schemes.some((item) => item.id === state.applicationSchemeId)) {
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
      }
      if (state.applicationSchemeSource === "official" && !state.officialSchemeMatches.some((item) => item.scheme_id === state.applicationSchemeId)) {
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
      }
      state.mode = "workspace";
      state.error = "";
      await loadCompanies(false);
    } catch (error) {
      state.error = error.message;
    } finally {
      if (showLoader) {
        state.loading = false;
        render();
      }
    }
  }

  async function loadMappedSchemeReview(answers = null, showLoader = true) {
    if (!state.activeCompanyId || !state.selectedSchemeId) return null;
    if (showLoader) {
      state.reviewLoading = true;
      render();
    }
    try {
      const payload = await api.reviewMappedScheme(state.activeCompanyId, state.selectedSchemeId, answers || {});
      state.reviewAssessment = payload;
      state.error = "";
      return payload;
    } catch (error) {
      state.error = error.message;
      return null;
    } finally {
      if (showLoader) {
        state.reviewLoading = false;
        render();
      }
    }
  }

  function currentMetrics() {
    return state.company ? state.company.metrics : null;
  }

  function currentAnalysisFocus() {
    return state.company?.analysis_focus || null;
  }

  function renderAnalysisFocus() {
    const focus = currentAnalysisFocus();
    if (!focus) return "";
    const valueDrivers = Array.isArray(focus.what_adds_value) ? focus.what_adds_value : [];
    const nextActions = Array.isArray(focus.next_actions) ? focus.next_actions : [];
    if (!focus.summary && !valueDrivers.length && !nextActions.length) return "";

    return `
      <article class="workspace-card">
        <div class="section-top">
          <div>
            <h3>What is adding value here</h3>
            <p class="muted">A short platform read on why this analysis is materially useful for this company, not just more data on screen.</p>
          </div>
        </div>
        ${focus.summary ? `<div class="note-block">${escapeHtml(focus.summary)}</div>` : ""}
        <div class="cards-grid">
          <article class="summary-card summary-card-tight">
            <strong>Value drivers</strong>
            ${
              valueDrivers.length
                ? `<ul class="reason-list">${valueDrivers.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
                : '<p class="muted">No value drivers have been summarised yet.</p>'
            }
          </article>
          <article class="summary-card summary-card-tight">
            <strong>Best next moves</strong>
            ${
              nextActions.length
                ? `<ul class="reason-list">${nextActions.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`
                : '<p class="muted">No next actions have been summarised yet.</p>'
            }
          </article>
        </div>
      </article>
    `;
  }

  function renderTopbar(title, subtitle, actions) {
    return `
      <header class="topbar">
        <div class="topbar-left">
          <button class="button button-ghost button-small home-button" data-action="go-home">Home</button>
          <button class="brand brand-button" data-action="go-home">
            <div class="brand-mark">CI</div>
            <div class="brand-copy">
              <h2>${escapeHtml(title)}</h2>
              <p>${escapeHtml(subtitle)}</p>
            </div>
          </button>
        </div>
        <div class="topbar-actions">${actions}</div>
      </header>
    `;
  }

  function renderError() {
    if (!state.error) return "";
    return `
      <div class="alert danger">
        <strong>Error</strong>
        <span>${escapeHtml(state.error)}</span>
      </div>
    `;
  }

  let toastTimer = null;

  function showToast(message, tone = "danger") {
    state.toast = { message, tone };
    render();
    if (toastTimer) window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      state.toast = null;
      render();
    }, 2600);
  }

  function renderToast() {
    if (!state.toast) return "";
    return `<div class="toast ${escapeHtml(state.toast.tone)}">${escapeHtml(state.toast.message)}</div>`;
  }

  function renderLanding() {
    return `
      <div class="shell shell-wide">
        ${renderTopbar(
          "ComplianceIQ",
          "Company-first compliance and scheme intelligence for India.",
          `
            ${state.companies.length ? '<button class="button button-ghost" data-action="open-workspace">Open latest analysis</button>' : ""}
            <button class="button button-primary" data-action="start-onboarding">Analyze a company</button>
          `
        )}
        <section class="hero hero-simple">
          <div class="hero-copy">
            <div class="eyebrow">Compliance intelligence for Indian companies</div>
            <h1>Find the schemes first. Then see what the company needs to stay compliant.</h1>
            <p>
              Start with a company name or website. The product resolves the likely entity, asks only the questions that materially change the result, and leads with the highest-value schemes and savings paths worth reviewing.
            </p>
            <div class="hero-search">
              <input id="hero-company-name" class="hero-input" placeholder="Enter a company name or website, for example The Tea Shelf or theteashelf.com">
              <button class="button button-primary" data-action="hero-analyze">Analyze company</button>
            </div>
            <div class="hero-cta">
              <button class="button button-secondary" data-action="go-to-schemes-explainer">Open a scheme-led view</button>
            </div>
            <div class="hero-metrics">
              <article class="summary-card summary-card-tight">
                <strong>${iconBadge("scheme")} Scheme-first output</strong>
                <p>Current-fit schemes, strategic unlocks, and conservative value estimates.</p>
              </article>
              <article class="summary-card summary-card-tight">
                <strong>${iconBadge("shield")} Compliance after context</strong>
                <p>Operational obligations are shown after the business facts are clear. GST and tax stay in a separate review lane.</p>
              </article>
              <article class="summary-card summary-card-tight">
                <strong>${iconBadge("official")} Official-source posture</strong>
                <p>Public evidence is auto-read first. Official IDs are only confirmed when they materially improve certainty.</p>
              </article>
            </div>
          </div>
          <div class="hero-side stack hero-playbook">
            <article class="summary-card hero-visual-card">
              <div class="hero-visual">
                <div class="visual-pill">${iconBadge("company", "soft")} Resolve the company</div>
                <div class="visual-pill">${iconBadge("scheme", "soft")} Curate only valuable schemes</div>
                <div class="visual-pill">${iconBadge("rupee", "soft")} Quantify usable value</div>
              </div>
            </article>
            <article class="summary-card">
              <strong>${iconBadge("spark")} How the flow feels</strong>
              <div class="playbook-list">
                <div>
                  <span>1</span>
                  <p>Resolve the brand, legal entity, and business line from public evidence.</p>
                </div>
                <div>
                  <span>2</span>
                  <p>Ask only the missing questions that change scheme or compliance mapping.</p>
                </div>
                <div>
                  <span>3</span>
                  <p>Lead with schemes and savings, then separate operational compliance from GST and tax review.</p>
                </div>
              </div>
            </article>
          </div>
        </section>
        ${renderError()}
      </div>
    `;
  }

  function renderOnboarding() {
    const company = state.draftCompany;
    const visibleSteps = visibleOnboardingSteps(company);
    const step = visibleSteps.some((item) => item.id === state.onboardingStep)
      ? state.onboardingStep
      : visibleSteps[visibleSteps.length - 1].id;
    const officialIdentifierQuestions = buildOfficialIdentifierQuestions(company);
    const followUpQuestions = buildFollowUpQuestions(company);
    const ruleQuestionGroups = buildRuleQuestionGroups(company);
    const detectedIdentifiers = officialIdentifierQuestions.filter((question) => state.detectedOfficialIds[question.field]);
    const confirmedIdentifierQuestions = officialIdentifierQuestions.filter(
      (question) => !state.detectedOfficialIds[question.field] && company[question.field]
    );
    const recommendedIdentifierQuestions = officialIdentifierQuestions.filter(
      (question) => !state.detectedOfficialIds[question.field] && !company[question.field]
    );

    const body = (() => {
      if (step === 1) {
        return `
          <div class="stack">
            <label class="field">
              <span>Company name</span>
              <input name="name" value="${escapeHtml(company.name)}" placeholder="Enter company name">
            </label>
            <label class="field">
              <span>Website URL (optional but recommended)</span>
              <input name="website_url" value="${escapeHtml(company.website_url || "")}" placeholder="https://www.company.com">
            </label>
            <p class="muted">Enter at least a company name or a website. We will resolve the brand, legal entity, likely business line, and any public identifiers we can find before asking for confirmation.</p>
          </div>
        `;
      }
      if (step === 2) {
        return `
          <div class="stack">
            ${
              state.discovery
                ? `
                  <div class="discovery-card">
                    <div class="section-top">
                      <div>
                        <h3>Resolved profile</h3>
                        <p class="muted">We drafted the profile that will drive compliance and scheme mapping. Confirm only what looks off.</p>
                      </div>
                      ${badge(`Confidence ${titleCase(state.discovery.detection_summary?.confidence || "low")}`, state.discovery.detection_summary?.confidence === "high" ? "success" : state.discovery.detection_summary?.confidence === "medium" ? "warning" : "neutral")}
                    </div>
                    <div class="resolution-grid">
                      ${summaryItem("Website", state.discovery?.website_summary?.website_domain || state.discovery?.inferred?.website_domain || company.website_domain || "Not found")}
                      ${summaryItem("Legal entity", state.discovery?.inferred?.legal_name || company.legal_name || "Needs confirmation")}
                      ${summaryItem("Assessment scope", scopeLabel(company.analysis_scope))}
                      ${summaryItem("Business line", activityLabel(company.operating_activity), effectiveSector(company) ? `Evaluated as ${titleCase(effectiveSector(company))}` : "")}
                    </div>
                    ${
                      state.discovery.website_summary?.operator_name && state.discovery.website_summary.operator_name !== state.discovery.inferred?.legal_name
                        ? `<div class="note-block">The public site appears to be a customer-facing brand or unit operated by ${escapeHtml(state.discovery.website_summary.operator_name)}. Choose below whether you want to evaluate the current legal entity, the brand unit, or a separate-entity scenario.</div>`
                        : ""
                    }
                    ${
                      state.discovery.existing_company_id
                        ? `
                          <div class="inline-choice">
                            <div>
                              <strong>Existing analysis found</strong>
                              <p class="muted">There is already a saved analysis for this business. You can open it, or continue to create a separate scenario.</p>
                            </div>
                            <div class="toolbar">
                              <button class="button button-secondary button-small" data-action="open-existing-workspace">Open saved analysis</button>
                            </div>
                          </div>
                        `
                        : ""
                    }
                    ${
                      (state.discovery.detection_summary?.notes || []).length
                        ? `
                          <details class="evidence-details">
                            <summary>See evidence trail</summary>
                            <ul class="reason-list">${(state.discovery.detection_summary.notes || []).map((note) => `<li>${escapeHtml(note)}</li>`).join("")}</ul>
                          </details>
                        `
                        : ""
                    }
                  </div>
                `
                : ""
            }
            <div class="workspace-card compact-card">
              <div class="section-top">
                <div>
                  <h3>How should this be evaluated?</h3>
                  <p class="muted">This decides whether the mapping should behave like a parent entity review, a brand-unit review, or a spinout/newco scenario.</p>
                </div>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>Assessment scope <em class="required">*</em></span>
                  <select name="analysis_scope">
                    ${analysisScopeOptions(company.analysis_scope)}
                  </select>
                </label>
                <label class="field">
                  <span>Operating activity for this assessment <em class="required">*</em></span>
                  <select name="operating_activity">
                    ${operatingActivityOptions(company.operating_activity)}
                  </select>
                </label>
              </div>
              ${
                company.group_sector_hint
                  ? `<p class="muted">Parent-group signals suggest ${escapeHtml(titleCase(company.group_sector_hint))} operations as well. Those can create additional financing or subsidy opportunities that may sit with the parent entity instead of the brand unit.</p>`
                  : ""
              }
            </div>
            <div class="form-grid">
              <label class="field">
                <span>Operating name <em class="required">*</em></span>
                <input name="name" value="${escapeHtml(company.name)}" placeholder="The Tea Shelf">
              </label>
              <label class="field">
                <span>Legal name</span>
                <input name="legal_name" value="${escapeHtml(company.legal_name || "")}" placeholder="Mahadeobari Tea Co. Pvt. Ltd.">
              </label>
              <label class="field">
                <span>Entity type <em class="required">*</em></span>
                <select name="entity_type">${entityOptions(company.entity_type)}</select>
              </label>
              <label class="field">
                <span>Sector <em class="required">*</em></span>
                <select name="sector">${sectorOptions(company.sector)}</select>
              </label>
              <label class="field">
                <span>State <em class="required">*</em></span>
                <select name="state">${stateOptions(company.state)}</select>
              </label>
              <label class="field">
                <span>City <em class="required">*</em></span>
                <input name="city" value="${escapeHtml(company.city)}" placeholder="Bengaluru">
              </label>
              <label class="field">
                <span>Website</span>
                <input name="website_url" value="${escapeHtml(company.website_url || "")}" placeholder="https://www.company.com">
              </label>
            </div>
            <div class="note-block">State and operating activity materially change scheme and compliance mapping. Use the state and business line you want this exact assessment to reflect.</div>
          </div>
        `;
      }
      if (step === 3) {
        return `
          <div class="stack">
            <div class="form-grid">
              <label class="field">
                <span>Annual turnover <em class="required">*</em></span>
                <select name="annual_turnover">${turnoverOptions(company.annual_turnover)}</select>
              </label>
              <label class="field">
                <span>Employee count <em class="required">*</em></span>
                <select name="employee_count">${employeeOptions(company.employee_count)}</select>
              </label>
              <label class="field">
                <span>Founded year <em class="required">*</em></span>
                <input type="number" min="1990" max="${new Date().getFullYear()}" name="founded_year" value="${escapeHtml(String(company.founded_year))}">
              </label>
            </div>
            ${
              company.analysis_scope === "new_entity_scenario"
                ? `<div class="note-block">For a new-entity scenario, enter the expected size and age of the entity you would actually set up. This can materially change startup, MSME, and tax-benefit eligibility.</div>`
                : ""
            }
          </div>
        `;
      }
      if (step === 4) {
        return `
          <div class="stack">
              <div class="section-top">
                <div>
                  <h3>Official identifiers that improve accuracy</h3>
                  <p class="muted">These are optional, but they materially improve the result when you have them. We ask only for identifiers that help verify the entity, sharpen compliance mapping, or make scheme readiness more reliable.</p>
                </div>
              </div>
            ${
              detectedIdentifiers.length || confirmedIdentifierQuestions.length || recommendedIdentifierQuestions.length
                ? `
                  ${
                    detectedIdentifiers.length
                      ? `
                        <article class="workspace-card compact-card">
                          <div class="section-top">
                            <div>
                              <h3>Detected from public evidence</h3>
                              <p class="muted">Use these suggestions in one tap if they look right.</p>
                            </div>
                          </div>
                          <div class="form-grid">
                            ${detectedIdentifiers
                              .map((question) =>
                                textFieldCard(
                                  question.field,
                                  question.label,
                                  question.description,
                                  company[question.field],
                                  question.placeholder,
                                  state.detectedOfficialIds[question.field] || ""
                                )
                              )
                              .join("")}
                          </div>
                        </article>
                      `
                      : ""
                  }
                  ${
                    confirmedIdentifierQuestions.length
                      ? `
                        <article class="workspace-card compact-card">
                          <div class="section-top">
                            <div>
                              <h3>Already added</h3>
                              <p class="muted">You or the product already filled these. Adjust them here if needed.</p>
                            </div>
                          </div>
                          <div class="form-grid">
                            ${confirmedIdentifierQuestions
                              .map((question) =>
                                textFieldCard(
                                  question.field,
                                  question.label,
                                  question.description,
                                  company[question.field],
                                  question.placeholder,
                                  ""
                                )
                              )
                              .join("")}
                          </div>
                        </article>
                      `
                      : ""
                  }
                  ${
                    recommendedIdentifierQuestions.length
                      ? `
                        <article class="workspace-card compact-card">
                          <div class="section-top">
                            <div>
                              <h3>Recommended if you have them</h3>
                              <p class="muted">These are the identifiers most likely to improve output quality for this company. You can continue without them, but adding them now usually reduces uncertainty later.</p>
                            </div>
                          </div>
                          <div class="form-grid">
                            ${recommendedIdentifierQuestions
                              .map((question) =>
                                textFieldCard(
                                  question.field,
                                  question.label,
                                  question.description,
                                  company[question.field],
                                  question.placeholder,
                                  ""
                                )
                              )
                              .join("")}
                          </div>
                        </article>
                      `
                      : ""
                  }
                `
                : '<div class="note-block">No high-value official identifiers are being asked for this profile right now. The product will only ask for an ID later if it materially changes verification or application readiness.</div>'
            }
            <div class="note-block">These are trade-offs, not mandatory friction. If an identifier will materially improve certainty, we ask for it. If it will not materially change the answer, we do not interrupt the customer.</div>
            ${
              detectedIdentifiers.length
                ? `<p class="muted">${detectedIdentifiers.length} likely registration suggestion${detectedIdentifiers.length === 1 ? "" : "s"} were found from public evidence. Nothing is treated as confirmed until the customer fills or accepts it.</p>`
                : ""
            }
          </div>
        `;
      }
      if (step === 5) {
        return `
          <div class="stack">
            <div class="section-top">
              <div>
                <h3>Company-specific questions</h3>
                <p class="muted">These are the last questions before results. They are split into universal facts and sector-specific packs so the product only asks what actually changes the output for this company.</p>
              </div>
            </div>
            ${
              followUpQuestions.length
                ? ruleQuestionGroups
                    .map(
                      (group) => `
                        <article class="workspace-card compact-card">
                          <div class="section-top">
                            <div>
                              <h3>${escapeHtml(group.title)}</h3>
                              ${group.description ? `<p class="muted">${escapeHtml(group.description)}</p>` : ""}
                            </div>
                          </div>
                          <div class="flag-grid">${group.questions
                            .map((question) => factQuestionCard(question.field, question.label, question.description, company[question.field]))
                            .join("")}</div>
                        </article>
                      `
                    )
                    .join("")
                : '<div class="note-block">No extra company-specific questions are needed for this profile right now.</div>'
            }
          </div>
        `;
      }
      return `
        <div class="stack">
          <div class="section-top">
            <div>
              <h3>Credentials that unlock benefits</h3>
              <p class="muted">Only turn these on if they truly apply to the entity or scenario being evaluated.</p>
            </div>
          </div>
          <div class="flag-grid">
            ${flagCard("is_msme", "MSME registered", "Needed for MSME-linked programs like CGTMSE, TReDS, Samadhaan, and several credit-linked benefits.", company.is_msme)}
            ${flagCard("is_startup_india", "Startup India registered", "Useful for startup grants and some state innovation programs.", company.is_startup_india)}
            ${flagCard("is_dpiit", "DPIIT recognised", "Needed for Startup India tax exemption and some early-stage schemes.", company.is_dpiit)}
          </div>
        </div>
      `;
    })();

    return `
      <div class="shell">
        ${renderTopbar(
          "Analyze company",
          "Let the platform infer first, then confirm the details that change the result.",
          '<button class="button button-ghost" data-action="go-home">Back</button>'
        )}
        ${renderError()}
        ${state.onboardingBusy ? `<div class="progress-inline">${escapeHtml(state.onboardingMessage || "Working...")}</div>` : ""}
        <section class="workspace-card workspace-card-narrow">
          <div class="step-row">
            ${visibleSteps.map((item) => `<span class="step-pill ${step === item.id ? "active" : ""}">${escapeHtml(item.label)}</span>`).join("")}
          </div>
          <form id="company-form" class="stack">${body}</form>
          <div class="toolbar">
            ${step > 1 ? `<button class="button button-ghost" data-action="step-back" ${state.onboardingBusy || state.saving ? "disabled" : ""}>Back</button>` : ""}
            ${step !== visibleSteps[visibleSteps.length - 1].id
              ? `<button class="button button-primary" data-action="step-next" ${state.onboardingBusy || state.saving ? "disabled" : ""}>${escapeHtml(onboardingPrimaryLabel(step, company))}</button>`
              : `<button class="button button-primary" data-action="save-company" ${state.onboardingBusy || state.saving ? "disabled" : ""}>${escapeHtml(onboardingPrimaryLabel(step, company))}</button>`}
          </div>
        </section>
      </div>
    `;
  }

  function renderNavItem(view, label) {
    const icons = {
      overview: "spark",
      company: "company",
      compliance: "shield",
      tax: "rupee",
      schemes: "scheme",
    };
    return `<button class="nav-button ${state.activeView === view ? "active" : ""}" data-action="switch-view" data-view="${view}">${iconBadge(icons[view] || "spark", "soft")}${escapeHtml(label)}</button>`;
  }

  function renderOverview() {
    const metrics = currentMetrics();
    if (!state.company || !metrics) return "";
    const upcoming = operationalObligations().slice(0, 5);
    const taxItems = taxObligations();
    return `
      <section class="stack">
        ${
          metrics.overdue_count
            ? `<div class="alert danger"><strong>Status warning</strong><span>${metrics.overdue_count} items are overdue, driving ${formatCurrency(metrics.burn_rate)} per day and ${formatCurrency(metrics.annual_burn_estimate)} per year in potential exposure.</span></div>`
            : `<div class="alert success"><strong>Status healthy</strong><span>No overdue items right now. The company is currently in a good operating state.</span></div>`
        }
        <div class="grid-4">
          ${metricCard("Risk score", String(metrics.risk_score), "0 to 100 health score")}
          ${metricCard("Applicable obligations", String(state.obligations.length), `${metrics.pending_count + metrics.overdue_count} still need action`)}
          ${metricCard("Untapped scheme value", formatCurrency(metrics.potential), `${metrics.open_scheme_count} eligible or maybe-eligible programs`)}
          ${metricCard("Value already in motion", formatCurrency(metrics.applied_value + metrics.received_value), `${metrics.applied_scheme_count} applied • ${formatCurrency(metrics.received_value)} realized`)}
        </div>
        <div class="grid-2">
          <article class="workspace-card">
            <div class="section-top">
              <h3>Company snapshot</h3>
              ${badge(scopeLabel(state.company.analysis_scope || "current_entity"), "neutral")}
            </div>
            <dl class="detail-list">
              <div><dt>Entity</dt><dd>${titleCase(state.company.entity_type)}</dd></div>
              ${state.company.legal_name ? `<div><dt>Legal name</dt><dd>${escapeHtml(state.company.legal_name)}</dd></div>` : ""}
              <div><dt>Operating activity</dt><dd>${escapeHtml(activityLabel(state.company.operating_activity || "same_as_detected"))}</dd></div>
              <div><dt>Evaluation sector</dt><dd>${escapeHtml(titleCase(effectiveSector(state.company) || state.company.sector))}</dd></div>
              <div><dt>Turnover</dt><dd>${titleCase(state.company.annual_turnover)}</dd></div>
              <div><dt>Employees</dt><dd>${titleCase(state.company.employee_count)}</dd></div>
              <div><dt>Founded</dt><dd>${escapeHtml(String(state.company.founded_year))}</dd></div>
              ${state.company.website_domain ? `<div><dt>Website</dt><dd>${escapeHtml(state.company.website_domain)}</dd></div>` : ""}
              ${state.company.group_sector_hint ? `<div><dt>Parent-group signal</dt><dd>${escapeHtml(titleCase(state.company.group_sector_hint))}</dd></div>` : ""}
            </dl>
          </article>
          <article class="workspace-card">
            <div class="section-top">
              <h3>Scheme utilisation</h3>
              ${badge(`${metrics.open_scheme_count} open schemes`, "info")}
            </div>
            <dl class="detail-list">
              <div><dt>Untapped value</dt><dd class="mono">${formatCurrency(metrics.potential)}</dd></div>
              <div><dt>In-progress value</dt><dd class="mono">${formatCurrency(metrics.applied_value)}</dd></div>
              <div><dt>Realized value</dt><dd class="mono">${formatCurrency(metrics.received_value)}</dd></div>
              <div><dt>Total value at stake</dt><dd class="mono">${formatCurrency(metrics.total_value_at_stake)}</dd></div>
            </dl>
            <div class="tag-cloud">
              ${state.company.is_msme ? '<span class="tag">MSME</span>' : ""}
              ${state.company.is_startup_india ? '<span class="tag">Startup India</span>' : ""}
              ${state.company.is_dpiit ? '<span class="tag">DPIIT</span>' : ""}
              ${state.company.is_export_oriented ? '<span class="tag">Export oriented</span>' : ""}
              ${!state.company.is_msme && !state.company.is_startup_india && !state.company.is_dpiit && !state.company.is_export_oriented ? '<span class="tag tag-muted">No special flags</span>' : ""}
            </div>
            ${
              state.company.group_sector_hint
                ? `<div class="note-block">Some financing or subsidy programs may sit better with the parent or legal entity than the current brand-unit scope. Use the company view to explore a separate-entity scenario if you need to compare them.</div>`
                : ""
            }
          </article>
        </div>
        ${
          taxItems.length
            ? `
              <article class="workspace-card">
                <div class="section-top">
                  <div>
                    <h3>GST & tax review</h3>
                    <p class="muted">These items are separated because they usually depend on books, filings, and CA support.</p>
                  </div>
                  <button class="button button-ghost button-small" data-action="switch-view" data-view="tax">Open GST & Tax</button>
                </div>
                <div class="detail-grid">
                  <div><span>Items in review</span><strong>${escapeHtml(String(taxItems.length))}</strong></div>
                  <div><span>Overdue tax items</span><strong>${escapeHtml(String(taxItems.filter((item) => item.status === "overdue").length))}</strong></div>
                  <div><span>GSTIN</span><strong>${escapeHtml(state.company.gstin || "Not confirmed yet")}</strong></div>
                  <div><span>PAN</span><strong>${escapeHtml(state.company.pan || "Not confirmed yet")}</strong></div>
                </div>
              </article>
            `
            : ""
        }
        <article class="workspace-card">
          <div class="section-top">
            <h3>Next operational obligations</h3>
            <button class="button button-ghost button-small" data-action="switch-view" data-view="compliance">Open compliance</button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Obligation</th>
                  <th>Due</th>
                  <th>Status</th>
                  <th>Penalty/day</th>
                  <th>Exposure</th>
                </tr>
              </thead>
              <tbody>
                ${
                  upcoming.length
                    ? upcoming
                        .map(
                          (item) => `
                            <tr>
                              <td><strong>${escapeHtml(item.name)}</strong><span class="cell-subtle">${escapeHtml(item.description)}</span></td>
                              <td class="mono">${formatDate(item.due_date)}</td>
                              <td>${badge(titleCase(item.status), statusTone(item.status))}</td>
                              <td class="mono">${formatCurrency(item.penalty_per_day)}</td>
                              <td class="mono">${item.status === "overdue" ? formatCurrency(obligationExposure(item)) : `${formatCurrency(item.penalty_per_day)} if missed`}</td>
                            </tr>
                          `
                        )
                        .join("")
                    : '<tr><td colspan="5"><div class="empty-inline">No current operational obligations.</div></td></tr>'
                }
              </tbody>
            </table>
          </div>
        </article>
      </section>
    `;
  }

  function filterButton(scope, value, label, active) {
    return `<button class="filter-pill ${active === value ? "active" : ""}" data-action="filter-${scope}" data-value="${value}">${escapeHtml(label)}</button>`;
  }

  function renderCompliance() {
    const items = operationalObligations();
    return `
      <section class="stack">
        <div class="section-top">
          <div>
            <h3>Operational compliance</h3>
            <p class="muted">This view covers operating, labour, worker-condition, wage, ROC, environmental, and sector-linked obligations. GST and tax are separated into their own workflow.</p>
          </div>
          <div class="filter-row">
            ${filterButton("compliance", "all", "All", state.complianceFilter)}
            ${filterButton("compliance", "pending", "Pending", state.complianceFilter)}
            ${filterButton("compliance", "overdue", "Overdue", state.complianceFilter)}
            ${filterButton("compliance", "filed", "Filed", state.complianceFilter)}
          </div>
        </div>
        <div class="toolbar">
          <button class="button button-ghost button-small" data-action="switch-view" data-view="tax">Open GST & Tax review</button>
        </div>
        <article class="workspace-card">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Obligation</th>
                  <th>Category</th>
                  <th>Due</th>
                  <th>Days</th>
                  <th>Penalty/day</th>
                  <th>Exposure</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${
                  items.length
                    ? items
                        .map((item) => {
                          const delta = daysUntil(item.due_date);
                          return `
                            <tr>
                              <td><strong>${escapeHtml(item.name)}</strong><span class="cell-subtle">${escapeHtml(item.description)}</span></td>
                              <td>${badge(titleCase(item.category), "neutral")}</td>
                              <td class="mono">${formatDate(item.due_date)}</td>
                              <td class="mono">${delta >= 0 ? `${delta} days` : `${Math.abs(delta)} overdue`}</td>
                              <td class="mono">${formatCurrency(item.penalty_per_day)}</td>
                              <td class="mono">${item.status === "overdue" ? formatCurrency(obligationExposure(item)) : `${formatCurrency(item.penalty_per_day)} if missed`}</td>
                              <td>${badge(titleCase(item.status), statusTone(item.status))}</td>
                              <td>
                                <div class="table-actions">
                                  ${
                                    item.status !== "filed"
                                      ? `<button class="button button-secondary button-small" data-action="obligation-filed" data-id="${item.id}">Mark filed</button>`
                                      : `<button class="button button-ghost button-small" data-action="obligation-reopen" data-id="${item.id}">Reopen</button>`
                                  }
                                </div>
                              </td>
                            </tr>
                          `;
                        })
                        .join("")
                    : '<tr><td colspan="8"><div class="empty-inline">No operational obligations in this filter.</div></td></tr>'
                }
              </tbody>
            </table>
          </div>
        </article>
      </section>
    `;
  }

  function schemeReviewChecklist(item) {
    const checklist = ["Entity incorporation details and authorized signatory details"];
    if (state.company?.pan) checklist.push("PAN confirmation");
    if (state.company?.gstin) checklist.push("GST registration details");
    if (item.template_id === "cgtmse" || item.template_id === "treds") checklist.push("Udyam / MSME registration evidence");
    if (item.template_id === "startup-tax" || item.template_id === "seed-fund") checklist.push("DPIIT recognition proof");
    if (item.template_id === "mai") checklist.push("IEC and export documentation");
    if (item.template_id === "aif") checklist.push("Project report for agriculture or post-harvest infrastructure");
    if (item.template_id === "aif" || item.scheme_type === "loan") checklist.push("Lender discussion pack and projected financing requirement");
    if (item.template_id === "aif") checklist.push("Land title or lease proof, with the exact project location and LGD-backed location details");
    if (item.template_id === "aif") checklist.push("List of any existing or proposed AIF projects under the same applicant entity");
    if (item.template_id === "aif") checklist.push("Evidence that the project is primary processing or integrated primary + secondary, not standalone secondary processing");
    if (item.scheme_type === "tax_benefit") checklist.push("CA-led tax eligibility review and financial statements");
    if (effectiveSector(state.company) === "food_processing") checklist.push("FSSAI registration or license details");
    if (state.company?.serves_defence_sector || ["drdo-tdf", "telangana-aerospace-support"].includes(item.template_id)) {
      checklist.push("Industrial licence status or defence-item classification note");
      checklist.push("Plant or facility approvals and manufacturing-site summary");
      checklist.push("Capability note covering defence or aerospace products, components, or subsystems");
    }
    if (item.template_id === "drdo-tdf") {
      checklist.push("Technical proposal, development scope, and IP / collaboration summary");
    }
    return Array.from(new Set(checklist));
  }

  function aifOfficialClauses() {
    return [
      "3% interest subvention applies only up to ₹2 Cr of loan value, for a maximum of 7 years.",
      "Multiple projects at one location still share an overall ₹2 Cr cap at that location.",
      "Projects in different locations can each be considered separately, provided each location is distinct.",
      "For private-sector applicants such as agri-entrepreneurs and start-ups, the scheme caps the count at 25 projects.",
      "Standalone secondary processing is not eligible under the official guideline.",
      "For tea, coffee, and cocoa, eligible primary processing explicitly includes activities like withering, rolling, fermentation, drying, sorting, packaging, and tea bags.",
    ];
  }

  function schemeReviewQuestions(item) {
    const prompts = [];
    if (item.template_id === "aif") {
      prompts.push("Is the eligible project sitting in the parent agriculture/processing business or should a separate project vehicle be assessed?");
      prompts.push("Does the project involve post-harvest management, storage, cold chain, logistics, primary processing, or another qualifying agriculture infrastructure activity?");
    }
    if (item.template_id === "startup-tax" || item.template_id === "seed-fund") {
      prompts.push("Would the exact entity applying still qualify as an early-stage DPIIT-recognised startup after parent-entity ownership is considered?");
    }
    if (item.scheme_type === "loan") {
      prompts.push("What loan amount and use of funds are being considered?");
    }
    if (item.scheme_type === "tax_benefit") {
      prompts.push("Do the books and filings support the tax position, and does a CA need to review it before proceeding?");
    }
    return prompts;
  }

  function isNewEntityOpportunity(item) {
    return (item.unlock_actions || []).some((action) => /new[- ]entity|newco|separate-entity/i.test(action));
  }

  function selectedOfficialScheme() {
    return state.officialSchemeMatches.find((item) => item.scheme_id === state.selectedOfficialSchemeId) || null;
  }

  function parseOfficialSchemeFields(item) {
    if (!item?.raw_json) return {};
    try {
      const parsed = JSON.parse(item.raw_json);
      return parsed.fields || {};
    } catch (_error) {
      return {};
    }
  }

  function officialSourcesForMappedScheme(item) {
    const sourceIds = new Set(["myscheme", "mca_master_data"]);
    if (item.template_id === "mai" || /export/i.test(item.name)) sourceIds.add("dgft_export_schemes");
    if (item.template_id === "startup-tax" || item.template_id === "seed-fund" || item.scheme_type === "tax_benefit") sourceIds.add("startup_india_recognition");
    if (item.template_id === "cgtmse" || item.template_id === "treds" || item.template_id === "samadhaan") sourceIds.add("udyam_verification");
    if (state.company?.serves_defence_sector || ["drdo-tdf", "telangana-aerospace-support"].includes(item.template_id)) {
      sourceIds.add("dpiit_industrial_license_services");
    }
    if (item.template_id === "drdo-tdf" || state.company?.serves_defence_sector) {
      sourceIds.add("drdo_tdf_official");
    }
    if (state.company?.state === "Telangana" && (effectiveSector(state.company) === "manufacturing" || state.company?.serves_defence_sector || item.template_id === "telangana-aerospace-support")) {
      sourceIds.add("invest_telangana_tsipass");
    }
    if (state.company?.handles_food_products || effectiveSector(state.company) === "food_processing") {
      sourceIds.add("fssai_licensing");
      if (state.company?.fssai_license_number) sourceIds.add("fssai_license_verify");
    }
    if (item.scheme_type === "tax_benefit") sourceIds.add("gst_taxpayer_search");
    return state.officialSources.filter((source) => sourceIds.has(source.source_id));
  }

  function advisorLabelForScheme(item) {
    if (!item) return "CA advisor";
    if (item.scheme_type === "tax_benefit" || /tax/i.test(item.name)) return "Direct tax CA";
    if (state.company?.serves_defence_sector || /defence|defense|aerospace|drdo|industrial license/i.test(`${item.name} ${item.benefit_value}`)) {
      return "Defence manufacturing and industrial licensing advisor";
    }
    if (item.scheme_type === "loan" || /credit|loan|msme/i.test(item.name)) return "MSME finance and subsidy CA";
    if (item.scheme_type === "r_and_d") return "R&D grant and incentive advisor";
    if (/export|dgft|trade/i.test(item.name)) return "Export compliance CA";
    if (state.company?.handles_food_products || effectiveSector(state.company) === "food_processing") return "Food business compliance and subsidy CA";
    return "Scheme and subsidy specialist CA";
  }

  function officialReviewQuestions(item) {
    const fields = parseOfficialSchemeFields(item);
    const prompts = [];
    if (state.company?.analysis_scope === "brand_unit" && state.company?.group_sector_hint) {
      prompts.push("Confirm whether the applying entity should be the current brand unit or the parent/legal entity.");
    }
    if ((item.beneficiary_states || []).length && !item.beneficiary_states.includes("All")) {
      prompts.push(`Confirm the applying entity is actually based or operating in ${item.beneficiary_states.join(", ")}.`);
    }
    if (fields.schemeFor) {
      prompts.push(`The official listing is framed for ${fields.schemeFor.toLowerCase()}. Confirm the program is available to a business entity before acting.`);
    }
    prompts.push("Review the official source before treating the opportunity as confirmed; public listing screens can omit late-stage conditions.");
    return prompts;
  }

  function relatedOfficialMatchesForScheme(item) {
    const sourceWords = new Set(
      String(item.name || "")
        .toLowerCase()
        .replace(/[^a-z0-9 ]+/g, " ")
        .split(/\s+/)
        .filter((word) => word.length > 4 && !["scheme", "india", "credit", "grant"].includes(word))
    );
    return state.officialSchemeMatches
      .filter((official) => {
        const haystack = `${official.scheme_name} ${official.brief_description} ${(official.tags || []).join(" ")}`.toLowerCase();
        return Array.from(sourceWords).some((word) => haystack.includes(word));
      })
      .slice(0, 3);
  }

  function applicationChecklist(item, source = "mapped") {
    if (source === "official") {
      const base = ["Certificate of incorporation or entity registration details", "Authorized signatory details", "Current company profile and business activity note"];
      if ((item.beneficiary_states || []).length && !item.beneficiary_states.includes("All")) base.push("State-specific operating proof if required by the official scheme");
      if (/export|trade|international/i.test(`${item.scheme_name} ${(item.tags || []).join(" ")}`)) base.push("IEC and export documentation");
      if (/food|tea|fssai/i.test(`${item.scheme_name} ${item.brief_description}`) || state.company?.handles_food_products) base.push("FSSAI registration or license details");
      if (/defence|defense|aerospace|drdo|industrial licen[cs]e/i.test(`${item.scheme_name} ${item.brief_description} ${(item.tags || []).join(" ")}`) || state.company?.serves_defence_sector) {
        base.push("Industrial licence status or defence-item classification note");
        base.push("Plant or facility approvals and manufacturing-site summary");
      }
      return Array.from(new Set(base));
    }
    return schemeReviewChecklist(item);
  }

  function activeApplicationScheme() {
    if (!state.applicationSchemeId) return null;
    return state.applicationSchemeSource === "official"
      ? selectedOfficialScheme()
      : state.schemes.find((item) => item.id === state.applicationSchemeId) || null;
  }

  function selectedOpportunity() {
    return state.schemeOpportunities.find((item) => item.template_id === state.selectedOpportunityId) || null;
  }

  function activeReviewContext() {
    const mapped = state.schemes.find((item) => item.id === state.selectedSchemeId) || null;
    if (mapped) return { kind: "mapped", item: mapped };
    const official = selectedOfficialScheme();
    if (official) return { kind: "official", item: official };
    const opportunity = selectedOpportunity();
    if (opportunity) return { kind: "opportunity", item: opportunity };
    return null;
  }

  function mappedReviewAssessmentFor(item) {
    if (!item || !state.reviewAssessment) return null;
    return state.reviewAssessment.scheme_id === item.id ? state.reviewAssessment : null;
  }

  function reviewQuestionsForContext(kind, item) {
    const mappedAssessment = kind === "mapped" ? mappedReviewAssessmentFor(item) : null;
    if (mappedAssessment?.questions?.length) {
      return mappedAssessment.questions;
    }
    const questions = [];
    if (kind === "opportunity") {
      questions.push({
        key: "structural_change_interest",
        label: "Would the company realistically consider making a structural or registration change for this scheme?",
        options: [
          ["yes", "Yes, worth exploring"],
          ["maybe", "Maybe, needs modelling"],
          ["no", "No, not realistic"],
        ],
      });
    }
    if (kind !== "mapped" && state.company?.analysis_scope === "brand_unit" && state.company?.group_sector_hint) {
      questions.push({
        key: "correct_entity",
        label: "Should this scheme be reviewed for the current brand unit, or for the parent/legal entity?",
        options: [
          ["brand", "Current brand or business unit"],
          ["parent", "Parent or legal entity"],
          ["separate", "Separate new entity scenario"],
        ],
      });
    }
    if (kind === "official" && (item.beneficiary_states || []).length && !item.beneficiary_states.includes("All")) {
      questions.push({
        key: "state_fit",
        label: `Is the applying entity actually based or operating in ${item.beneficiary_states.join(", ")}?`,
        options: [
          ["yes", "Yes"],
          ["no", "No"],
          ["unsure", "Not sure"],
        ],
        blocking_values: ["no"],
        uncertain_values: ["unsure"],
        blocking_message: "The current entity does not satisfy the scheme's state condition.",
        warning_message: "State fit still needs confirmation before this scheme should be treated as usable.",
        success_message: "The state condition appears to be satisfied.",
      });
    }
    if (kind === "official" && parseOfficialSchemeFields(item).schemeFor) {
      questions.push({
        key: "entity_allowed",
        label: "Does the official listing appear available to a company entity, not just an individual applicant?",
        options: [
          ["yes", "Yes or likely yes"],
          ["unsure", "Not sure yet"],
          ["no", "No"],
        ],
        blocking_values: ["no"],
        uncertain_values: ["unsure"],
        blocking_message: "The official listing looks more individual-facing than company-facing, so do not treat it as company-eligible yet.",
        warning_message: "Applicant-type fit still needs confirmation from the official listing.",
        success_message: "The listing looks directionally usable for a company applicant.",
      });
    }
    (item.review_questions || []).forEach((question) => questions.push(question));
    if (!questions.length) {
      questions.push({
        key: "intent_ready",
        label: "Do you want to test this against the current company profile now?",
        options: [
          ["yes", "Yes"],
          ["later", "Later"],
        ],
      });
    }
    const deduped = [];
    const seenKeys = new Set();
    questions.forEach((question) => {
      if (seenKeys.has(question.key)) return;
      seenKeys.add(question.key);
      deduped.push(question);
    });
    return deduped;
  }

  function evaluateStructuredReviewQuestions(questions, answers) {
    const blockers = [];
    const warnings = [];
    const successes = [];
    (questions || []).forEach((question) => {
      const answer = answers?.[question.key];
      if (!answer) return;
      if ((question.blocking_values || []).includes(answer)) {
        if (question.blocking_message) blockers.push(question.blocking_message);
        return;
      }
      if ((question.uncertain_values || []).includes(answer)) {
        if (question.warning_message) warnings.push(question.warning_message);
        return;
      }
      if (question.success_message) successes.push(question.success_message);
    });
    return { blockers, warnings, successes };
  }

  function readReviewAnswers() {
    const form = document.querySelector(".review-form");
    if (!form) return;
    const nextAnswers = { ...state.reviewAnswers };
    for (const element of Array.from(form.elements)) {
      if (!element.name) continue;
      nextAnswers[element.name] = element.value;
    }
    state.reviewAnswers = nextAnswers;
  }

  function reviewOutcomeForContext(kind, item) {
    const answers = state.reviewAnswers || {};
    const financial = schemeFinancialSummary(item);
    const mappedAssessment = kind === "mapped" ? mappedReviewAssessmentFor(item) : null;
    if (mappedAssessment?.review_verdict) {
      return {
        verdict: mappedAssessment.review_verdict,
        tone: mappedAssessment.review_tone || "warning",
        message: mappedAssessment.review_message || (financial.primary ? `Current value view: ${financial.primary}.` : ""),
      };
    }
    const questions = reviewQuestionsForContext(kind, item);
    const structuredAssessment = evaluateStructuredReviewQuestions(questions, answers);
    if (kind === "opportunity") {
      if (answers.structural_change_interest === "no") {
        return {
          verdict: "Not worth pursuing right now",
          tone: "neutral",
          message: "This stays a strategic idea only unless the company genuinely wants to change structure, registrations, or operating model.",
        };
      }
      return {
        verdict: "Strategic upside worth modelling",
        tone: "warning",
        message: `This is not usable today, but it could unlock ${schemeValueNarrative(item)} if the required changes are realistic.`,
      };
    }

    if (item.template_id === "stand-up-india") {
      if (["women", "scst", "both"].includes(answers.founder_route)) {
        return {
          verdict: "Founder route looks available",
          tone: "success",
          message: `This looks viable if the applicant is prepared under a qualifying founder route. Financial access currently reads as ${financial.primary}.`,
        };
      }
    }

    if (item.template_id === "aif") {
      if (answers.aif_location_pattern === "single_location") {
        return {
          verdict: "Usable, but capped at one-location economics",
          tone: "warning",
          message: "AIF can still work here, but multiple projects at the same location share one overall ₹2 Cr interest-subvention cap. The product should value this on the capped benefit, not per asset.",
        };
      }
      if (answers.aif_location_pattern === "different_locations") {
        return {
          verdict: "Potentially strong fit if locations are distinct",
          tone: "success",
          message: "Different locations can each be considered separately under the official guideline, provided they are genuinely distinct project locations. That makes this materially more valuable than a one-location setup.",
        };
      }
      if (answers.aif_location_pattern === "apmc_multi_type") {
        return {
          verdict: "Only strong if the applicant route is APMC",
          tone: "warning",
          message: "The multi-infrastructure, same-market-area exception is framed for APMCs. Treat this as usable only if the applicant actually fits that route.",
        };
      }
    }

    if (answers.correct_entity === "parent") {
      return {
        verdict: "Better aligned to the parent or legal entity",
        tone: "warning",
        message: `The benefit may still be available, but it likely belongs with the parent/legal entity rather than the current brand-unit scope.`,
      };
    }
    if (answers.correct_entity === "separate") {
      return {
        verdict: "Better suited to a separate entity setup",
        tone: "warning",
        message: `This looks more viable in a separate-entity scenario than under the currently assessed entity. Expected value view: ${schemeValueNarrative(item)}.`,
      };
    }
    if (structuredAssessment.blockers.length) {
      return {
        verdict: kind === "opportunity" ? "Not usable until the missing conditions change" : "Not usable on the current answers",
        tone: "danger",
        message: `${structuredAssessment.blockers[0]} ${financial.primary ? `Current value view: ${financial.primary}.` : ""}`.trim(),
      };
    }
    if (structuredAssessment.warnings.length) {
      return {
        verdict: kind === "opportunity" ? "Promising, but still conditional" : "Still needs confirmation",
        tone: "warning",
        message: `${structuredAssessment.warnings[0]} ${financial.primary ? `Current value view: ${financial.primary}.` : ""}`.trim(),
      };
    }
    if (item.status === "eligible") {
      return {
        verdict: "Likely usable now",
        tone: "success",
        message: `On the current information, this looks actionable for the company, subject to official-source and document review. Expected value view: ${schemeValueNarrative(item)}.`,
      };
    }
    if (item.status === "maybe") {
      return {
        verdict: "Potentially usable after confirmation",
        tone: "warning",
        message: `This looks promising, but it still needs a tighter entity/document check before being treated as truly eligible. Expected value view: ${schemeValueNarrative(item)}.`,
      };
    }
    return {
      verdict: "Worth official review",
      tone: "info",
      message: `This looks relevant enough to review on official sources. The benefit currently reads as ${schemeValueNarrative(item)} for this company profile.`,
    };
  }

  function renderReviewOverlay() {
    if (state.mode !== "workspace") return "";
    const context = activeReviewContext();
    if (!context) return "";

    const { kind, item } = context;
    const step = state.reviewStep || 1;
    const stepLabels = kind === "opportunity"
      ? ["Benefit", "What must change", "Value unlocked", "Next steps"]
      : ["Benefit", "Eligibility check", "Fit and value", "Activation plan", "CA support"];
    const maxStep = stepLabels.length;
    const advisor = advisorLabelForScheme(item);
    const officialFields = kind === "official" ? parseOfficialSchemeFields(item) : {};
    const questions = reviewQuestionsForContext(kind, item);
    const outcome = reviewOutcomeForContext(kind, item);
    const mappedAssessment = kind === "mapped" ? mappedReviewAssessmentFor(item) : null;
    const reviewClauses = mappedAssessment?.clauses || item.review_clauses || [];
    const reviewIssues = mappedAssessment
      ? [...(mappedAssessment.unmet_conditions || []), ...(mappedAssessment.remaining_checks || [])]
      : item.blockers || [];
    const activationSteps = mappedAssessment?.activation_steps || [];
    const officialRoute = kind === "mapped" ? officialSourcesForMappedScheme(item) : [];
    const relatedOfficial = kind === "mapped" ? relatedOfficialMatchesForScheme(item) : [];
    const checklist = applicationChecklist(item, kind === "official" ? "official" : "mapped");
    const financial = schemeFinancialSummary(item);

    let body = "";
    if (step === 1) {
      body = `
        <div class="review-stage">
          <div class="review-hero">
            ${iconBadge(kind === "official" ? "official" : kind === "opportunity" ? "spark" : "scheme", kind === "opportunity" ? "warning" : kind === "official" ? "info" : "brand")}
            <div>
              <p class="review-kicker">${kind === "official" ? "Official scheme review" : kind === "opportunity" ? "Strategic path review" : "Company-mapped scheme review"}</p>
              <h3>${escapeHtml(kind === "official" ? item.scheme_name : item.name)}</h3>
              <p class="muted">${escapeHtml(kind === "official" ? (item.ministry || "Official source") : item.ministry)}${kind === "official" && item.level ? ` • ${escapeHtml(item.level)}` : ""}</p>
            </div>
          </div>
          <div class="grid-2">
            <article class="info-panel">
              <strong>What the benefit is</strong>
              <p>${escapeHtml(kind === "official" ? (item.brief_description || "Official summary unavailable.") : item.benefit_value)}</p>
              <p class="muted">For ${escapeHtml(state.company?.name || "this company")}, the question is whether this benefit belongs to the current entity, the parent/legal entity, or a more suitable separate-entity setup.</p>
            </article>
            <article class="info-panel">
              <strong>${escapeHtml(financial.title)}</strong>
              <p class="review-value ${financial.tone === "money" || /₹|\d/.test(financial.primary) ? "mono" : ""}">${escapeHtml(financial.primary)}</p>
              ${financial.secondary ? `<p class="muted">${escapeHtml(financial.secondary)}</p>` : ""}
              <p class="muted">${kind === "opportunity" ? "Value that could open up if the required changes are realistic." : "Shown conservatively before final official verification and documentation review."}</p>
              ${
                item.source_url
                  ? `<a class="button button-ghost button-small review-link-button" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">Official page</a>`
                  : ""
              }
            </article>
          </div>
          ${reviewClauses.length ? `<article class="info-panel"><strong>Official clauses the product is checking</strong><ul class="reason-list">${reviewClauses.map((clause) => `<li>${escapeHtml(clause)}</li>`).join("")}</ul></article>` : ""}
          ${
            kind === "official" && item.reasons?.length
              ? `<article class="info-panel"><strong>Why this official program surfaced for this company</strong><ul class="reason-list">${item.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul></article>`
              : ""
          }
          ${
            kind !== "official" && item.reasons?.length
              ? `<article class="info-panel"><strong>Why the platform mapped it</strong><ul class="reason-list">${item.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul></article>`
              : ""
          }
        </div>
      `;
    } else if (step === 2) {
      body = `
        <div class="review-stage">
          <article class="info-panel">
            <strong>${kind === "opportunity" ? "What would need to change" : "Quick eligibility check"}</strong>
            <p class="muted">${kind === "opportunity" ? "This is not for immediate use. First decide whether the required changes are commercially realistic." : "Answer a few focused questions so the product can judge whether this is really worth pursuing for this company."}</p>
          </article>
          <form class="review-form stack">
            ${questions
              .map((question) => `
                <label class="field field-card">
                  <span>${escapeHtml(question.label)}</span>
                  <select name="${escapeHtml(question.key)}">
                    <option value="" ${state.reviewAnswers[question.key] ? "" : "selected"}>Select an answer</option>
                    ${(question.options || [])
                      .map(([value, label]) => `<option value="${escapeHtml(value)}" ${state.reviewAnswers[question.key] === value ? "selected" : ""}>${escapeHtml(label)}</option>`)
                      .join("")}
                  </select>
                </label>
              `)
              .join("")}
          </form>
          ${state.reviewLoading ? '<div class="empty-inline">Checking the scheme conditions against the company profile...</div>' : ""}
          ${
            kind === "opportunity" && item.unlock_actions?.length
              ? `<article class="info-panel"><strong>Likely unlock actions</strong><ul class="reason-list">${item.unlock_actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul></article>`
              : ""
          }
        </div>
      `;
    } else if (step === 3) {
      body = `
        <div class="review-stage">
          <article class="outcome-card ${outcome.tone}">
            <span class="outcome-kicker">Assessment outcome</span>
            <strong>${escapeHtml(outcome.verdict)}</strong>
            <p>${escapeHtml(outcome.message)}</p>
          </article>
          <div class="grid-2">
            <article class="info-panel">
              <strong>What this means for the company</strong>
              <ul class="reason-list">
                <li>${escapeHtml(financial.title)}: ${escapeHtml(financial.primary)}</li>
                ${financial.secondary ? `<li>Value note: ${escapeHtml(financial.secondary)}</li>` : ""}
                <li>Assessment scope: ${escapeHtml(scopeLabel(state.company.analysis_scope || "current_entity"))}</li>
                <li>Evaluation sector: ${escapeHtml(titleCase(effectiveSector(state.company) || state.company.sector))}</li>
                <li>State: ${escapeHtml(state.company.state || "To confirm")}</li>
              </ul>
            </article>
            <article class="info-panel">
              <strong>${kind === "opportunity" ? "Current blockers" : "What still needs checking"}</strong>
              ${
                reviewIssues.length
                  ? `<ul class="reason-list">${reviewIssues.map((blocker) => `<li>${escapeHtml(blocker)}</li>`).join("")}</ul>`
                  : '<p class="muted">No hard blockers are showing right now beyond official verification and documentation review.</p>'
              }
            </article>
          </div>
          ${(mappedAssessment?.uncertainty || item.uncertainty) ? `<div class="note-block">${escapeHtml(mappedAssessment?.uncertainty || item.uncertainty)}</div>` : ""}
        </div>
      `;
    } else if (step === 4) {
      body = `
        <div class="review-stage">
          <article class="info-panel">
            <strong>${kind === "opportunity" ? "How to activate this strategic path" : "How to activate this scheme"}</strong>
            ${
              kind === "opportunity"
                ? `<ul class="reason-list">${(item.unlock_actions || []).map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>`
                : activationSteps.length
                  ? `<ul class="reason-list">${activationSteps.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>`
                  : `<p class="muted">Use the official route below and get the paperwork ready before treating the application as live.</p>`
            }
          </article>
          <div class="grid-2">
            <article class="info-panel">
              <strong>Paperwork to prepare first</strong>
              <ul class="reason-list">${checklist.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul>
            </article>
            <article class="info-panel">
              <strong>Official route and checks</strong>
              ${
                kind === "official"
                  ? `<ul class="reason-list"><li><a class="link-inline" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">Open the official myScheme page</a></li>${officialReviewQuestions(item).map((question) => `<li>${escapeHtml(question)}</li>`).join("")}</ul>`
                  : officialRoute.length
                    ? `<ul class="reason-list">${officialRoute.map((source) => `<li><a class="link-inline" href="${escapeHtml(source.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(source.name)}</a> — ${escapeHtml(source.description)}</li>`).join("")}</ul>`
                    : '<p class="muted">No linked official route has been attached yet.</p>'
              }
            </article>
          </div>
          ${
            relatedOfficial.length
              ? `<article class="info-panel"><strong>Related official listings</strong><ul class="reason-list">${relatedOfficial.map((related) => `<li><button class="link-button" data-action="open-official-scheme-detail" data-id="${related.scheme_id}">${escapeHtml(related.scheme_name)}</button></li>`).join("")}</ul></article>`
              : ""
          }
        </div>
      `;
    } else {
      body = `
        <div class="review-stage">
          <article class="info-panel">
            <strong>Would you like specialist help?</strong>
            <p>${escapeHtml(advisor)} is the best next handoff if you want support validating fit, preparing documents, or structuring the application correctly.</p>
          </article>
          <div class="application-actions">
            <button class="button button-secondary" data-action="connect-ca-expert" data-scheme-name="${escapeHtml(kind === "official" ? item.scheme_name : item.name)}" data-advisor="${escapeHtml(advisor)}">Prepare CA handoff</button>
            ${
              kind === "official"
                ? `<a class="button button-primary" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">Open official source</a>`
                : `<button class="button button-primary" data-action="confirm-scheme-application" data-id="${escapeHtml(item.id)}">Mark application started</button>`
            }
          </div>
        </div>
      `;
    }

    return `
      <div class="modal-shell">
        <div class="modal-card">
          <div class="section-top">
            <div class="topbar-left">
              <button class="button button-ghost button-small home-button" data-action="go-home">Home</button>
              <div class="topbar-title-block">
                <p class="review-kicker">Guided scheme review</p>
                <h3>${escapeHtml(kind === "official" ? item.scheme_name : item.name)}</h3>
              </div>
            </div>
            <button class="button button-ghost button-small" data-action="close-review-overlay">Close</button>
          </div>
          <div class="step-row review-steps">
            ${stepLabels.map((label, index) => `<span class="step-pill ${step === index + 1 ? "active" : ""}">${index + 1}. ${escapeHtml(label)}</span>`).join("")}
          </div>
          ${body}
          <div class="toolbar modal-footer">
            ${step > 1 ? '<button class="button button-ghost" data-action="prev-review-step">Back</button>' : ""}
            ${
              step < maxStep
                ? `<button class="button button-primary" data-action="next-review-step" data-max-step="${maxStep}" ${state.reviewLoading ? "disabled" : ""}>${state.reviewLoading && step === 2 ? "Checking…" : step === 1 ? "Check eligibility" : step === 2 ? "See fit and value" : step === 3 ? "See activation plan" : "Continue"}</button>`
                : '<button class="button button-ghost" data-action="close-review-overlay">Done</button>'
            }
          </div>
        </div>
      </div>
    `;
  }

  function renderTaxReview() {
    const items = taxObligations();
    return `
      <section class="stack">
        <div class="section-top">
          <div>
            <h3>GST & Tax review</h3>
            <p class="muted">These items usually need financial data, filing history, and CA support before the platform should mark them safe.</p>
          </div>
          <div class="tag-cloud">
            ${state.company?.gstin ? `<span class="tag">GSTIN confirmed</span>` : '<span class="tag tag-muted">GSTIN pending</span>'}
            ${state.company?.pan ? `<span class="tag">PAN confirmed</span>` : '<span class="tag tag-muted">PAN pending</span>'}
          </div>
        </div>
        <article class="workspace-card">
          <div class="detail-grid">
            <div><span>GSTIN</span><strong>${escapeHtml(state.company?.gstin || "Not provided yet")}</strong></div>
            <div><span>PAN</span><strong>${escapeHtml(state.company?.pan || "Not provided yet")}</strong></div>
            <div><span>TDS flag</span><strong>${state.company?.deducts_tds ? "Marked yes" : "Needs confirmation"}</strong></div>
            <div><span>Recommended owner</span><strong>Finance team / CA</strong></div>
          </div>
        </article>
        <article class="workspace-card">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Category</th>
                  <th>Due</th>
                  <th>Days</th>
                  <th>Penalty/day</th>
                  <th>Exposure</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                ${
                  items.length
                    ? items
                        .map((item) => {
                          const delta = daysUntil(item.due_date);
                          return `
                            <tr>
                              <td><strong>${escapeHtml(item.name)}</strong><span class="cell-subtle">${escapeHtml(item.description)}</span></td>
                              <td>${badge(titleCase(item.category), "neutral")}</td>
                              <td class="mono">${formatDate(item.due_date)}</td>
                              <td class="mono">${delta >= 0 ? `${delta} days` : `${Math.abs(delta)} overdue`}</td>
                              <td class="mono">${formatCurrency(item.penalty_per_day)}</td>
                              <td class="mono">${item.status === "overdue" ? formatCurrency(obligationExposure(item)) : `${formatCurrency(item.penalty_per_day)} if missed`}</td>
                              <td>${badge(titleCase(item.status), statusTone(item.status))}</td>
                              <td>
                                <div class="table-actions">
                                  ${
                                    item.status !== "filed"
                                      ? `<button class="button button-secondary button-small" data-action="obligation-filed" data-id="${item.id}">Mark reviewed / filed</button>`
                                      : `<button class="button button-ghost button-small" data-action="obligation-reopen" data-id="${item.id}">Reopen</button>`
                                  }
                                </div>
                              </td>
                            </tr>
                          `;
                        })
                        .join("")
                    : '<tr><td colspan="8"><div class="empty-inline">No GST or tax obligations in this filter.</div></td></tr>'
                }
              </tbody>
            </table>
          </div>
        </article>
      </section>
    `;
  }

  function renderSchemes() {
    const openSchemes = state.schemes.filter((item) => ["eligible", "maybe"].includes(item.status));
    const appliedSchemes = state.schemes.filter((item) => item.status === "applied");
    const realizedSchemes = state.schemes.filter((item) => item.status === "received");
    const officialMatchedTotal = state.officialSchemeMeta.matchedTotal || state.officialSchemeMatches.length || 0;
    const officialCachedTotal = state.officialSchemeMeta.cachedTotal || 0;
    const officialSyncedAt = state.officialSchemeMeta.lastSyncedAt
      ? formatDate(state.officialSchemeMeta.lastSyncedAt)
      : "";
    return `
      <section class="stack">
        <div class="section-top">
          <div>
            <h3>Scheme centre</h3>
            <p class="muted">Review what looks usable now, what official sources are surfacing, and which strategic changes could unlock more value.</p>
          </div>
          <div class="filter-row">
            ${filterButton("scheme", "all", "All", state.schemeFilter)}
            ${filterButton("scheme", "open", "Open", state.schemeFilter)}
            ${filterButton("scheme", "applied", "Applied", state.schemeFilter)}
            ${filterButton("scheme", "received", "Received", state.schemeFilter)}
          </div>
        </div>
        <div class="grid-4">
          ${metricCard("Open now", String(openSchemes.length), "Eligible or review-now programs")}
          ${metricCard("Applied", String(appliedSchemes.length), "Applications already in motion")}
          ${metricCard("Realized", formatCurrency(realizedSchemes.reduce((sum, item) => sum + Number(item.benefit_received_amount || 0), 0)), "Value already realized")}
          ${metricCard("Strategic upside", formatCurrency((state.schemeOpportunities || []).reduce((sum, item) => sum + Number(item.max_benefit_amount || 0), 0)), "Programs unlocked by real changes")}
        </div>
        ${renderAnalysisFocus()}
        <article class="workspace-card">
          <div class="section-top">
            <div>
              <h3>Current scheme recommendations</h3>
              <p class="muted">Everything below belongs in one journey: what already looks relevant for this company, plus official-source leads that still deserve guided review.</p>
            </div>
            ${badge(`${state.schemes.length + state.officialSchemeMatches.length} total leads`, "info")}
          </div>
          ${
            state.schemes.length
              ? `
                <div class="section-subhead">
                  <strong>${iconBadge("scheme")} Company-mapped schemes</strong>
                  <p class="muted">Higher-conviction programs that already look aligned to the current company profile.</p>
                </div>
              `
              : ""
          }
          <div class="cards-grid">
            ${
              state.schemes.length
                ? state.schemes
                    .map(
                      (item) => `
                        <article class="scheme-card interactive-card ${state.selectedSchemeId === item.id ? "active" : ""}" data-action="open-scheme-detail" data-id="${item.id}" role="button" tabindex="0">
                          <div class="section-top">
                            <div>
                              <div class="card-title-row">
                                ${iconBadge("scheme", "brand")}
                                <div>
                                  <h3>${escapeHtml(item.name)}</h3>
                                  <p class="muted">${escapeHtml(item.ministry)}</p>
                                </div>
                              </div>
                            </div>
                            ${badge(titleCase(item.status), statusTone(item.status))}
                          </div>
                          <div class="meta-row">
                            ${badge(titleCase(item.scheme_type), "neutral")}
                            ${renderSchemeValuePill(item)}
                          </div>
                          <div class="scheme-summary">
                            <strong>Benefit</strong>
                            <p>${escapeHtml(item.benefit_value)}</p>
                          </div>
                          ${renderFinancialSummary(item)}
                          ${item.reasons.length ? `<p class="muted">${escapeHtml(item.reasons[0])}</p>` : ""}
                          ${item.uncertainty ? `<div class="note-block">${escapeHtml(item.uncertainty)}</div>` : ""}
                          <div class="toolbar">
                            <button class="button button-ghost button-small" data-action="open-scheme-detail" data-id="${item.id}">Guided review</button>
                            ${
                              item.source_url
                                ? `<a class="button button-ghost button-small" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">Official page</a>`
                                : ""
                            }
                            ${
                              item.status === "eligible" || item.status === "maybe"
                                ? `<button class="button button-primary button-small" data-action="start-scheme-application" data-id="${item.id}" data-source="mapped">Start application</button>`
                                : ""
                            }
                            ${
                              item.status === "applied"
                                ? `<button class="button button-secondary button-small" data-action="scheme-receive" data-id="${item.id}">Mark received</button>`
                                : ""
                            }
                            ${
                              item.status === "received"
                                ? `<button class="button button-ghost button-small" data-action="scheme-reopen" data-id="${item.id}">Reopen</button>`
                                : ""
                            }
                          </div>
                        </article>
                      `
                    )
                    .join("")
                    : '<div class="empty-inline">No scheme records in this filter.</div>'
            }
          </div>
          ${
            state.officialSchemeMatches.length
              ? `
                <div class="section-subhead">
                  <strong>${iconBadge("official", "info")} Additional official-source leads</strong>
                  <p class="muted">These came from the live official catalog and still need company-specific guided review before they should be treated as truly usable.</p>
                </div>
                <div class="cards-grid">
                  ${state.officialSchemeMatches
                    .map(
                      (item) => `
                        <article class="scheme-card official-card interactive-card ${state.selectedOfficialSchemeId === item.scheme_id ? "active" : ""}" data-action="open-official-scheme-detail" data-id="${item.scheme_id}" role="button" tabindex="0">
                          <div class="section-top">
                            <div>
                              <div class="card-title-row">
                                ${iconBadge("official", "info")}
                                <div>
                                  <h3>${escapeHtml(item.scheme_name)}</h3>
                                  <p class="muted">${escapeHtml(item.ministry || "Official source")}</p>
                                </div>
                              </div>
                            </div>
                            ${badge(item.level || "Official", "info")}
                          </div>
                          <div class="meta-row">
                            ${item.scheme_close_date ? badge(`Closes ${formatDate(item.scheme_close_date)}`, "warning") : badge("No close date published", "success")}
                            ${renderSchemeValuePill(item)}
                          </div>
                          <div class="scheme-summary">
                            <strong>Benefit</strong>
                            <p>${escapeHtml(item.brief_description || "No official summary available.")}</p>
                          </div>
                          ${renderFinancialSummary(item)}
                          ${item.reasons?.length ? `<p class="muted">${escapeHtml(item.reasons[0])}</p>` : ""}
                          ${item.uncertainty ? `<div class="note-block">${escapeHtml(item.uncertainty)}</div>` : ""}
                          <div class="toolbar">
                            <button class="button button-ghost button-small" data-action="open-official-scheme-detail" data-id="${item.scheme_id}">Guided review</button>
                            ${
                              item.source_url
                                ? `<a class="button button-ghost button-small" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">Official page</a>`
                                : ""
                            }
                            <button class="button button-primary button-small" data-action="start-scheme-application" data-id="${item.scheme_id}" data-source="official">Prepare application</button>
                          </div>
                        </article>
                      `
                    )
                    .join("")}
                </div>
                <p class="muted">Showing ${officialMatchedTotal} matched official lead(s) from ${officialCachedTotal} cached official scheme record(s)${officialSyncedAt ? ` · last synced ${officialSyncedAt}` : ""}.</p>
              `
              : ""
          }
        </article>
        <article class="workspace-card">
          <div class="section-top">
            <div>
              <h3>Ways to unlock more savings</h3>
              <p class="muted">These schemes do not cleanly apply yet, but may become relevant if the company makes legitimate changes such as formal registrations, export setup, or a separate-entity structure.</p>
            </div>
            ${badge(`${state.schemeOpportunities.length || 0} strategic paths`, "neutral")}
          </div>
          ${
            state.schemeOpportunities.length
              ? `
                <div class="cards-grid">
                  ${state.schemeOpportunities
                    .map(
                      (item) => `
                        <article class="opportunity-card interactive-card" data-action="open-opportunity-detail" data-id="${item.template_id}" role="button" tabindex="0">
                          <div class="section-top">
                            <div>
                              <div class="card-title-row">
                                ${iconBadge("spark", "warning")}
                                <div>
                                  <h3>${escapeHtml(item.name)}</h3>
                                  <p class="muted">${escapeHtml(item.ministry)}</p>
                                </div>
                              </div>
                            </div>
                            ${badge("Strategic", "warning")}
                          </div>
                          <div class="meta-row">
                            ${badge(titleCase(item.scheme_type), "neutral")}
                            ${renderSchemeValuePill(item)}
                          </div>
                          <div class="scheme-summary">
                            <strong>Potential benefit</strong>
                            <p>${escapeHtml(item.benefit_value)}</p>
                          </div>
                          ${renderFinancialSummary(item)}
                          ${
                            item.blockers?.length
                              ? `<div><strong>Why it is blocked today</strong><ul class="reason-list">${item.blockers.map((blocker) => `<li>${escapeHtml(blocker)}</li>`).join("")}</ul></div>`
                              : ""
                          }
                          <div>
                            <strong>What would need to change</strong>
                            <ul class="reason-list">${(item.unlock_actions || []).map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>
                          </div>
                          ${item.uncertainty ? `<div class="note-block">${escapeHtml(item.uncertainty)}</div>` : ""}
                          <div class="toolbar">
                            <button class="button button-ghost button-small" data-action="open-opportunity-detail" data-id="${item.template_id}">Strategic review</button>
                            ${
                              item.source_url
                                ? `<a class="button button-ghost button-small" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer" onclick="event.stopPropagation()">Official page</a>`
                                : ""
                            }
                            ${isNewEntityOpportunity(item) ? '<button class="button button-secondary button-small" data-action="explore-newco-scenario">Explore separate-entity scenario</button>' : ""}
                          </div>
                        </article>
                      `
                    )
                    .join("")}
                </div>
              `
              : '<div class="empty-inline">No meaningful unlockable opportunities are showing for this profile right now.</div>'
          }
        </article>
      </section>
    `;
  }

  function renderCompanyDetails() {
    if (!state.company) return "";
    const verificationPlan = state.verificationPlan || { identifier_questions: [], verification_plan: [] };
    const readyChecks = verificationPlan.verification_plan.filter((item) => item.status === "ready").length;
    const manualChecks = verificationPlan.verification_plan.filter((item) => item.status === "manual_verification_required").length;
    return `
      <section class="stack">
        <article class="workspace-card">
          <div class="section-top">
            <h3>Company details</h3>
            ${badge(scopeLabel(state.company.analysis_scope || "current_entity"), "neutral")}
          </div>
          <div class="detail-grid">
            <div><span>Name</span><strong>${escapeHtml(state.company.name)}</strong></div>
            ${state.company.legal_name ? `<div><span>Legal entity</span><strong>${escapeHtml(state.company.legal_name)}</strong></div>` : ""}
            <div><span>Operating activity</span><strong>${escapeHtml(activityLabel(state.company.operating_activity || "same_as_detected"))}</strong></div>
            <div><span>Evaluation sector</span><strong>${escapeHtml(titleCase(effectiveSector(state.company) || state.company.sector))}</strong></div>
            <div><span>Location</span><strong>${escapeHtml(state.company.city)}, ${escapeHtml(state.company.state)}</strong></div>
            <div><span>Turnover</span><strong>${titleCase(state.company.annual_turnover)}</strong></div>
            <div><span>Employees</span><strong>${titleCase(state.company.employee_count)}</strong></div>
            <div><span>Founded</span><strong>${escapeHtml(String(state.company.founded_year))}</strong></div>
            ${state.company.group_sector_hint ? `<div><span>Parent-group signal</span><strong>${escapeHtml(titleCase(state.company.group_sector_hint))}</strong></div>` : ""}
          </div>
          <div class="toolbar">
            <button class="button button-secondary button-small" data-action="explore-newco-scenario">Explore separate-entity scenario</button>
          </div>
        </article>
        <article class="workspace-card">
          <div class="section-top">
            <h3>Decision guidance</h3>
          </div>
          ${
            state.company.group_sector_hint
              ? `<div class="note-block">This company has brand-level signals and parent-group ${escapeHtml(titleCase(state.company.group_sector_hint))} signals. Keep parent-entity financing and subsidy opportunities separate from brand-unit operating recommendations unless the same legal entity will actually apply.</div>`
              : `<div class="note-block">Use this view to confirm whether the analysis is evaluating the actual current entity or a scenario. The scope you choose changes which schemes and obligations should count.</div>`
          }
          <div class="tag-cloud">
            ${state.company.is_msme ? '<span class="tag">MSME registered</span>' : '<span class="tag tag-muted">No MSME</span>'}
            ${state.company.is_startup_india ? '<span class="tag">Startup India registered</span>' : '<span class="tag tag-muted">No Startup India</span>'}
            ${state.company.is_dpiit ? '<span class="tag">DPIIT recognised</span>' : '<span class="tag tag-muted">No DPIIT</span>'}
            ${state.company.is_export_oriented === true ? '<span class="tag">Export oriented</span>' : state.company.is_export_oriented === false ? '<span class="tag tag-muted">No export activity</span>' : '<span class="tag tag-muted">Export activity not confirmed</span>'}
            ${state.company.deducts_tds === true ? '<span class="tag">Deducts TDS</span>' : state.company.deducts_tds === false ? '<span class="tag tag-muted">No TDS deduction</span>' : '<span class="tag tag-muted">TDS flow not confirmed</span>'}
            ${state.company.has_factory_operations === true ? '<span class="tag">Factory operations</span>' : state.company.has_factory_operations === false ? '<span class="tag tag-muted">No factory operations</span>' : '<span class="tag tag-muted">Factory setup not confirmed</span>'}
            ${state.company.handles_food_products === true ? '<span class="tag">Food handling</span>' : state.company.handles_food_products === false ? '<span class="tag tag-muted">No food handling</span>' : '<span class="tag tag-muted">Food handling not confirmed</span>'}
            ${state.company.has_rd_collaboration === true ? '<span class="tag">R&D collaboration</span>' : state.company.has_rd_collaboration === false ? '<span class="tag tag-muted">No R&D collaboration</span>' : '<span class="tag tag-muted">R&D route not confirmed</span>'}
            ${state.company.has_new_hires === true ? '<span class="tag">Recent qualifying hires</span>' : state.company.has_new_hires === false ? '<span class="tag tag-muted">No recent qualifying hires</span>' : '<span class="tag tag-muted">Recent-hire status not confirmed</span>'}
            ${state.company.women_led === true ? '<span class="tag">Women-led</span>' : state.company.women_led === false ? '<span class="tag tag-muted">Not women-led</span>' : '<span class="tag tag-muted">Women-led route not confirmed</span>'}
            ${state.company.has_scst_founder === true ? '<span class="tag">SC/ST founder route</span>' : state.company.has_scst_founder === false ? '<span class="tag tag-muted">No SC/ST founder route</span>' : '<span class="tag tag-muted">SC/ST route not confirmed</span>'}
            ${state.company.serves_defence_sector === true ? '<span class="tag">Aerospace / defence</span>' : state.company.serves_defence_sector === false ? '<span class="tag tag-muted">Not marked aerospace / defence</span>' : '<span class="tag tag-muted">Aerospace / defence role not confirmed</span>'}
            ${state.company.uses_contract_labour === true ? '<span class="tag">Uses contract labour</span>' : state.company.uses_contract_labour === false ? '<span class="tag tag-muted">No contract labour</span>' : '<span class="tag tag-muted">Contract-labour use not confirmed</span>'}
            ${state.company.uses_interstate_migrant_workers === true ? '<span class="tag">Inter-state migrant workforce</span>' : state.company.uses_interstate_migrant_workers === false ? '<span class="tag tag-muted">No migrant workforce flagged</span>' : '<span class="tag tag-muted">Migrant-worker use not confirmed</span>'}
          </div>
        </article>
        <article class="workspace-card">
          <div class="section-top">
            <div>
              <h3>Official identifiers</h3>
              <p class="muted">Only official sources are used for live verification. PAN and GST live in the separate GST & Tax lane.</p>
            </div>
            ${badge(`${readyChecks} ready • ${manualChecks} manual`, "info")}
          </div>
          <div class="detail-grid">
            <div><span>CIN</span><strong>${escapeHtml(state.company.cin || "Not provided")}</strong></div>
            <div><span>LLPIN</span><strong>${escapeHtml(state.company.llpin || "Not provided")}</strong></div>
            <div><span>Udyam</span><strong>${escapeHtml(state.company.udyam_number || "Not provided")}</strong></div>
            <div><span>DPIIT certificate</span><strong>${escapeHtml(state.company.dpiit_certificate_number || "Not provided")}</strong></div>
            <div><span>FSSAI license</span><strong>${escapeHtml(state.company.fssai_license_number || "Not provided")}</strong></div>
            <div><span>IEC</span><strong>${escapeHtml(state.company.iec_number || "Not provided")}</strong></div>
          </div>
        </article>
        <article class="workspace-card">
          <div class="section-top">
            <div>
              <h3>Official verification path</h3>
              <p class="muted">The product decides which official systems should be used based on the company profile and confirmed identifiers.</p>
            </div>
          </div>
          <div class="cards-grid">
            ${
              verificationPlan.verification_plan.length
                ? verificationPlan.verification_plan
                    .map(
                      (item) => `
                        <article class="summary-card summary-card-tight">
                          <div class="section-top">
                            <div>
                              <strong>${escapeHtml(item.source_name)}</strong>
                              <p class="muted">${escapeHtml(item.category.replaceAll("_", " "))}</p>
                            </div>
                            ${badge(titleCase(item.status.replaceAll("_", " ")), item.status === "ready" ? "success" : item.status === "manual_verification_required" ? "warning" : "neutral")}
                          </div>
                          <p>${escapeHtml(item.description)}</p>
                          <div class="meta-row">
                            ${badge(titleCase(item.access_mode.replaceAll("_", " ")), "neutral")}
                            <a class="link-inline" href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">Open official source</a>
                          </div>
                          ${
                            item.missing_fields.length
                              ? `<div class="note-block">Missing: ${item.missing_fields.map((field) => escapeHtml(field.replaceAll("_", " "))).join(", ")}</div>`
                              : ""
                          }
                        </article>
                      `
                    )
                    .join("")
                : '<div class="empty-inline">No official verification path available yet.</div>'
            }
          </div>
        </article>
        <article class="workspace-card">
          <div class="section-top">
            <div>
              <h3>Live official scheme feed</h3>
              <p class="muted">This is a conservative company-facing slice of the official myScheme catalog.</p>
            </div>
            ${badge(`${state.officialSchemeMeta.matchedTotal || 0} matches`, "info")}
          </div>
          <div class="detail-grid">
            <div><span>Source</span><strong>myScheme</strong></div>
            <div><span>Expired items</span><strong>Excluded</strong></div>
            <div><span>Current matches</span><strong>${escapeHtml(String(state.officialSchemeMeta.matchedTotal || 0))}</strong></div>
            <div><span>Catalog synced</span><strong>${state.officialSchemeMeta.lastSyncedAt ? escapeHtml(formatDate(state.officialSchemeMeta.lastSyncedAt)) : "Not synced yet"}</strong></div>
          </div>
          <div class="toolbar">
            <button class="button button-secondary button-small" data-action="sync-official-schemes">Sync official schemes</button>
            <button class="button button-ghost button-small" data-action="switch-view" data-view="schemes">Open scheme review</button>
          </div>
        </article>
      </section>
    `;
  }

  function renderWorkspace() {
    const metrics = currentMetrics();
    if (!state.company || !metrics) {
      return `
        <div class="shell shell-wide">
          ${renderTopbar("ComplianceIQ", "No company selected", '<button class="button button-primary" data-action="start-onboarding">Analyze company</button>')}
          ${renderError()}
        </div>
      `;
    }

    const main = (() => {
      if (state.loading) {
        return '<section class="workspace-card"><div class="empty-inline">Loading company data...</div></section>';
      }
      if (state.activeView === "compliance") return renderCompliance();
      if (state.activeView === "tax") return renderTaxReview();
      if (state.activeView === "schemes") return renderSchemes();
      if (state.activeView === "company") return renderCompanyDetails();
      return renderSchemes();
    })();

    return `
      <div class="shell shell-wide">
        ${renderTopbar(
          state.company.name,
          "Applicable obligations, incentives, and value at stake for this company.",
          `
            ${badge(`Risk ${metrics.risk_score}`, metrics.risk_score >= 80 ? "success" : metrics.risk_score >= 60 ? "warning" : "danger")}
            <button class="button button-secondary" data-action="start-onboarding">New analysis</button>
          `
        )}
        ${renderError()}
        <div class="app-layout">
          <aside class="side-panel">
            <div class="side-block">
              <h3>Navigation</h3>
              <nav class="nav-list">
                ${renderNavItem("schemes", "Schemes")}
                ${renderNavItem("overview", "Overview")}
                ${renderNavItem("company", "Profile")}
                ${renderNavItem("compliance", "Compliance")}
                ${renderNavItem("tax", "GST & Tax")}
              </nav>
            </div>
            <div class="side-block">
              <h3>At a glance</h3>
              <div class="quick-facts">
                <div>
                  <span>Open scheme value</span>
                  <strong class="mono">${formatCurrency(metrics.potential)}</strong>
                </div>
                <div>
                  <span>Annual compliance exposure</span>
                  <strong class="mono">${formatCurrency(metrics.annual_burn_estimate)}</strong>
                </div>
                <div>
                  <span>Official leads</span>
                  <strong>${escapeHtml(String(state.officialSchemeMeta.matchedTotal || 0))}</strong>
                </div>
                <div>
                  <span>Tax review items</span>
                  <strong>${escapeHtml(String(taxObligations().length))}</strong>
                </div>
              </div>
            </div>
          </aside>
          <main class="main-panel">${main}</main>
        </div>
      </div>
    `;
  }

  function render() {
    const root = document.getElementById("app");
    const screen = state.mode === "landing"
      ? renderLanding()
      : state.mode === "onboarding"
        ? renderOnboarding()
        : renderWorkspace();
    root.innerHTML = `${screen}${renderToast()}${renderReviewOverlay()}`;
  }

  function entityOptions(selected) {
    return [
      ["", "Select entity type"],
      ["pvt_ltd", "Private limited"],
      ["public_ltd", "Public limited"],
      ["llp", "LLP"],
      ["opc", "OPC"],
      ["partnership", "Partnership"],
      ["proprietorship", "Proprietorship"],
      ["trust", "Trust"],
      ["society", "Society"],
      ["section_8", "Section 8 company"],
    ]
      .map(([value, label]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${label}</option>`)
      .join("");
  }

  function stateOptions(selected) {
    return ["", ...states]
      .map((value) => `<option value="${value}" ${selected === value ? "selected" : ""}>${value || "Select state"}</option>`)
      .join("");
  }

  function sectorOptions(selected) {
    return ["", ...sectors]
      .map((value) => `<option value="${value}" ${selected === value ? "selected" : ""}>${value ? titleCase(value) : "Select sector"}</option>`)
      .join("");
  }

  function turnoverOptions(selected) {
    return [
      ["", "Select turnover"],
      ["under_40L", "Under ₹40L"],
      ["40L_1Cr", "₹40L to ₹1Cr"],
      ["1Cr_10Cr", "₹1Cr to ₹10Cr"],
      ["10Cr_100Cr", "₹10Cr to ₹100Cr"],
      ["100Cr_500Cr", "₹100Cr to ₹500Cr"],
      ["above_500Cr", "Above ₹500Cr"],
    ]
      .map(([value, label]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${label}</option>`)
      .join("");
  }

  function employeeOptions(selected) {
    return [
      ["", "Select employee count"],
      ["1_10", "1 to 10"],
      ["11_50", "11 to 50"],
      ["51_200", "51 to 200"],
      ["201_500", "201 to 500"],
      ["above_500", "500+"],
    ]
      .map(([value, label]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${label}</option>`)
      .join("");
  }

  function flagCard(name, label, description, checked) {
    return `
      <label class="flag-card">
        <input type="checkbox" name="${name}" ${checked ? "checked" : ""}>
        <span>
          <strong>${escapeHtml(label)}</strong>
          <small>${escapeHtml(description)}</small>
        </span>
      </label>
    `;
  }

  function factQuestionCard(name, label, description, value) {
    const selected = value === true ? "yes" : value === false ? "no" : value === "unknown" ? "unknown" : "";
    return `
      <div class="field-card fact-card">
        <span>${escapeHtml(label)} <em class="required">*</em></span>
        <small class="field-help">${escapeHtml(description)}</small>
        <div class="fact-choice-row">
          ${[
            ["yes", "Yes"],
            ["no", "No"],
            ["unknown", "Not sure yet"],
          ]
            .map(
              ([option, optionLabel]) => `
                <label class="fact-choice ${selected === option ? "active" : ""}">
                  <input type="radio" name="${escapeHtml(name)}" value="${option}" ${selected === option ? "checked" : ""}>
                  <span>${escapeHtml(optionLabel)}</span>
                </label>
              `
            )
            .join("")}
        </div>
      </div>
    `;
  }

  function textFieldCard(name, label, description, value, placeholder = "", suggestedValue = "") {
    return `
      <label class="field field-card ${value ? "prefilled" : ""}">
        <span>${escapeHtml(label)}</span>
        <input name="${name}" value="${escapeHtml(value || "")}" placeholder="${escapeHtml(placeholder)}">
        <small class="field-help">${escapeHtml(description)}</small>
        ${
          suggestedValue && !value
            ? `<div class="field-suggestion"><span>Suggested from public website evidence: ${escapeHtml(suggestedValue)}</span><button class="button button-ghost button-small" type="button" data-action="use-detected-id" data-field="${escapeHtml(name)}" data-value="${escapeHtml(suggestedValue)}">Use suggestion</button></div>`
            : ""
        }
      </label>
    `;
  }

  function analysisScopeOptions(selected) {
    return [
      ["current_entity", "Current legal entity"],
      ["brand_unit", "Brand or business unit"],
      ["new_entity_scenario", "Separate new entity scenario"],
    ]
      .map(([value, label]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${label}</option>`)
      .join("");
  }

  function operatingActivityOptions(selected) {
    return [
      ["same_as_detected", "Use detected business line"],
      ["procurement_ecommerce", "Procurement and ecommerce"],
      ["manufacturing_processing", "Manufacturing or processing"],
      ["agriculture_plantation", "Agriculture or plantation"],
      ["services_software", "Services or software"],
      ["healthcare_services", "Healthcare services"],
    ]
      .map(([value, label]) => `<option value="${value}" ${selected === value ? "selected" : ""}>${label}</option>`)
      .join("");
  }

  function buildOfficialIdentifierQuestions(company) {
    const sector = effectiveSector(company) || company.sector;
    const sectorBucket = sectorBucketName(sector);
    const needsFoodVerification = company.handles_food_products || sectorBucket === "food_processing";
    const questions = [];
    if (company.entity_type === "llp") {
      questions.push({
        field: "llpin",
        label: "LLPIN",
        description: "Optional but high-value. This lets the product verify the LLP with MCA and reduces entity-level ambiguity.",
        placeholder: "AAA-1234",
      });
    } else {
      questions.push({
        field: "cin",
        label: "CIN",
        description: "Optional but high-value. This lets the product verify the legal entity with MCA and usually sharpens company-law mapping.",
        placeholder: "L12345MH2024PLC123456",
      });
    }
    if (company.is_msme || ["under_40L", "40L_1Cr", "1Cr_10Cr"].includes(company.annual_turnover)) {
      questions.push({
        field: "udyam_number",
        label: "Udyam number",
        description: "Recommended if available. This confirms MSME status and materially improves MSME-linked scheme accuracy.",
        placeholder: "UDYAM-XX-00-0000000",
      });
    }
    if (company.is_startup_india || company.is_dpiit) {
      questions.push({
        field: "dpiit_certificate_number",
        label: "Startup India / DPIIT certificate number",
        description: "Recommended if available. This confirms DPIIT-backed startup routes like tax exemption and seed-fund readiness.",
        placeholder: "DIPP12345",
      });
    }
    if (needsFoodVerification) {
      questions.push({
        field: "fssai_license_number",
        label: "FSSAI license number",
        description: "Recommended for food businesses. This improves food-licence certainty and can sharpen facility-level mapping.",
        placeholder: "10012022000001",
      });
    }
    if (company.is_export_oriented) {
      questions.push({
        field: "iec_number",
        label: "IEC number",
        description: "Recommended for exporters. This improves DGFT-linked scheme and export-compliance confidence.",
        placeholder: "0512345678",
      });
    }
    return questions;
  }

  function buildFollowUpQuestions(company) {
    return buildRuleQuestionGroups(company).flatMap((group) => group.questions);
  }

  function buildRuleQuestionGroups(company) {
    const sectorPack = inferredSectorPack(company);
    const questions = [];
    const ask = (section, field, label, description, priority) => {
      questions.push({ section, field, label, description, priority });
    };

    if (company.has_gstin == null && !company.gstin) {
      ask("universal", "has_gstin", "Is the operating entity registered under GST?", "This is the gate for GST returns, e-invoicing, and GST-linked compliance.", 1);
    }
    if (["pvt_ltd", "public_ltd", "llp", "partnership", "opc"].includes(company.entity_type) && company.deducts_tds == null) {
      ask("universal", "deducts_tds", "Does this company deduct TDS?", "This determines whether quarterly TDS return obligations should apply.", 2);
    }
    if (company.is_export_oriented == null) {
      ask("universal", "is_export_oriented", "Does the company export or sell cross-border?", "This changes DGFT-linked opportunities, export-support routes, and some sector-specific approvals.", 3);
    }
    if (company.is_msme === true && company.has_b2b_receivables == null) {
      ask("universal", "has_b2b_receivables", "Does the business raise B2B invoices to companies, distributors, institutions, or government buyers?", "This decides whether receivables routes like TReDS and delayed-payment tools like Samadhaan are genuinely relevant.", 3);
    }
    if (company.women_led == null) {
      ask("founder", "women_led", "Is the company women-led with majority ownership?", "This affects founder-route credit schemes such as Stand-Up India.", 4);
    }
    if (company.has_scst_founder == null) {
      ask("founder", "has_scst_founder", "Is the business majority-owned or controlled by an SC/ST founder?", "This affects founder-route procurement and credit programs.", 5);
    }
    if ((company.women_led === true || company.has_scst_founder === true) && company.greenfield_for_promoter == null) {
      ask("founder", "greenfield_for_promoter", "If you use a founder-route scheme, would this be a genuinely greenfield business for that promoter?", "This is a critical clause for routes like Stand-Up India and should not be assumed.", 6);
    }
    if (["pvt_ltd", "public_ltd", "opc"].includes(company.entity_type) && company.is_listed == null) {
      ask("universal", "is_listed", "Is the company listed on a stock exchange or SME platform?", "This changes SEBI / LODR, BRSR, and governance obligations.", 7);
    }
    if (["pvt_ltd", "public_ltd", "llp"].includes(company.entity_type) && company.has_foreign_investment == null && ["40L_1Cr", "1Cr_10Cr", "10Cr_100Cr", "100Cr_500Cr", "above_500Cr"].includes(company.annual_turnover)) {
      ask("universal", "has_foreign_investment", "Has the company received foreign investment or other FEMA-linked funding?", "This changes foreign-investment reporting and FLA-return obligations.", 8);
    }

    if (sectorPack === "food_agri") {
      if (company.handles_food_products == null) {
        ask("sector_food_agri", "handles_food_products", "Does the business manufacture, process, store, or sell regulated food products?", "This changes FSSAI, food-labelling, and food-sector scheme mapping.", 9);
      }
      if (company.has_primary_processing == null) {
        ask("sector_food_agri", "has_primary_processing", "Does the business do primary or integrated processing instead of only resale or standalone secondary processing?", "This materially changes agri-processing scheme fit, including AIF-type routes.", 10);
      }
      if (company.has_warehouse == null) {
        ask("sector_food_agri", "has_warehouse", "Does the business operate warehouses, storage sites, or post-harvest infrastructure?", "This changes storage-linked compliance and agri-infrastructure schemes.", 11);
      }
      if (company.has_cold_chain == null) {
        ask("sector_food_agri", "has_cold_chain", "Does the business operate cold-chain or temperature-controlled infrastructure?", "This changes cold-chain support routes and some facility obligations.", 12);
      }
      if (company.has_factory_operations == null) {
        ask("sector_food_agri", "has_factory_operations", "Does the business operate a processing unit, plant, or industrial food facility?", "This affects plant, environmental, fire-safety, and facility-linked compliance.", 13);
      }
    }

    if (sectorPack === "manufacturing" || sectorPack === "manufacturing_defence") {
      if (company.has_factory_operations == null) {
        ask("sector_manufacturing", "has_factory_operations", "Does the company operate a factory, plant, workshop, or industrial site?", "This affects factory, plant, environmental, fire-safety, and premises-linked compliance.", 9);
      }
      if (company.generates_hazardous_waste == null) {
        ask("sector_manufacturing", "generates_hazardous_waste", "Do operations generate hazardous waste, emissions, effluents, solvents, or regulated scrap?", "This changes pollution-control and hazardous-waste obligations.", 10);
      }
      if (company.uses_contract_labour == null) {
        ask("sector_manufacturing", "uses_contract_labour", "Does the business rely on contract labour?", "This changes whether contract-labour licensing, registers, and labour-condition reviews should be flagged.", 11);
      }
      if (company.uses_interstate_migrant_workers == null) {
        ask("sector_manufacturing", "uses_interstate_migrant_workers", "Are inter-state migrant workers engaged?", "This changes migrant-worker allowance, accommodation, and record-keeping obligations.", 12);
      }
      if (sectorPack === "manufacturing_defence" && company.serves_defence_sector == null) {
        ask("sector_manufacturing", "serves_defence_sector", "Does the business manufacture or supply aerospace / defence systems, components, or controlled products?", "This changes industrial-licence, defence-industry support, and sector-specific opportunity mapping.", 13);
      }
      if ((company.serves_defence_sector === true || sectorPack === "manufacturing_defence") && company.controlled_items_exposure == null) {
        ask("sector_manufacturing", "controlled_items_exposure", "Are any products or assemblies potentially controlled, licensable, or security-sensitive?", "This tightens defence-manufacturing compliance and scheme relevance.", 14);
      }
    }

    if (sectorPack === "technology" && company.has_rd_collaboration == null) {
      ask("sector_technology", "has_rd_collaboration", "Is there a formal R&D or academic collaboration?", "This changes eligibility for R&D grant programs.", 9);
    }
    if (["technology", "manufacturing", "healthcare"].includes(sectorPack) && company.has_patent_activity == null) {
      ask(
        sectorPack === "technology" ? "sector_technology" : sectorPack === "manufacturing" ? "sector_manufacturing" : "sector_healthcare",
        "has_patent_activity",
        "Is the business filing patents, prosecuting IP, or funding patentable product development?",
        "This is the real gate for patent-cost support routes; we should not show them just because the company is an MSME or startup.",
        10
      );
    }

    if (sectorPack === "healthcare") {
      if (company.has_healthcare_facility == null) {
        ask("sector_healthcare", "has_healthcare_facility", "Does the business operate a clinic, hospital, medical facility, or healthcare site?", "This changes clinical-establishment, facility, and biomedical-waste compliance.", 9);
      }
      if (company.has_diagnostic_lab == null) {
        ask("sector_healthcare", "has_diagnostic_lab", "Does the business operate a diagnostic or pathology lab?", "This changes healthcare-facility and biomedical-waste obligations.", 10);
      }
      if (company.generates_hazardous_waste == null) {
        ask("sector_healthcare", "generates_hazardous_waste", "Do medical or lab operations generate biomedical or hazardous waste?", "This changes waste-authorisation and disposal obligations.", 11);
      }
    }

    if (sectorPack === "finance" && company.regulated_financial_entity == null) {
      ask("sector_finance", "regulated_financial_entity", "Is the company actually carrying a regulated financial activity requiring RBI, SEBI, or IRDAI oversight?", "This separates true regulated-finance compliance from generic fintech software or enablement businesses.", 9);
    }

    if (sectorPack === "construction_real_estate") {
      if (company.project_based_operations == null) {
        ask("sector_construction", "project_based_operations", "Does the business run project-based construction or real-estate operations?", "This changes project-level compliance such as RERA and BOCW.", 9);
      }
      if (company.uses_contract_labour == null) {
        ask("sector_construction", "uses_contract_labour", "Does the business rely on contract labour?", "This changes contract-labour and site-worker obligations.", 10);
      }
      if (company.uses_interstate_migrant_workers == null) {
        ask("sector_construction", "uses_interstate_migrant_workers", "Are inter-state migrant workers engaged on projects or sites?", "This changes site-worker allowances and record-keeping obligations.", 11);
      }
    }

    if (sectorPack === "logistics") {
      if (company.has_warehouse == null) {
        ask("sector_logistics", "has_warehouse", "Does the business operate warehouses or storage infrastructure?", "This changes warehousing, site, and logistics-linked rule mapping.", 9);
      }
      if (company.has_cold_chain == null) {
        ask("sector_logistics", "has_cold_chain", "Is any cold-chain or temperature-controlled infrastructure involved?", "This changes food/logistics support schemes and some operating obligations.", 10);
      }
      if (company.uses_contract_labour == null) {
        ask("sector_logistics", "uses_contract_labour", "Does the business rely on contract labour?", "This changes labour licensing and register obligations.", 11);
      }
    }

    const sectionMeta = {
      universal: {
        title: "Universal business facts",
        description: "These affect tax, corporate, export, and founder-route logic across many company types.",
      },
      founder: {
        title: "Founder-route facts",
        description: "These are only here because ownership structure changes certain loan and procurement schemes materially.",
      },
      sector_food_agri: {
        title: "Food / tea / agri operations",
        description: "These answers change FSSAI, agri-processing, storage, and infrastructure scheme logic.",
      },
      sector_manufacturing: {
        title: "Manufacturing / defence operations",
        description: "These answers change factory, labour, environmental, and defence-industry mapping.",
      },
      sector_technology: {
        title: "Technology-specific facts",
        description: "These answers help separate export software and R&D routes from generic tech positioning.",
      },
      sector_healthcare: {
        title: "Healthcare facility facts",
        description: "These answers separate true healthcare operations from health-tech or distribution businesses.",
      },
      sector_finance: {
        title: "Regulated finance facts",
        description: "These answers prevent fintech enablement companies from being treated like NBFCs or other regulated entities.",
      },
      sector_construction: {
        title: "Project and site facts",
        description: "These answers change project-level labour, RERA, and worker-law mapping.",
      },
      sector_logistics: {
        title: "Logistics and infrastructure facts",
        description: "These answers change warehouse, labour, and cold-chain logic.",
      },
    };

    const grouped = {};
    questions.forEach((question) => {
      grouped[question.section] = grouped[question.section] || [];
      grouped[question.section].push(question);
    });
    return Object.entries(grouped)
      .map(([section, items]) => ({
        id: section,
        title: sectionMeta[section]?.title || "Company-specific questions",
        description: sectionMeta[section]?.description || "",
        questions: items.sort((a, b) => (a.priority || 99) - (b.priority || 99)),
      }))
      .sort((a, b) => {
        const aPriority = Math.min(...a.questions.map((item) => item.priority || 99));
        const bPriority = Math.min(...b.questions.map((item) => item.priority || 99));
        return aPriority - bPriority;
      });
  }

  function shouldShowOfficialIdStep(company = state.draftCompany) {
    return buildOfficialIdentifierQuestions(company).length > 0;
  }

  function visibleOnboardingSteps(company = state.draftCompany) {
    const steps = [
      { id: 1, label: "Company" },
      { id: 2, label: "Scope & profile" },
      { id: 3, label: "Business facts" },
    ];
    if (shouldShowOfficialIdStep(company)) {
      steps.push({ id: 4, label: "Accuracy boosters" });
    }
    steps.push({ id: 5, label: "Company-specific questions" });
    steps.push({ id: 6, label: "Credentials" });
    return steps;
  }

  function nextVisibleStepLabel(currentStep, company = state.draftCompany) {
    const steps = visibleOnboardingSteps(company);
    const currentIndex = steps.findIndex((item) => item.id === currentStep);
    return steps[currentIndex + 1]?.label || "";
  }

  function onboardingPrimaryLabel(step, company = state.draftCompany) {
    if (state.onboardingBusy) return state.onboardingMessage || "Working...";
    if (step === 1) return "Resolve company";
    const nextLabel = nextVisibleStepLabel(step, company);
    if (nextLabel) return `Continue to ${nextLabel}`;
    return state.saving ? "Creating analysis..." : "Create company analysis";
  }

  function nextVisibleOnboardingStep(currentStep, company = state.draftCompany) {
    const steps = visibleOnboardingSteps(company).map((item) => item.id);
    const index = steps.indexOf(currentStep);
    if (index === -1) return steps[0];
    return steps[Math.min(index + 1, steps.length - 1)];
  }

  function previousVisibleOnboardingStep(currentStep, company = state.draftCompany) {
    const steps = visibleOnboardingSteps(company).map((item) => item.id);
    const index = steps.indexOf(currentStep);
    if (index <= 0) return steps[0];
    return steps[index - 1];
  }

  function readTriState(formData, name, fallback) {
    const value = formData.get(name);
    if (value === "yes") return true;
    if (value === "no") return false;
    if (value === "unknown") return "unknown";
    return fallback;
  }

  function readCompanyForm() {
    const form = document.getElementById("company-form");
    if (!form) return state.draftCompany;
    const formData = new FormData(form);
    const hasField = (name) => Array.from(form.elements).some((element) => element.name === name);
    return {
      name: String(formData.get("name") || state.draftCompany.name).trim(),
      legal_name: String(formData.get("legal_name") || state.draftCompany.legal_name || "").trim(),
      website_url: String(formData.get("website_url") || state.draftCompany.website_url || "").trim(),
      website_domain: String(formData.get("website_domain") || state.draftCompany.website_domain || "").trim(),
      analysis_scope: String(formData.get("analysis_scope") || state.draftCompany.analysis_scope || "current_entity"),
      operating_activity: String(formData.get("operating_activity") || state.draftCompany.operating_activity || "same_as_detected"),
      group_sector_hint: String(formData.get("group_sector_hint") || state.draftCompany.group_sector_hint || "").trim(),
      state: String(formData.get("state") || state.draftCompany.state),
      city: String(formData.get("city") || state.draftCompany.city).trim(),
      entity_type: String(formData.get("entity_type") || state.draftCompany.entity_type),
      sector: String(formData.get("sector") || state.draftCompany.sector),
      annual_turnover: String(formData.get("annual_turnover") || state.draftCompany.annual_turnover),
      employee_count: String(formData.get("employee_count") || state.draftCompany.employee_count),
      founded_year: Number(formData.get("founded_year") || state.draftCompany.founded_year),
      cin: String(formData.get("cin") || state.draftCompany.cin || "").trim(),
      llpin: String(formData.get("llpin") || state.draftCompany.llpin || "").trim(),
      gstin: String(formData.get("gstin") || state.draftCompany.gstin || "").trim(),
      pan: String(formData.get("pan") || state.draftCompany.pan || "").trim(),
      udyam_number: String(formData.get("udyam_number") || state.draftCompany.udyam_number || "").trim(),
      dpiit_certificate_number: String(formData.get("dpiit_certificate_number") || state.draftCompany.dpiit_certificate_number || "").trim(),
      fssai_license_number: String(formData.get("fssai_license_number") || state.draftCompany.fssai_license_number || "").trim(),
      iec_number: String(formData.get("iec_number") || state.draftCompany.iec_number || "").trim(),
      is_msme: hasField("is_msme") ? formData.get("is_msme") === "on" : state.draftCompany.is_msme,
      is_startup_india: hasField("is_startup_india") ? formData.get("is_startup_india") === "on" : state.draftCompany.is_startup_india,
      is_dpiit: hasField("is_dpiit") ? formData.get("is_dpiit") === "on" : state.draftCompany.is_dpiit,
      has_gstin: hasField("has_gstin") ? readTriState(formData, "has_gstin", state.draftCompany.has_gstin) : state.draftCompany.has_gstin,
      is_export_oriented: hasField("is_export_oriented") ? readTriState(formData, "is_export_oriented", state.draftCompany.is_export_oriented) : state.draftCompany.is_export_oriented,
      has_foreign_investment: hasField("has_foreign_investment") ? readTriState(formData, "has_foreign_investment", state.draftCompany.has_foreign_investment) : state.draftCompany.has_foreign_investment,
      is_listed: hasField("is_listed") ? readTriState(formData, "is_listed", state.draftCompany.is_listed) : state.draftCompany.is_listed,
      deducts_tds: hasField("deducts_tds") ? readTriState(formData, "deducts_tds", state.draftCompany.deducts_tds) : state.draftCompany.deducts_tds,
      has_factory_operations: hasField("has_factory_operations") ? readTriState(formData, "has_factory_operations", state.draftCompany.has_factory_operations) : state.draftCompany.has_factory_operations,
      handles_food_products: hasField("handles_food_products") ? readTriState(formData, "handles_food_products", state.draftCompany.handles_food_products) : state.draftCompany.handles_food_products,
      has_rd_collaboration: hasField("has_rd_collaboration") ? readTriState(formData, "has_rd_collaboration", state.draftCompany.has_rd_collaboration) : state.draftCompany.has_rd_collaboration,
      has_new_hires: hasField("has_new_hires") ? readTriState(formData, "has_new_hires", state.draftCompany.has_new_hires) : state.draftCompany.has_new_hires,
      women_led: hasField("women_led") ? readTriState(formData, "women_led", state.draftCompany.women_led) : state.draftCompany.women_led,
      has_scst_founder: hasField("has_scst_founder") ? readTriState(formData, "has_scst_founder", state.draftCompany.has_scst_founder) : state.draftCompany.has_scst_founder,
      uses_contract_labour: hasField("uses_contract_labour") ? readTriState(formData, "uses_contract_labour", state.draftCompany.uses_contract_labour) : state.draftCompany.uses_contract_labour,
      uses_interstate_migrant_workers: hasField("uses_interstate_migrant_workers") ? readTriState(formData, "uses_interstate_migrant_workers", state.draftCompany.uses_interstate_migrant_workers) : state.draftCompany.uses_interstate_migrant_workers,
      serves_defence_sector: hasField("serves_defence_sector") ? readTriState(formData, "serves_defence_sector", state.draftCompany.serves_defence_sector) : state.draftCompany.serves_defence_sector,
      controlled_items_exposure: hasField("controlled_items_exposure") ? readTriState(formData, "controlled_items_exposure", state.draftCompany.controlled_items_exposure) : state.draftCompany.controlled_items_exposure,
      generates_hazardous_waste: hasField("generates_hazardous_waste") ? readTriState(formData, "generates_hazardous_waste", state.draftCompany.generates_hazardous_waste) : state.draftCompany.generates_hazardous_waste,
      has_warehouse: hasField("has_warehouse") ? readTriState(formData, "has_warehouse", state.draftCompany.has_warehouse) : state.draftCompany.has_warehouse,
      has_cold_chain: hasField("has_cold_chain") ? readTriState(formData, "has_cold_chain", state.draftCompany.has_cold_chain) : state.draftCompany.has_cold_chain,
      has_primary_processing: hasField("has_primary_processing") ? readTriState(formData, "has_primary_processing", state.draftCompany.has_primary_processing) : state.draftCompany.has_primary_processing,
      has_b2b_receivables: hasField("has_b2b_receivables") ? readTriState(formData, "has_b2b_receivables", state.draftCompany.has_b2b_receivables) : state.draftCompany.has_b2b_receivables,
      has_patent_activity: hasField("has_patent_activity") ? readTriState(formData, "has_patent_activity", state.draftCompany.has_patent_activity) : state.draftCompany.has_patent_activity,
      regulated_financial_entity: hasField("regulated_financial_entity") ? readTriState(formData, "regulated_financial_entity", state.draftCompany.regulated_financial_entity) : state.draftCompany.regulated_financial_entity,
      has_healthcare_facility: hasField("has_healthcare_facility") ? readTriState(formData, "has_healthcare_facility", state.draftCompany.has_healthcare_facility) : state.draftCompany.has_healthcare_facility,
      has_diagnostic_lab: hasField("has_diagnostic_lab") ? readTriState(formData, "has_diagnostic_lab", state.draftCompany.has_diagnostic_lab) : state.draftCompany.has_diagnostic_lab,
      project_based_operations: hasField("project_based_operations") ? readTriState(formData, "project_based_operations", state.draftCompany.project_based_operations) : state.draftCompany.project_based_operations,
      greenfield_for_promoter: hasField("greenfield_for_promoter") ? readTriState(formData, "greenfield_for_promoter", state.draftCompany.greenfield_for_promoter) : state.draftCompany.greenfield_for_promoter,
    };
  }

  function validateDraft(step) {
    if (step === 1) {
      if (state.draftCompany.name.trim() || state.draftCompany.website_url.trim()) return "";
      return "Enter a company name or website to continue.";
    }
    if (step === 2) {
      if (!state.draftCompany.name.trim()) return "Enter the operating name before continuing.";
      if (!state.draftCompany.entity_type) return "Select the entity type before continuing.";
      if (!state.draftCompany.sector) return "Select the sector before continuing.";
      if (!state.draftCompany.state) return "Select the state before continuing.";
      if (!state.draftCompany.city.trim()) return "Enter the city before continuing.";
      return "";
    }
    if (step === 3) {
      if (!state.draftCompany.annual_turnover) return "Select the annual turnover before continuing.";
      if (!state.draftCompany.employee_count) return "Select the employee count before continuing.";
      if (!state.draftCompany.founded_year) return "Enter the founded year before continuing.";
      return "";
    }
    if (step === 5) {
      const unanswered = buildFollowUpQuestions(state.draftCompany).filter((question) => state.draftCompany[question.field] == null || state.draftCompany[question.field] === "");
      if (unanswered.length) {
        return "Answer the company-specific questions before continuing so the mapping is not based on hidden assumptions.";
      }
      return "";
    }
    return "";
  }

  async function runCompanyDiscovery(input) {
    state.loading = true;
    state.onboardingBusy = true;
    state.onboardingMessage = "Resolving company and checking public evidence...";
    state.error = "";
    render();
    try {
      const payload = await api.discoverCompany(input);
      const discovery = payload.discovery;
      const detectedOfficialIds = {
        cin: discovery.inferred.cin || "",
        llpin: discovery.inferred.llpin || "",
        gstin: discovery.inferred.gstin || "",
        pan: discovery.inferred.pan || "",
        udyam_number: discovery.inferred.udyam_number || "",
        dpiit_certificate_number: discovery.inferred.dpiit_certificate_number || "",
        fssai_license_number: discovery.inferred.fssai_license_number || "",
        iec_number: discovery.inferred.iec_number || "",
      };
      state.discovery = discovery;
      state.detectedOfficialIds = Object.fromEntries(
        Object.entries(detectedOfficialIds).filter(([, value]) => value)
      );
      state.draftCompany = {
        ...defaultDraftCompany(),
        ...state.draftCompany,
        ...discovery.inferred,
        name: discovery.inferred.name || input.name || state.draftCompany.name,
        legal_name: discovery.inferred.legal_name || "",
        website_url: discovery.inferred.website_url || input.website || state.draftCompany.website_url,
        website_domain: discovery.inferred.website_domain || "",
        analysis_scope: discovery.inferred.analysis_scope || state.draftCompany.analysis_scope || "current_entity",
        operating_activity: discovery.inferred.operating_activity || state.draftCompany.operating_activity || "same_as_detected",
        group_sector_hint: discovery.inferred.group_sector_hint || state.draftCompany.group_sector_hint || "",
        cin: state.draftCompany.cin || "",
        llpin: state.draftCompany.llpin || "",
        gstin: state.draftCompany.gstin || "",
        pan: state.draftCompany.pan || "",
        udyam_number: state.draftCompany.udyam_number || "",
        dpiit_certificate_number: state.draftCompany.dpiit_certificate_number || "",
        fssai_license_number: state.draftCompany.fssai_license_number || "",
        iec_number: state.draftCompany.iec_number || "",
      };
      state.onboardingStep = 2;
    } catch (error) {
      state.error = error.message;
    } finally {
      state.loading = false;
      state.onboardingBusy = false;
      state.onboardingMessage = "";
      render();
    }
  }

  async function createCompanyFromDraft(payload) {
    state.saving = true;
    state.onboardingBusy = true;
    state.onboardingMessage = "Building company analysis...";
    render();
    try {
      const created = await api.createCompany(payload);
      state.mode = "workspace";
      state.activeView = "schemes";
      state.draftCompany = defaultDraftCompany();
      state.onboardingStep = 1;
      state.discovery = null;
      state.detectedOfficialIds = {};
      state.selectedSchemeId = null;
      state.error = "";
      await loadCompanies(false);
      await loadWorkspace(created.company.id, false);
    } catch (error) {
      state.error = error.message;
    } finally {
      state.saving = false;
      state.onboardingBusy = false;
      state.onboardingMessage = "";
      render();
    }
  }

  async function resetAllData() {
    state.loading = true;
    render();
    try {
      await api.reset();
      state.companies = [];
      state.company = null;
      state.obligations = [];
      state.schemes = [];
      state.verificationPlan = null;
      state.officialSchemeMatches = [];
      state.officialSchemeMeta = { matchedTotal: 0, cachedTotal: 0, lastSyncedAt: null };
      state.schemeOpportunities = [];
      state.detectedOfficialIds = {};
      state.activeCompanyId = null;
      state.selectedSchemeId = null;
      state.selectedOpportunityId = null;
      state.selectedOfficialSchemeId = null;
      state.applicationSchemeId = null;
      state.applicationSchemeSource = null;
      state.reviewStep = 1;
      state.reviewAnswers = {};
      state.mode = "landing";
      state.error = "";
      await loadOfficialSources(false);
    } catch (error) {
      state.error = error.message;
    } finally {
      state.loading = false;
      render();
    }
  }

  document.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) return;
    const action = target.dataset.action;

    try {
      if (action === "hero-analyze") {
        const input = document.getElementById("hero-company-name");
        const rawValue = input ? input.value.trim() : "";
        if (!rawValue) {
          state.error = "Enter a company name or website first.";
          showToast("Enter a company name or website first.");
          render();
          return;
        }
        const isWebsite = looksLikeWebsiteInput(rawValue);
        state.mode = "onboarding";
        state.onboardingStep = 1;
        state.draftCompany = {
          ...defaultDraftCompany(),
          name: isWebsite ? "" : rawValue,
          website_url: isWebsite ? rawValue : "",
        };
        state.discovery = null;
        state.detectedOfficialIds = {};
        await runCompanyDiscovery({
          name: isWebsite ? "" : rawValue,
          website: isWebsite ? rawValue : "",
        });
        return;
      }

      if (action === "go-home") {
        state.mode = "landing";
        state.selectedSchemeId = null;
        state.selectedOfficialSchemeId = null;
        state.selectedOpportunityId = null;
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        render();
        return;
      }

      if (action === "go-to-schemes-explainer") {
        if (state.company && state.activeCompanyId) {
          state.mode = "workspace";
          state.activeView = "schemes";
          render();
        } else if (state.companies.length) {
          await loadWorkspace(state.companies[0].id);
          state.activeView = "schemes";
          render();
        } else {
          state.mode = "onboarding";
          state.onboardingStep = 1;
          state.draftCompany = defaultDraftCompany();
          state.discovery = null;
          state.detectedOfficialIds = {};
          render();
        }
        return;
      }

      if (action === "open-workspace") {
        if (state.companies.length) {
          state.mode = "workspace";
          state.activeView = "schemes";
          const latest = state.companies[0];
          if ((!state.company || state.activeCompanyId !== latest.id) && latest) {
            await loadWorkspace(latest.id);
          } else {
            render();
          }
        }
        return;
      }

      if (action === "start-onboarding") {
        state.error = "";
        state.mode = "onboarding";
        state.onboardingStep = 1;
        state.draftCompany = defaultDraftCompany();
        state.discovery = null;
        state.detectedOfficialIds = {};
        state.selectedSchemeId = null;
        state.selectedOfficialSchemeId = null;
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        render();
        return;
      }

      if (action === "open-existing-workspace") {
        if (state.discovery?.existing_company_id) {
          state.activeView = "schemes";
          await loadWorkspace(state.discovery.existing_company_id);
        }
        return;
      }

      if (action === "use-detected-id") {
        const form = document.getElementById("company-form");
        if (form) {
          const field = form.querySelector(`[name="${target.dataset.field}"]`);
          if (field) field.value = target.dataset.value || "";
        }
        state.draftCompany = {
          ...state.draftCompany,
          [target.dataset.field]: target.dataset.value || "",
        };
        render();
        return;
      }

      if (action === "step-next") {
        state.draftCompany = readCompanyForm();
        const validationMessage = validateDraft(state.onboardingStep);
        if (validationMessage) {
          state.error = validationMessage;
          showToast(validationMessage);
          render();
          return;
        }
        if (state.onboardingStep === 1) {
          await runCompanyDiscovery({
            name: state.draftCompany.name,
            website: state.draftCompany.website_url,
          });
          return;
        }
        state.onboardingBusy = true;
        state.onboardingMessage = `Preparing ${nextVisibleStepLabel(state.onboardingStep, state.draftCompany) || "the next step"}...`;
        render();
        await new Promise((resolve) => setTimeout(resolve, 140));
        state.error = "";
        state.onboardingStep = nextVisibleOnboardingStep(state.onboardingStep, state.draftCompany);
        state.onboardingBusy = false;
        state.onboardingMessage = "";
        render();
        return;
      }

      if (action === "step-back") {
        state.draftCompany = readCompanyForm();
        state.onboardingStep = previousVisibleOnboardingStep(state.onboardingStep, state.draftCompany);
        render();
        return;
      }

      if (action === "save-company") {
        state.draftCompany = readCompanyForm();
        const validationMessage = validateDraft(3);
        if (validationMessage) {
          state.error = validationMessage;
          showToast(validationMessage);
          render();
          return;
        }
        await createCompanyFromDraft(state.draftCompany);
        return;
      }

      if (action === "refresh-official-sources") {
        state.loading = true;
        render();
        const payload = await api.refreshOfficialSources();
        state.officialSources = payload.sources || [];
        state.loading = false;
        render();
        return;
      }

      if (action === "sync-official-schemes") {
        state.loading = true;
        render();
        await api.syncOfficialSchemes();
        if (state.activeCompanyId) {
          await loadWorkspace(state.activeCompanyId, false);
        }
        state.loading = false;
        render();
        return;
      }

      if (action === "switch-view") {
        state.activeView = target.dataset.view;
        render();
        return;
      }

      if (action === "filter-compliance") {
        state.complianceFilter = target.dataset.value || "all";
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "filter-scheme") {
        state.schemeFilter = target.dataset.value || "all";
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "obligation-filed") {
        await api.obligationAction(state.activeCompanyId, target.dataset.id, "filed");
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "obligation-reopen") {
        await api.obligationAction(state.activeCompanyId, target.dataset.id, "reopen");
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "scheme-apply") {
        await api.schemeAction(state.activeCompanyId, target.dataset.id, "apply");
        state.selectedSchemeId = target.dataset.id;
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "scheme-receive") {
        await api.schemeAction(state.activeCompanyId, target.dataset.id, "receive");
        state.selectedSchemeId = target.dataset.id;
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "scheme-reopen") {
        await api.schemeAction(state.activeCompanyId, target.dataset.id, "reopen");
        state.selectedSchemeId = target.dataset.id;
        await loadWorkspace(state.activeCompanyId);
        return;
      }

      if (action === "open-scheme-detail") {
        state.selectedSchemeId = target.dataset.id || null;
        state.selectedOfficialSchemeId = null;
        state.selectedOpportunityId = null;
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        state.reviewAssessment = null;
        state.reviewLoading = false;
        await loadMappedSchemeReview({}, true);
        return;
      }

      if (action === "open-official-scheme-detail") {
        state.selectedOfficialSchemeId = target.dataset.id || null;
        state.selectedSchemeId = null;
        state.selectedOpportunityId = null;
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        state.reviewAssessment = null;
        state.reviewLoading = false;
        render();
        return;
      }

      if (action === "open-opportunity-detail") {
        state.selectedOpportunityId = target.dataset.id || null;
        state.selectedOfficialSchemeId = null;
        state.selectedSchemeId = null;
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        state.reviewAssessment = null;
        state.reviewLoading = false;
        render();
        return;
      }

      if (action === "close-review-overlay") {
        state.selectedSchemeId = null;
        state.selectedOfficialSchemeId = null;
        state.selectedOpportunityId = null;
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        state.reviewAssessment = null;
        state.reviewLoading = false;
        render();
        return;
      }

      if (action === "start-scheme-application") {
        state.applicationSchemeId = target.dataset.id || null;
        state.applicationSchemeSource = target.dataset.source || "mapped";
        state.selectedOpportunityId = null;
        state.reviewStep = 4;
        if (state.applicationSchemeSource === "mapped") {
          state.selectedSchemeId = target.dataset.id || null;
          state.selectedOfficialSchemeId = null;
        } else {
          state.selectedOfficialSchemeId = target.dataset.id || null;
          state.selectedSchemeId = null;
        }
        render();
        return;
      }

      if (action === "next-review-step") {
        readReviewAnswers();
        const context = activeReviewContext();
        if (context?.kind === "mapped" && state.reviewStep === 2) {
          const assessment = await loadMappedSchemeReview(state.reviewAnswers, true);
          if (!assessment) return;
        }
        const maxStep = Number(target.dataset.maxStep || 1);
        state.reviewStep = Math.min(maxStep, state.reviewStep + 1);
        render();
        return;
      }

      if (action === "prev-review-step") {
        readReviewAnswers();
        state.reviewStep = Math.max(1, state.reviewStep - 1);
        render();
        return;
      }

      if (action === "confirm-scheme-application") {
        await api.schemeAction(state.activeCompanyId, target.dataset.id, "apply");
        state.applicationSchemeId = null;
        state.applicationSchemeSource = null;
        state.selectedSchemeId = target.dataset.id;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        await loadWorkspace(state.activeCompanyId);
        showToast("Application workflow started.", "success");
        return;
      }

      if (action === "connect-ca-expert") {
        const advisor = target.dataset.advisor || "specialist CA";
        const schemeName = target.dataset.schemeName || "this scheme";
        const brief = `Scheme: ${schemeName}\nCompany: ${state.company?.name || ""}\nRecommended advisor: ${advisor}\nAssessment scope: ${scopeLabel(state.company?.analysis_scope || "current_entity")}\nState: ${state.company?.state || ""}`;
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(brief);
        }
        showToast(`${advisor} brief prepared for ${schemeName}.`, "info");
        return;
      }

      if (action === "explore-newco-scenario") {
        if (!state.company) return;
        state.mode = "onboarding";
        state.discovery = null;
        state.detectedOfficialIds = {};
        state.onboardingStep = 2;
        state.selectedOpportunityId = null;
        state.reviewStep = 1;
        state.reviewAnswers = {};
        state.draftCompany = {
          ...defaultDraftCompany(),
          ...state.company,
          analysis_scope: "new_entity_scenario",
          operating_activity: state.company.operating_activity && state.company.operating_activity !== "same_as_detected"
            ? state.company.operating_activity
            : "procurement_ecommerce",
          cin: "",
          llpin: "",
          gstin: "",
          pan: "",
          udyam_number: "",
          dpiit_certificate_number: "",
          fssai_license_number: "",
          iec_number: "",
        };
        render();
        return;
      }

      if (action === "reset-data") {
        await resetAllData();
      }
    } catch (error) {
      state.error = error.message || "Something went wrong.";
      state.loading = false;
      state.saving = false;
      render();
    }
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.matches(".interactive-card")) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    target.click();
  });

  bootstrap();
})();
