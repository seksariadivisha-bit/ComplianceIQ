from __future__ import annotations

from html import unescape
import re
import ssl
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


COMMON_ABOUT_PATHS = [
    "",
    "/about",
    "/about-us",
    "/pages/about",
    "/pages/about-us",
    "/pages/our-story",
    "/our-story",
    "/company",
    "/company/about",
    "/about/company",
    "/contact",
    "/contact-us",
    "/pages/contact",
    "/pages/contact-us",
    "/terms",
    "/terms-and-conditions",
    "/privacy",
    "/privacy-policy",
    "/legal",
    "/pages/legal",
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

try:
    import certifi
except ImportError:  # pragma: no cover - optional dependency
    certifi = None

LEGAL_ENTITY_PATTERNS = [
    re.compile(
        r"(?:brought to you by|owned by|operated by|a brand of|brand of|run by|managed by)\s+"
        r"([A-Z][A-Za-z0-9&.,'() -]{3,140}?"
        r"(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Company|Co\.?\s*Pvt\.?\s*Ltd\.?))",
        re.IGNORECASE,
    ),
    re.compile(
        r"([A-Z][A-Za-z0-9&.,'() -]{3,140}?"
        r"(?:Private Limited|Pvt\.?\s*Ltd\.?|Limited|Ltd\.?|LLP|Company|Co\.?\s*Pvt\.?\s*Ltd\.?))"
        r"\s*[-–]\s*(?:a subsidiary|subsidiary)",
        re.IGNORECASE,
    ),
]

OPERATOR_PATTERNS = [
    re.compile(
        r"(?:brought to you by|owned by|operated by|a brand of|brand of|run by|managed by)\s+([^.;:\n]+)",
        re.IGNORECASE,
    ),
]

IDENTIFIER_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "cin": [
        re.compile(
            r"(?:cin|corporate identification number)\s*[:#-]?\s*([A-Z]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})",
            re.IGNORECASE,
        ),
    ],
    "llpin": [
        re.compile(r"(?:llpin|llp identification number)\s*[:#-]?\s*([A-Z]{3}-\d{4})", re.IGNORECASE),
    ],
    "gstin": [
        re.compile(
            r"(?:gstin|gst(?:\s+registration)?(?:\s+number)?|gst\s+no)\s*[:#-]?\s*(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d])",
            re.IGNORECASE,
        ),
    ],
    "pan": [
        re.compile(r"(?:pan(?:\s+number)?|permanent account number)\s*[:#-]?\s*([A-Z]{5}\d{4}[A-Z])", re.IGNORECASE),
    ],
    "fssai_license_number": [
        re.compile(
            r"(?:fssai(?:\s+license)?(?:\s+(?:no|number))?|license\s+no)\s*[:#-]?\s*(\d{10,14})",
            re.IGNORECASE,
        ),
    ],
    "iec_number": [
        re.compile(r"(?:iec|import export code)\s*[:#-]?\s*(\d{10})", re.IGNORECASE),
    ],
}

ECOMMERCE_KEYWORDS = [
    "shop",
    "store",
    "buy online",
    "order online",
    "cart",
    "checkout",
    "gift",
    "gifting",
    "subscription",
    "delivery",
    "shipping",
    "marketplace",
]

MANUFACTURING_KEYWORDS = [
    "processing",
    "manufacturing",
    "blending",
    "factory",
    "production",
    "processing unit",
    "assembly",
    "fabrication",
    "machining",
    "precision engineering",
    "plant",
    "industrial",
    "aerospace",
    "defence",
    "defense",
    "avionics",
    "aircraft",
    "missile",
    "uav",
    "drone",
]

HIGH_CONFIDENCE_DEFENCE_KEYWORDS = [
    "aerospace",
    "aviation",
    "avionics",
    "aircraft",
    "drone",
    "uav",
    "missile",
    "defence manufacturing",
    "defense manufacturing",
    "ministry of defence",
    "armed forces",
    "military",
    "naval",
]

