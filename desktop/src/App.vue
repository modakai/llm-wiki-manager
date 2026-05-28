<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ApiClient } from "./services/api";
import { resolveBackendUrl } from "./services/backend";
import type { ModelConfigPayload, WikiPage } from "./types";
import { invoke } from "@tauri-apps/api/core";
import { marked } from "marked";

/* ---- App Step ---- */
type AppStep = "workspace" | "config" | "main";
const step = ref<AppStep>("workspace");

let api = new ApiClient();

/* ---- Model Config ---- */
const config = reactive<ModelConfigPayload>({
  base_url: "https://api.deepseek.com/v1",
  api_key: "",
  model: "deepseek-chat",
  temperature: 0.2,
  timeout: 60,
});

/* ---- Wiki State ---- */
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

/* ---- Onboarding State ---- */
const workspaceLoading = ref(false);
const configSaving = ref(false);
const testResult = ref<{ ok: boolean; text: string } | null>(null);
const testing = ref(false);

/* ---- Settings Modal ---- */
const showSettings = ref(false);

/* ---- Computed ---- */
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

const stepIndex = computed(() => {
  if (step.value === "workspace") return 0;
  if (step.value === "config") return 1;
  return 2;
});

/* ================================================================
   Init
   ================================================================ */
onMounted(async () => {
  api = new ApiClient(await resolveBackendUrl());
  try {
    await waitForBackend(10, 400);
  } catch {
    step.value = "workspace";
    return;
  }

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
    } catch { /* ignore */ }
  }

  let configured = false;
  try {
    const remote = await api.loadModelConfig();
    config.base_url = remote.base_url || config.base_url;
    config.model = remote.model || config.model;
    config.temperature = remote.temperature ?? config.temperature;
    config.timeout = remote.timeout ?? config.timeout;
    configured = remote.configured;
  } catch { /* ignore */ }

  if (workspacePath.value && configured) {
    await refreshPages();
    status.value = `已加载模型配置：${config.model}`;
    step.value = "main";
  } else if (workspacePath.value) {
    step.value = "config";
  } else {
    step.value = "workspace";
  }
});

/* ================================================================
   Step 1: Choose Workspace
   ================================================================ */
async function chooseWorkspace() {
  workspaceLoading.value = true;
  try {
    let path = "";
    if (isTauri.value) {
      path = await invoke<string>("select_workspace_dir");
    } else {
      path = workspacePath.value || "未在桌面端运行，使用默认工作目录";
    }
    if (path) {
      workspacePath.value = path;
      await waitForBackend(20, 300);
      try {
        const info = await api.fetchWorkspaceInfo();
        wikiDir.value = info.directories.wiki;
      } catch { /* ignore */ }
      step.value = "config";
    }
  } catch (error) {
    console.error("选择工作空间失败:", error);
  } finally {
    workspaceLoading.value = false;
  }
}

/* ================================================================
   Step 2: Config Model & Enter
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

function backToWorkspace() {
  step.value = "workspace";
}

function backToConfig() {
  step.value = "config";
}

/* ================================================================
   Wiki Operations
   ================================================================ */
