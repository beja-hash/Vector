export interface CompanyResult {
  id: string;
  search_id: string;
  company_name: string;
  inn: string;
  ogrn: string;
  region: string | null;
  city: string | null;
  okved_main: string | null;
  okved_description: string | null;
  revenue: number | null;
  employees_count: number | null;
  company_age: number | null;
  website: string | null;
  has_website: boolean;
  vacancies_total: number;
  sales_vacancies: number;
  marketing_vacancies: number;
  business_type: string;
  source_name: string;
  source_url: string | null;
  comment: string | null;
  created_at: string;
}
