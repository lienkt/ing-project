import React, { useEffect, useState } from "react";
import { request } from "./api/campaigns";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
  Link,
  NavLink,
  Outlet,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import {
  LayoutDashboard,
  ChartColumn,
  ChevronDown,
  FilePlus2,
  Landmark,
  PackagePlus,
  Download,
} from "lucide-react";
import Scraping from "./pages/Scraping";
import Compare from "./pages/Compare";
import Dashboard from "./pages/Dashboard";
import Create from "./pages/Create";
import Catalog from "./pages/Catalog";
import DetailsPage from "./pages/Details";
import LabelPage from "./pages/Label";
import Evaluate from "./pages/Evaluate";
import "./styles.css";
function Layout() {
  const [mode, setMode] = useState<"real" | "demo" | null>(null);
  useEffect(() => {
    let active = true;
    request<{ data_mode: "real" | "demo" }>("/environment")
      .then((result) => {
        if (active) setMode(result.data_mode);
      })
      .catch(() => {
        if (active) setMode(null);
      });
    return () => {
      active = false;
    };
  }, []);
  const { pathname } = useLocation();
  return (
    <div className="app">
      <aside className="sidebar">
        <Link
          className="brand brand-signature"
          to="/"
          aria-label="Banking campaigns comparator — Overview"
        >
          <img
            className="brand-symbol"
            src="/brand-mark.svg"
            alt=""
            width="48"
            height="48"
          />
          <span className="brand-wordmark">
            <span className="brand-banking">
              Banking<span className="brand-accent">.</span>
            </span>
            <span className="brand-campaigns">Campaigns</span>
            <span className="brand-comparator">Comparator</span>
          </span>
        </Link>
        <div className="nav-label">ANALYSIS</div>
        <nav>
          <NavLink to="/" end>
            <LayoutDashboard size={18} /> Dataset
          </NavLink>
          <NavLink to="/compare">
            <ChartColumn size={18} /> Compare
          </NavLink>
        </nav>
        <div className="nav-label">TOOLS</div>
        <nav aria-label="Tools">
          <NavLink to="/scraping">
            <Download size={18} aria-hidden="true" /> Scraping
          </NavLink>
        </nav>
        <details className="workspace-menu">
          <summary>
            <span>SETTINGS</span>
            <ChevronDown size={16} aria-hidden="true" />
          </summary>
          <nav aria-label="Settings">
            <NavLink to="/campaigns/new">
              <FilePlus2 size={18} aria-hidden="true" /> Add campaign
            </NavLink>
            <NavLink to="/banks/new">
              <Landmark size={18} aria-hidden="true" /> Add bank
            </NavLink>
            <NavLink to="/projects/new">
              <PackagePlus size={18} aria-hidden="true" /> Add category
            </NavLink>
          </nav>
        </details>
        <div className="sidebar-note"></div>
        <div className="workspace-user">
          <span className="user-avatar">BC</span>
          <div>
            Research workspace<small>Local environment</small>
          </div>
          <span className="online-dot" />
        </div>
      </aside>
      <div className="main-wrap">
        <header className="topbar">
          <span>Bank communication research</span>
          <span className={`data-mode ${mode === "demo" ? "demo" : ""}`}>
            {mode === "demo"
              ? "Demo database · Synthetic data"
              : mode === "real"
                ? "Real database"
                : "Database mode unavailable"}
          </span>
        </header>
        <main
          className={
            pathname === "/" || pathname === "/compare"
              ? "wide-page"
              : pathname.endsWith("/label")
                ? "label-page"
                : "form-page"
          }
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="scraping" element={<Scraping />} />
          <Route path="compare" element={<Compare />} />
          <Route path="banks/new" element={<Catalog key="bank" kind="bank" />} />
          <Route
            path="projects/new"
            element={<Catalog key="project" kind="project" />}
          />
          <Route path="campaigns/new" element={<Create />} />
          <Route path="campaigns/:id/edit" element={<Create />} />
          <Route path="campaigns/:id" element={<DetailsPage />} />
          <Route path="campaigns/:id/label" element={<LabelPage />} />
          <Route path="campaigns/:id/evaluate" element={<Evaluate />} />
          <Route
            path="*"
            element={
              <>
                <h1>Page not found</h1>
                <Link to="/">Back to dashboard</Link>
              </>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
