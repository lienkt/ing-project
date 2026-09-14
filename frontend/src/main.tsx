import React from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
  Link,
  NavLink,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";
import { LayoutDashboard, Plus, ArrowUpRight } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import Create from "./pages/Create";
import Catalog from "./pages/Catalog";
import DetailsPage from "./pages/Details";
import Evaluate from "./pages/Evaluate";
import "./styles.css";
function Layout() {
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
        <div className="nav-label"></div>
        <nav>
          <NavLink to="/" end>
            <LayoutDashboard size={18} /> Overview
          </NavLink>
          <NavLink to="/campaigns/new">
            <Plus size={18} /> Add campaign
          </NavLink>
          <NavLink to="/banks/new">
            <Plus size={18} /> Add bank
          </NavLink>
          <NavLink to="/projects/new">
            <Plus size={18} /> Add project
          </NavLink>
        </nav>
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
        </header>
        <main>
          <Outlet />
        </main>
        <footer>
          <span></span>
          <span>Observe with purpose. Evaluate with clarity.</span>
        </footer>
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
          <Route
            path="banks/new"
            element={<Catalog key="bank" kind="bank" />}
          />
          <Route
            path="projects/new"
            element={<Catalog key="project" kind="project" />}
          />
          <Route path="campaigns/new" element={<Create />} />
          <Route path="campaigns/:id/edit" element={<Create />} />
          <Route path="campaigns/:id" element={<DetailsPage />} />
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
