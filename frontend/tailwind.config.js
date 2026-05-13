/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        muted: "#657080",
        line: "#dde3ea",
        canvas: "#f7f9fb",
        panel: "#ffffff",
        accent: "#0f766e"
      }
    }
  },
  plugins: []
};
