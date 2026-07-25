/**
 * Auth store — manages authentication state, tokens, and user info.
 */
import { create } from "zustand";
import { api } from "@/lib/api/client";
import type { User } from "@healthcare-os/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  requiresMfa: boolean;
  mfaSetupUri: string | null;
  tenantSlug: string | null;

  // Actions
  login: (email: string, password: string, tenantSlug: string, totpCode?: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchCurrentUser: () => Promise<void>;
  setupMfa: () => Promise<string>;
  confirmMfa: (code: string) => Promise<void>;
  disableMfa: (code: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  setTenantSlug: (slug: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  requiresMfa: false,
  mfaSetupUri: null,
  tenantSlug: null,

  setTenantSlug: (slug: string) => set({ tenantSlug: slug }),

  login: async (email, password, tenantSlug, totpCode) => {
    const response = await api.post<{
      user: User;
      tokens: { access: string; refresh: string };
      requires_mfa: boolean;
    }>("/auth/login/", {
      email,
      password,
      tenant_slug: tenantSlug,
      totp_code: totpCode,
      device_type: "web",
    }, { requireAuth: false });

    if (response.requires_mfa && !totpCode) {
      set({ requiresMfa: true });
      return;
    }

    api.setTokens(response.tokens.access, response.tokens.refresh);
    set({
      user: response.user,
      isAuthenticated: true,
      requiresMfa: false,
      tenantSlug,
    });
  },

  logout: async () => {
    try {
      const refreshToken = typeof window !== "undefined"
        ? localStorage.getItem("refresh_token")
        : null;
      if (refreshToken) {
        await api.post("/auth/logout/", { refresh: refreshToken });
      }
    } catch {
      // Logout is best-effort
    } finally {
      api.clearTokens();
      set({ user: null, isAuthenticated: false, requiresMfa: false });
    }
  },

  fetchCurrentUser: async () => {
    try {
      api.loadTokens();
      if (!api.isAuthenticated) {
        set({ isLoading: false });
        return;
      }
      const user = await api.get<User>("/auth/users/me/");
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      api.clearTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  setupMfa: async () => {
    const result = await api.post<{ secret: string; qr_uri: string }>(
      "/auth/mfa/setup/",
    );
    set({ mfaSetupUri: result.qr_uri });
    return result.qr_uri;
  },

  confirmMfa: async (code: string) => {
    await api.post("/auth/mfa/confirm/", { code });
    set({ mfaSetupUri: null });
    // Refresh user to get updated mfa_enabled
    await get().fetchCurrentUser();
  },

  disableMfa: async (code: string) => {
    await api.post("/auth/mfa/disable/", { code });
    await get().fetchCurrentUser();
  },

  changePassword: async (currentPassword: string, newPassword: string) => {
    await api.post("/auth/password/change/", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  clearAuth: () => {
    api.clearTokens();
    set({ user: null, isAuthenticated: false, requiresMfa: false, mfaSetupUri: null });
  },
}));
