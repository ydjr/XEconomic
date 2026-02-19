import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  publicDir: "../public",
  server: {
    proxy: {
      "/dashboard": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
