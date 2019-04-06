"""Helper functions useful to multiple middlewares."""

from abc import ABC, abstractmethod
from ipaddress import ip_address
import logging
import sys
from urllib.parse import urlparse

from typing import Any, Callable, Dict, Optional, Tuple, Union


logger = logging.getLogger(__name__)


class Attributes(ABC):
    """Abstract class representing any attributes that also have a standard, dictionary form."""

    @abstractmethod
    def standardize(self) -> Dict[str, Any]:
        """Return the standard format for the attributes."""
        return dict()


class NetworkAttributes(Attributes):
    """Normalized form of network attributes."""

    def __init__(self,
                 extract_header: Callable[[str], Any],
                 remote_addr: Optional[str] = None,
                 bytes_read: Optional[int] = None,
                 bytes_written: Optional[int] = None) -> None:
        """Populate network attributes.

        :param extract_header:  Framework-agnostic callable that returns the value
                                of the provided request header.
        :param remote_addr:     IPv4/v6 and optional port (delimitted by ':') of the
                                client /machine/ that is connected to the server. This
                                address may not be the same as the machine that initiated the
                                request.
        :param bytes_read:      Number of bytes the server has read from the client request.
                                This number refers to the size of the request's message entity,
                                which is indicated by Content-Length in most cases.
        :param bytes_written:   Number of bytes the server has written to the client.
                                This number refers to the size of the response's message entity.

        """
        self.remote_addr = remote_addr
        self.client_ip, self.client_port = self._derive_client_host(extract_header)
        self.bytes_read = int(bytes_read or 0)
        self.bytes_written = int(bytes_written or 0)

    def _derive_client_host(self, extract_header: Callable[[str], Any]) -> Tuple[Optional[str], Optional[str]]:
        ip = extract_header("Cf-Connecting-Ip") or extract_header("True-Client-Ip") or self._resolve_forwarded(extract_header) or self.remote_addr

        if not ip:
            ip, port = None, None
        elif ":" not in ip:
            ip, port = ip, None
        else:
            # Could be ipv4 w/ port, or ipv6 (w/ or w/o port). Best to just parse it.
            try:
                ip = str(ip_address(ip))
                port = None
            except ValueError:
                parsed = urlparse(f"//{ip}")
                ip = str(ip_address(parsed.hostname))
                port = str(parsed.port)

        return ip, port

    def _resolve_forwarded(self, extract_header: Callable[[str], Any]) -> Optional[str]:
        forwarded_ip_list = extract_header("Forwarded") or extract_header("X-Forwarded-For") or ""
        forwarded_ip_list = forwarded_ip_list.replace(" ", "")
        return forwarded_ip_list.split(",")[0] if forwarded_ip_list else None

    def standardize(self) -> Dict[str, Any]:
        """See :func:`Attributes.standardize`."""
        result = dict()

        if self.client_ip:
            result["network.client.ip"] = self.client_ip
        if self.client_port:
            result["network.client.port"] = self.client_port
        result["network.bytes_read"] = self.bytes_read
        result["network.bytes_written"] = self.bytes_written

        return result


class HttpAttributes(Attributes):
    """Normalized form of http attributes."""

    def __init__(self,
                 extract_header: Callable[[str], Any],
                 url: str,
                 method: str,
                 status_code: int) -> None:
        """Populate http attributes.

        :param extract_header:  Framework-agnostic callable that returns the value
                                of the provided request header.
        :param url:             Full request URL. This should be the url exactly
                                as the client sent it. Also permissible: framework-specific
                                sanitized version of the url.
        :param method:          Request method in capital letters (GET, PUT, PATCH, ...).
        :param status_code:     Response status code.
        """
        self.url = url
        self.method = method
        self.status_code = status_code
        self.request_id = extract_header("X-Request-Id") or extract_header("X-Amzn-Trace-Id")
        self.referrer = extract_header("Referer")
        self.user_agent = extract_header("User-Agent")

    def standardize(self) -> Dict[str, Any]:
        """See :func:`Attributes.standardize`."""
        result = {
            "http.url": self.url,
            "http.method": self.method,
            "http.status_code": self.status_code
        }

        if self.request_id:
            result["http.request_id"] = self.request_id

        if self.referrer:
            result["http.referer"] = self.referrer

        if self.user_agent:
            result["http.useragent"] = self.user_agent

        return result


def log_request(path: str,
                duration_secs: int,
                network_attrs: NetworkAttributes,
                http_attrs: HttpAttributes,
                user_id: Optional[Union[str, int]] = None):
    """Log the provided request information in a standardized format.

    :param duration_secs:   Seconds spent processing the request.
    :param network_attrs:   See :class:`NetworkAttributes`
    :param http_attrs:      See :class:`HttpAttributes`
    :param user_id:         GDPR-compliant (not a name, username, or email) user identifier, if available.
    """
    status_code = http_attrs.status_code
    if status_code < 400:
        log_method = logger.info
    elif status_code < 500:
        log_method = logger.warning
    elif not sys.exc_info()[0]:
        log_method = logger.error
    else:
        log_method = logger.exception

    duration_ms = duration_secs * 1000
    extra = {
        "duration": duration_ms * 1000000,
        **network_attrs.standardize(),
        **http_attrs.standardize()
    }
    if user_id:
        extra["usr.id"] = user_id

    log_method(
        "%d %s %s (%s) %.2fms",
        status_code,
        http_attrs.method,
        path,
        network_attrs.client_ip or "?",
        duration_ms,
        extra=extra
    )
