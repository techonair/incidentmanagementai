import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18202a",
        line: "#d9e0e8",
        field: "#f6f8fb",
        accent: "#6750a4",
        danger: "#b3261e",
        ok: "#146c43"
      }
    }
  },
  plugins: []
};

export default config;
