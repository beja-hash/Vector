import { apiRequest } from "./client";
import type { LlmSettings } from "../types/search";

export function getLlmSettings(): Promise<LlmSettings> {
  return apiRequest<LlmSettings>("/api/settings/llm");
}
