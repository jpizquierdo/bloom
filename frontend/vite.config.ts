import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { tanstackRouter } from "@tanstack/router-plugin/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
    host: true,
    // Mirrors production, where the API serves this app: relative /api calls just work.
    proxy: {
      "/api": {
        target: process.env.BLOOM_API_URL ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
