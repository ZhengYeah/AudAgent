"""
The HTTP Core package provides a minimal low-level HTTP client, which does one thing only: sending HTTP requests.
HTTPX is a fully featured HTTP client for Python 3, which provides sync and async APIs.
========
We use httpcore to
"""
import logging
from typing import Any, Optional

import httpcore
import httpx

from audagent.enums import HookEventType
from audagent.hooks.http.http_async_iterator import HttpAsyncIterator
from audagent.hooks.http.http_base_hook import HttpInterceptHook
from audagent.hooks.http.models import HttpRequestData, HttpResponseData
from audagent.hooks.models import HookEvent

logger = logging.getLogger(__name__)

class HttpcoreHook(HttpInterceptHook):
    def __init__(self, callback_handler: Any) -> None:
        super().__init__(callback_handler)
        self._original_handle_request: Optional[Any] = None
        self._original_handle_async_request: Optional[Any] = None

    def apply_hook(self) -> None:
        """
        Apply the httpcore hook by monkey-patching the handle_request and handle_async_request methods.
        Method `remove_hook` can be used to remove the hook and restore the original methods.
        """
        # Function object `handle_request`: Send an HTTP request, and return an HTTP response.
        self._original_handle_request = httpcore.HTTPConnection.handle_request
        def sync_wrapper(conn_self: httpcore.HTTPConnection, request: httpcore.Request) -> httpcore.Response:
            return self._intercepted_handle_request(conn_self, request)
        httpcore.HTTPConnection.handle_request = sync_wrapper
        # Async version (if available)
        if hasattr(httpcore, 'AsyncHTTPConnection'):
            self._original_handle_async_request = httpcore.AsyncHTTPConnection.handle_async_request
            async def async_wrapper(conn_self: httpcore.AsyncHTTPConnection, request: httpcore.Request) -> httpcore.Response:
                return await self._intercepted_handle_async_request(conn_self, request)
            httpcore.AsyncHTTPConnection.handle_async_request = async_wrapper
        logger.debug("Httpcore hook applied.")

    def _normalize_request(self, request: httpcore.Request) -> HookEvent:
        # Convert httpcore.Request to httpx.Request
        httpx_request = httpx.Request(
            method=request.method.decode('ascii'),
            url=str(request.url),
            headers=[(k.decode('ascii'), v.decode('ascii')) for k, v in request.headers],
            content=b"".join(request.stream).decode()
        )
        request_data = HttpRequestData(
            method=httpx_request.method,
            url=str(httpx_request.url),
            headers=dict(httpx_request.headers),
            body=httpx_request.content.decode() if httpx_request.content else None
        )
        hook_event = HookEvent(
            event_type=HookEventType.HTTP_REQUEST,
            data=request_data.model_dump()
        )
        return hook_event

    async def _normalize_response(self, response: httpcore.Response) -> HookEvent:
        httpx_response = httpx.Response(
            status_code=response.status,
            headers=response.headers,
            content= await response.aread(),
            extensions=response.extensions
        )
        response_data = HttpResponseData(
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            body=httpx_response.text
        )
        hook_event = HookEvent(
            event_type=HookEventType.HTTP_RESPONSE,
            data=response_data.model_dump()
        )
        return hook_event

    def _normalize_response_sync(self, response: httpcore.Response) -> HookEvent:
        httpx_response = httpx.Response(
            status_code=response.status,
            headers=response.headers,
            content=b"".join(response.stream),
            extensions=response.extensions
        )
        response_data = HttpResponseData(
            status_code=httpx_response.status_code,
            headers=dict(httpx_response.headers),
            body=httpx_response.text
        )
        hook_event = HookEvent(
            event_type=HookEventType.HTTP_RESPONSE,
            data=response_data.model_dump()
        )
        return hook_event

    """
    Callbacks act as notifiers for request/response events.
    _request_callback: called (by the intercept handle function) before sending a Http request
    _response_callback: called (by the intercept handle function) after receiving a Http response
    """
    def _request_callback_sync(self, request: httpcore.Request) -> None:
        normalized = self._normalize_request(request)
        self._callback_handler.on_hook_callback_sync(self, normalized)

    def _response_callback_sync(self, response: httpcore.Response) -> None:
        normalized = self._normalize_response_sync(response)
        self._callback_handler.on_hook_callback_sync(self, normalized)

    async def _request_callback(self, request: httpcore.Request) -> None:
        normalized = self._normalize_request(request)
        await self._callback_handler.on_hook_callback(self, normalized)

    async def _response_callback(self, response: httpcore.Response) -> None:
        normalized = await self._normalize_response(response)
        await self._callback_handler.on_hook_callback(self, normalized)

    def _intercepted_handle_request(self, conn_self: httpcore.HTTPConnection, request: httpcore.Request) -> httpcore.Response:
        self._request_callback_sync(request)
        response: httpcore.Response = self._original_handle_request(conn_self, request)
        try:
            self._response_callback_sync(response)
        except Exception as e:
            logger.error(f"Error in response callback sync: {e}")
            return response
        # Change back to httpcore.Response
        new_response = httpcore.Response(
            status=response.status,
            headers=response.headers,
            content=response.read(),
            extensions=response.extensions.copy() if response.extensions else {}
        )
        return new_response

    async def _intercepted_handle_async_request(self, conn_self: httpcore.AsyncHTTPConnection, request: httpcore.Request) -> httpcore.Response:
        """
        When an async HTTP request is made, this method intercepts the request and response.
        :param conn_self:
        """
        await self._request_callback(request)
        response: httpcore.Response = await self._original_handle_async_request(conn_self, request)
        if self._is_event_stream(response):
            """
            Get the 'host' header from the original request and put it in the response headers
            This is a workaround for the fact that httpcore doesn't pass the host header to the response when using streamed responses
            """
            for kvp in request.headers:
                header, value = kvp
                if header.decode().lower() == 'host':
                    response.headers.append((b'host', value))
                    break
            new_response = httpcore.Response(
                status=response.status,
                headers=response.headers,
                content=HttpAsyncIterator(response, self._handle_streamed_hook),
                extensions=response.extensions.copy() if response.extensions else {}
            )
            return new_response
        # If not streamed, normal processing
        try:
            await self._response_callback(response)
        except Exception as e:
            logger.error(f"Error in response callback async: {e}")
            return response
        new_response = httpcore.Response(
            status=response.status,
            headers=response.headers,
            content=await response.aread(),
            extensions=response.extensions.copy() if response.extensions else {}
        )
        return new_response

    @staticmethod
    def _is_event_stream(response: httpcore.Response) -> bool:
        for kvp in response.headers:
            header, value = kvp
            if header.decode().lower() == 'content-type':
                if 'text/event-stream' in value.decode().lower():
                    return True
        return False

    async def _handle_streamed_hook(self, event: HookEvent) -> None:
         await self._callback_handler.on_hook_callback(self, event)

    def remove_hook(self) -> None:
        if self._original_handle_request:
            httpcore.HTTPConnection.handle_request = self._original_handle_request
        if self._original_handle_async_request and hasattr(httpcore, 'AsyncHTTPConnection'):
            httpcore.AsyncHTTPConnection.handle_async_request = self._original_handle_async_request
        logger.debug("Httpcore hook removed.")
