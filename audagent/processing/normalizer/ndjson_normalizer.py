import copy
import json
from typing import Any

from jsonpath_ng import parse

from audagent.processing.normalizer.base import BaseHttpContentNormalizer


class NdjsonContentNormalizer(BaseHttpContentNormalizer):
    def __init__(self, anchor_jsonpath: str = "$.message.content") -> None:
        super().__init__()
        self._anchor_jsonpath = anchor_jsonpath
        self._supported_content_types = ["application/x-ndjson"]

    def normalize(self, content: str) -> str:
        all_objects: list[dict[str, Any]] = []
        merged: dict[str, Any] = {}
        for line in content.split("\n"):
            if line:
                all_objects.append(json.loads(line))
        if len(all_objects) == 0:
            return "{}"
        merged = copy.deepcopy(all_objects[0])
        self._set_content(merged, str())
        for obj in all_objects:
            new_content = self._extract_content(obj)
            if new_content:
                previous_content = self._extract_content(merged)
                self._set_content(merged, previous_content + new_content)
            for k, v in obj.items():
                if k not in merged:
                    merged[k] = v
        return json.dumps(merged)

    def _set_content(self, data: dict[str, Any], new_value: str) -> None:
        # Define the jsonpath expression
        jsonpath_expr = parse(self._anchor_jsonpath)
        jsonpath_expr.update(data, new_value)

    def _extract_content(self, data: dict[str, Any]) -> Any:
        # Define the jsonpath expression
        jsonpath_expr = parse(self._anchor_jsonpath)
        # Apply the expression to the data
        match = jsonpath_expr.find(data)
        # If a match is found, return the content
        if match:
            return match[0].value
        else:
            return None
