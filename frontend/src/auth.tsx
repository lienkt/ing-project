import Keycloak from "keycloak-js";
import { useEffect, useState, type ReactNode } from "react";

export const authEnabled = import.meta.env.VITE_AUTH_ENABLED === "true";
const keycloak = authEnabled
  ? new Keycloak({
      url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
      realm: import.meta.env.VITE_KEYCLOAK_REALM || "banking",
      clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "banking-web",
    })
  : undefined;
let initialization: Promise<boolean> | undefined;
export type Permission =
  | "workspace.read"
  | "campaigns.write"
  | "campaigns.delete"
  | "catalog.write"
  | "labels.write"
  | "capture.write"
  | "evaluation.write";
let permissions = new Set<string>();
export const can = (permission: Permission) =>
  !authEnabled || permissions.has(permission);
async function loadPermissions() {
  const base = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
    /\/$/,
    "",
  );
  const response = await fetch(`${base}/api/auth/permissions`, {
    headers: await authHeaders(),
  });
  if (!response.ok) throw new Error("Cannot load account permissions.");
  const result: { permissions: string[] } = await response.json();
  permissions = new Set(result.permissions);
}
export const logout = () => keycloak?.logout({ redirectUri: window.location.origin });
export const username = () =>
  keycloak?.tokenParsed?.preferred_username || "Local workspace";

export async function authHeaders(): Promise<Record<string, string>> {
  if (!keycloak) return {};
  try {
    await keycloak.updateToken(30);
  } catch {
    throw new Error("Session expired. Reload to sign in again.");
  }
  if (!keycloak.token) throw new Error("Login required");
  return { Authorization: `Bearer ${keycloak.token}` };
}

export function AuthGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(!authEnabled);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!keycloak) return;
    initialization ??= keycloak.init({
      onLoad: "login-required",
      pkceMethod: "S256",
      checkLoginIframe: false,
    });
    initialization
      .then(async () => {
        await loadPermissions();
        if (!can("workspace.read")) {
          setError("Your account needs workspace access.");
        } else setReady(true);
      })
      .catch(() =>
        setError(
          "Cannot sign in or load permissions. Check the server configuration and reload.",
        ),
      );
  }, []);
  if (error)
    return (
      <main>
        <p role="alert">{error}</p>
        <button onClick={() => void logout()}>Sign out</button>
      </main>
    );
  if (!ready) return <p role="status">Signing in…</p>;
  return children;
}

export function PermissionOnly({
  permission,
  children,
}: {
  permission: Permission;
  children: ReactNode;
}) {
  return can(permission) ? (
    children
  ) : (
    <p role="alert">You do not have permission to open this page.</p>
  );
}
