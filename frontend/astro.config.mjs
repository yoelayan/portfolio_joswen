import { defineConfig } from "astro/config";
import node from "@astrojs/node";

// SSR: el contenido sale de la API de Wagtail en cada petición, así que lo que se
// sube desde el admin aparece sin volver a desplegar.
export default defineConfig({
  output: "server",
  adapter: node({ mode: "standalone" }),
  server: { host: true },
  devToolbar: { enabled: false },
});
