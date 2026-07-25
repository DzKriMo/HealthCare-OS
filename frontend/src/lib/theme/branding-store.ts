/**
 * White-label branding store — resolves tenant branding at runtime.
 *
 * Theming is driven by CSS custom properties set on :root.
 * Tenant branding overrides the default design tokens.
 *
 * Branding is fetched once on login and cached in localStorage.
 * The theme provider applies tokens to document.documentElement.
 */
import { create } from "zustand";

export interface TenantBranding {
  logo_url: string | null;
  primary_color: string;
  secondary_color: string;
  dark_mode: boolean;
  typography: "default" | "modern" | "classic";
  clinic_name: string;
  language: string;
  currency: string;
}

interface BrandingState {
  branding: TenantBranding | null;
  isLoading: boolean;

  fetchBranding: (tenantSlug: string) => Promise<void>;
  applyBranding: (branding: TenantBranding) => void;
  clearBranding: () => void;
}

const DEFAULT_BRANDING: TenantBranding = {
  logo_url: null,
  primary_color: "#0369a1",
  secondary_color: "#f8fafc",
  dark_mode: false,
  typography: "default",
  clinic_name: "Healthcare OS",
  language: "en",
  currency: "USD",
};

/**
 * Convert a hex color to HSL for CSS custom properties.
 */
function hexToHsl(hex: string): { h: number; s: number; l: number } {
  // Strip #
  let h = 0, s = 0, l = 0;
  const clean = hex.replace("#", "");

  // Convert to RGB
  const r = parseInt(clean.substring(0, 2), 16) / 255;
  const g = parseInt(clean.substring(2, 4), 16) / 255;
  const b = parseInt(clean.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  l = (max + min) / 2;

  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  };
}

/**
 * Generate CSS custom property overrides from branding config.
 */
function brandingToCSS(branding: TenantBranding): Record<string, string> {
  const primary = hexToHsl(branding.primary_color);
  const secondary = hexToHsl(branding.secondary_color);

  return {
    "--primary": `${primary.h} ${primary.s}% ${primary.l}%`,
    "--primary-foreground": primary.l > 50 ? "222.2 47.4% 11.2%" : "210 40% 98%",
    "--secondary": `${secondary.h} ${secondary.s}% ${secondary.l}%`,
    "--secondary-foreground": secondary.l > 50 ? "222.2 47.4% 11.2%" : "210 40% 98%",
    "--brand-clinic-name": `"${branding.clinic_name}"`,
  };
}

export const useBrandingStore = create<BrandingState>((set, get) => ({
  branding: null,
  isLoading: false,

  fetchBranding: async (tenantSlug: string) => {
    set({ isLoading: true });
    try {
      // Check cache first (24h TTL)
      const cached = localStorage.getItem(`branding_${tenantSlug}`);
      const cachedAt = localStorage.getItem(`branding_${tenantSlug}_at`);
      const cacheAge = cachedAt ? Date.now() - parseInt(cachedAt) : Infinity;

      if (cached && cacheAge < 86_400_000) {
        const branding = JSON.parse(cached) as TenantBranding;
        get().applyBranding(branding);
        set({ branding, isLoading: false });
        return;
      }

      // Fetch from real API
      const res = await fetch(`/api/tenancy/branding/`, {
        headers: { "X-Tenant-Slug": tenantSlug },
      });
      if (res.ok) {
        const branding = (await res.json()) as TenantBranding;
        localStorage.setItem(`branding_${tenantSlug}`, JSON.stringify(branding));
        localStorage.setItem(`branding_${tenantSlug}_at`, String(Date.now()));
        get().applyBranding(branding);
        set({ branding, isLoading: false });
        return;
      }
    } catch {
      // fall through to defaults
    }
    get().applyBranding(DEFAULT_BRANDING);
    set({ branding: DEFAULT_BRANDING, isLoading: false });
  },

  applyBranding: (branding: TenantBranding) => {
    const root = document.documentElement;
    const tokens = brandingToCSS(branding);

    Object.entries(tokens).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });

    // Update document title and meta
    document.title = branding.clinic_name;

    // Set typography class
    root.classList.remove("font-default", "font-modern", "font-classic");
    root.classList.add(`font-${branding.typography}`);

    // Cache in localStorage
    if (typeof window !== "undefined") {
      const slug = get().branding?.clinic_name || "default";
      localStorage.setItem(`branding_${slug}`, JSON.stringify(branding));
    }
  },

  clearBranding: () => {
    const root = document.documentElement;
    const tokens = brandingToCSS(DEFAULT_BRANDING);
    Object.entries(tokens).forEach(([key, value]) => {
      root.style.setProperty(key, value);
    });
    document.title = "Healthcare OS";
    set({ branding: null });
  },
}));
