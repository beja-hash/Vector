import { BriefcaseBusiness, Globe2, Target, Users } from "lucide-react";

import { Card, CardBody } from "../ui/Card";
import { formatCurrency, formatNumber } from "../../lib/format";
import type { CompanyResult } from "../../types/company";

interface StatsCardsProps {
  results: CompanyResult[];
}

export function StatsCards({ results }: StatsCardsProps) {
  const withWebsite = results.filter((company) => company.has_website).length;
  const withVacancies = results.filter((company) => company.vacancies_total > 0).length;
  const withSalesVacancies = results.filter((company) => company.sales_vacancies > 0).length;
  const revenues = results.map((company) => company.revenue).filter((value): value is number => value !== null);
  const averageRevenue = revenues.length
    ? Math.round(revenues.reduce((sum, value) => sum + value, 0) / revenues.length)
    : null;

  const cards = [
    { label: "Найдено компаний", value: formatNumber(results.length), icon: Target },
    { label: "С сайтами", value: formatNumber(withWebsite), icon: Globe2 },
    { label: "С вакансиями", value: formatNumber(withVacancies), icon: BriefcaseBusiness },
    { label: "С вакансиями продажников", value: formatNumber(withSalesVacancies), icon: Users },
    { label: "Средняя выручка", value: formatCurrency(averageRevenue), icon: Target },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card key={card.label}>
            <CardBody className="flex items-start justify-between gap-3 p-4">
              <div>
                <div className="text-sm text-slate-500">{card.label}</div>
                <div className="mt-2 text-xl font-semibold text-slate-950">{card.value}</div>
              </div>
              <div className="rounded-md bg-indigo-50 p-2 text-vector">
                <Icon className="h-4 w-4" />
              </div>
            </CardBody>
          </Card>
        );
      })}
    </div>
  );
}
