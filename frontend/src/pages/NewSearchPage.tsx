import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { getProject } from "../api/projectsApi";
import { createSearch } from "../api/searchesApi";
import { Button } from "../components/ui/Button";
import { IcpStep } from "../components/wizard/IcpStep";
import { ProjectStep } from "../components/wizard/ProjectStep";
import { SearchSummary } from "../components/wizard/SearchSummary";
import { SignalsStep } from "../components/wizard/SignalsStep";
import { VolumeStep } from "../components/wizard/VolumeStep";
import { WizardProgress } from "../components/wizard/WizardProgress";
import type { ProjectPayload } from "../types/project";
import type { SearchPayload } from "../types/search";

const steps = ["Проект", "ICP", "Сигналы", "Запуск"];

const defaultProject: ProjectPayload = {
  name: "",
  client_offer: "",
  average_deal_size: null,
  sales_type: "B2B",
  usual_customers: "",
  excluded_customers: "",
  comment: "",
};

const defaultSearch: SearchPayload = {
  project: defaultProject,
  project_id: null,
  industry: null,
  okved: null,
  region: "Москва",
  city: null,
  revenue_min: null,
  revenue_max: null,
  employees_min: null,
  employees_max: null,
  company_age_min: null,
  active_only: true,
  business_type: "B2B",
  website_requirement: "any",
  vacancies_requirement: "any",
  vacancy_categories: [],
  sales_department_requirement: "any",
  check_website: false,
  exclude_ip: true,
  exclude_liquidated: true,
  exclude_no_revenue: false,
  exclude_microbusiness: false,
  exclude_government: false,
  exclude_marketplace_sellers: false,
  requested_companies_count: 50,
  data_completeness: "partial_allowed",
  export_format: "CSV",
};

export function NewSearchPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<SearchPayload>({ ...defaultSearch, project: { ...defaultProject } });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const projectId = searchParams.get("projectId");
    if (!projectId) return;

    getProject(projectId)
      .then((project) => {
        setForm((current) => ({
          ...current,
          project_id: project.id,
          project: {
            name: project.name,
            client_offer: project.client_offer,
            average_deal_size: project.average_deal_size,
            sales_type: project.sales_type,
            usual_customers: project.usual_customers || "",
            excluded_customers: project.excluded_customers || "",
            comment: project.comment || "",
          },
        }));
      })
      .catch((err: Error) => setError(err.message));
  }, [searchParams]);

  const project = form.project ?? defaultProject;

  const updateProject = <K extends keyof ProjectPayload>(key: K, value: ProjectPayload[K]) => {
    setForm((current) => ({
      ...current,
      project: { ...(current.project ?? defaultProject), [key]: value },
    }));
  };

  const updateSearch = <K extends keyof SearchPayload>(key: K, value: SearchPayload[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async () => {
    setError(null);
    if (!project.name.trim() || !project.client_offer.trim()) {
      setStep(0);
      setError("Заполните название проекта и оффер клиента.");
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: SearchPayload = form.project_id ? { ...form, project: null } : form;
      const created = await createSearch(payload);
      navigate(`/searches/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось запустить поиск");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-950">Создание поиска</h1>
        <p className="mt-1 text-sm text-slate-500">Заполните параметры ICP, Vector сохранит поиск и сгенерирует mock-результаты.</p>
      </section>

      <WizardProgress currentStep={step} steps={steps} />

      {form.project_id ? (
        <div className="rounded-md border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
          Новый поиск будет сохранён в существующий проект: <strong>{project.name}</strong>.
        </div>
      ) : null}

      {error ? <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
        <div>
          {step === 0 ? <ProjectStep project={project} onChange={updateProject} /> : null}
          {step === 1 ? <IcpStep search={form} onChange={updateSearch} /> : null}
          {step === 2 ? <SignalsStep search={form} onChange={updateSearch} /> : null}
          {step === 3 ? <VolumeStep search={form} onChange={updateSearch} /> : null}

          <div className="mt-5 flex items-center justify-between">
            <Button disabled={step === 0 || isSubmitting} type="button" variant="secondary" onClick={() => setStep((value) => value - 1)}>
              Назад
            </Button>
            {step < steps.length - 1 ? (
              <Button type="button" onClick={() => setStep((value) => value + 1)}>
                Далее
              </Button>
            ) : (
              <Button disabled={isSubmitting} type="button" onClick={handleSubmit}>
                {isSubmitting ? "Запускаем…" : "Запустить поиск"}
              </Button>
            )}
          </div>
        </div>
        <SearchSummary search={{ ...form, project }} />
      </div>
    </div>
  );
}
