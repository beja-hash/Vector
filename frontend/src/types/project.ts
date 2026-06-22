export type SalesType = "B2B" | "B2C" | "B2G";

export interface Project {
  id: string;
  name: string;
  client_offer: string;
  average_deal_size: number | null;
  sales_type: SalesType;
  usual_customers: string | null;
  excluded_customers: string | null;
  comment: string | null;
  created_at: string;
  updated_at: string;
  search_count: number;
  companies_count: number;
  status: string;
}

export interface ProjectPayload {
  name: string;
  client_offer: string;
  average_deal_size: number | null;
  sales_type: SalesType;
  usual_customers: string;
  excluded_customers: string;
  comment: string;
}
