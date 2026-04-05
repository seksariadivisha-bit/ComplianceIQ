create extension if not exists pgcrypto;

do $$
begin
  if not exists (select 1 from pg_type where typname = 'entity_type_enum') then
    create type entity_type_enum as enum (
      'pvt_ltd',
      'llp',
      'partnership',
      'proprietorship',
      'public_ltd',
      'ngo'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'sector_enum') then
    create type sector_enum as enum (
      'manufacturing',
      'technology',
      'retail',
      'food_processing',
      'healthcare',
      'fintech',
      'edtech',
      'logistics',
      'construction',
      'export',
      'agriculture',
      'other'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'turnover_range_enum') then
    create type turnover_range_enum as enum (
      'under_40L',
      '40L_1Cr',
      '1Cr_10Cr',
      '10Cr_100Cr',
      '100Cr_500Cr',
      'above_500Cr'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'employee_count_enum') then
    create type employee_count_enum as enum (
      '1_10',
      '11_50',
      '51_200',
      '201_500',
      'above_500'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'subscription_tier_enum') then
    create type subscription_tier_enum as enum (
      'starter',
      'growth',
      'scale',
      'enterprise'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'compliance_category_enum') then
    create type compliance_category_enum as enum (
      'gst',
      'tds',
      'roc',
      'pf',
      'esi',
      'labour',
      'environmental',
      'fema',
      'sebi',
      'sectoral',
      'tax',
      'other'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'compliance_frequency_enum') then
    create type compliance_frequency_enum as enum (
      'monthly',
      'quarterly',
      'annual',
      'event_based'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'compliance_status_enum') then
    create type compliance_status_enum as enum (
      'pending',
      'filed',
      'overdue',
      'not_applicable',
      'waived'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'scheme_type_enum') then
    create type scheme_type_enum as enum (
      'grant',
      'loan',
      'subsidy',
      'tax_benefit',
      'certification',
      'market_access',
      'r_and_d',
      'insurance'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'scheme_status_enum') then
    create type scheme_status_enum as enum (
      'eligible',
      'ineligible',
      'maybe',
      'saved',
      'applied',
      'approved',
      'received',
      'rejected'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'user_role_enum') then
    create type user_role_enum as enum (
      'admin',
      'compliance_manager',
      'viewer',
      'ca_advisor',
      'super_admin'
    );
  end if;

  if not exists (select 1 from pg_type where typname = 'alert_type_enum') then
    create type alert_type_enum as enum (
      'compliance_due',
      'compliance_overdue',
      'new_scheme',
      'scheme_deadline',
      'regulatory_update'
    );
  end if;
end $$;

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  gstin text,
  pan text,
  cin text,
  entity_type entity_type_enum not null,
  sector sector_enum not null,
  state text not null,
  city text not null,
  annual_turnover_range turnover_range_enum not null,
  employee_count_range employee_count_enum not null,
  founded_year integer not null,
  is_msme boolean not null default false,
  is_startup_india_registered boolean not null default false,
  is_dpiit_recognised boolean not null default false,
  is_export_oriented boolean not null default false,
  subscription_tier subscription_tier_enum not null default 'starter',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  company_id uuid references companies(id) on delete set null,
  full_name text not null,
  email text not null unique,
  role user_role_enum not null default 'admin',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists compliance_obligations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  category compliance_category_enum not null,
  frequency compliance_frequency_enum not null,
  due_day integer,
  due_month integer,
  applicable_entity_types entity_type_enum[] not null default '{}',
  applicable_sectors sector_enum[] not null default '{}',
  applicable_states text[] not null default '{}',
  min_turnover_lakhs numeric,
  max_turnover_lakhs numeric,
  min_employees integer,
  max_employees integer,
  penalty_per_day numeric not null default 0,
  max_penalty numeric,
  description text not null,
  source_url text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists company_compliances (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  obligation_id uuid not null references compliance_obligations(id) on delete cascade,
  status compliance_status_enum not null default 'pending',
  due_date date not null,
  filed_date date,
  filing_reference text,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_id, obligation_id, due_date)
);

create table if not exists government_schemes (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  ministry text not null,
  scheme_type scheme_type_enum not null,
  benefit_description text not null,
  benefit_value text not null,
  max_benefit_amount numeric,
  eligibility_entity_types entity_type_enum[] not null default '{}',
  eligibility_sectors sector_enum[] not null default '{}',
  eligibility_states text[] not null default '{}',
  min_turnover_lakhs numeric,
  max_turnover_lakhs numeric,
  requires_msme boolean not null default false,
  requires_startup_india boolean not null default false,
  requires_dpiit boolean not null default false,
  requires_export boolean not null default false,
  min_employees integer,
  max_employees integer,
  max_company_age_years integer,
  application_url text,
  deadline date,
  is_central boolean not null default true,
  state text,
  is_active boolean not null default true,
  last_verified_date date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists company_schemes (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  scheme_id uuid not null references government_schemes(id) on delete cascade,
  eligibility_status scheme_status_enum not null,
  why_eligible jsonb not null default '[]'::jsonb,
  blockers jsonb not null default '[]'::jsonb,
  applied_date date,
  application_reference text,
  benefit_received_amount numeric,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (company_id, scheme_id)
);

create table if not exists regulatory_updates (
  id uuid primary key default gen_random_uuid(),
  category compliance_category_enum not null,
  title text not null,
  summary text not null,
  source_url text,
  effective_date date,
  relevant_states text[] not null default '{}',
  relevant_sectors sector_enum[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  type alert_type_enum not null,
  title text not null,
  message text not null,
  due_date date,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  tier subscription_tier_enum not null,
  status text not null,
  provider_customer_id text,
  provider_subscription_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_profiles_company_id on profiles(company_id);
create index if not exists idx_company_compliances_company_due on company_compliances(company_id, due_date);
create index if not exists idx_company_compliances_status on company_compliances(company_id, status);
create index if not exists idx_company_schemes_company_status on company_schemes(company_id, eligibility_status);
create index if not exists idx_alerts_company_unread on alerts(company_id, is_read);

comment on table profiles is 'Application profiles layered on top of Supabase auth.users.';
comment on table company_schemes is 'Stores explainable matching results for each company and scheme.';
