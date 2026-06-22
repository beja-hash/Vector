import { Card, CardBody, CardHeader } from "../ui/Card";
import { Checkbox } from "../ui/Checkbox";
import { Select } from "../ui/Select";
import type { SearchPayload } from "../../types/search";

interface SignalsStepProps {
  search: SearchPayload;
  onChange: <K extends keyof SearchPayload>(key: K, value: SearchPayload[K]) => void;
}

const vacancyCategories = [
  { label: "Продажи", value: "sales" },
  { label: "Маркетинг", value: "marketing" },
  { label: "Разработка", value: "development" },
  { label: "Руководители", value: "leadership" },
  { label: "Любые", value: "any" },
];

const exclusions: Array<{ key: keyof SearchPayload; label: string }> = [
  { key: "exclude_ip", label: "ИП" },
  { key: "exclude_liquidated", label: "Ликвидированные компании" },
  { key: "exclude_no_revenue", label: "Компании без выручки" },
  { key: "exclude_microbusiness", label: "Микробизнес" },
  { key: "exclude_government", label: "Госучреждения" },
  { key: "exclude_marketplace_sellers", label: "Маркетплейс-селлеров" },
];

export function SignalsStep({ search, onChange }: SignalsStepProps) {
  const toggleCategory = (value: string) => {
    const next = search.vacancy_categories.includes(value)
      ? search.vacancy_categories.filter((item) => item !== value)
      : [...search.vacancy_categories, value];
    onChange("vacancy_categories", next);
  };

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold text-slate-950">Сигналы качества</h2>
        <p className="mt-1 text-sm text-slate-500">Настройте признаки, которые делают компанию более похожей на ICP.</p>
      </CardHeader>
      <CardBody className="grid gap-5">
        <div className="grid gap-4 lg:grid-cols-3">
          <Select
            label="Нужен сайт"
            options={[
              { label: "Не важно", value: "any" },
              { label: "Да", value: "required" },
              { label: "Нет", value: "not_required" },
            ]}
            value={search.website_requirement}
            onChange={(event) => onChange("website_requirement", event.target.value)}
          />
          <Select
            label="Вакансии"
            options={[
              { label: "Не важно", value: "any" },
              { label: "Есть вакансии", value: "has_vacancies" },
            ]}
            value={search.vacancies_requirement}
            onChange={(event) => onChange("vacancies_requirement", event.target.value)}
          />
          <Select
            label="Наличие отдела продаж"
            options={[
              { label: "Не важно", value: "any" },
              { label: "Желательно", value: "preferred" },
              { label: "Обязательно", value: "required" },
            ]}
            value={search.sales_department_requirement}
            onChange={(event) => onChange("sales_department_requirement", event.target.value)}
          />
        </div>

        <div>
          <div className="mb-2 text-sm font-medium text-slate-700">Какие вакансии искать</div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
            {vacancyCategories.map((category) => (
              <Checkbox
                key={category.value}
                checked={search.vacancy_categories.includes(category.value)}
                label={category.label}
                onChange={() => toggleCategory(category.value)}
              />
            ))}
          </div>
        </div>

        <Checkbox
          checked={search.check_website}
          label="Проверять сайт компании"
          description="Сейчас это влияет только на сохранённую конфигурацию поиска."
          onChange={(checked) => onChange("check_website", checked)}
        />

        <div>
          <div className="mb-2 text-sm font-medium text-slate-700">Исключать</div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {exclusions.map((item) => (
              <Checkbox
                key={item.key}
                checked={Boolean(search[item.key])}
                label={item.label}
                onChange={(checked) => onChange(item.key, checked as never)}
              />
            ))}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
