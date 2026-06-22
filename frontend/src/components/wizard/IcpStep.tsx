import { Card, CardBody, CardHeader } from "../ui/Card";
import { Checkbox } from "../ui/Checkbox";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import type { SearchPayload } from "../../types/search";

interface IcpStepProps {
  search: SearchPayload;
  onChange: <K extends keyof SearchPayload>(key: K, value: SearchPayload[K]) => void;
}

const industryOptions = [
  "IT",
  "Маркетинг",
  "Производство",
  "Логистика",
  "Медицина",
  "Образование",
  "Консалтинг",
  "Строительство",
  "Финансы",
  "Юридические услуги",
  "Другое",
].map((value) => ({ label: value, value }));

const regionOptions = ["Москва", "Санкт-Петербург", "Московская область", "Вся РФ", "Другой регион"].map(
  (value) => ({ label: value, value }),
);

export function IcpStep({ search, onChange }: IcpStepProps) {
  const nullable = (value: string) => (value ? value : null);
  const numberOrNull = (value: string) => (value ? Number(value) : null);

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold text-slate-950">ICP / кого искать</h2>
        <p className="mt-1 text-sm text-slate-500">Фильтры компании: отрасль, география, масштаб и профиль.</p>
      </CardHeader>
      <CardBody className="grid gap-4">
        <div className="grid gap-4 lg:grid-cols-3">
          <Select
            label="Отрасль"
            options={[{ label: "Не выбрано", value: "" }, ...industryOptions]}
            value={search.industry}
            onChange={(event) => onChange("industry", nullable(event.target.value))}
          />
          <Input
            label="ОКВЭД"
            placeholder="62.01"
            value={search.okved}
            onChange={(event) => onChange("okved", nullable(event.target.value))}
          />
          <Select
            label="Тип бизнеса"
            options={["B2B", "B2C", "B2G", "Любой"].map((value) => ({ label: value, value }))}
            value={search.business_type}
            onChange={(event) => onChange("business_type", event.target.value)}
          />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Select
            label="Регион"
            options={[{ label: "Не выбрано", value: "" }, ...regionOptions]}
            value={search.region}
            onChange={(event) => onChange("region", nullable(event.target.value))}
          />
          <Input
            label="Город"
            placeholder="Москва"
            value={search.city}
            onChange={(event) => onChange("city", nullable(event.target.value))}
          />
        </div>
        <div className="grid gap-4 lg:grid-cols-4">
          <Input
            label="Выручка от"
            type="number"
            value={search.revenue_min}
            onChange={(event) => onChange("revenue_min", numberOrNull(event.target.value))}
          />
          <Input
            label="Выручка до"
            type="number"
            value={search.revenue_max}
            onChange={(event) => onChange("revenue_max", numberOrNull(event.target.value))}
          />
          <Input
            label="Сотрудников от"
            type="number"
            value={search.employees_min}
            onChange={(event) => onChange("employees_min", numberOrNull(event.target.value))}
          />
          <Input
            label="Сотрудников до"
            type="number"
            value={search.employees_max}
            onChange={(event) => onChange("employees_max", numberOrNull(event.target.value))}
          />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Input
            label="Возраст компании от, лет"
            type="number"
            value={search.company_age_min}
            onChange={(event) => onChange("company_age_min", numberOrNull(event.target.value))}
          />
          <Checkbox
            checked={search.active_only}
            label="Только действующие компании"
            description="Моковый provider учитывает это как ограничение качества."
            onChange={(checked) => onChange("active_only", checked)}
          />
        </div>
      </CardBody>
    </Card>
  );
}