CONTEXTUAL_DEFENCE_KEYWORDS = ["defence", "defense"]

FALSE_DEFENCE_PHRASES = [
    "cold defence",
    "cold defense",
    "line of defence",
    "first line of defence",
    "immune defense",
    "immune defence",
    "defence against",
    "defense against",
    "social defence",
    "civil defence",
]

INDUSTRIAL_DEFENCE_CONTEXT_KEYWORDS = [
    "manufacturing",
    "manufacturer",
    "component",
    "components",
    "assembly",
    "assemblies",
    "aerospace",
    "aviation",
    "avionics",
    "aircraft",
    "drone",
    "uav",
    "missile",
    "military",
    "naval",
    "industrial",
    "ordnance",
    "propulsion",
    "precision engineering",
    "defence manufacturing",
    "defense manufacturing",
]

FACTORY_SIGNAL_PATTERNS = [
    re.compile(r"\bfactory\b", re.IGNORECASE),
    re.compile(r"\bmanufacturing (?:facility|unit|plant|site)\b", re.IGNORECASE),
    re.compile(r"\bproduction (?:facility|unit|site)\b", re.IGNORECASE),
    re.compile(r"\bassembly line\b", re.IGNORECASE),
    re.compile(r"\bindustrial unit\b", re.IGNORECASE),
    re.compile(r"\bshop floor\b", re.IGNORECASE),
]

AGRI_KEYWORDS = [
    "tea estate",
    "tea estates",
    "plantation",
    "farm",
    "agriculture",
    "horticulture",
    "estate",
]

SERVICES_SOFTWARE_KEYWORDS = [
    "software",
    "saas",
    "platform",
    "cloud",
    "app",
]

PRIORITY_LINK_KEYWORDS = [
    "about",
    "our-story",
    "company",
    "contact",
    "legal",
    "privacy",
    "terms",
    "shipping",
    "return",
    "refund",
]


def looks_like_website(value: str) -> bool:
    candidate = str(value or "").strip()
    if not candidate:
        return False
    if candidate.startswith(("http://", "https://")):
        return True
    return "." in candidate and " " not in candidate


def normalize_website_url(value: str) -> str:
    candidate = str(value or "").strip()
    if not candidate:
        raise ValueError("Website URL is required")
    if not candidate.startswith(("http://", "https://")):
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    if not parsed.netloc:
        raise ValueError("Website URL looks invalid")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path or ''}"


