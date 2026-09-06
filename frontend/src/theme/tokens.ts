/**
 * Design tokens -- single source of truth.
 * Do not hard-code colors/spacing outside these tokens.
 */
export const tokens = {
  colors: {
    background: "#0B0F19",
    surface: "#111827",
    surfaceElevated: "#1F2937",
    border: "#374151",
    borderSubtle: "#1F2937",
    primary: "#38BDF8",
    primaryHover: "#7DD3FC",
    primaryMuted: "rgba(56, 189, 248, 0.15)",
    accent: "#A78BFA",
    success: "#34D399",
    warning: "#FBBF24",
    danger: "#FB7185",
    text: "#F8FAFC",
    textMuted: "#94A3B8",
    textSubtle: "#64748B",
  },
  radius: {
    sm: "6px",
    md: "10px",
    lg: "14px",
    xl: "20px",
    full: "9999px",
  },
  spacing: {
    1: "4px",
    2: "8px",
    3: "12px",
    4: "16px",
    5: "20px",
    6: "24px",
    8: "32px",
    10: "40px",
    12: "48px",
  },
  typography: {
    fontSans: "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif",
    display: "2.25rem",
    h1: "1.875rem",
    h2: "1.5rem",
    h3: "1.25rem",
    body: "0.9375rem",
    caption: "0.8125rem",
  },
  shadow: {
    sm: "0 1px 2px rgba(0,0,0,0.4)",
    md: "0 4px 12px rgba(0,0,0,0.45)",
    lg: "0 12px 32px rgba(0,0,0,0.5)",
  },
  motion: {
    fast: "150ms",
    normal: "220ms",
    slow: "320ms",
    ease: "cubic-bezier(0.4, 0, 0.2, 1)",
  },
} as const;

export type Tokens = typeof tokens;