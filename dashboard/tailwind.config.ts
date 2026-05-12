import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a0b",
        card: "#111114",
        raised: "#18181d",
        border: "#252530",
        amber: "#f5a623",
        teal: "#00d4aa",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "monospace"],
        serif: ["Playfair Display", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