def base_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def domain_from_url(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def candidate_urls_from_name(name: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9 ]+", " ", str(name or "").lower())
    if any(token in cleaned.split() for token in {"private", "pvt", "ltd", "limited", "llp"}):
        return []
    tokens = [token for token in cleaned.split() if token not in {"private", "pvt", "ltd", "limited", "llp", "co", "company"}]
    if not tokens:
        return []

    variants: list[str] = []

    def push_variant(value: str) -> None:
        if value and value not in variants:
            variants.append(value)

    compact = "".join(tokens)
    hyphenated = "-".join(tokens)
    push_variant(compact)
    push_variant(hyphenated)
    if tokens and tokens[0] == "the":
        push_variant("".join(tokens[1:]))
        push_variant("-".join(tokens[1:]))

    urls: list[str] = []
    for variant in variants:
        urls.append(f"https://www.{variant}.com")
        urls.append(f"https://{variant}.com")
        urls.append(f"https://www.{variant}.in")
        urls.append(f"https://{variant}.in")
        urls.append(f"https://www.{variant}.co.in")
        urls.append(f"https://{variant}.co.in")
    return urls[:6]


def candidate_urls_from_website(website: str) -> list[str]:
    normalized = normalize_website_url(website)
    parsed = urlparse(normalized)
    domain = parsed.netloc
    domain_no_www = domain[4:] if domain.startswith("www.") else domain
    path = parsed.path or ""
    variants: list[str] = []

    def push(url: str) -> None:
        if url and url not in variants:
            variants.append(url)

    for scheme in ["https", "http"]:
        push(f"{scheme}://{domain}{path}")
        push(f"{scheme}://{domain_no_www}{path}")
        push(f"{scheme}://www.{domain_no_www}{path}")
        if path:
            push(f"{scheme}://{domain}")
            push(f"{scheme}://{domain_no_www}")
            push(f"{scheme}://www.{domain_no_www}")
    return variants


def website_looks_relevant(name: str, title: str, text: str, domain: str) -> bool:
    query = re.sub(r"[^a-z0-9 ]+", " ", str(name or "").lower())
    tokens = [
        token
        for token in query.split()
        if token not in {"the", "private", "pvt", "ltd", "limited", "llp", "co", "company", "and"}
    ]
    if not tokens:
        return True
    haystack = f"{title} {text[:1200]} {domain}".lower()
    overlap = sum(1 for token in tokens if token in haystack)
    return overlap >= max(1, min(2, len(tokens)))


def fetch_html(url: str, *, timeout: float = 6.0) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    ssl_context = ssl.create_default_context(cafile=certifi.where()) if certifi else ssl.create_default_context()
    try:
        with urlopen(request, timeout=timeout, context=ssl_context) as response:  # noqa: S310
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="ignore")
    except (HTTPError, URLError, TimeoutError, OSError):
        result = subprocess.run(  # noqa: S603
            [
                "curl",
                "-fsSL",
                "--compressed",
                "--connect-timeout",
                str(max(4, int(timeout // 2))),
                "--max-time",
                str(int(timeout)),
                "-A",
                USER_AGENT,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
        )
        if result.returncode != 0:
            insecure = subprocess.run(  # noqa: S603
                [
                    "curl",
                    "-kfsSL",
                    "--compressed",
                    "--connect-timeout",
                    str(max(4, int(timeout // 2))),
                    "--max-time",
                    str(int(timeout)),
                    "-A",
                    USER_AGENT,
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=timeout + 2,
            )
            if insecure.returncode != 0:
                raise subprocess.CalledProcessError(
                    insecure.returncode or result.returncode,
                    insecure.args if insecure.returncode else result.args,
                    output=insecure.stdout or result.stdout,
                    stderr=insecure.stderr or result.stderr,
                )
            return insecure.stdout
        return result.stdout


def html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = unescape(text)
    return " ".join(text.split())


def extract_title(html: str) -> str:
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    return " ".join(unescape(match.group(1)).split()) if match else ""


def extract_meta_description(html: str) -> str:
    match = re.search(
        r'(?is)<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html,
    )
    return " ".join(unescape(match.group(1)).split()) if match else ""


def extract_brand_name(title: str, domain: str, provided_name: str) -> str:
    if provided_name:
        return provided_name.strip()
    for candidate in re.split(r"\s+[|\-–]\s+", title):
        candidate = candidate.strip()
        if candidate and "http" not in candidate.lower():
            return candidate
    bare = domain.split(".")[0].replace("-", " ").strip()
    return " ".join(part.capitalize() for part in bare.split())


def extract_legal_name(text: str) -> str:
    for pattern in LEGAL_ENTITY_PATTERNS:
        match = pattern.search(text)
        if match:
            return " ".join(match.group(1).split())
    return ""


def extract_operator_name(text: str) -> str:
    for pattern in OPERATOR_PATTERNS:
        match = pattern.search(text)
        if match:
            value = " ".join(match.group(1).split())
            value = re.sub(r"\s*[-–]\s*a subsidiary.*$", "", value, flags=re.IGNORECASE)
            return value.strip(" -–,")
    return ""


def extract_identifier_candidates(*texts: str) -> dict[str, str]:
    candidates: dict[str, str] = {}
    for field, patterns in IDENTIFIER_PATTERNS.items():
        for haystack in texts:
            if not haystack:
                continue
            for pattern in patterns:
                match = pattern.search(haystack)
                if not match:
                    continue
                value = re.sub(r"\s+", "", match.group(1)).upper()
                candidates[field] = value
                break
            if field in candidates:
                break
    return candidates


def extract_relevant_links(html: str, base_url: str) -> list[str]:
    origin = base_origin(base_url)
    candidates: list[str] = []
    for href in re.findall(r"""href=["']([^"'#]+)["']""", html, flags=re.IGNORECASE):
        full_url = urljoin(base_url, href.strip())
        parsed = urlparse(full_url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if base_origin(full_url) != origin:
            continue
        path = (parsed.path or "").lower()
        if not path or path == "/":
            continue
        if not any(keyword in path for keyword in PRIORITY_LINK_KEYWORDS):
            continue
        if full_url not in candidates:
            candidates.append(full_url)
    return candidates[:8]


def infer_operating_activity(text: str) -> str:
    lowered = " ".join(str(text or "").lower().split())
    if any(keyword in lowered for keyword in ECOMMERCE_KEYWORDS):
        return "procurement_ecommerce"
    if any(keyword in lowered for keyword in MANUFACTURING_KEYWORDS):
        return "manufacturing_processing"
    if any(keyword in lowered for keyword in AGRI_KEYWORDS):
        return "agriculture_plantation"
    if any(keyword in lowered for keyword in SERVICES_SOFTWARE_KEYWORDS):
        return "services_software"
    return ""


def contains_defence_signal(text: str) -> bool:
    lowered = " ".join(str(text or "").lower().split())
    for phrase in FALSE_DEFENCE_PHRASES:
        lowered = lowered.replace(phrase, " ")
    if any(keyword in lowered for keyword in HIGH_CONFIDENCE_DEFENCE_KEYWORDS):
        return True
    for match in re.finditer(r"\bdefen[cs]e\b", lowered):
        window = lowered[max(0, match.start() - 120) : min(len(lowered), match.end() + 120)]
        if any(keyword in window for keyword in INDUSTRIAL_DEFENCE_CONTEXT_KEYWORDS):
            return True
    return False


def contains_factory_signal(text: str) -> bool:
    compact = " ".join(str(text or "").split())
    return any(pattern.search(compact) for pattern in FACTORY_SIGNAL_PATTERNS)


def build_website_context(name: str = "", website: str = "") -> dict[str, Any] | None:
    explicit_url = normalize_website_url(website) if website.strip() else ""
    candidates = candidate_urls_from_website(explicit_url) if explicit_url else candidate_urls_from_name(name)
    if not candidates:
        return None

    notes: list[str] = []
    pages_fetched: list[str] = []
    snippets: list[str] = []
    raw_fragments: list[str] = []
    final_url = ""
    title = ""
    meta_description = ""

    for candidate_url in candidates:
        try:
            homepage_html = fetch_html(candidate_url)
        except (HTTPError, URLError, TimeoutError, OSError, subprocess.SubprocessError) as exc:
            notes.append(f"Could not reach {candidate_url}: {exc.__class__.__name__}.")
            continue

        final_url = candidate_url
        pages_fetched.append(candidate_url)
        raw_fragments.append(homepage_html)
        title = extract_title(homepage_html)
        meta_description = extract_meta_description(homepage_html)
        homepage_text = html_to_text(homepage_html)
        if not explicit_url and not website_looks_relevant(name, title, homepage_text, domain_from_url(candidate_url)):
            notes.append(f"Skipped {candidate_url} because the page did not look like a credible match.")
            final_url = ""
            continue
        snippets.append(homepage_text)

        page_candidates = [urljoin(candidate_url, path) for path in COMMON_ABOUT_PATHS[1:]]
        page_candidates.extend(extract_relevant_links(homepage_html, candidate_url))
        deduped_pages: list[str] = []
        for page_url in page_candidates:
            if page_url not in deduped_pages:
                deduped_pages.append(page_url)

        for page_url in deduped_pages[:6]:
            try:
                page_html = fetch_html(page_url)
            except (HTTPError, URLError, TimeoutError, OSError, subprocess.SubprocessError):
                continue
            page_text = html_to_text(page_html)
            page_title = extract_title(page_html)
            if "404" in page_title.lower() or "page not found" in page_text.lower():
                continue
            if len(page_text) < 80:
                continue
            pages_fetched.append(page_url)
            raw_fragments.append(page_html)
            snippets.append(page_text)

        break

    if not final_url:
        if explicit_url:
            return {
                "website_url": explicit_url,
                "website_domain": domain_from_url(explicit_url),
                "brand_name": extract_brand_name("", domain_from_url(explicit_url), name),
                "legal_name": "",
                "operator_name": "",
                "title": "",
                "meta_description": "",
                "search_text": "",
                "pages_fetched": [],
                "source": "website",
                "notes": notes or ["The website could not be reached from the server, so discovery fell back to name-based inference."],
            }
        return None

    combined_text = " ".join(snippets)
    domain = domain_from_url(final_url)
    brand_name = extract_brand_name(title, domain, name)
    legal_name = extract_legal_name(combined_text)
    operator_name = extract_operator_name(combined_text)
    identifier_candidates = extract_identifier_candidates(combined_text, " ".join(raw_fragments))
    operating_activity_hint = infer_operating_activity(combined_text)
    source = "website" if explicit_url else "guessed_website"
    normalized_text = " ".join(combined_text.lower().split())
    defence_signal = contains_defence_signal(normalized_text)
    factory_signal = contains_factory_signal(combined_text)
    warehouse_signal = any(keyword in normalized_text for keyword in ["warehouse", "warehousing", "distribution center", "distribution centre", "fulfilment center", "fulfillment center", "storage facility"])
    cold_chain_signal = any(keyword in normalized_text for keyword in ["cold chain", "cold storage", "temperature controlled", "reefer", "temperature-controlled"])
    healthcare_facility_signal = any(keyword in normalized_text for keyword in ["hospital", "clinic", "medical center", "medical centre", "patient care", "healthcare facility"])
    diagnostic_lab_signal = any(keyword in normalized_text for keyword in ["diagnostic lab", "pathology lab", "diagnostic centre", "diagnostic center", "laboratory services"])
    regulated_finance_signal = any(keyword in normalized_text for keyword in ["nbfc", "rbi registered", "sebi registered", "irdai", "regulated financial", "payment aggregator", "brokerage"])
    primary_processing_signal = any(keyword in normalized_text for keyword in ["primary processing", "post harvest", "post-harvest", "tea processing", "coffee processing", "grading", "sorting", "warehousing"])
    b2b_receivables_signal = any(keyword in normalized_text for keyword in ["wholesale", "institutional sales", "enterprise customers", "corporate clients", "distributors", "channel partners", "b2b"])
    patent_signal = any(keyword in normalized_text for keyword in ["patent", "patented", "intellectual property", "ipr", "ip portfolio"])

    context = {
        "website_url": final_url,
        "website_domain": domain,
        "brand_name": brand_name,
        "legal_name": legal_name,
        "operator_name": operator_name,
        "identifier_candidates": identifier_candidates,
        "operating_activity_hint": operating_activity_hint,
        "defence_signal": defence_signal,
        "factory_signal": factory_signal,
        "warehouse_signal": warehouse_signal,
        "cold_chain_signal": cold_chain_signal,
        "healthcare_facility_signal": healthcare_facility_signal,
        "diagnostic_lab_signal": diagnostic_lab_signal,
        "regulated_finance_signal": regulated_finance_signal,
        "primary_processing_signal": primary_processing_signal,
        "b2b_receivables_signal": b2b_receivables_signal,
        "patent_signal": patent_signal,
        "title": title,
        "meta_description": meta_description,
        "search_text": combined_text,
        "pages_fetched": pages_fetched,
        "source": source,
        "notes": notes,
    }
    return context
