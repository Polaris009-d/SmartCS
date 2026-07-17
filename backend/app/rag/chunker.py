"""
文档分块器 — 针对中文电商场景优化
"""
import re


class DocumentChunker:
    """
    根据 source_type 选择不同的分块策略。
    - product_desc: 256 字符，30 字符重叠
    - faq: 按 ## 标题切分 + 内容分块
    - policy: 1024 字符，100 字符重叠
    - size_chart: 256 字符，保持完整性
    """

    def __init__(self):
        self._langchain_splitter = None

    def _get_langchain_splitter(self):
        """懒加载 langchain splitter（避免启动时加载 torch）"""
        if self._langchain_splitter is None:
            try:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
                self._langchain_splitter = RecursiveCharacterTextSplitter
            except Exception:
                self._langchain_splitter = False  # torch DLL/Import 等均标记不可用
        return self._langchain_splitter if self._langchain_splitter is not False else None

    def _split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        """智能分块：优先用 langchain，降级用简单分块"""
        splitter_cls = self._get_langchain_splitter()
        if splitter_cls:
            splitter = splitter_cls(
                separators=["\n\n", "\n", "。", ". ", " ", ""],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            return splitter.split_text(text)
        # 降级：简单句子分块
        return self._simple_split(text, chunk_size, chunk_overlap)

    def _simple_split(self, text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
        """简单分块：按句子边界切分"""
        sentences = re.split(r'(?<=[。！？.!?\n])', text)
        chunks = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) > chunk_size and current:
                chunks.append(current.strip())
                current = current[-chunk_overlap:] if chunk_overlap > 0 else ""
            current += sent
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text]

    def chunk(
        self,
        text: str,
        source_type: str = "faq",
        title: str = "",
        product_id: str | None = None,
        metadata: dict | None = None,
    ) -> list[dict]:
        """将文本切分为片段列表"""
        if source_type in ("product_desc", "size_chart"):
            texts = self._split_text(text, chunk_size=256, chunk_overlap=30)
        elif source_type == "policy":
            texts = self._split_text(text, chunk_size=1024, chunk_overlap=100)
        else:
            texts = self._split_text(text, chunk_size=512, chunk_overlap=50)

        chunks = []
        for i, chunk_text in enumerate(texts):
            chunk_meta = {
                "source_type": source_type,
                "title": title,
                "chunk_index": i,
                **(metadata or {}),
            }
            if product_id:
                chunk_meta["product_id"] = product_id
            chunks.append({
                "content": chunk_text.strip(),
                "chunk_metadata": chunk_meta,
            })
        return chunks
