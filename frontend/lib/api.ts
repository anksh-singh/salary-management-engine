import type { ApiError } from "./types";

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, headers: { Accept: "application/json", ...init?.headers } });
  if (!response.ok) {
    let payload: ApiError = {};
    try { payload = await response.json() as ApiError; } catch { /* use a safe fallback */ }
    const message = payload.error?.message ?? `Request failed (${response.status})`;
    const detail = payload.error?.details?.map((item) => item.message).filter(Boolean).join("; ");
    throw new Error(detail ? `${message}: ${detail}` : message);
  }
  return response.json() as Promise<T>;
}

export function formatCount(value: number): string {
  return new Intl.NumberFormat("en").format(value);
}
