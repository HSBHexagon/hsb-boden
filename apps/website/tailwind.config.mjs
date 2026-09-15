/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  theme: {
    extend: {
      colors: {
        hsb: {
          red: "#cb0000",
          "red-light": "#ff8a7d",
          black: "#161a20",
          steel: "#3d4652",
          mist: "#f3f5f7",
          line: "#d8dde3",
          signal: "#f6c343",
        },
      },
      fontFamily: {
        sans: ["Outfit", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        industrial: "0 18px 50px rgba(22, 26, 32, 0.12)",
      },
    },
  },
  plugins: [require("@tailwindcss/typography"), require("tailwindcss-animate")],
};
