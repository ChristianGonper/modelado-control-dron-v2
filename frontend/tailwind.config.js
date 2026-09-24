/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        aerolab: {
          text: "#10284E",
          secondary: "#5D6F8A",
          action: "#0284C7",      // PD clásico / acción primaria (Azul Eléctrico)
          mlp: "#10B981",         // MLP neuronal (Verde Esmeralda)
          gru: "#F59E0B",         // GRU neuronal (Ámbar Cálido)
          lstm: "#8B5CF6",        // LSTM neuronal (Púrpura Eléctrico)
          nominal: "#334155",     // Ruta nominal (Gris Pizarra)
          canvas: "#F5F8FC",
          surface: "#FFFFFF",
          border: "#D9E3F0",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["IBM Plex Mono", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
