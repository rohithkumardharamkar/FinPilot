/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#4F46E5",   // Indigo
          success: "#10B981",   // Emerald
          warning: "#F59E0B",   // Amber
          danger: "#EF4444",    // Red
          bg: "#0F172A",        // Slate 900
          card: "#1E293B",      // Slate 800
          text: "#FFFFFF"       // White
        }
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"]
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
