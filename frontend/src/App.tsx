import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { NewSearchPage } from "./pages/NewSearchPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { SearchResultsPage } from "./pages/SearchResultsPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="searches/new" element={<NewSearchPage />} />
        <Route path="searches/:searchId" element={<SearchResultsPage />} />
      </Route>
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  );
}
