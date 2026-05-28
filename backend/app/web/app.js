let currentSourceId = null;

const $ = (id) => document.getElementById(id);

// MVP 使用原生 fetch，保持前端足够薄，方便后续替换为 Vue/Tauri。
async function request(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

async function loadSettings() {
  const config = await request("/api/settings/model");
  $("baseUrl").value = config.base_url || "https://api.deepseek.com/v1";
  $("model").value = config.model || "";
  $("temperature").value = config.temperature ?? 0.2;
  $("timeout").value = config.timeout ?? 60;
  $("settingsStatus").textContent = config.configured
    ? `已配置：${config.model} / ${config.api_key_masked}`
    : "尚未配置模型。";
}

async function saveSettings() {
  const payload = {
    base_url: $("baseUrl").value.trim(),
    api_key: $("apiKey").value.trim(),
    model: $("model").value.trim(),
    temperature: Number($("temperature").value || 0.2),
    timeout: Number($("timeout").value || 60),
  };
  const saved = await request("/api/settings/model", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  $("settingsStatus").textContent = `已保存：${saved.model} / ${saved.api_key_masked}`;
}

async function uploadFile() {
  const file = $("fileInput").files[0];
  if (!file) {
    $("uploadStatus").textContent = "请选择文件。";
    return;
  }
  const form = new FormData();
  form.append("file", file);
  const uploaded = await request("/api/uploads", { method: "POST", body: form });
  currentSourceId = uploaded.source_id;
  $("generateWiki").disabled = false;
  $("uploadStatus").textContent = `已解析 ${uploaded.filename}，文本 ${uploaded.text_chars} 字。`;
}

async function generateWiki() {
  if (!currentSourceId) return;
  $("uploadStatus").textContent = "正在调用模型生成 Wiki...";
  const page = await request("/api/wiki/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source_id: currentSourceId }),
  });
  $("uploadStatus").textContent = `已生成 Wiki：${page.title}`;
  await loadPages();
  await openPage(page.page_id);
}

async function loadPages() {
  const pages = await request("/api/wiki/pages");
  $("pageList").innerHTML = "";
  for (const page of pages) {
    const button = document.createElement("button");
    button.className = "page-item";
    button.textContent = page.title;
    button.onclick = () => openPage(page.page_id);
    $("pageList").appendChild(button);
  }
}

async function openPage(pageId) {
  const page = await request(`/api/wiki/pages/${pageId}`);
  $("previewTitle").textContent = page.title;
  $("markdownPreview").textContent = page.markdown;
}

$("saveSettings").onclick = () => saveSettings().catch((error) => ($("settingsStatus").textContent = error.message));
$("uploadFile").onclick = () => uploadFile().catch((error) => ($("uploadStatus").textContent = error.message));
$("generateWiki").onclick = () => generateWiki().catch((error) => ($("uploadStatus").textContent = error.message));
$("refreshPages").onclick = () => loadPages();

loadSettings().catch((error) => ($("settingsStatus").textContent = error.message));
loadPages();
