import logging
from typing import Any, Optional

from pydantic import ValidationError

from audagent.enums import HookEventType
from audagent.graph.enums import HttpModel
from audagent.graph.models import GraphExtractor, GraphStructure
from audagent.hooks.http.models import HttpRequestData, HttpResponseData
from audagent.processing.base import BaseProcessor
from audagent.processing.normalizer.base import BaseHttpContentNormalizer
from audagent.processing.normalizer.event_stream_normalizer import EventStreamNormalizer
from audagent.processing.normalizer.ndjson_normalizer import NdjsonContentNormalizer
from audagent.llm.ollama_models import graph_extractor_fm # This import all the graph extractor models; refer to llm/__init__.py

logger = logging.getLogger(__name__)

class HttpProcessor(BaseProcessor):
    def __init__(self) -> None:
        super().__init__()
        self._supported_events = [
            HookEventType.HTTP_REQUEST,
            HookEventType.HTTP_RESPONSE
        ]
        self._content_normalizers: list[BaseHttpContentNormalizer] = [
            NdjsonContentNormalizer(),
            EventStreamNormalizer(),
        ]

    async def process(self, event_type: HookEventType, data: dict[str, Any]) -> Optional[GraphStructure]:
        model_mapping: dict[HookEventType, type[HttpRequestData | HttpResponseData]] = {
            HookEventType.HTTP_REQUEST: HttpRequestData,
            HookEventType.HTTP_RESPONSE: HttpResponseData
        }
        payload: HttpRequestData | HttpResponseData = model_mapping[event_type].model_validate(data)
        return await self._handle_payload(payload)

    async def _handle_payload(self, request: HttpRequestData | HttpResponseData) -> Optional[GraphStructure]:
        """
        Handle the HTTP request/response payload to extract graph structure according to http requests.
        Make sure to implement all the necessary graph extractors for models in HttpModel.
        This is a brute-force approach that tries to match the body content to each model until one succeeds.
        """
        # Creat a list of graph extractor instances (of requests and responses) based on HttpModel enum; refer to llm/*_models.py for details.
        # Actually, this is where the FlavorManager benefits us: Create instances based on a set of flavors (HttpModel enum here).
        models: list[type[GraphExtractor]] = [graph_extractor_fm[model] for model in HttpModel]
        body: Optional[str] = request.body

        if body is not None and body != "":
            for normalizer in self._content_normalizers:
                # Normalize to json if the content type is text stream or ndjson
                if any(sct in request.headers.get("content-type", 'text/plain') for sct in normalizer.supported_content_types):
                    body = normalizer.normalize(body)
                    break
            for model_type in models:
                try:
                    req_model = model_type.model_validate_json(body)
                    return self._parse_nodes_and_edges(req_model, request=request)
                # TODO: Check presidio info from edges, also return presidio info updates if any
                except ValidationError:
                    continue
        logger.warning(f"Did not find a suitable model for: {body}")
        return None

    def _parse_nodes_and_edges(self, payload: GraphExtractor, **kwargs: Any) -> Optional[GraphStructure]: # payload = req_model, i.e. LLM data model
        nodes, edges = payload.extract_graph_structure(**kwargs) # Refer to each LLM's extract_graph_structure() method
        logger.debug(f"Extracted {len(nodes)} nodes and {len(edges)} edges from HTTP payload")
        return nodes, edges
