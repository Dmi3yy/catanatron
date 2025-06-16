import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  envPrefix: "CTRON_",
  test: {
    environment: "jsdom",
    setupFiles: "vitest.setup.ts",
  },
  server: {
    host: true,
    port: 3000,
    allowedHosts: ['.dmi3yy.com'],
  },
  preview: {
    host: true,
    port: 4173,
    allowedHosts: ['.dmi3yy.com'],
  },
});
