import { Building2, LayoutDashboard, Search } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Проекты", icon: Building2 },
  { to: "/searches/new", label: "Создать поиск", icon: Search },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white px-4 py-5 lg:block">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-graphite text-sm font-bold text-white">
          V
        </div>
        <div>
          <div className="text-base font-semibold text-slate-950">Vector</div>
          <div className="text-xs text-slate-500">ConnectUp internal</div>
        </div>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition ${
                  isActive ? "bg-indigo-50 text-vector" : "text-slate-600 hover:bg-slate-50 hover:text-slate-950"
                }`
              }
              to={item.to}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
