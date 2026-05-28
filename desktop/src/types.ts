// 这些类型与 FastAPI 响应保持一致，避免 Vue 组件直接依赖裸 JSON。
export interface ModelConfigPayload {
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
  timeout: number;
}

export interface ModelConfigView {
  base_url: string;
  api_key: null;
  api_key_masked: string;
  model: string;
  temperature: number;
  timeout: number;
  configured: boolean;
}

export interface UploadResult {
  source_id: string;
  filename: string;
  status: string;
  text_chars: number;
}

export interface WikiPage {
  page_id: string;
  title: string;
  path: string;
}

export interface WikiPageContent {
  page_id: string;
  title: string;
  markdown: string;
}

export interface WorkspaceInfo {
  path: string;
  directories: {
    raw: string;
    parsed: string;
    wiki: string;
  };
}
