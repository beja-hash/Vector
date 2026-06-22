import type { TextareaHTMLAttributes } from "react";

interface TextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "value"> {
  label?: string;
  hint?: string;
  value?: string | null;
}

export function Textarea({ label, hint, className = "", value, ...props }: TextareaProps) {
  return (
    <label className="block">
      {label ? <span className="mb-1.5 block text-sm font-medium text-slate-700">{label}</span> : null}
      <textarea
        className={`min-h-24 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-vector focus:ring-2 focus:ring-vector/15 ${className}`}
        value={value ?? ""}
        {...props}
      />
      {hint ? <span className="mt-1 block text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
}
