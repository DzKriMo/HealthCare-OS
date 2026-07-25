/**
 * API client with JWT interceptor — auto-attaches tokens, handles refresh,
 * request timeout, and offline queue for Electron.
 */
import type { ApiError } from "@healthcare-os/types";
import { getElectronBridge } from "@/lib/electron/bridge";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

const MUTATION_METHODS = ["POST", "PUT", "PATCH", "DELETE"];

/** Default request timeout in milliseconds. */
const DEFAULT_TIMEOUT_MS = 30_000;

interface RequestOptions extends RequestInit {
  requireAuth?: boolean;
  /** Set false to opt a mutation out of offline queueing (e.g. auth). */
  queueable?: boolean;
  /** Request timeout in milliseconds. */
  timeout?: number;
}

/** Returned to callers when a mutation is queued offline instead of sent. */
export interface QueuedResult {
  _queued: true;
  id: string;
  queueId: string | null;
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshPromise: Promise<boolean> | null = null;

  // ── Token management ───────────────────────────────────

  setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
    }
  }

  loadTokens() {
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token");
      this.refreshToken = localStorage.getItem("refresh_token");
    }
  }

  clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  get isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // ── HTTP methods ───────────────────────────────────────

  async get<T = unknown>(
    path: string,
    options: RequestOptions = {},
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  async post<T = unknown>(
    path: string,
    body?: unknown,
    options: RequestOptions = {},
  ): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T = unknown>(
    path: string,
    body?: unknown,
    options: RequestOptions = {},
  ): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T = unknown>(
    path: string,
    body?: unknown,
    options: RequestOptions = {},
  ): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T = unknown>(
    path: string,
    options: RequestOptions = {},
  ): Promise<T> {
    return this.request<T>(path, { ...options, method: "DELETE" });
  }

  // ── Core request ───────────────────────────────────────

  private async request<T = unknown>(
    path: string,
    options: RequestOptions = {},
  ): Promise<T> {
    const { requireAuth = true, timeout = DEFAULT_TIMEOUT_MS, ...fetchOptions } = options;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(fetchOptions.headers as Record<string, string>),
    };

    if (requireAuth && this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`;
    }

    const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
    const method = (fetchOptions.method || "GET").toUpperCase();
    const queueable = options.queueable !== false;

    // Create an AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    const signal = controller.signal;

    let response: Response;
    try {
      response = await fetch(url, { ...fetchOptions, headers, signal });
    } catch (networkErr) {
      clearTimeout(timeoutId);
      // Fetch rejects on network failure (offline / server down / timeout).
      const bridge = getElectronBridge();
      if (bridge && queueable && MUTATION_METHODS.includes(method)) {
        const tempId = `local_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
        let queueId: string | null = null;
        try {
          const res = await bridge.enqueueMutation({
            entityType: path.split("/").filter(Boolean)[0] || "unknown",
            entityId: tempId,
            operationType:
              method === "DELETE" ? "delete" : method === "POST" ? "create" : "update",
            method,
            endpoint: path,
            payload: fetchOptions.body ? JSON.parse(fetchOptions.body as string) : null,
            idempotencyKey: tempId,
          });
          queueId = res.id;
        } catch {
          /* queue write failed — fall through to throw */
        }
        if (queueId) {
          return { _queued: true, id: tempId, queueId } as unknown as T;
        }
      }
      const isTimeout = networkErr instanceof DOMException && networkErr.name === "AbortError";
      throw new ApiRequestError(
        isTimeout ? "Request timed out" : (networkErr instanceof Error ? networkErr.message : "Network error"),
        0,
      );
    }
    clearTimeout(timeoutId);

    // Handle 401 — attempt token refresh
    if (response.status === 401 && this.refreshToken && requireAuth) {
      const refreshed = await this.tryRefreshToken();
      if (refreshed) {
        headers["Authorization"] = `Bearer ${this.accessToken}`;
        response = await fetch(url, { ...fetchOptions, headers });
      }
    }

    if (!response.ok) {
      const errorBody: ApiError = await response.json().catch(() => ({
        error: {
          type: "NetworkError",
          detail: response.statusText,
          correlation_id: "",
        },
      }));
      const detail = errorBody.error?.detail;
      const message =
        typeof detail === "string"
          ? detail
          : detail
            ? JSON.stringify(detail)
            : response.statusText;
      throw new ApiRequestError(
        message,
        response.status,
        errorBody.error?.correlation_id,
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  /**
   * Replay all pending offline mutations in order. Called on reconnect.
   */
  async flushQueue(): Promise<number> {
    const bridge = getElectronBridge();
    if (!bridge) return 0;

    let pending: Record<string, unknown>[];
    try {
      pending = await bridge.getPendingMutations();
    } catch {
      return 0;
    }

    let synced = 0;
    for (const item of pending) {
      const id = String(item.id);
      const method = String(item.method);
      const endpoint = String(item.endpoint);
      const payload = item.payload ? JSON.parse(String(item.payload)) : undefined;
      try {
        await this.request(endpoint, {
          method,
          body: payload ? JSON.stringify(payload) : undefined,
          queueable: false,
        });
        await bridge.resolveMutation(id, true);
        synced += 1;
      } catch (err) {
        await bridge.resolveMutation(
          id,
          false,
          err instanceof Error ? err.message : "sync failed",
        );
        break;
      }
    }
    return synced;
  }

  private async tryRefreshToken(): Promise<boolean> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this._doRefresh();
    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async _doRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh: this.refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return false;
      }

      const data = await response.json();
      this.setTokens(data.access, data.refresh);
      return true;
    } catch {
      this.clearTokens();
      return false;
    }
  }
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public status: number,
    public correlationId?: string,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

export const api = new ApiClient();
