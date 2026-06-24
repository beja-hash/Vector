import { Card, CardBody, CardHeader } from "../ui/Card";
import { Checkbox } from "../ui/Checkbox";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import type { LlmSettings, SearchPayload } from "../../types/search";

interface VolumeStepProps {
  search: SearchPayload;
  llmSettings: LlmSettings | null;
  onChange: <K extends keyof SearchPayload>(key: K, value: SearchPayload[K]) => void;
}

const presetCounts = [10, 50, 100, 300, 500];

export function VolumeStep({ search, llmSettings, onChange }: VolumeStepProps) {
  const selectedCount = presetCounts.includes(search.requested_companies_count)
    ? String(search.requested_companies_count)
    : "custom";
  const llmAvailable = Boolean(llmSettings?.polza_enabled && llmSettings.llm_scoring_enabled);
  const threshold = search.llm_scoring_threshold ?? llmSettings?.threshold ?? 75;

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold text-slate-950">Объём и запуск</h2>
        <p className="mt-1 text-sm text-slate-500">Выберите размер выборки и минимальную полноту данных.</p>
      </CardHeader>
      <CardBody className="grid gap-4">
        <div className="grid gap-4 lg:grid-cols-3">
          <Select
            label="Источник данных"
            options={[
              { label: "Mock", value: "mock" },
              { label: "Rusprofile", value: "rusprofile" },
            ]}
            value={search.data_source}
            onChange={(event) => onChange("data_source", event.target.value as SearchPayload["data_source"])}
          />
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
        {search.data_source === "rusprofile" ? (
          <div className="grid gap-3 rounded-md border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800 md:grid-cols-2">
            <Checkbox checked={search.visible_browser} label="Видимый браузер" onChange={(checked) => onChange("visible_browser", checked)} />
            <Checkbox checked={search.human_mode} label="Human-like режим" onChange={(checked) => onChange("human_mode", checked)} />
            <Checkbox
              checked={search.llm_scoring_enabled && llmAvailable}
              disabled={!llmAvailable}
              label="LLM ICP scoring"
              description={llmAvailable ? "Polza.ai будет оценивать компании после hard prefilter." : "Выключено в backend env."}
              onChange={(checked) => onChange("llm_scoring_enabled", checked)}
            />
            <Input
              label="Threshold"
              max={100}
              min={0}
              type="number"
              value={threshold}
              onChange={(event) => onChange("llm_scoring_threshold", Number(event.target.value || threshold))}
            />
            <Input className="font-mono" label="Model" readOnly value={llmSettings?.model || "—"} />
            <div className="rounded-md border border-indigo-100 bg-white/70 px-3 py-2 text-xs text-indigo-800">
              Review min score: {llmSettings?.review_min_score ?? 50}
            </div>
            <div className="md:col-span-2">
              Поиск сохранится как draft. На странице результата нажмите «Запустить Rusprofile», чтобы открыть браузер и собрать реальные компании.
            </div>
          </div>
        ) : (
          <div className="rounded-md border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
            Mock provider сразу сгенерирует демо-результаты и переведёт поиск в completed.
          </div>
        )}
      </CardBody>
    </Card>
  );
}
