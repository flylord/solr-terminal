"""Async HTTP client for a standalone Solr server with Basic Auth."""

from dataclasses import dataclass
from urllib.parse import quote

import httpx


class SolrError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class QueryResult:
    url: str
    status: int
    content_type: str
    body: str


class SolrClient:
    def __init__(self, base_url: str, user: str, password: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(auth=(user, password), timeout=timeout)

    async def _get(self, path: str, params: list[tuple[str, str]]) -> httpx.Response:
        try:
            return await self._http.get(f"{self.base_url}/{path}", params=params)
        except httpx.HTTPError as exc:
            raise SolrError(f"Cannot reach Solr at {self.base_url}: {exc}") from exc

    async def _admin_json(self, path: str, params: list[tuple[str, str]]) -> dict:
        response = await self._get(path, [*params, ("wt", "json")])
        if response.status_code == 401:
            raise SolrError("Authentication failed (401)")
        if response.status_code == 403:
            raise SolrError("Access denied (403)")
        unexpected = SolrError(f"Unexpected response from {response.url}: HTTP {response.status_code}")
        if response.status_code != 200:
            raise unexpected
        try:
            return response.json()
        except ValueError as exc:
            raise unexpected from exc

    async def list_cores(self) -> list[str]:
        data = await self._admin_json("admin/cores", [("action", "STATUS")])
        return sorted(data.get("status", {}))

    async def solr_version(self) -> str:
        data = await self._admin_json("admin/info/system", [])
        return data.get("lucene", {}).get("solr-spec-version", "unknown")

    async def paramsets(self, core: str) -> list[str]:
        try:
            data = await self._admin_json(f"{quote(core, safe='')}/config/params", [])
        except SolrError:
            return []
        return sorted((data.get("response", {}).get("params") or {}).keys())

    async def query(self, path: str, params: list[tuple[str, str]]) -> QueryResult:
        response = await self._get(path, params)
        return QueryResult(
            url=str(response.url),
            status=response.status_code,
            content_type=response.headers.get("content-type", ""),
            body=response.text,
        )

    async def aclose(self) -> None:
        await self._http.aclose()
