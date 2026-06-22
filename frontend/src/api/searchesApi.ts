import { API_BASE_URL, apiRequest } from "./client";
import type { CompanyResult } from "../types/company";
import type { Search, SearchPayload } from "../types/search";

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

export function getSearchCsvUrl(searchId: string): string {
  return `${API_BASE_URL}/api/searches/${searchId}/export.csv`;
}
