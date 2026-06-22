import { Plus } from "lucide-react";
import { Link } from "react-router-dom";

export function Topbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur lg:px-8">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-950 lg:hidden">Vector</div>
          <div className="truncate text-xs text-slate-500">Внутренний инструмент поиска компаний под ICP</div>
        </div>
        <Link
          className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-vector px-3 text-sm font-medium text-white transition hover:bg-indigo-700"
          to="/searches/new"
        >
          <Plus className="h-4 w-4" />
          Создать поиск
        </Link>
      </div>
    </header>
  );
}
