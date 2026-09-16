// Resolve the backend URL for local development and GitHub Codespaces.
function resolveBaseUrl() {
  const configured = import.meta.env.VITE_API_URL?.trim();

  if (configured) {
    return configured.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;

    // GitHub Codespaces:
    // frontend: <codespace>-5173.app.github.dev
    // backend:  <codespace>-8000.app.github.dev
    if (hostname.includes("-5173.app.github.dev")) {
      return `${protocol}//${hostname.replace(
        "-5173.app.github.dev",
        "-8000.app.github.dev"
      )}`;
    }
  }

  return "http://localhost:8000";
}

const BASE_URL = resolveBaseUrl();

async function get(path) {
  const res = await fetch(`${BASE_URL}${path}`);

  if (!res.ok) {
    throw new Error(`Request to ${path} failed with ${res.status}`);
  }

  return res.json();
}

export const api = {
  listSuppliers: () => get("/suppliers"),
  getSupplier: (id) => get(`/suppliers/${id}`),
  getForecast: (id) => get(`/suppliers/${id}/forecast`),
};
