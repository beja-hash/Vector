import type { Project, ProjectPayload } from "./project";

export type SearchStatus = "draft" | "running" | "completed" | "failed";

export interface SearchPayload {
  project_id?: string | null;
  project?: ProjectPayload | null;
  industry: string | null;
  okved: string | null;
  region: string | null;
  city: string | null;
  revenue_min: number | null;
  revenue_max: number | null;
  employees_min: number | null;
  employees_max: number | null;
  company_age_min: number | null;
  active_only: boolean;
  business_type: string;
  website_requirement: string;
  vacancies_requirement: string;
  vacancy_categories: string[];
  sales_department_requirement: string;
  check_website: boolean;
  exclude_ip: boolean;
  exclude_liquidated: boolean;
  exclude_no_revenue: boolean;
  exclude_microbusiness: boolean;
  exclude_government: boolean;
  exclude_marketplace_sellers: boolean;
  requested_companies_count: number;
  data_completeness: string;
  export_format: string;
}

export interface Search extends Omit<SearchPayload, "project"> {
  id: string;
  project_id: string;
  status: SearchStatus;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  error_message: string | null;
  found_companies_count: number;
  project: Project | null;
}
