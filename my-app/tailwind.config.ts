import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      container: {
        center: true,
        padding: { DEFAULT: "1rem", sm: "1rem", md: "1.5rem", lg: "2rem" },
        screens: { sm: "640px", md: "768px", lg: "1024px", xl: "1280px", "2xl": "1536px" },
      },
      colors: {
        bg: "var(--bg)",
        "bg-soft": "var(--bg-soft)",
        fg: "var(--fg)",
        muted: "var(--muted)",
        accent: { DEFAULT: "var(--accent)", 600: "var(--accent-600)", 700: "var(--accent-700)" },
        card: "var(--card)",
        "card-hover": "var(--card-hover)",
        border: "var(--border)",
      },
      borderRadius: { xl2: "1rem" },
      boxShadow: { soft: "0 8px 24px rgba(0,0,0,0.25)" },
    },
  },
  plugins: [],
};

export default config;
