<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ApiClient } from "./services/api";
import { resolveBackendUrl } from "./services/backend";
import type { ModelConfigPayload, WikiPage } from "./types";

let api = new ApiClient();

const config = reactive<ModelConfigPayload>({
  base_url: "https://api.deepseek.com/v1",
  api_key: "",
  model: "deepseek-chat",
  temperature: 0.2,
  timeout: 60,
});

const pages = ref<WikiPage[]>([]);
const selectedPageId = ref("");
const previewTitle = ref("预览");
const markdown = ref("");
const currentSourceId = ref("");
const selectedFile = ref<File | null>(null);
const status = ref("正在连接本地后端...");
const busy = ref(false);

// 这些派生状态只服务界面展示，不改变后端 MVP 数据模型。
const canGenerate = computed(() => Boolean(currentSourceId.value) && !busy.value);
const selectedFileName = computed(() => selectedFile.value?.name ?? "尚未选择文件");
const pageCountLabel = computed(() => `${pages.value.length} 个页面`);
const connectionTone = computed(() => (status.value.includes("错误") || status.value.includes("失败") ? "danger" : "ready"));

onMounted(async () => {
  await guarded("初始化完成。", async () => {
    api = new ApiClient(await resolveBackendUrl());
    const remote = await api.loadModelConfig();
    config.base_url = remote.base_url || config.base_url;
    config.model = remote.model || config.model;
    config.temperature = remote.temperature ?? config.temperature;
    config.timeout = remote.timeout ?? config.timeout;
    await refreshPages();
    status.value = remote.configured ? `已加载模型配置：${remote.model}` : "请先保存模型配置。";
  });
});

async function saveSettings() {
  await guarded("模型配置已保存。", async () => {
    const saved = await api.saveModelConfig(config);
    status.value = `模型配置已保存：${saved.model} / ${saved.api_key_masked}`;
    config.api_key = "";
  });
}

async function uploadSelectedFile() {
  if (!selectedFile.value) {
    status.value = "请选择要上传的文件。";
    return;
  }
  await guarded("文件解析完成。", async () => {
    const uploaded = await api.uploadFile(selectedFile.value as File);
    currentSourceId.value = uploaded.source_id;
    status.value = `已解析 ${uploaded.filename}，提取 ${uploaded.text_chars} 字。`;
  });
}

async function generateWiki() {
  if (!currentSourceId.value) return;
  await guarded("Wiki 已生成。", async () => {
    status.value = "正在调用模型生成 Wiki...";
    const page = await api.generateWiki(currentSourceId.value);
    await refreshPages();
    await openPage(page.page_id);
    status.value = `已生成 Wiki：${page.title}`;
  });
}

async function refreshPages() {
  pages.value = await api.loadPages();
}

async function openPage(pageId: string) {
  await guarded("页面已加载。", async () => {
    const page = await api.loadPage(pageId);
    selectedPageId.value = page.page_id;
    previewTitle.value = page.title;
    markdown.value = page.markdown;
  });
}

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] ?? null;
}

async function guarded(successMessage: string, action: () => Promise<void>) {
  busy.value = true;
  try {
    await action();
    if (successMessage) status.value = status.value || successMessage;
  } catch (error) {
    status.value = error instanceof Error ? error.message : "未知错误。";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main class="workbench">
    <aside class="panel control-panel">
      <div class="brand">
        <div class="app-mark">W</div>
        <div>
          <p class="eyebrow">LLM WIKI MANAGER</p>
          <h1>知识整理工作台</h1>
        </div>
      </div>

      <div class="status-card" :class="connectionTone">
        <span class="status-dot"></span>
        <p>{{ status }}</p>
      </div>

      <section class="section glass-section">
        <div class="section-title">
          <span>01</span>
          <h2>模型配置</h2>
        </div>
        <label>
          Base URL
          <input v-model="config.base_url" autocomplete="off" />
        </label>
        <label>
          API Key
          <input v-model="config.api_key" type="password" placeholder="保存后会在后端加密落盘" />
        </label>
        <label>
          Model
          <input v-model="config.model" autocomplete="off" />
        </label>
        <div class="two-cols">
          <label>
            Temperature
            <input v-model.number="config.temperature" type="number" min="0" max="2" step="0.1" />
          </label>
          <label>
            Timeout
            <input v-model.number="config.timeout" type="number" min="1" max="600" />
          </label>
        </div>
        <button class="primary-action" :disabled="busy" @click="saveSettings">保存配置</button>
      </section>

      <section class="section glass-section">
        <div class="section-title">
          <span>02</span>
          <h2>导入资料</h2>
        </div>
        <label class="file-picker">
          <input type="file" accept=".pdf,.docx,.doc,.txt,.md" @change="onFileChange" />
          <span class="file-button">选择文件</span>
          <strong>{{ selectedFileName }}</strong>
        </label>
        <div class="action-row">
          <button class="secondary" :disabled="busy" @click="uploadSelectedFile">解析</button>
          <button class="primary-action" :disabled="!canGenerate" @click="generateWiki">生成 Wiki</button>
        </div>
      </section>
    </aside>

    <section class="panel page-panel">
      <header class="panel-header">
        <div>
          <p class="eyebrow">{{ pageCountLabel }}</p>
          <h2>Wiki 页面</h2>
        </div>
        <button class="icon-button" :disabled="busy" title="刷新页面列表" @click="refreshPages">⟳</button>
      </header>
      <div class="page-list">
        <div v-if="pages.length === 0" class="empty-state">
          <strong>还没有 Wiki 页面</strong>
          <span>上传资料并生成后会显示在这里。</span>
        </div>
        <button
          v-for="page in pages"
          :key="page.page_id"
          class="page-item"
          :class="{ active: page.page_id === selectedPageId }"
          @click="openPage(page.page_id)"
        >
          {{ page.title }}
        </button>
      </div>
    </section>

    <section class="panel preview-panel">
      <header class="panel-header">
        <div>
          <p class="eyebrow">MARKDOWN</p>
          <h2>{{ previewTitle }}</h2>
        </div>
      </header>
      <article class="reader">
        <pre class="markdown-preview">{{ markdown || "选择或生成一个 Wiki 页面后在这里查看。" }}</pre>
      </article>
    </section>
  </main>
</template>
