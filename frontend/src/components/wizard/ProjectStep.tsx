import { Card, CardBody, CardHeader } from "../ui/Card";
import { Input } from "../ui/Input";
import { Select } from "../ui/Select";
import { Textarea } from "../ui/Textarea";
import type { ProjectPayload } from "../../types/project";

interface ProjectStepProps {
  project: ProjectPayload;
  onChange: <K extends keyof ProjectPayload>(key: K, value: ProjectPayload[K]) => void;
}

export function ProjectStep({ project, onChange }: ProjectStepProps) {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold text-slate-950">Проект клиента</h2>
        <p className="mt-1 text-sm text-slate-500">Опишите, что продаёт клиент и кому обычно подходит оффер.</p>
      </CardHeader>
      <CardBody className="grid gap-4">
        <div className="grid gap-4 lg:grid-cols-2">
          <Input
            label="Название проекта"
            placeholder="CRM-интеграторы РФ"
            value={project.name}
            onChange={(event) => onChange("name", event.target.value)}
          />
          <Input
            label="Средний чек"
            placeholder="300000"
            type="number"
            value={project.average_deal_size}
            onChange={(event) =>
              onChange("average_deal_size", event.target.value ? Number(event.target.value) : null)
            }
          />
        </div>
        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <Input
            label="Что продаёт клиент"
            placeholder="Внедрение amoCRM и Битрикс24"
            value={project.client_offer}
            onChange={(event) => onChange("client_offer", event.target.value)}
          />
          <Select
            label="Тип продажи"
            options={[
              { label: "B2B", value: "B2B" },
              { label: "B2C", value: "B2C" },
              { label: "B2G", value: "B2G" },
            ]}
            value={project.sales_type}
            onChange={(event) => onChange("sales_type", event.target.value as ProjectPayload["sales_type"])}
          />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Textarea
            label="Кому обычно продаёт"
            placeholder="B2B-компании с отделом продаж"
            value={project.usual_customers}
            onChange={(event) => onChange("usual_customers", event.target.value)}
          />
          <Textarea
            label="Кому точно НЕ продаёт"
            placeholder="ИП, микробизнес, госучреждения"
            value={project.excluded_customers}
            onChange={(event) => onChange("excluded_customers", event.target.value)}
          />
        </div>
        <Textarea
          label="Комментарий"
          placeholder="Важные ограничения или контекст для команды"
          value={project.comment}
          onChange={(event) => onChange("comment", event.target.value)}
        />
      </CardBody>
    </Card>
  );
}
