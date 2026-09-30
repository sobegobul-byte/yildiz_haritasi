/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        night: "#0b1026",
        nightdeep: "#070b1d",
        cream: "#f5f1e6",
        starlight: "#e8c46a",
      },
    },
  },
  plugins: [],
};
