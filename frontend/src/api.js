const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
