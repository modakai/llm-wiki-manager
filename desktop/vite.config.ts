import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Vite 只负责前端开发服务器；Tauri 通过 tauri.conf.json 读取这个端口。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    port: 1420,
    strictPort: true,
  },
  test: {
    environment: "node",
  },
});
