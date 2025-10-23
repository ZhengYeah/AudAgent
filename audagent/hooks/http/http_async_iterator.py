"""
Used in `httpcore_hook.py` to wrap async iterators for HTTP response streaming.
"""
from collections.abc import AsyncIterator
from typing import AsyncIterator as AsyncIterType
from typing import Awaitable, Callable, Generic, Optional, TypeVar, cast

import httpcore
import httpx

from audagent.enums import HookEventType
from audagent.hooks.http.models import HttpResponseData
from audagent.hooks.models import HookEvent

T = TypeVar('T')

class HttpAsyncIterator(Generic[T]):
    """
    A wrapper class that handles iteration over an AsyncIterable object.
    This class receives a typing.AsyncIterable object during initialization and provides an interface to iterate over it, yielding the results.
    """
    def __init__(self, response: httpcore.Response, callback: Callable[[HookEvent], Awaitable[None]]) -> None:
        super().__init__()
        self._async_iterable = response.aiter_stream()
        self._response = response
        self._callback = callback
        self._iterator: Optional[AsyncIterType[T]] = None

    def __aiter__(self) -> 'AsyncIterator[T]':
        return self

    async def __anext__(self) -> T:
        """
        Get the next item from the async iterator.
        Raises `StopAsyncIteration` when there are no more items
        """
        if self._iterator is None:
            self._iterator = cast(AsyncIterator[T], self._async_iterable.__aiter__())
        try:
            original = await self._iterator.__anext__()
            try:
                httpx_response = httpx.Response(
                    status_code=self._response.status,
                    headers=self._response.headers,
                    content=cast(bytes, original),
                    extensions=self._response.extensions
                )
            except Exception as e:
                return original
            response_data = HttpResponseData(
                status_code=httpx_response.status_code,
                headers=dict(httpx_response.headers),
                body=httpx_response.text
            )
            hook_event = HookEvent(
                event_type=HookEventType.HTTP_RESPONSE,
                data=response_data.model_dump()
            )
            await self._callback(hook_event)
            return original
        except StopAsyncIteration:
            self._iterator = None
            raise

    async def aclose(self) -> None:
        """
        Close the async iterator if it has an aclose method.
        """
        if self._iterator is not None and hasattr(self._iterator, 'aclose'):
            try:
                await self._iterator.aclose()
            except Exception:
                pass
            self._iterator = None
