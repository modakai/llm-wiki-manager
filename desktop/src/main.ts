import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";

// Vue 入口保持极薄，业务状态集中在 App.vue 这一层 MVP 工作台中。
createApp(App).mount("#app");
