import { apiRequest } from "./client";
import type { Project, ProjectPayload } from "../types/project";

export function getProjects(): Promise<Project[]> {
  return apiRequest<Project[]>("/api/projects");
}

export function getProject(projectId: string): Promise<Project> {
  return apiRequest<Project>(`/api/projects/${projectId}`);
}

export function createProject(payload: ProjectPayload): Promise<Project> {
  return apiRequest<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
