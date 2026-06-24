import { API_BASE_URL, apiRequest } from "./client";
import type { CompanyResult } from "../types/company";
import type { RusprofileRunResponse, Search, SearchPayload } from "../types/search";

export function getSearches(): Promise<Search[]> {
  return apiRequest<Search[]>("/api/searches");
}

export function createSearch(payload: SearchPayload): Promise<Search> {
  return apiRequest<Search>("/api/searches", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getSearch(searchId: string): Promise<Search> {
  return apiRequest<Search>(`/api/searches/${searchId}`);
}

export function getSearchResults(searchId: string): Promise<CompanyResult[]> {
  return apiRequest<CompanyResult[]>(`/api/searches/${searchId}/results`);
}

interface RunRusprofileOptions {
  visible_browser?: boolean;
  llm_scoring_enabled?: boolean;
  llm_scoring_threshold?: number | null;
}

export function runRusprofileSearch(searchId: string, options: RunRusprofileOptions = {}): Promise<RusprofileRunResponse> {
  return apiRequest<RusprofileRunResponse>(`/api/searches/${searchId}/run-rusprofile`, {
    method: "POST",
    body: JSON.stringify(options),
  });
}

export function getSearchCsvUrl(searchId: string): string {
  return `${API_BASE_URL}/api/searches/${searchId}/export.csv`;
}
