/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        hsb: {
          red: "#cb0000",
          black: "#0f1114",
          steel: "#3d4652",
          mist: "#f3f5f7",
          line: "#d8dde3",
          signal: "#f6c343",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        industrial: "0 18px 50px rgba(15, 17, 20, 0.12)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography"), require("tailwindcss-animate")],
};
