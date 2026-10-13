import os
from typing import List, Optional, Any
from pydantic import Field, PrivateAttr
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from flashrank import Ranker, RerankRequest
from src.config import Config

class FlashRankRerank(BaseNodePostprocessor):
    """
    Reranker sử dụng thư viện FlashRank siêu nhẹ, tối ưu tốc độ CPU/GPU 
    để xếp hạng lại (Re-rank) các đoạn văn bản truy xuất được từ Retriever.
    """
    model_name: str = Field(default="ms-marco-MiniLM-L-12-v2", description="Tên mô hình rerank")
    top_n: int = Field(default=5, description="Số lượng kết quả giữ lại sau khi rerank")
    cache_dir: Optional[str] = Field(default=None, description="Thư mục cache mô hình")
    _ranker: Any = PrivateAttr()

    def __init__(
        self,
        model_name: str = "ms-marco-MiniLM-L-12-v2",
        top_n: int = 5,
        cache_dir: Optional[str] = None,
        **kwargs: Any
    ):
        target_cache = cache_dir or getattr(Config, "LOCAL_MODEL_DIR", "./local_model")
        super().__init__(model_name=model_name, top_n=top_n, cache_dir=target_cache, **kwargs)

        # Ánh xạ tên mô hình: FlashRank đóng gói phiên bản MiniLM dưới tên 'ms-marco-MiniLM-L-12-v2'
        # Hỗ trợ tự động ánh xạ nếu người dùng truyền 'ms-marco-MiniLM-L-6-v2'
        resolved_model = model_name
        if "MiniLM" in model_name:
            resolved_model = "ms-marco-MiniLM-L-12-v2"

        os.makedirs(target_cache, exist_ok=True)
        self._ranker = Ranker(model_name=resolved_model, cache_dir=target_cache)

    def _postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> List[NodeWithScore]:
        if not nodes:
            return []

        query_str = query_bundle.query_str if query_bundle else ""
        if not query_str:
            return nodes[:self.top_n]

        # Chuẩn bị danh sách passages để đưa vào FlashRank
        passages = [
            {"id": i, "text": node.node.get_content()}
            for i, node in enumerate(nodes)
        ]

        rerank_request = RerankRequest(query=query_str, passages=passages)
        results = self._ranker.rerank(rerank_request)

        # Xếp hạng lại và cập nhật điểm số tương quan mới
        reranked_nodes: List[NodeWithScore] = []
        for item in results[:self.top_n]:
            idx = item["id"]
            node_with_score = nodes[idx]
            new_score = float(item.get("score", node_with_score.score or 0.0))
            # Tạo bản sao NodeWithScore với điểm số sau rerank
            reranked_nodes.append(
                NodeWithScore(node=node_with_score.node, score=new_score)
            )

        return reranked_nodes
