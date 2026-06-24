import { Download, Plus } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { getLlmSettings } from "../api/settingsApi";
import { getSearch, getSearchCsvUrl, getSearchResults, runRusprofileSearch } from "../api/searchesApi";
import { ResultsTable } from "../components/results/ResultsTable";
import { StatsCards } from "../components/results/StatsCards";
import { Badge } from "../components/ui/Badge";
import { Card, CardBody } from "../components/ui/Card";
import { formatDate, formatNumber } from "../lib/format";
import type { CompanyResult } from "../types/company";
import type { LlmSettings, Search } from "../types/search";

function statusTone(status: Search["status"]) {
  if (status === "completed") return "green";
  if (status === "running") return "yellow";
  if (status === "failed") return "red";
  return "slate";
}

function formatRunError(message: string) {
  if (message === "captcha_required") {
    return "Rusprofile показал проверку «Я не робот». Пройдите ее в открытом браузере и запустите Rusprofile еще раз.";
  }
  if (message.includes("without having a XServer") || message.includes("Missing X server") || message.includes("$DISPLAY")) {
    return "Playwright не может открыть видимый браузер внутри Docker: в контейнере нет X Server/$DISPLAY. Запустите Rusprofile в headless-режиме или поднимите backend через xvfb-run.";
  }
  return message;
}

export function SearchResultsPage() {
  const { searchId } = useParams();
  const [search, setSearch] = useState<Search | null>(null);
  const [results, setResults] = useState<CompanyResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningRusprofile, setIsRunningRusprofile] = useState(false);
  const [runSummary, setRunSummary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [llmSettings, setLlmSettings] = useState<LlmSettings | null>(null);

  const loadSearch = () => {
    if (!searchId) return;

    setIsLoading(true);
    Promise.all([getSearch(searchId), getSearchResults(searchId)])
      .then(([searchData, resultsData]) => {
        setSearch(searchData);
        setResults(resultsData);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadSearch();
  }, [searchId]);

  useEffect(() => {
    getLlmSettings()
      .then(setLlmSettings)
      .catch(() => setLlmSettings(null));
  }, []);

  const handleRunRusprofile = async () => {
    if (!searchId) return;
    setError(null);
    setRunSummary("Открываем Rusprofile...");
    setIsRunningRusprofile(true);
    try {
      const llmAvailable = Boolean(llmSettings?.polza_enabled && llmSettings.llm_scoring_enabled);
      const result = await runRusprofileSearch(searchId, {
        visible_browser: search?.visible_browser,
        llm_scoring_enabled: llmAvailable ? true : search?.llm_scoring_enabled,
        llm_scoring_threshold: search?.llm_scoring_threshold ?? llmSettings?.threshold,
      });
      setRunSummary(
        `Готово: собрано ${result.collected}, match ${result.saved}, review ${result.manual_review}, skip ${result.skipped}, LLM scored ${result.scored}, дублей ${result.duplicates}, ошибок ${result.failed}.`,
      );
      const [searchData, resultsData] = await Promise.all([getSearch(searchId), getSearchResults(searchId)]);
      setSearch(searchData);
      setResults(resultsData);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Не удалось запустить Rusprofile";
      setError(formatRunError(message));
      setRunSummary(null);
      const [searchData, resultsData] = await Promise.all([getSearch(searchId), getSearchResults(searchId)]);
      setSearch(searchData);
      setResults(resultsData);
    } finally {
      setIsRunningRusprofile(false);
    }
  };

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
          <button
            className="inline-flex h-10 items-center justify-center rounded-md border border-indigo-200 bg-indigo-50 px-4 text-sm font-medium text-indigo-700 transition hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isRunningRusprofile}
            type="button"
            onClick={handleRunRusprofile}
          >
            {isRunningRusprofile ? "Rusprofile работает..." : "Запустить Rusprofile"}
          </button>
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
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {formatRunError(search.error_message)}
        </div>
      ) : null}

      <Card>
        <CardBody className="grid gap-3 text-sm text-slate-600 md:grid-cols-5">
          {[
            "Открываем Rusprofile",
            "Применяем фильтры",
            "Собираем выдачу",
            "Открываем карточки",
            "Нормализуем и скорим",
          ].map((label) => (
            <div key={label} className="rounded-md bg-slate-50 px-3 py-2">
              <span className="block text-xs text-slate-400">Этап</span>
              {label}
            </div>
          ))}
          <div className="md:col-span-5 rounded-md border border-indigo-100 bg-indigo-50 px-3 py-2 text-indigo-800">
            {runSummary ||
              (search.data_source === "rusprofile"
                ? "Готово к запуску. Подробные шаги Rusprofile пишутся в backend logs."
                : "Сейчас показаны mock-результаты. Нажмите «Запустить Rusprofile», чтобы заменить их реальными компаниями.")}
          </div>
        </CardBody>
      </Card>

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
            {search.data_source === "rusprofile" ? "Rusprofile" : "MockProvider"}
          </div>
          <div>
            <span className="block text-xs text-slate-400">LLM scoring</span>
            {llmSettings?.polza_enabled && llmSettings.llm_scoring_enabled
              ? `вкл., ${llmSettings.model}, threshold ${llmSettings.threshold}`
              : "выкл."}
          </div>
        </CardBody>
      </Card>

      <ResultsTable results={results} />
    </div>
  );
}
