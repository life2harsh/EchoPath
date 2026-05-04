import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";

import { fetchHealth } from "../lib/api";

const navItems = [
  { to: "/", label: "Library" },
  { to: "/builder", label: "Builder" },
  { to: "/results", label: "Results" },
  { to: "/analytics", label: "Analytics" },
];

export function Shell() {
  const { data } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="app-shell">
      <header className="hero">
        <div className="hero__content">
          <p className="eyebrow">EchoPath / Web Console</p>
          <h1>Graph-guided playlists with a frontend that already feels real.</h1>
          <p className="hero__lede">
            This first pass is wired for the course demo: browse the track universe, choose a search
            strategy, inspect transitions, and keep the dataset handoff clean.
          </p>
        </div>
        <div className="hero__status">
          <div className="status-panel">
            <span>Dataset</span>
            <strong>{data?.dataset.track_count ?? "--"} tracks</strong>
            <small>{data?.dataset.using_sample_data ? "Sample metadata active" : "Real manifest loaded"}</small>
          </div>
          <div className="status-panel">
            <span>Backend</span>
            <strong>{data?.status ?? "starting"}</strong>
            <small>{data?.app_name ?? "Connecting to API"}</small>
          </div>
        </div>
      </header>

      <nav className="top-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `top-nav__link ${isActive ? "top-nav__link--active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="page-shell">
        <Outlet />
      </main>
    </div>
  );
}
