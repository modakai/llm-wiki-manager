from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.core.config import load_model_config
from app.schemas.wiki import WikiGenerateRequest, WikiPageContentResponse, WikiPageResponse
from app.services.llm_service import LLMError, OpenAICompatibleClient
from app.services.wiki_service import (
    build_wiki_prompt,
    list_wiki_pages,
    parse_llm_markdown,
    write_wiki_page,
)

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


@router.post("/generate", response_model=WikiPageResponse)
async def generate_wiki(payload: WikiGenerateRequest, request: Request) -> WikiPageResponse:
    """读取解析文本，调用模型生成 Wiki，并写入本地 Markdown。"""

    paths = request.app.state.paths
    parsed_path = paths.parsed_dir / f"{payload.source_id}.txt"
    if not parsed_path.exists():
        raise HTTPException(status_code=404, detail="未找到对应解析文本，请先上传文件。")

    source_path = _find_source_file(paths.raw_dir, payload.source_id)
    source_filename = _display_source_filename(source_path, payload.source_id)
    system_prompt, user_prompt = build_wiki_prompt(
        source_filename=source_filename,
        text=parsed_path.read_text(encoding="utf-8"),
    )

    try:
        client = OpenAICompatibleClient(load_model_config(paths))
        markdown = await client.chat_completion(system_prompt, user_prompt)
        result = parse_llm_markdown(markdown, source_filename)
        page = write_wiki_page(paths, result, source_filename=source_filename)
    except (LLMError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return WikiPageResponse(page_id=page.page_id, title=page.title, path=str(page.path))


@router.get("/pages", response_model=list[WikiPageResponse])
def get_wiki_pages(request: Request) -> list[WikiPageResponse]:
    """列出已生成的 Wiki 页面。"""

    return [
        WikiPageResponse(page_id=page.page_id, title=page.title, path=str(page.path))
        for page in list_wiki_pages(request.app.state.paths)
    ]


@router.get("/pages/{page_id}", response_model=WikiPageContentResponse)
def get_wiki_page(page_id: str, request: Request) -> WikiPageContentResponse:
    """读取单个 Wiki Markdown 页面，限制只能访问 wiki 目录。"""

    paths = request.app.state.paths
    page_path = (paths.wiki_dir / f"{page_id}.md").resolve()
    if paths.wiki_dir.resolve() not in page_path.parents or not page_path.exists():
        raise HTTPException(status_code=404, detail="Wiki 页面不存在。")
    markdown = page_path.read_text(encoding="utf-8")
    title = next((line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")), page_id)
    return WikiPageContentResponse(page_id=page_id, title=title, markdown=markdown)


@router.get("/index", response_model=WikiPageContentResponse)
def get_wiki_index(request: Request) -> WikiPageContentResponse:
    """读取 Wiki 首页。"""

    paths = request.app.state.paths
    paths.ensure()
    markdown = paths.index_file.read_text(encoding="utf-8")
    return WikiPageContentResponse(page_id="index", title="LLM Wiki 首页", markdown=markdown)


def _find_source_file(raw_dir: Path, source_id: str) -> Path:
    """通过 source_id 找到原始文件，避免依赖数据库。"""

    matches = list(raw_dir.glob(f"{source_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail="未找到原始文件。")
    return matches[0]


def _display_source_filename(source_path: Path, source_id: str) -> str:
    """去掉 source_id 前缀，展示用户原文件名。"""

    prefix = f"{source_id}_"
    return source_path.name.removeprefix(prefix)
