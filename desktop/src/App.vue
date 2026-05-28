<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ApiClient } from "./services/api";
import { resolveBackendUrl } from "./services/backend";
import type { ModelConfigPayload, WikiPage } from "./types";
import { invoke } from "@tauri-apps/api/core";
import { marked } from "marked";

/* ---- 应用步骤 ---- */
type AppStep = "workspace" | "config" | "main";
const step = ref<AppStep>("workspace");
const stepTransition = ref("");

let api = new ApiClient();

/* ---- 模型配置 ---- */
const config = reactive<ModelConfigPayload>({
  base_url: "https://api.deepseek.com/v1",
  api_key: "",
  model: "deepseek-chat",
  temperature: 0.2,
  timeout: 60,
});

/* ---- Wiki 主页状态 ---- */
const pages = ref<WikiPage[]>([]);
const selectedPageId = ref("");
const previewTitle = ref("预览");
const markdown = ref("");
const currentSourceId = ref("");
const selectedFile = ref<File | null>(null);
const status = ref("");
const busy = ref(false);
const generating = ref(false);
const workspacePath = ref("");
const wikiDir = ref("");
const switchingWorkspace = ref(false);

/* ---- 引导页状态 ---- */
const workspaceLoading = ref(false);
const configSaving = ref(false);
const testResult = ref<{ ok: boolean; text: string } | null>(null);
const testing = ref(false);

/* ---- 计算属性 ---- */
const canGenerate = computed(() => Boolean(currentSourceId.value) && !busy.value && !generating.value);
const selectedFileName = computed(() => selectedFile.value?.name ?? "尚未选择文件");
const pageCountLabel = computed(() => `${pages.value.length} 个页面`);
const connectionTone = computed(() => (status.value.includes("错误") || status.value.includes("失败") ? "danger" : "ready"));
const isTauri = computed(() => Boolean((window as any).__TAURI_INTERNALS__));
const anyBusy = computed(() => busy.value || switchingWorkspace.value || generating.value);

const renderedMarkdown = computed(() => {
  if (!markdown.value) return "";
  return marked.parse(markdown.value, { breaks: true, gfm: true }) as string;
});

/* ---- 当前步骤名称（用于进度点） ---- */
const stepIndex = computed(() => {
  if (step.value === "workspace") return 0;
  if (step.value === "config") return 1;
  return 2;
});

/* ================================================================
   初始化
   ================================================================ */
onMounted(async () => {
  api = new ApiClient(await resolveBackendUrl());
  try {
    /* 检查后端连通性 */
    await waitForBackend(10, 400);
  } catch {
    step.value = "workspace";
    return;
  }

  /* 检查是否已有 workspace */
  try {
    const info = await api.fetchWorkspaceInfo();
    workspacePath.value = info.path;
    wikiDir.value = info.directories.wiki;
  } catch {
    try {
      const health = await api.healthCheck();
      if (health.workspace) {
        workspacePath.value = health.workspace;
        wikiDir.value = health.workspace.replace(/\\/g, "/").replace(/\/$/, "") + "/wiki";
      }
    } catch { /* 忽略 */ }
  }

  /* 检查模型是否已配置 */
  let configured = false;
  try {
    const remote = await api.loadModelConfig();
    config.base_url = remote.base_url || config.base_url;
    config.model = remote.model || config.model;
    config.temperature = remote.temperature ?? config.temperature;
    config.timeout = remote.timeout ?? config.timeout;
    configured = remote.configured;
  } catch { /* 忽略 */ }

  if (workspacePath.value && configured) {
    /* 已完全配置 → 直接进入主页 */
    await refreshPages();
    status.value = `已加载模型配置：${config.model}`;
    step.value = "main";
  } else if (workspacePath.value) {
    /* 有 workspace 但无模型配置 → 去配置页 */
    step.value = "config";
  } else {
    step.value = "workspace";
  }
});

/* ================================================================
   步骤 1：选择工作空间
   ================================================================ */
async function chooseWorkspace() {
  workspaceLoading.value = true;
  try {
    let path = "";
    if (isTauri.value) {
      path = await invoke<string>("select_workspace_dir");
    } else {
      /* 浏览器模式：使用默认路径 */
      path = workspacePath.value || "未在桌面端运行，使用默认工作目录";
    }
    if (path) {
      workspacePath.value = path;
      await waitForBackend(20, 300);
      try {
        const info = await api.fetchWorkspaceInfo();
        wikiDir.value = info.directories.wiki;
      } catch { /* 忽略 */ }
      /* 跳转到模型配置页 */
      step.value = "config";
    }
  } catch (error) {
    console.error("选择工作空间失败:", error);
  } finally {
    workspaceLoading.value = false;
  }
}

