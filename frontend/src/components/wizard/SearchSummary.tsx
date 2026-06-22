import { Card, CardBody, CardHeader } from "../ui/Card";
import { formatCurrency, formatNumber } from "../../lib/format";
import type { SearchPayload } from "../../types/search";

interface SearchSummaryProps {
  search: SearchPayload;
}

function valueOrDash(value?: string | number | null) {
  return value === null || value === undefined || value === "" ? "—" : String(value);
}

export function SearchSummary({ search }: SearchSummaryProps) {
  const project = search.project;
  const rows = [
    ["Проект", project?.name || "—"],
    ["Оффер", project?.client_offer || "—"],
    ["Средний чек", formatCurrency(project?.average_deal_size)],
    ["Отрасль", valueOrDash(search.industry)],
    ["Регион", valueOrDash(search.region)],
    ["Тип бизнеса", search.business_type],
    ["Выручка", `${formatNumber(search.revenue_min)} - ${formatNumber(search.revenue_max)}`],
    ["Сотрудники", `${formatNumber(search.employees_min)} - ${formatNumber(search.employees_max)}`],
    ["Компаний", formatNumber(search.requested_companies_count)],
    ["Сайт", search.website_requirement === "required" ? "нужен" : search.website_requirement === "not_required" ? "не нужен" : "не важно"],
    ["Вакансии", search.vacancies_requirement === "has_vacancies" ? "есть" : "не важно"],
  ];

  return (
    <Card className="sticky top-24">
      <CardHeader>
        <h2 className="text-base font-semibold text-slate-950">Сводка поиска</h2>
        <p className="mt-1 text-xs text-slate-500">Параметры, которые уйдут в backend.</p>
      </CardHeader>
      <CardBody className="space-y-3">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-start justify-between gap-4 border-b border-slate-100 pb-2 last:border-0 last:pb-0">
            <span className="text-xs text-slate-500">{label}</span>
            <span className="max-w-44 text-right text-sm font-medium text-slate-800">{value}</span>
          </div>
        ))}
      </CardBody>
    </Card>
  );
}
