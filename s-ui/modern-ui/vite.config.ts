import { defineConfig } from "vite";

export default defineConfig({
  base: "/modern/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    assetsDir: "assets",
  },
});
