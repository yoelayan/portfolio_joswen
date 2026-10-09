import { DEFAULT_SITE } from "./defaults.js";

// En Railway: BACKEND_URL = http://<servicio-backend>.railway.internal:8000 (red privada).
const BACKEND = (process.env.BACKEND_URL || "http://localhost:8000").replace(/\/+$/, "");
const TTL_MS = 10_000;
const cache = new Map();

async function request(path) {
  const hit = cache.get(path);
  if (hit && Date.now() - hit.at < TTL_MS) return hit.data;

  const response = await fetch(`${BACKEND}${path}`, {
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(8000),
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`El backend respondió ${response.status} en ${path}`);

  const data = await response.json();
  cache.set(path, { at: Date.now(), data });
  return data;
}

export async function getSite() {
  try {
    return (await request("/api/site/")) ?? DEFAULT_SITE;
  } catch (error) {
    console.error("[api] getSite:", error.message);
    return DEFAULT_SITE;
  }
}

export async function getProjects() {
  try {
    return (await request("/api/projects/")) ?? { projects: [], categories: [] };
  } catch (error) {
    console.error("[api] getProjects:", error.message);
    return { projects: [], categories: [] };
  }
}

export async function getProject(slug) {
  try {
    return await request(`/api/projects/${encodeURIComponent(slug)}/`);
  } catch (error) {
    console.error("[api] getProject:", error.message);
    return null;
  }
}