async function saveSettings() {
  await guarded("模型配置已保存。", async () => {
    const saved = await api.saveModelConfig(config);
    status.value = `模型配置已保存：${saved.model} / ${saved.api_key_masked}`;
    config.api_key = "";
    showSettings.value = false;
    testResult.value = null;
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
  const prevPath = workspacePath.value;
  const prevWikiDir = wikiDir.value;
  try {
    const path = await invoke<string>("select_workspace_dir");
    if (!path) { status.value = "就绪"; return; }
    workspacePath.value = path;
    await waitForBackend();
    try { const info = await api.fetchWorkspaceInfo(); wikiDir.value = info.directories.wiki; } catch { /* ignore */ }
    currentSourceId.value = "";
    await refreshPages();
    status.value = `已切换到：${path}`;
  } catch (error) {
    workspacePath.value = prevPath;
    wikiDir.value = prevWikiDir;
    status.value = error instanceof Error ? error.message : "切换目录失败。";
  } finally {
    switchingWorkspace.value = false;
  }
}

async function openNewWorkspace() {
  if (!isTauri.value) return;
  switchingWorkspace.value = true;
  status.value = "正在打开新工作空间...";
  const prevPath = workspacePath.value;
  const prevWikiDir = wikiDir.value;
  try {
    const path = await invoke<string>("select_workspace_dir");
    if (!path) { status.value = "就绪"; return; }
    workspacePath.value = path;
    await waitForBackend(20, 300);
    try { const info = await api.fetchWorkspaceInfo(); wikiDir.value = info.directories.wiki; } catch { /* ignore */ }
    currentSourceId.value = "";
    selectedPageId.value = "";
    previewTitle.value = "预览";
    markdown.value = "";
    pages.value = [];
    await refreshPages();
    status.value = `已打开新工作空间：${path}`;
    step.value = "main";
  } catch (error) {
    workspacePath.value = prevPath;
    wikiDir.value = prevWikiDir;
    status.value = error instanceof Error ? error.message : "打开工作空间失败。";
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
       Step 1: Workspace Selection
       ================================================================ -->
  <div v-if="step === 'workspace'" class="absolute inset-0 flex flex-col items-center justify-center p-10 overflow-y-auto bg-surface-50">
    <div class="w-full max-w-[440px] flex flex-col gap-6 p-10 bg-white border border-surface-200 rounded-3xl shadow-xl animate-scale-in">

      <!-- Icon -->
      <div class="flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-50">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="text-brand-600">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
      </div>

      <!-- Title -->
      <div>
        <h1 class="font-serif text-[24px] font-semibold tracking-[-0.01em] text-surface-900 m-0">选择工作空间</h1>
        <p class="mt-1.5 text-[15px] text-surface-500 leading-relaxed m-0">
          你的 Wiki 页面和上传资料将保存在此目录中。请选择一个空目录或已有数据的目录。
        </p>
      </div>

      <!-- Path Display -->
      <div class="flex flex-col gap-2 p-4 border border-dashed border-surface-300 rounded-xl bg-surface-50">
        <span class="text-[11px] font-semibold tracking-[0.04em] uppercase text-surface-400">工作目录</span>
        <span class="text-[13px] font-mono text-surface-700 leading-relaxed break-all">{{ workspacePath || "尚未选择" }}</span>
      </div>

      <!-- Actions -->
      <div class="flex flex-col gap-3">
        <button
          class="inline-flex items-center justify-center gap-2 w-full min-h-[44px] px-6 py-2.5 rounded-full text-[15px] font-semibold tracking-[-0.01em] bg-brand-600 text-white shadow-md hover:bg-brand-700 active:bg-brand-800 active:scale-[0.985] transition-all duration-150 disabled:opacity-35 disabled:pointer-events-none"
          :disabled="workspaceLoading"
          @click="chooseWorkspace"
        >
          <svg v-if="workspaceLoading" class="animate-spin shrink-0" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="8" cy="8" r="6" stroke-opacity="0.3"/>
            <path d="M14 8a6 6 0 0 0-10.4-4" stroke-linecap="round"/>
          </svg>
          {{ workspaceLoading ? "正在准备..." : "选择目录" }}
        </button>
      </div>

      <!-- Step Dots -->
      <div class="flex items-center justify-center gap-2 pt-1">
        <span class="w-6 h-2 rounded-full bg-brand-600 transition-all duration-300" />
        <span class="w-[18px] h-px bg-surface-200" />
        <span class="w-2 h-2 rounded-full bg-surface-300 transition-all duration-300" />
        <span class="w-[18px] h-px bg-surface-200" />
        <span class="w-2 h-2 rounded-full bg-surface-300 transition-all duration-300" />
      </div>
    </div>

    <div class="flex items-center justify-center gap-1.5 mt-4 text-[12px] text-surface-400">
      已有工作空间？
      <button class="border-0 bg-transparent text-brand-600 font-medium px-1.5 py-0.5 rounded hover:bg-brand-50 cursor-pointer text-[12px]" @click="step = 'config'">跳过，配置模型</button>
    </div>
  </div>

  <!-- ================================================================
       Step 2: Model Configuration
       ================================================================ -->
  <div v-else-if="step === 'config'" class="absolute inset-0 flex flex-col items-center justify-center p-10 overflow-y-auto bg-surface-50">
    <div class="w-full max-w-[440px] flex flex-col gap-6 p-10 bg-white border border-surface-200 rounded-3xl shadow-xl animate-scale-in">

      <!-- Icon -->
      <div class="flex items-center justify-center w-14 h-14 rounded-2xl bg-brand-50">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="text-brand-600">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      </div>

      <!-- Title -->
      <div>
        <h1 class="font-serif text-[24px] font-semibold tracking-[-0.01em] text-surface-900 m-0">配置大模型</h1>
        <p class="mt-1.5 text-[15px] text-surface-500 leading-relaxed m-0">
          连接 OpenAI 兼容 API，用于生成 Wiki 内容。API Key 将加密保存在本地。
        </p>
      </div>

      <!-- Form -->
      <div class="flex flex-col gap-3.5">
        <label class="grid gap-1.5 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
          Base URL
          <input
            v-model="config.base_url"
            autocomplete="off"
            placeholder="https://api.deepseek.com/v1"
            class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[15px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)] placeholder:text-surface-300"
          />
        </label>
        <label class="grid gap-1.5 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
          API Key
          <input
            v-model="config.api_key"
            type="password"
            placeholder="sk-..."
            class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[15px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)] placeholder:text-surface-300"
          />
        </label>
        <label class="grid gap-1.5 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
          Model
          <input
            v-model="config.model"
            autocomplete="off"
            placeholder="deepseek-chat"
            class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[15px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)] placeholder:text-surface-300"
          />
        </label>
        <div class="grid grid-cols-2 gap-2.5">
          <label class="grid gap-1.5 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
            Temperature
            <input
              v-model.number="config.temperature"
              type="number" min="0" max="2" step="0.1"
              class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[15px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)]"
            />
          </label>
          <label class="grid gap-1.5 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
            Timeout (s)
            <input
              v-model.number="config.timeout"
              type="number" min="1" max="600"
              class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[15px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)]"
            />
          </label>
        </div>

        <!-- Test Result -->
        <div v-if="testResult" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] font-medium" :class="testResult.ok ? 'bg-teal-50 text-teal-600' : 'bg-red-50 text-red-500'">
          {{ testResult.ok ? '✓' : '✗' }} {{ testResult.text }}
        </div>
      </div>

      <!-- Actions -->
      <div class="flex flex-col gap-2.5">
        <button
          class="inline-flex items-center justify-center w-full min-h-[44px] px-6 py-2.5 rounded-full text-[15px] font-semibold tracking-[-0.01em] border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 active:scale-[0.985] transition-all duration-150 disabled:opacity-35"
          :disabled="testing"
          @click="testConnection"
        >
          {{ testing ? "测试中..." : "测试连接" }}
        </button>
        <button
          class="inline-flex items-center justify-center w-full min-h-[44px] px-6 py-2.5 rounded-full text-[15px] font-semibold tracking-[-0.01em] bg-brand-600 text-white shadow-md hover:bg-brand-700 active:bg-brand-800 active:scale-[0.985] transition-all duration-150 disabled:opacity-35 disabled:pointer-events-none"
          :disabled="configSaving"
          @click="saveConfigAndEnter"
        >
          {{ configSaving ? "保存中..." : "保存并进入工作台" }}
        </button>
      </div>

      <!-- Step Dots -->
      <div class="flex items-center justify-center gap-2 pt-1">
        <span class="w-2 h-2 rounded-full bg-teal-500 transition-all duration-300" />
        <span class="w-[18px] h-px bg-surface-200" />
        <span class="w-6 h-2 rounded-full bg-brand-600 transition-all duration-300" />
        <span class="w-[18px] h-px bg-surface-200" />
        <span class="w-2 h-2 rounded-full bg-surface-300 transition-all duration-300" />
      </div>
    </div>

    <div class="flex items-center justify-center gap-1.5 mt-4 text-[12px] text-surface-400">
      <button class="border-0 bg-transparent text-brand-600 font-medium px-1.5 py-0.5 rounded hover:bg-brand-50 cursor-pointer text-[12px]" @click="backToWorkspace">← 返回选择目录</button>
      <span class="text-surface-300">·</span>
      <button class="border-0 bg-transparent text-brand-600 font-medium px-1.5 py-0.5 rounded hover:bg-brand-50 cursor-pointer text-[12px]" @click="step = 'main'">跳过，直接进入</button>
    </div>
  </div>

  <!-- ================================================================
       Step 3: Wiki Workbench (Main)
       ================================================================ -->
  <main v-else class="grid h-screen bg-surface-200" style="grid-template-columns: 320px 260px minmax(480px, 1fr); gap: 1px;">

    <!-- ===== Left Sidebar ===== -->
    <aside class="flex flex-col min-w-0 overflow-y-auto bg-white">

      <!-- Brand -->
      <div class="flex items-center gap-3 px-5 py-5">
        <img class="w-10 h-10 rounded-lg object-cover shrink-0 shadow-[0_4px_10px_rgba(0,0,0,0.12),0_0_0_0.5px_rgba(0,0,0,0.06)]" src="/logo.png" alt="LLM Wiki Manager" />
        <div class="flex-1 min-w-0">
          <p class="m-0 mb-0.5 text-[11px] font-semibold tracking-[0.06em] uppercase text-surface-400">LLM Wiki Manager</p>
          <h1 class="m-0 text-[18px] font-bold tracking-[-0.022em] leading-tight text-surface-900">知识整理工作台</h1>
        </div>
        <button
          class="inline-flex items-center justify-center w-8 h-8 rounded-lg text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-colors duration-150 shrink-0"
          title="设置"
          @click="showSettings = true"
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>
      </div>

      <!-- Status Indicator -->
      <div class="mx-4 mb-1.5 flex items-start gap-2 px-3 py-2.5 rounded-xl text-[13px] leading-snug transition-colors duration-150"
        :class="{
          'bg-surface-50 text-surface-500': connectionTone === 'ready' && !anyBusy,
          'bg-red-50 text-red-500': connectionTone === 'danger',
          'bg-brand-50 text-brand-600': anyBusy,
          'bg-amber-50 text-amber-600': switchingWorkspace,
        }"
      >
        <span class="w-2 h-2 mt-1 shrink-0 rounded-full"
          :class="{
            'bg-teal-500 shadow-[0_0_0_3px_var(--color-teal-100)]': connectionTone === 'ready' && !anyBusy,
            'bg-red-400 shadow-[0_0_0_3px_rgba(248,113,113,0.2)]': connectionTone === 'danger',
            'bg-brand-500 shadow-[0_0_0_3px_var(--color-brand-100)] animate-pulse-dot': anyBusy && !switchingWorkspace,
            'bg-amber-500 shadow-[0_0_0_3px_rgba(245,158,11,0.2)] animate-statusPulse': switchingWorkspace,
          }"
        ></span>
        <p class="m-0 flex-1 min-w-0">{{ status || "就绪" }}</p>
      </div>

      <!-- Progress Bar -->
      <div v-if="anyBusy" class="mx-4 mb-1.5 h-0.5 rounded-full bg-surface-100 overflow-hidden">
        <div class="w-[40%] h-full rounded-full bg-brand-500 animate-progress-slide"></div>
      </div>

      <!-- Section: Workspace -->
      <div class="px-4 py-3.5">
        <div class="flex items-center gap-2 mb-2.5">
          <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-surface-100 text-[11px] font-bold text-surface-400">00</span>
          <h2 class="m-0 text-[13px] font-semibold tracking-[-0.01em] text-surface-700">存储目录</h2>
        </div>
        <div class="flex flex-col gap-1.5">
          <div class="flex flex-col gap-0.5">
            <span class="text-[11px] font-medium text-surface-400">数据根目录</span>
            <span class="text-[12px] text-surface-500 truncate leading-relaxed" :title="workspacePath">{{ workspacePath || "未设置" }}</span>
          </div>
          <div class="flex flex-col gap-0.5">
            <span class="text-[11px] font-medium text-surface-400">Wiki 文件位置</span>
            <span class="text-[12px] text-brand-600 font-medium truncate leading-relaxed" :title="wikiDir">{{ wikiDir || "—" }}</span>
          </div>
          <button
            v-if="isTauri"
            class="self-start mt-1 inline-flex items-center h-7 px-3 rounded-full text-[12px] font-medium border border-surface-200 bg-white text-surface-600 hover:bg-surface-50 active:scale-[0.98] transition-all duration-150 disabled:opacity-35"
            :disabled="anyBusy"
            @click="changeWorkspace"
          >
            更换目录
          </button>
        </div>
      </div>

      <!-- Section: Import -->
      <div class="px-4 py-3.5 border-t border-surface-100">
        <div class="flex items-center gap-2 mb-2.5">
          <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-surface-100 text-[11px] font-bold text-surface-400">01</span>
          <h2 class="m-0 text-[13px] font-semibold tracking-[-0.01em] text-surface-700">导入资料</h2>
        </div>

        <!-- File Picker -->
        <div class="relative flex items-center gap-2.5 min-h-[36px] mt-1.5 px-2 py-1.5 border border-dashed border-surface-300 rounded-xl bg-surface-50 hover:border-surface-400 hover:bg-surface-100 transition-all duration-150 cursor-pointer overflow-hidden">
          <input type="file" accept=".pdf,.docx,.doc,.txt,.md" class="absolute inset-0 opacity-0 cursor-pointer" @change="onFileChange" />
          <span class="inline-flex items-center justify-center h-[26px] px-3 rounded-full bg-brand-50 text-brand-600 text-[12px] font-semibold pointer-events-none shrink-0">选择文件</span>
          <strong class="text-[13px] font-normal text-surface-700 truncate pointer-events-none">{{ selectedFileName }}</strong>
        </div>

        <div class="grid grid-cols-2 gap-2 mt-2">
          <button
            class="inline-flex items-center justify-center min-h-[32px] px-4 py-1.5 rounded-full text-[13px] font-semibold border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 active:scale-[0.985] transition-all duration-150 disabled:opacity-35"
            :disabled="anyBusy"
            @click="uploadSelectedFile"
          >
            解析文件
          </button>
          <button
            class="inline-flex items-center justify-center min-h-[32px] px-4 py-1.5 rounded-full text-[13px] font-semibold bg-brand-600 text-white shadow-sm hover:bg-brand-700 active:bg-brand-800 active:scale-[0.985] transition-all duration-150 disabled:opacity-35"
            :disabled="!canGenerate"
            @click="generateWiki"
          >
            生成 Wiki
          </button>
        </div>
      </div>

      <!-- Bottom: Settings -->
      <div class="px-4 py-3 mt-auto border-t border-surface-100 flex flex-col gap-2">
        <button
          class="w-full inline-flex items-center justify-center gap-2 min-h-[32px] px-4 py-1.5 rounded-full text-[13px] font-medium border border-surface-200 bg-white text-surface-500 hover:bg-surface-50 active:scale-[0.985] transition-all duration-150"
          @click="showSettings = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          模型设置
        </button>
        <button
          v-if="isTauri"
          class="w-full inline-flex items-center justify-center gap-2 min-h-[32px] px-4 py-1.5 rounded-full text-[13px] font-medium border border-surface-200 bg-white text-surface-500 hover:bg-surface-50 active:scale-[0.985] transition-all duration-150 disabled:opacity-35"
          :disabled="anyBusy"
          @click="openNewWorkspace"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
          </svg>
          打开新工作空间
        </button>
      </div>
    </aside>

    <!-- ===== Middle: Page List ===== -->
    <section class="flex flex-col min-w-0 bg-white">
      <header class="flex items-center justify-between gap-3 min-h-[52px] px-4 py-3 border-b border-surface-100">
        <div>
          <p class="m-0 mb-0.5 text-[11px] font-semibold tracking-[0.06em] uppercase text-surface-400">{{ pageCountLabel }}</p>
          <h2 class="m-0 text-[16px] font-bold tracking-[-0.022em] text-surface-900">页面</h2>
        </div>
        <button
          class="inline-flex items-center justify-center w-7 h-7 rounded-md text-surface-400 hover:bg-surface-50 hover:text-surface-600 transition-colors duration-150 disabled:opacity-35"
          :disabled="anyBusy"
          title="刷新页面列表"
          @click="refreshPages"
        >
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M2 8a6 6 0 0 1 10.47-4M14 8a6 6 0 0 1-10.47 4"/>
            <path d="M14 2v4h-4M2 14v-4h4"/>
          </svg>
        </button>
      </header>

      <div class="flex flex-col gap-0.5 overflow-y-auto p-1.5 flex-1">
        <div v-if="pages.length === 0" class="flex flex-col items-center justify-center gap-1 mx-2 my-6 px-5 py-7 rounded-2xl bg-surface-50 text-surface-400 text-[13px] text-center">
          <strong class="text-[15px] font-medium text-surface-500">还没有 Wiki 页面</strong>
          <span>上传资料并生成后，页面会显示在这里</span>
        </div>
        <button
          v-for="(page, idx) in pages"
          :key="page.page_id"
          class="w-full text-left min-h-[40px] px-3 py-2 rounded-xl text-[15px] tracking-[-0.01em] transition-all duration-150 border-0 cursor-pointer animate-fade-in-up"
          :class="{
            'bg-brand-50 text-brand-600 font-medium': page.page_id === selectedPageId,
            'bg-brand-50 text-brand-600 font-medium cursor-default': page.page_id === '__generating__',
            'bg-transparent text-surface-700 hover:bg-surface-50': page.page_id !== selectedPageId && page.page_id !== '__generating__',
          }"
          :style="{ animationDelay: `${Math.min(idx, 5) * 30}ms` }"
          :disabled="page.page_id === '__generating__'"
          @click="openPage(page.page_id)"
        >
          <span v-if="page.page_id === '__generating__'" class="inline-block w-3 h-3 mr-2 shrink-0 border-2 border-brand-200 border-t-brand-600 rounded-full animate-spin align-middle"></span>
          {{ page.title }}
        </button>
      </div>
    </section>

    <!-- ===== Right: Markdown Preview ===== -->
    <section class="flex flex-col min-w-0 bg-white">
      <header class="flex items-center min-h-[52px] px-4 py-3 border-b border-surface-100">
        <div>
          <p class="m-0 mb-0.5 text-[11px] font-semibold tracking-[0.06em] uppercase text-surface-400">Markdown 预览</p>
          <h2 class="m-0 text-[16px] font-bold tracking-[-0.022em] text-surface-900 truncate">{{ previewTitle }}</h2>
        </div>
      </header>

      <article class="flex-1 overflow-y-auto p-5 bg-surface-50">
        <!-- Loading -->
        <div v-if="generating" class="flex flex-col items-center justify-center gap-2.5 min-h-full max-w-[700px] mx-auto border border-surface-200 rounded-3xl bg-white shadow-md px-8 py-14 text-center">
          <div class="w-8 h-8 border-[3px] border-surface-200 border-t-brand-500 rounded-full animate-spin mb-1"></div>
          <p class="m-0 text-[17px] font-semibold text-surface-800">正在生成 Wiki</p>
          <p class="m-0 text-[15px] text-surface-500 max-w-[340px] leading-relaxed">AI 模型正在分析「{{ selectedFileName }}」并整理知识...</p>
          <p class="m-0 mt-1 text-[12px] text-surface-400">这可能需要 10-30 秒</p>
        </div>

        <!-- Empty -->
        <div v-else-if="!markdown" class="flex items-center justify-center min-h-full max-w-[700px] mx-auto border border-dashed border-surface-200 rounded-3xl bg-surface-50 text-surface-400 text-[15px] text-center px-8 py-12">
          选择或生成一个 Wiki 页面后在此处查看。
        </div>

        <!-- Content -->
        <div v-else class="min-h-full max-w-[780px] mx-auto border border-surface-200 rounded-3xl bg-white shadow-md px-8 py-8 text-[17px] leading-relaxed tracking-[-0.01em] text-surface-800 markdown-body" v-html="renderedMarkdown"></div>
      </article>
    </section>
  </main>

  <!-- ================================================================
       Settings Modal (overlay on main workbench)
       ================================================================ -->
  <Teleport to="body">
    <div
      v-if="step === 'main' && showSettings"
      class="fixed inset-0 z-50 flex items-center justify-center p-8"
      @click.self="showSettings = false"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-surface-950/30 backdrop-blur-sm"></div>

      <!-- Modal Card -->
      <div class="relative w-full max-w-[420px] flex flex-col gap-5 p-8 bg-white border border-surface-200 rounded-3xl shadow-xl animate-scale-in">

        <!-- Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="flex items-center justify-center w-9 h-9 rounded-xl bg-brand-50">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="text-brand-600">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </div>
            <div>
              <h2 class="m-0 text-[16px] font-bold tracking-[-0.022em] text-surface-900">模型设置</h2>
              <p class="m-0 text-[12px] text-surface-400">配置 OpenAI 兼容 API 参数</p>
            </div>
          </div>
          <button
            class="inline-flex items-center justify-center w-7 h-7 rounded-md text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-colors duration-150"
            @click="showSettings = false"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <!-- Form -->
        <div class="flex flex-col gap-3">
          <label class="grid gap-1 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
            Base URL
            <input
              v-model="config.base_url"
              autocomplete="off"
              placeholder="https://api.deepseek.com/v1"
              class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[14px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)] placeholder:text-surface-300"
            />
          </label>
          <label class="grid gap-1 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
            API Key
            <input
              v-model="config.api_key"
              type="password"
              placeholder="sk-..."
              class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[14px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)] placeholder:text-surface-300"
            />
          </label>
          <label class="grid gap-1 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
            Model
            <input
              v-model="config.model"
              autocomplete="off"
              placeholder="deepseek-chat"
              class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[14px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)] placeholder:text-surface-300"
            />
          </label>
          <div class="grid grid-cols-2 gap-2.5">
            <label class="grid gap-1 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
              Temperature
              <input
                v-model.number="config.temperature"
                type="number" min="0" max="2" step="0.1"
                class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[14px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)]"
              />
            </label>
            <label class="grid gap-1 text-[12px] font-medium text-surface-500 tracking-[-0.01em]">
              Timeout (s)
              <input
                v-model.number="config.timeout"
                type="number" min="1" max="600"
                class="w-full h-10 px-3 border border-surface-200 rounded-lg bg-white text-surface-900 text-[14px] outline-none transition-all duration-150 hover:border-surface-300 focus:border-brand-500 focus:shadow-[0_0_0_3px_var(--color-brand-100)]"
              />
            </label>
          </div>

          <!-- Test Result -->
          <div v-if="testResult" class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[12px] font-medium" :class="testResult.ok ? 'bg-teal-50 text-teal-600' : 'bg-red-50 text-red-500'">
            {{ testResult.ok ? '✓' : '✗' }} {{ testResult.text }}
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-col gap-2.5">
          <button
            class="inline-flex items-center justify-center w-full min-h-[40px] px-5 py-2 rounded-full text-[14px] font-semibold tracking-[-0.01em] border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 active:scale-[0.985] transition-all duration-150 disabled:opacity-35"
            :disabled="testing"
            @click="testConnection"
          >
            {{ testing ? "测试中..." : "测试连接" }}
          </button>
          <button
            class="inline-flex items-center justify-center w-full min-h-[40px] px-5 py-2 rounded-full text-[14px] font-semibold tracking-[-0.01em] bg-brand-600 text-white shadow-md hover:bg-brand-700 active:bg-brand-800 active:scale-[0.985] transition-all duration-150 disabled:opacity-35 disabled:pointer-events-none"
            :disabled="configSaving"
            @click="saveSettings"
          >
            {{ configSaving ? "保存中..." : "保存配置" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
