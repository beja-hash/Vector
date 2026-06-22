import { Check } from "lucide-react";

interface WizardProgressProps {
  currentStep: number;
  steps: string[];
}

export function WizardProgress({ currentStep, steps }: WizardProgressProps) {
  return (
    <div className="grid gap-2 sm:grid-cols-4">
      {steps.map((step, index) => {
        const isDone = index < currentStep;
        const isActive = index === currentStep;
        return (
          <div
            key={step}
            className={`flex items-center gap-3 rounded-md border px-3 py-2 ${
              isActive
                ? "border-vector bg-indigo-50 text-vector"
                : isDone
                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                  : "border-slate-200 bg-white text-slate-500"
            }`}
          >
            <span
              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                isDone ? "bg-emerald-600 text-white" : isActive ? "bg-vector text-white" : "bg-slate-100"
              }`}
            >
              {isDone ? <Check className="h-3.5 w-3.5" /> : index + 1}
            </span>
            <span className="text-sm font-medium">{step}</span>
          </div>
        );
      })}
    </div>
  );
}
