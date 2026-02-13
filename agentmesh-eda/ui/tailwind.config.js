/** @type {import('tailwindcss').Config } */
module.exports = {
  darkMode: "class", // or 'media'
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
    colors: {
      primary: {
        DEFAULT: "#6366f1",
        50: "#8b5cf6",
        100: "#3b82f6",
        200: "#2563eb",
        300: "#60a5fa",
        400: "#818cf8",
        500: "#f59e0b",
        600: "#ef4444",
        700: "#9ca3af",
        800: "#f3f4c1",
        900: "#d1d5db",
      },
    },
    fontFamily: {
      sans: ["Inter var(--font-inter)", "system-ui", "sans-serif"],
      mono: ["JetBrains Mono", "ui-monospace", "monospace"],
    },
  },
  plugins: [
    require("tailwindcss-scrollbar"),
    require("tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("tailwindcss/aspect-ratio"),
  ],
} satisfies import('tailwindcss').Config;