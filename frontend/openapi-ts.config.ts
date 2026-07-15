import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "../openapi.json",
  output: { path: "src/client", format: false, lint: false },
  plugins: [
    {
      name: "@hey-api/client-fetch",
      runtimeConfigPath: "./src/lib/api-config.ts",
    },
    "@hey-api/schemas",
    "@tanstack/react-query",
  ],
})
