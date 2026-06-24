import { useMemo, useState } from "react";

import { Badge } from "../ui/Badge";
import { Checkbox } from "../ui/Checkbox";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { formatCurrency, formatNumber } from "../../lib/format";
import type { CompanyResult } from "../../types/company";

interface ResultsTableProps {
  results: CompanyResult[];
}

const cellClass = "px-3 py-3 align-top";

function compactText(value: string | null | undefined, maxLength = 220) {
  const text = (value || "").replace(/\s+/g, " ").trim();
  if (!text) return "—";
  return text.length > maxLength ? `${text.slice(0, maxLength).trim()}...` : text;
}

function cleanOkvedDescription(value: string | null) {
  const text = compactText(value, 120);
  return /[A-Za-zА-Яа-яЁё0-9]/.test(text) ? text : "—";
}

function icpTone(action: CompanyResult["icp_recommended_action"]) {
  if (action === "add_to_results") return "green";
  if (action === "manual_review") return "yellow";
  if (action === "skip") return "red";
  return "slate";
}

function icpLabel(action: CompanyResult["icp_recommended_action"]) {
  if (action === "add_to_results") return "Match";
  if (action === "manual_review") return "Review";
  if (action === "skip") return "Skip";
  return "Not scored";
}

function icpReason(company: CompanyResult) {
  return company.icp_fit_reason || company.icp_mismatch_reason || company.comment || company.summary_text;
}

export function ResultsTable({ results }: ResultsTableProps) {
  const [query, setQuery] = useState("");
  const [onlyWebsite, setOnlyWebsite] = useState(false);
  const [onlyVacancies, setOnlyVacancies] = useState(false);
  const [onlyB2B, setOnlyB2B] = useState(false);
  const [icpFilter, setIcpFilter] = useState<"match" | "review" | "all">("match");

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return results.filter((company) => {
      const matchesQuery =
        !normalizedQuery ||
        company.company_name.toLowerCase().includes(normalizedQuery) ||
        (company.inn || "").includes(normalizedQuery);
      const matchesWebsite = !onlyWebsite || company.has_website;
      const matchesVacancies = !onlyVacancies || company.vacancies_total > 0;
      const matchesB2B = !onlyB2B || company.business_type === "B2B";
      const matchesIcp =
        icpFilter === "all" ||
        (icpFilter === "review" && company.icp_recommended_action === "manual_review") ||
        (icpFilter === "match" && company.icp_recommended_action === "add_to_results");
      return matchesQuery && matchesWebsite && matchesVacancies && matchesB2B && matchesIcp;
    });
  }, [icpFilter, onlyB2B, onlyVacancies, onlyWebsite, query, results]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="grid gap-3 border-b border-slate-100 p-4 lg:grid-cols-[1fr_180px_auto_auto_auto]">
        <Input
          label="Поиск по названию / ИНН"
          placeholder="ООО или 770..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Select
          label="ICP"
          options={[
            { label: "Match", value: "match" },
            { label: "Review", value: "review" },
            { label: "All", value: "all" },
          ]}
          value={icpFilter}
          onChange={(event) => setIcpFilter(event.target.value as "match" | "review" | "all")}
        />
        <Checkbox checked={onlyWebsite} label="Только с сайтом" onChange={setOnlyWebsite} />
        <Checkbox checked={onlyVacancies} label="Только с вакансиями" onChange={setOnlyVacancies} />
        <Checkbox checked={onlyB2B} label="Только B2B" onChange={setOnlyB2B} />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[1720px] table-fixed border-collapse text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {[
                ["Компания", "w-44"],
                ["ICP", "w-40"],
                ["ИНН", "w-28"],
                ["ОГРН", "w-32"],
                ["Регион", "w-28"],
                ["Город", "w-28"],
                ["ОКВЭД", "w-48"],
                ["Выручка", "w-32"],
                ["Сотрудники", "w-28"],
                ["Возраст", "w-24"],
                ["Сайт", "w-24"],
                ["Вакансии", "w-24"],
                ["Продажи", "w-24"],
                ["Маркетинг", "w-28"],
                ["Тип бизнеса", "w-28"],
                ["Источник", "w-28"],
                ["LLM reason", "w-72"],
                ["Комментарий", "w-72"],
              ].map(([column, width]) => (
                <th key={column} className={`border-b border-slate-200 px-3 py-3 font-semibold ${width}`}>
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((company) => (
              <tr key={company.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className={`${cellClass} font-medium text-slate-950`}>{company.company_name}</td>
                <td className={cellClass}>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone={icpTone(company.icp_recommended_action)}>{icpLabel(company.icp_recommended_action)}</Badge>
                    <span className="text-xs font-medium text-slate-700">
                      {company.icp_score === null ? "—" : `${company.icp_score}/100`}
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-slate-500">confidence: {company.icp_confidence || "—"}</div>
                  <div className="mt-1 truncate text-xs text-slate-400">{company.llm_model || "—"}</div>
                </td>
                <td className={`${cellClass} text-slate-700`}>{company.inn || "—"}</td>
                <td className={`${cellClass} text-slate-700`}>{company.ogrn || "—"}</td>
                <td className={`${cellClass} text-slate-700`}>{company.region || "—"}</td>
                <td className={`${cellClass} text-slate-700`}>{company.city || "—"}</td>
                <td className={cellClass}>
                  <div className="font-medium text-slate-800">{company.okved_main || "—"}</div>
                  <div className="max-h-10 overflow-hidden text-xs leading-5 text-slate-500">
                    {cleanOkvedDescription(company.okved_description)}
                  </div>
                </td>
                <td className={`${cellClass} text-slate-700`}>{formatCurrency(company.revenue)}</td>
                <td className={`${cellClass} text-slate-700`}>{formatNumber(company.employees_count)}</td>
                <td className={`${cellClass} text-slate-700`}>{formatNumber(company.company_age)}</td>
                <td className={cellClass}>
                  {company.website ? (
                    <a className="font-medium text-vector hover:underline" href={company.website} rel="noreferrer" target="_blank">
                      сайт
                    </a>
                  ) : (
                    <Badge tone="slate">нет</Badge>
                  )}
                </td>
                <td className={`${cellClass} text-slate-700`}>{formatNumber(company.vacancies_total)}</td>
                <td className={`${cellClass} text-slate-700`}>{formatNumber(company.sales_vacancies)}</td>
                <td className={`${cellClass} text-slate-700`}>{formatNumber(company.marketing_vacancies)}</td>
                <td className={cellClass}>
                  <Badge tone={company.business_type === "B2B" ? "blue" : "slate"}>{company.business_type}</Badge>
                </td>
                <td className={`${cellClass} text-slate-700`}>{company.source_name}</td>
                <td className={`${cellClass} text-slate-600`}>
                  <div className="max-h-20 overflow-hidden text-xs leading-5">{compactText(icpReason(company), 260)}</div>
                </td>
                <td className={`${cellClass} text-slate-600`}>
                  <div className="max-h-16 overflow-hidden text-xs leading-5">
                    {compactText(company.summary_text || company.comment)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!filtered.length ? (
        <div className="px-4 py-10 text-center text-sm text-slate-500">По текущим фильтрам компаний нет.</div>
      ) : null}
    </div>
  );
}
