import { Route, Routes } from "react-router-dom";

import { Shell } from "./components/Shell";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { BuilderPage } from "./pages/BuilderPage";
import { LibraryPage } from "./pages/LibraryPage";
import { ResultsPage } from "./pages/ResultsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Shell />}>
        <Route index element={<LibraryPage />} />
        <Route path="/builder" element={<BuilderPage />} />
        <Route path="/results">
          <Route path=":playlistId" element={<ResultsPage />} />
          <Route index element={<ResultsPage />} />
        </Route>
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  );
}