/* ================================================================
   步骤 2：配置模型并进入主页
   ================================================================ */
async function saveConfigAndEnter() {
  configSaving.value = true;
  try {
    await api.saveModelConfig(config);
    await refreshPages();
    status.value = `已加载模型配置：${config.model}`;
    config.api_key = "";
    step.value = "main";
  } catch (error) {
    status.value = error instanceof Error ? error.message : "配置保存失败。";
  } finally {
    configSaving.value = false;
  }
}

async function testConnection() {
  testing.value = true;
  testResult.value = null;
  try {
    /* 临时保存配置并测试 */
    await api.saveModelConfig(config);
    testResult.value = { ok: true, text: `连接成功 — ${config.model}` };
  } catch (error) {
    testResult.value = {
      ok: false,
      text: error instanceof Error ? error.message : "连接测试失败",
    };
  } finally {
    testing.value = false;
  }
}

/* 从配置页回退到工作空间页 */
function backToWorkspace() {
  step.value = "workspace";
}

/* 从主页回到配置（重新配置） */
function backToConfig() {
  step.value = "config";
}

/* ================================================================
   Wiki 主页操作
   ================================================================ */
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
  const placeholderId = "__generating__";
  const placeholderTitle = "正在生成 Wiki...";

  generating.value = true;
  status.value = "正在调用模型生成 Wiki...";
  previewTitle.value = placeholderTitle;
  markdown.value = "";
  selectedPageId.value = placeholderId;
  pages.value = [{ page_id: placeholderId, title: placeholderTitle, path: "" }, ...pages.value];

  try {
    const page = await api.generateWiki(currentSourceId.value);
    await refreshPages();
    await openPage(page.page_id);
    status.value = `已生成 Wiki：${page.title}`;
  } catch (error) {
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
  if (pageId === "__generating__") return;
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
    try { const info = await api.fetchWorkspaceInfo(); wikiDir.value = info.directories.wiki; } catch { /* 忽略 */ }
    currentSourceId.value = "";
    await refreshPages();
    status.value = `已切换到：${path}`;
  } catch (error) {
    status.value = error instanceof Error ? error.message : "切换目录失败。";
  } finally {
    switchingWorkspace.value = false;
  }
}

