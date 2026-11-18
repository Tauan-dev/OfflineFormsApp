import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "@tailwindcss/vite"

// base "./": o Streamlit serve o build a partir de um caminho próprio do componente.
export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
  build: { outDir: "build", emptyOutDir: true, sourcemap: false },
})
