import { AuthGate, PermissionOnly, authEnabled, can, logout, username } from "./auth";
import React from "react";
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
        {(can("capture.write") || can("campaigns.write") || can("catalog.write")) && (
          <>
            <div className="nav-label">TOOLS</div>
            <nav aria-label="Tools">
              {can("capture.write") && (
                <NavLink to="/scraping">
                  <Download size={18} aria-hidden="true" /> Scraping
                </NavLink>
              )}
            </nav>
            <details className="workspace-menu">
              <summary>
                <span>SETTINGS</span>
                <ChevronDown size={16} aria-hidden="true" />
              </summary>
              <nav aria-label="Settings">
                {can("campaigns.write") && (
                  <NavLink to="/campaigns/new">
                    <FilePlus2 size={18} aria-hidden="true" /> Add campaign
                  </NavLink>
                )}
                {can("catalog.write") && (
                  <NavLink to="/banks/new">
                    <Landmark size={18} aria-hidden="true" /> Add bank
                  </NavLink>
                )}
                {can("catalog.write") && (
                  <NavLink to="/projects/new">
                    <PackagePlus size={18} aria-hidden="true" /> Add category
                  </NavLink>
                )}
              </nav>
            </details>
          </>
        )}
        <div className="sidebar-note"></div>
        <div className="workspace-user">
          <span className="user-avatar">BC</span>
          <div className="workspace-user-details">
            {username()}
            {authEnabled && (
              <button className="signout-button" onClick={() => void logout()}>
                Sign out
              </button>
            )}
          </div>
        </div>
      </aside>
      <div className="main-wrap">
        <header className="topbar">
          <span>Bank communication research</span>
        </header>
        <main
          className={
            pathname === "/" || pathname === "/compare" || pathname === "/scraping"
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
    <AuthGate>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route
              path="scraping"
              element={
                <PermissionOnly permission="capture.write">
                  <Scraping />
                </PermissionOnly>
              }
            />
            <Route path="compare" element={<Compare />} />
            <Route
              path="banks/new"
              element={
                <PermissionOnly permission="catalog.write">
                  <Catalog key="bank" kind="bank" />
                </PermissionOnly>
              }
            />
            <Route
              path="projects/new"
              element={
                <PermissionOnly permission="catalog.write">
                  <Catalog key="project" kind="project" />
                </PermissionOnly>
              }
            />
            <Route
              path="campaigns/new"
              element={
                <PermissionOnly permission="campaigns.write">
                  <Create />
                </PermissionOnly>
              }
            />
            <Route
              path="campaigns/:id/edit"
              element={
                <PermissionOnly permission="campaigns.write">
                  <Create />
                </PermissionOnly>
              }
            />
            <Route path="campaigns/:id" element={<DetailsPage />} />
            <Route
              path="campaigns/:id/label"
              element={
                <PermissionOnly permission="labels.write">
                  <LabelPage />
                </PermissionOnly>
              }
            />
            <Route
              path="campaigns/:id/evaluate"
              element={
                <PermissionOnly permission="evaluation.write">
                  <Evaluate />
                </PermissionOnly>
              }
            />
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
    </AuthGate>
  </React.StrictMode>,
);
