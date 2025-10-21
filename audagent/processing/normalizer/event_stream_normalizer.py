from audagent.processing.normalizer.base import BaseHttpContentNormalizer


class EventStreamNormalizer(BaseHttpContentNormalizer):
    def __init__(self, event_data_tag: str = "data: ") -> None:
        super().__init__()
        self._event_data_tag = event_data_tag
        self._supported_content_types = ["text/event-stream"]

    def normalize(self, content: str) -> str:
        """
        Find all lines starting with the event data tag and extract their content.
        """
        if self._event_data_tag not in content:
            return content
        data_raw = str()
        for line in content.splitlines():
            if line.startswith(self._event_data_tag):
                data_raw = line[len(self._event_data_tag):]
                break
        return data_raw.strip() # Remove leading/trailing whitespace
