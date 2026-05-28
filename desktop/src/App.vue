<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ApiClient } from "./services/api";
import { resolveBackendUrl } from "./services/backend";
import type { ModelConfigPayload, WikiPage, WorkspaceInfo } from "./types";
import { invoke } from "@tauri-apps/api/core";
import { marked } from "marked";

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
const generating = ref(false);
const workspacePath = ref("");
const wikiDir = ref("");
const switchingWorkspace = ref(false);

const canGenerate = computed(() => Boolean(currentSourceId.value) && !busy.value && !switchingWorkspace.value && !generating.value);
const selectedFileName = computed(() => selectedFile.value?.name ?? "尚未选择文件");
const pageCountLabel = computed(() => `${pages.value.length} 个页面`);
const connectionTone = computed(() => (status.value.includes("错误") || status.value.includes("失败") ? "danger" : "ready"));
const isTauri = computed(() => Boolean((window as any).__TAURI_INTERNALS__));
const anyBusy = computed(() => busy.value || switchingWorkspace.value || generating.value);

/* 将 Markdown 源码渲染为 HTML */
const renderedMarkdown = computed(() => {
  if (!markdown.value) return "";
  return marked.parse(markdown.value, {
    breaks: true,
    gfm: true,
  }) as string;
});

onMounted(async () => {
  await guarded("初始化完成。", async () => {
    api = new ApiClient(await resolveBackendUrl());

    if (isTauri.value) {
      let path = "";
      try {
        path = await invoke<string>("get_workspace_path");
      } catch {
        // 浏览器模式回退
      }
      if (!path) {
        switchingWorkspace.value = true;
        status.value = "请选择 Wiki 存储目录...";
        try {
          path = await invoke<string>("select_workspace_dir");
        } catch {
          // 取消选择时 select_workspace_dir 会使用默认值
        }
        switchingWorkspace.value = false;
      }
      workspacePath.value = path;
    }

    await waitForBackend();
    await loadWorkspaceInfo();
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
  if (!currentSourceId.value || generating.value) return;

  /* 立即创建占位页面，让用户看到反馈 */
  const placeholderId = "__generating__";
  const placeholderTitle = "正在生成 Wiki...";
  const sourceFileName = selectedFile.value?.name ?? "未知文件";

  generating.value = true;
  status.value = "正在调用模型生成 Wiki...";
  previewTitle.value = placeholderTitle;
  markdown.value = "";
  selectedPageId.value = placeholderId;

  /* 将占位条目插入页面列表顶部 */
  pages.value = [
    { page_id: placeholderId, title: placeholderTitle, path: "" },
    ...pages.value,
  ];

  try {
    const page = await api.generateWiki(currentSourceId.value);
    /* 生成成功 — 替换占位条目为真实页面 */
    await refreshPages();
    await openPage(page.page_id);
    status.value = `已生成 Wiki：${page.title}`;
  } catch (error) {
    /* 生成失败 — 移除占位条目，恢复状态 */
    pages.value = pages.value.filter((p) => p.page_id !== placeholderId);
    selectedPageId.value = "";
    previewTitle.value = "预览";
    markdown.value = "";
    status.value = error instanceof Error ? error.message : "Wiki 生成失败。";
  } finally {
    generating.value = false;
  }
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

async function changeWorkspace() {
  if (!isTauri.value) return;
  switchingWorkspace.value = true;
  status.value = "正在切换存储目录...";
  try {
    const path = await invoke<string>("select_workspace_dir");
    workspacePath.value = path;
    await waitForBackend();
    await loadWorkspaceInfo();
    currentSourceId.value = "";
    await refreshPages();
    status.value = `已切换到：${path}`;
  } catch (error) {
    status.value = error instanceof Error ? error.message : "切换目录失败。";
  } finally {
    switchingWorkspace.value = false;
  }
}

async function loadWorkspaceInfo() {
  try {
    const info = await api.fetchWorkspaceInfo();
    workspacePath.value = info.path;
    wikiDir.value = info.directories.wiki;
  } catch {
    // 如果 /api/workspace 端点不存在（旧版后端），从 health 兜底
    try {
      const health = await api.healthCheck();
      if (health.workspace) {
        workspacePath.value = health.workspace;
        wikiDir.value = health.workspace.replace(/\\/g, "/").replace(/\/$/, "") + "/wiki";
      }
    } catch {
      // 最终兜底：保持 Tauri 侧设置的值
    }
  }
}

async function waitForBackend(retries = 30, delayMs = 500): Promise<void> {
  for (let i = 0; i < retries; i++) {
    try {
      await api.healthCheck();
      return;
    } catch {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error("后端无响应，请检查服务是否正常启动。");
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
    <!-- ========== 左侧：控制面板 ========== -->
    <aside class="panel control-panel">
      <div class="brand">
        <div class="app-mark">W</div>
        <div>
          <p class="eyebrow">LLM WIKI MANAGER</p>
          <h1>知识整理工作台</h1>
        </div>
      </div>

      <div class="status-card" :class="[connectionTone, { busy: anyBusy, switching: switchingWorkspace }]">
        <span class="status-dot"></span>
        <p>{{ status }}</p>
      </div>
      <!-- 进度条：操作进行中显示 -->
      <div v-if="anyBusy" class="progress-bar">
        <div class="progress-track"></div>
      </div>

      <!-- Workspace 存储目录 -->
      <div class="section">
        <div class="section-title">
          <span>00</span>
          <h2>存储目录</h2>
        </div>
        <div class="workspace-display">
          <div class="workspace-info">
            <span class="workspace-label">数据根目录</span>
            <span class="workspace-path" :title="workspacePath">{{ workspacePath || "未设置" }}</span>
          </div>
          <div class="workspace-info">
            <span class="workspace-label">Wiki 文件位置</span>
            <span class="workspace-path wiki-path" :title="wikiDir">{{ wikiDir || "—" }}</span>
          </div>
          <button
            v-if="isTauri"
            class="secondary workspace-btn"
            :disabled="anyBusy"
            @click="changeWorkspace"
          >
            更换目录
          </button>
        </div>
      </div>

      <!-- 模型配置 -->
      <div class="section">
        <div class="section-title">
          <span>01</span>
          <h2>模型配置</h2>
        </div>
        <label>
          Base URL
          <input v-model="config.base_url" autocomplete="off" placeholder="https://api.deepseek.com/v1" />
        </label>
        <label>
          API Key
          <input v-model="config.api_key" type="password" placeholder="保存后加密落盘" />
        </label>
        <label>
          Model
          <input v-model="config.model" autocomplete="off" placeholder="deepseek-chat" />
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
        <button class="primary-action" :disabled="anyBusy" @click="saveSettings">保存配置</button>
      </div>

      <!-- 导入资料 -->
      <div class="section">
        <div class="section-title">
          <span>02</span>
          <h2>导入资料</h2>
        </div>
        <div class="file-picker">
          <input type="file" accept=".pdf,.docx,.doc,.txt,.md" @change="onFileChange" />
          <span class="file-button">选择文件</span>
          <strong>{{ selectedFileName }}</strong>
        </div>
        <div class="action-row">
          <button class="secondary" :disabled="anyBusy" @click="uploadSelectedFile">解析文件</button>
          <button class="primary-action" :disabled="!canGenerate" @click="generateWiki">生成 Wiki</button>
        </div>
      </div>
    </aside>

    <!-- ========== 中间：Wiki 页面列表 ========== -->
    <section class="panel page-panel">
      <header class="panel-header">
        <div>
          <p class="eyebrow">{{ pageCountLabel }}</p>
          <h2>页面</h2>
        </div>
        <button class="icon-button" :disabled="anyBusy" title="刷新页面列表" @click="refreshPages">
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8a6 6 0 0 1 10.47-4M14 8a6 6 0 0 1-10.47 4"/>
            <path d="M14 2v4h-4M2 14v-4h4"/>
          </svg>
        </button>
      </header>
      <div class="page-list">
        <div v-if="pages.length === 0" class="empty-state">
          <strong>还没有 Wiki 页面</strong>
          <span>上传资料并生成后，页面会显示在这里</span>
        </div>
        <button
          v-for="page in pages"
          :key="page.page_id"
          class="page-item"
          :class="{ active: page.page_id === selectedPageId, generating: page.page_id === '__generating__' }"
          :disabled="page.page_id === '__generating__'"
          @click="openPage(page.page_id)"
        >
          <span v-if="page.page_id === '__generating__'" class="page-item-spinner"></span>
          {{ page.title }}
        </button>
      </div>
    </section>

    <!-- ========== 右侧：Markdown 预览 ========== -->
    <section class="panel preview-panel">
      <header class="panel-header">
        <div>
          <p class="eyebrow">MARKDOWN 预览</p>
          <h2>{{ previewTitle }}</h2>
        </div>
      </header>
      <article class="reader">
        <!-- 生成中：加载动画 -->
        <div v-if="generating" class="markdown-loading">
          <div class="loading-spinner"></div>
          <p class="loading-title">正在生成 Wiki</p>
          <p class="loading-desc">AI 模型正在分析「{{ selectedFileName }}」并整理知识...</p>
          <p class="loading-hint">这可能需要 10-30 秒</p>
        </div>
        <!-- 正常内容 -->
        <div v-else-if="markdown" class="markdown-body" v-html="renderedMarkdown"></div>
        <!-- 空状态 -->
        <div v-else class="markdown-empty">选择或生成一个 Wiki 页面后在此处查看。</div>
      </article>
    </section>
  </main>
</template>
