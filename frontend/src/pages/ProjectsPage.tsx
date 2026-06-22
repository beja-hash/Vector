import { ArrowRight, Plus } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import { getProjects } from "../api/projectsApi";
import { getSearches } from "../api/searchesApi";
import { Badge } from "../components/ui/Badge";
import { Card, CardBody } from "../components/ui/Card";
import { formatCurrency, formatDate, formatNumber } from "../lib/format";
import type { Project } from "../types/project";
import type { Search } from "../types/search";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [searches, setSearches] = useState<Search[]>([]);
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

  const latestSearchByProject = useMemo(() => {
    const map = new Map<string, Search>();
    searches.forEach((search) => {
      if (!map.has(search.project_id)) {
        map.set(search.project_id, search);
      }
    });
    return map;
  }, [searches]);

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Проекты</h1>
          <p className="mt-1 text-sm text-slate-500">Клиентские проекты и сохранённые поиски компаний.</p>
        </div>
        <Link
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-vector px-4 text-sm font-medium text-white transition hover:bg-indigo-700"
          to="/searches/new"
        >
          <Plus className="h-4 w-4" />
          Новый поиск
        </Link>
      </section>

      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      {isLoading ? <div className="text-sm text-slate-500">Загрузка проектов…</div> : null}

      {!isLoading && projects.length === 0 ? (
        <Card>
          <CardBody className="px-6 py-10 text-center">
            <div className="text-base font-medium text-slate-950">Пока нет проектов.</div>
            <div className="mt-1 text-sm text-slate-500">Создайте первый поиск компаний под ICP.</div>
            <Link
              className="mt-4 inline-flex h-10 items-center justify-center rounded-md bg-vector px-4 text-sm font-medium text-white transition hover:bg-indigo-700"
              to="/searches/new"
            >
              Создать поиск
            </Link>
          </CardBody>
        </Card>
      ) : null}

      <div className="grid gap-4">
        {projects.map((project) => {
          const latestSearch = latestSearchByProject.get(project.id);
          return (
            <Card key={project.id}>
              <CardBody className="grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-lg font-semibold text-slate-950">{project.name}</h2>
                    <Badge tone="green">{project.status}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{project.client_offer}</p>
                  <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2 xl:grid-cols-5">
                    <div>
                      <span className="block text-xs text-slate-400">Средний чек</span>
                      {formatCurrency(project.average_deal_size)}
                    </div>
                    <div>
                      <span className="block text-xs text-slate-400">Создан</span>
                      {formatDate(project.created_at)}
                    </div>
                    <div>
                      <span className="block text-xs text-slate-400">Поисков</span>
                      {formatNumber(project.search_count)}
                    </div>
                    <div>
                      <span className="block text-xs text-slate-400">Компаний</span>
                      {formatNumber(project.companies_count)}
                    </div>
                    <div>
                      <span className="block text-xs text-slate-400">Тип продажи</span>
                      {project.sales_type}
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 lg:justify-end">
                  <Link
                    className={`inline-flex h-9 items-center justify-center gap-2 rounded-md border px-3 text-sm font-medium transition ${
                      latestSearch
                        ? "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                        : "pointer-events-none border-slate-100 bg-slate-50 text-slate-400"
                    }`}
                    to={latestSearch ? `/searches/${latestSearch.id}` : "#"}
                  >
                    Открыть
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                  <Link
                    className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-vector px-3 text-sm font-medium text-white transition hover:bg-indigo-700"
                    to={`/searches/new?projectId=${project.id}`}
                  >
                    Новый поиск
                  </Link>
                </div>
              </CardBody>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
