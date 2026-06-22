import { Download, Plus } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { getSearch, getSearchCsvUrl, getSearchResults } from "../api/searchesApi";
import { ResultsTable } from "../components/results/ResultsTable";
import { StatsCards } from "../components/results/StatsCards";
import { Badge } from "../components/ui/Badge";
import { Card, CardBody } from "../components/ui/Card";
import { formatDate, formatNumber } from "../lib/format";
import type { CompanyResult } from "../types/company";
import type { Search } from "../types/search";

function statusTone(status: Search["status"]) {
  if (status === "completed") return "green";
  if (status === "running") return "yellow";
  if (status === "failed") return "red";
  return "slate";
}

export function SearchResultsPage() {
  const { searchId } = useParams();
  const [search, setSearch] = useState<Search | null>(null);
  const [results, setResults] = useState<CompanyResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!searchId) return;

    Promise.all([getSearch(searchId), getSearchResults(searchId)])
      .then(([searchData, resultsData]) => {
        setSearch(searchData);
        setResults(resultsData);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, [searchId]);

  if (!searchId) {
    return <div className="text-sm text-slate-500">Search ID не найден.</div>;
  }

  if (isLoading) {
    return <div className="text-sm text-slate-500">Загрузка результатов…</div>;
  }

  if (error || !search) {
    return <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error || "Поиск не найден"}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-950">
              {search.project?.name || "Результаты поиска"}
            </h1>
            <Badge tone={statusTone(search.status)}>{search.status}</Badge>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Создан: {formatDate(search.created_at)} · Запрошено: {formatNumber(search.requested_companies_count)} · Найдено:{" "}
            {formatNumber(search.found_companies_count)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-medium text-slate-800 transition hover:bg-slate-50"
            href={getSearchCsvUrl(search.id)}
          >
            <Download className="h-4 w-4" />
            Скачать CSV
          </a>
          <Link
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-vector px-4 text-sm font-medium text-white transition hover:bg-indigo-700"
            to={`/searches/new?projectId=${search.project_id}`}
          >
            <Plus className="h-4 w-4" />
            Новый поиск
          </Link>
        </div>
      </section>

      {search.error_message ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{search.error_message}</div>
      ) : null}

      <StatsCards results={results} />

      <Card>
        <CardBody className="grid gap-3 text-sm text-slate-600 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <span className="block text-xs text-slate-400">Отрасль</span>
            {search.industry || "—"}
          </div>
          <div>
            <span className="block text-xs text-slate-400">Регион</span>
            {search.region || "—"}
          </div>
          <div>
            <span className="block text-xs text-slate-400">Тип бизнеса</span>
            {search.business_type}
          </div>
          <div>
            <span className="block text-xs text-slate-400">Источник</span>
            MockProvider
          </div>
        </CardBody>
      </Card>

      <ResultsTable results={results} />
    </div>
  );
}
