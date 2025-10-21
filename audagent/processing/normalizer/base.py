import abc


class BaseHttpContentNormalizer(abc.ABC):
    def __init__(self) -> None:
        self.support_content_types: list[str] = []

    # As a property to prevent modification
    @property
    def supported_content_types(self) -> list[str]:
        return self.support_content_types

    @abc.abstractmethod
    def normalize(self, content: str) -> str: ...
    