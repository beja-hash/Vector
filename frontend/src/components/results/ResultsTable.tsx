import { useMemo, useState } from "react";

import { Badge } from "../ui/Badge";
import { Checkbox } from "../ui/Checkbox";
import { Input } from "../ui/Input";
import { formatCurrency, formatNumber } from "../../lib/format";
import type { CompanyResult } from "../../types/company";

interface ResultsTableProps {
  results: CompanyResult[];
}

export function ResultsTable({ results }: ResultsTableProps) {
  const [query, setQuery] = useState("");
  const [onlyWebsite, setOnlyWebsite] = useState(false);
  const [onlyVacancies, setOnlyVacancies] = useState(false);
  const [onlyB2B, setOnlyB2B] = useState(false);

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return results.filter((company) => {
      const matchesQuery =
        !normalizedQuery ||
        company.company_name.toLowerCase().includes(normalizedQuery) ||
        company.inn.includes(normalizedQuery);
      const matchesWebsite = !onlyWebsite || company.has_website;
      const matchesVacancies = !onlyVacancies || company.vacancies_total > 0;
      const matchesB2B = !onlyB2B || company.business_type === "B2B";
      return matchesQuery && matchesWebsite && matchesVacancies && matchesB2B;
    });
  }, [onlyB2B, onlyVacancies, onlyWebsite, query, results]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="grid gap-3 border-b border-slate-100 p-4 lg:grid-cols-[1fr_auto_auto_auto]">
        <Input
          label="Поиск по названию / ИНН"
          placeholder="ООО или 770..."
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Checkbox checked={onlyWebsite} label="Только с сайтом" onChange={setOnlyWebsite} />
        <Checkbox checked={onlyVacancies} label="Только с вакансиями" onChange={setOnlyVacancies} />
        <Checkbox checked={onlyB2B} label="Только B2B" onChange={setOnlyB2B} />
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-[1400px] w-full border-collapse text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              {[
                "Компания",
                "ИНН",
                "ОГРН",
                "Регион",
                "Город",
                "ОКВЭД",
                "Выручка",
                "Сотрудники",
                "Возраст",
                "Сайт",
                "Вакансии",
                "Продажи",
                "Маркетинг",
                "Тип бизнеса",
                "Источник",
                "Комментарий",
              ].map((column) => (
                <th key={column} className="border-b border-slate-200 px-3 py-3 font-semibold">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((company) => (
              <tr key={company.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <td className="px-3 py-3 font-medium text-slate-950">{company.company_name}</td>
                <td className="px-3 py-3 text-slate-700">{company.inn}</td>
                <td className="px-3 py-3 text-slate-700">{company.ogrn}</td>
                <td className="px-3 py-3 text-slate-700">{company.region || "—"}</td>
                <td className="px-3 py-3 text-slate-700">{company.city || "—"}</td>
                <td className="px-3 py-3">
                  <div className="font-medium text-slate-800">{company.okved_main || "—"}</div>
                  <div className="max-w-56 text-xs text-slate-500">{company.okved_description || "—"}</div>
                </td>
                <td className="px-3 py-3 text-slate-700">{formatCurrency(company.revenue)}</td>
                <td className="px-3 py-3 text-slate-700">{formatNumber(company.employees_count)}</td>
                <td className="px-3 py-3 text-slate-700">{formatNumber(company.company_age)}</td>
                <td className="px-3 py-3">
                  {company.website ? (
                    <a className="font-medium text-vector hover:underline" href={company.website} rel="noreferrer" target="_blank">
                      сайт
                    </a>
                  ) : (
                    <Badge tone="slate">нет</Badge>
                  )}
                </td>
                <td className="px-3 py-3 text-slate-700">{formatNumber(company.vacancies_total)}</td>
                <td className="px-3 py-3 text-slate-700">{formatNumber(company.sales_vacancies)}</td>
                <td className="px-3 py-3 text-slate-700">{formatNumber(company.marketing_vacancies)}</td>
                <td className="px-3 py-3">
                  <Badge tone={company.business_type === "B2B" ? "blue" : "slate"}>{company.business_type}</Badge>
                </td>
                <td className="px-3 py-3 text-slate-700">{company.source_name}</td>
                <td className="max-w-64 px-3 py-3 text-slate-600">{company.comment || "—"}</td>
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
