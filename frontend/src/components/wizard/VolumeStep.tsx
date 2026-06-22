import { Card, CardBody, CardHeader } from "../ui/Card";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import type { SearchPayload } from "../../types/search";

interface VolumeStepProps {
  search: SearchPayload;
  onChange: <K extends keyof SearchPayload>(key: K, value: SearchPayload[K]) => void;
}

const presetCounts = [10, 50, 100, 300, 500];

export function VolumeStep({ search, onChange }: VolumeStepProps) {
  const selectedCount = presetCounts.includes(search.requested_companies_count)
    ? String(search.requested_companies_count)
    : "custom";

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold text-slate-950">Объём и запуск</h2>
        <p className="mt-1 text-sm text-slate-500">Выберите размер выборки и минимальную полноту данных.</p>
      </CardHeader>
      <CardBody className="grid gap-4">
        <div className="grid gap-4 lg:grid-cols-3">
          <Select
            label="Сколько компаний найти"
            options={[
              ...presetCounts.map((count) => ({ label: String(count), value: String(count) })),
              { label: "Своё число", value: "custom" },
            ]}
            value={selectedCount}
            onChange={(event) => {
              if (event.target.value === "custom") {
                onChange("requested_companies_count", search.requested_companies_count);
              } else {
                onChange("requested_companies_count", Number(event.target.value));
              }
            }}
          />
          {selectedCount === "custom" ? (
            <Input
              label="Своё число"
              min={1}
              type="number"
              value={search.requested_companies_count}
              onChange={(event) => onChange("requested_companies_count", Number(event.target.value || 1))}
            />
          ) : null}
          <Select
            label="Формат выгрузки"
            options={["CSV", "XLSX", "JSON"].map((value) => ({ label: value, value }))}
            value={search.export_format}
            onChange={(event) => onChange("export_format", event.target.value)}
          />
        </div>
        <Select
          label="Минимальная полнота данных"
          options={[
            { label: "Можно частично заполненные", value: "partial_allowed" },
            { label: "Только компании с сайтом", value: "website_only" },
            { label: "Только компании с выручкой", value: "revenue_only" },
            { label: "Только компании с вакансиями", value: "vacancies_only" },
          ]}
          value={search.data_completeness}
          onChange={(event) => onChange("data_completeness", event.target.value)}
        />
        <div className="rounded-md border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
          Поиск будет выполнен через mock provider и сразу перейдёт в статус completed. Реальные источники можно
          подключить позже через интерфейс CompanyProvider.
        </div>
      </CardBody>
    </Card>
  );
}
