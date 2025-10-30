/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // 🎨 Paleta institucional inspirada en Banco de Chile
        primary: {
          DEFAULT: "#0033A0", // azul Banco de Chile
          dark: "#002470",
          light: "#1E50C2",
        },
        secondary: {
          DEFAULT: "#E5E9F2", // gris claro elegante
          dark: "#C7CEDB",
        },
        accent: {
          DEFAULT: "#00AEEF", // celeste acento
          dark: "#008EC6",
        },
        neutral: {
          DEFAULT: "#222222",
          light: "#444444",
          gray: "#6B7280",
        },
      },
      fontFamily: {
        sans: ["Inter", "Poppins", "ui-sans-serif", "system-ui"],
      },
      boxShadow: {
        soft: "0 4px 12px rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};