async function waitForBackend(retries = 30, delayMs = 500): Promise<void> {
  for (let i = 0; i < retries; i++) {
    try { await api.healthCheck(); return; } catch {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error("后端无响应，请检查服务是否正常启动。");
}

async function guarded(successMessage: string, action: () => Promise<void>) {
  busy.value = true;
  try {
    await action();
    if (successMessage && !status.value) status.value = successMessage;
  } catch (error) {
    status.value = error instanceof Error ? error.message : "未知错误。";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <!-- ================================================================
       步骤 1：工作空间选择
       ================================================================ -->
  <div v-if="step === 'workspace'" class="onboard-shell">
    <div class="onboard-card">
      <!-- 图标 -->
      <div class="onboard-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="color: var(--blue);">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
      </div>

      <!-- 标题 -->
      <div>
        <h1>选择工作空间</h1>
        <p class="onboard-desc" style="margin-top: 6px;">
          你的 Wiki 页面和上传资料将保存在此目录中。请选择一个空目录或已有数据的目录。
        </p>
      </div>

      <!-- 路径展示 -->
      <div class="workspace-card">
        <span class="ws-label">工作目录</span>
        <span class="ws-path">{{ workspacePath || "尚未选择" }}</span>
      </div>

      <!-- 按钮 -->
      <div class="onboard-actions">
        <button class="onboard-btn primary" :disabled="workspaceLoading" @click="chooseWorkspace">
          <svg v-if="workspaceLoading" class="btn-spin" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="8" cy="8" r="6" stroke-opacity="0.3"/>
            <path d="M14 8a6 6 0 0 0-10.4-4" stroke-linecap="round"/>
          </svg>
          {{ workspaceLoading ? "正在准备..." : "选择目录" }}
        </button>
      </div>

      <!-- 进度点 -->
      <div class="step-dots" style="align-self: center;">
        <span class="step-dot active"></span>
        <span class="step-dot-line"></span>
        <span class="step-dot"></span>
        <span class="step-dot-line"></span>
        <span class="step-dot"></span>
      </div>
    </div>

    <div class="onboard-footer">
      已有工作空间？
      <button @click="step = 'config'">跳过，配置模型</button>
    </div>
  </div>

  <!-- ================================================================
       步骤 2：模型配置
       ================================================================ -->
  <div v-else-if="step === 'config'" class="onboard-shell">
    <div class="onboard-card">
      <!-- 图标 -->
      <div class="onboard-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="color: var(--blue);">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      </div>

      <!-- 标题 -->
      <div>
        <h1>配置大模型</h1>
        <p class="onboard-desc" style="margin-top: 6px;">
          连接 OpenAI 兼容 API，用于生成 Wiki 内容。API Key 将加密保存在本地。
        </p>
      </div>

      <!-- 表单 -->
      <div class="onboard-form">
        <label>
          Base URL
          <input v-model="config.base_url" autocomplete="off" placeholder="https://api.deepseek.com/v1" />
        </label>
        <label>
          API Key
          <input v-model="config.api_key" type="password" placeholder="sk-..." />
        </label>
        <label>
          Model
          <input v-model="config.model" autocomplete="off" placeholder="deepseek-chat" />
        </label>
        <div class="form-row">
          <label>
            Temperature
            <input v-model.number="config.temperature" type="number" min="0" max="2" step="0.1" />
          </label>
          <label>
            Timeout (s)
            <input v-model.number="config.timeout" type="number" min="1" max="600" />
          </label>
        </div>

        <!-- 测试结果 -->
        <div v-if="testResult" class="test-result" :class="testResult.ok ? 'success' : 'fail'">
          {{ testResult.ok ? '✓' : '✗' }} {{ testResult.text }}
        </div>
      </div>

      <!-- 按钮 -->
      <div class="onboard-actions">
        <button class="onboard-btn secondary" :disabled="testing" @click="testConnection">
          {{ testing ? "测试中..." : "测试连接" }}
        </button>
        <button class="onboard-btn primary" :disabled="configSaving" @click="saveConfigAndEnter">
          {{ configSaving ? "保存中..." : "保存并进入工作台" }}
        </button>
      </div>

      <!-- 进度点 -->
      <div class="step-dots" style="align-self: center;">
        <span class="step-dot done"></span>
        <span class="step-dot-line"></span>
        <span class="step-dot active"></span>
        <span class="step-dot-line"></span>
        <span class="step-dot"></span>
      </div>
    </div>

    <div class="onboard-footer">
      <button @click="backToWorkspace">← 返回选择目录</button>
      <span style="color: var(--separator-opaque);">·</span>
      <button @click="step = 'main'">跳过，直接进入</button>
    </div>
  </div>

  <!-- ================================================================
       步骤 3：Wiki 管理工作台（主页）
       ================================================================ -->
  <main v-else class="workbench">
    <!-- ========== 左侧：控制面板 ========== -->
    <aside class="panel control-panel">
      <div class="brand">
        <img class="app-mark" src="/logo.png" alt="LLM Wiki Manager" />
        <div>
          <p class="eyebrow">LLM WIKI MANAGER</p>
          <h1>知识整理工作台</h1>
        </div>
      </div>

      <div class="status-card" :class="[connectionTone, { busy: anyBusy, switching: switchingWorkspace }]">
        <span class="status-dot"></span>
        <p>{{ status || "就绪" }}</p>
      </div>
      <div v-if="anyBusy" class="progress-bar">
        <div class="progress-track"></div>
      </div>

      <!-- 存储目录 -->
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
          <button v-if="isTauri" class="secondary workspace-btn" :disabled="anyBusy" @click="changeWorkspace">
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
        <label>Base URL <input v-model="config.base_url" autocomplete="off" placeholder="https://api.deepseek.com/v1" /></label>
        <label>API Key <input v-model="config.api_key" type="password" placeholder="保存后加密落盘" /></label>
        <label>Model <input v-model="config.model" autocomplete="off" placeholder="deepseek-chat" /></label>
        <div class="two-cols">
          <label>Temperature <input v-model.number="config.temperature" type="number" min="0" max="2" step="0.1" /></label>
          <label>Timeout <input v-model.number="config.timeout" type="number" min="1" max="600" /></label>
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

      <!-- 重新配置入口 -->
      <div class="section" style="padding-top: 8px; border-top: 1px solid var(--separator);">
        <button class="secondary" style="width: 100%;" @click="backToConfig">
          ← 重新配置模型
        </button>
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
        <div v-if="generating" class="markdown-loading">
          <div class="loading-spinner"></div>
          <p class="loading-title">正在生成 Wiki</p>
          <p class="loading-desc">AI 模型正在分析「{{ selectedFileName }}」并整理知识...</p>
          <p class="loading-hint">这可能需要 10-30 秒</p>
        </div>
        <div v-else-if="markdown" class="markdown-body" v-html="renderedMarkdown"></div>
        <div v-else class="markdown-empty">选择或生成一个 Wiki 页面后在此处查看。</div>
      </article>
    </section>
  </main>
</template>
