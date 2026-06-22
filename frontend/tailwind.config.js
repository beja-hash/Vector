/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: "#172033",
        vector: "#2843c8",
      },
      boxShadow: {
        soft: "0 12px 36px rgba(16, 24, 40, 0.08)",
      },
    },
  },
  plugins: [],
};
