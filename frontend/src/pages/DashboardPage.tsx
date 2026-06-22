import { ArrowRight, Building2, Clock3, Database, Search } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";

import { getProjects } from "../api/projectsApi";
import { getSearches } from "../api/searchesApi";
import { Badge } from "../components/ui/Badge";
import { Card, CardBody, CardHeader } from "../components/ui/Card";
import { formatDate, formatNumber } from "../lib/format";
import type { Project } from "../types/project";
import type { Search as SearchType } from "../types/search";

export function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searches, setSearches] = useState<SearchType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getProjects(), getSearches()])
      .then(([projectsData, searchesData]) => {
        setProjects(projectsData);
        setSearches(searchesData);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, []);

  const companiesCount = searches.reduce((sum, search) => sum + search.found_companies_count, 0);
  const lastRun = searches[0]?.created_at;
  const stats = [
    { label: "Всего проектов", value: formatNumber(projects.length), icon: Building2 },
    { label: "Всего поисков", value: formatNumber(searches.length), icon: Search },
    { label: "Найдено компаний", value: formatNumber(companiesCount), icon: Database },
    { label: "Последний запуск", value: formatDate(lastRun), icon: Clock3 },
  ];

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Vector</h1>
          <p className="mt-1 text-sm text-slate-500">Внутренний инструмент поиска компаний под ICP</p>
        </div>
        <Link
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-vector px-4 text-sm font-medium text-white transition hover:bg-indigo-700"
          to="/searches/new"
        >
          Создать поиск
          <ArrowRight className="h-4 w-4" />
        </Link>
      </section>

      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardBody className="flex items-start justify-between gap-3 p-4">
                <div>
                  <div className="text-sm text-slate-500">{stat.label}</div>
                  <div className="mt-2 text-xl font-semibold text-slate-950">{isLoading ? "…" : stat.value}</div>
                </div>
                <div className="rounded-md bg-indigo-50 p-2 text-vector">
                  <Icon className="h-4 w-4" />
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-slate-950">Последние проекты</h2>
        </CardHeader>
        <CardBody>
          {isLoading ? <div className="text-sm text-slate-500">Загрузка проектов…</div> : null}
          {!isLoading && projects.length === 0 ? (
            <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
              <div className="text-base font-medium text-slate-950">Пока нет проектов.</div>
              <div className="mt-1 text-sm text-slate-500">Создайте первый поиск компаний под ICP.</div>
              <Link
                className="mt-4 inline-flex h-10 items-center justify-center rounded-md bg-vector px-4 text-sm font-medium text-white transition hover:bg-indigo-700"
                to="/searches/new"
              >
                Создать поиск
              </Link>
            </div>
          ) : null}
          {!isLoading && projects.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {projects.slice(0, 5).map((project) => (
                <div key={project.id} className="flex flex-col gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="font-medium text-slate-950">{project.name}</div>
                    <div className="mt-1 text-sm text-slate-500">{project.client_offer}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge tone="green">{project.status}</Badge>
                    <span className="text-sm text-slate-500">{formatNumber(project.companies_count)} компаний</span>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </CardBody>
      </Card>
    </div>
  );
}
