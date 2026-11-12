import base64

import httpx
import pytest
import respx

from solr_terminal.client import SolrError

BASE = "http://s/solr"
CORES = f"{BASE}/admin/cores"


@respx.mock
async def test_list_cores_sorted(client):
    respx.get(CORES).respond(json={"status": {"b": {}, "a": {}}})
    assert await client.list_cores() == ["a", "b"]


@respx.mock
async def test_list_cores_401(client):
    respx.get(CORES).respond(401)
    with pytest.raises(SolrError, match=r"Authentication failed \(401\)"):
        await client.list_cores()


@respx.mock
async def test_list_cores_connect_error(client):
    respx.get(CORES).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(SolrError, match="Cannot reach Solr at http://s/solr"):
        await client.list_cores()


@respx.mock
async def test_list_cores_404_is_unexpected(client):
    respx.get(CORES).respond(404, text="Not Found")
    with pytest.raises(SolrError, match="HTTP 404"):
        await client.list_cores()


@respx.mock
async def test_paramsets_empty_on_error(client):
    respx.get(f"{BASE}/a/config/params").respond(404)
    assert await client.paramsets("a") == []


@respx.mock
async def test_paramsets_names(client):
    respx.get(f"{BASE}/a/config/params").respond(json={"response": {"params": {"x": {}, "y": {}}}})
    assert await client.paramsets("a") == ["x", "y"]


@respx.mock
async def test_query_returns_error_body(client):
    respx.get(f"{BASE}/a/select").respond(400, text='{"error":{"msg":"bad"}}')
    r = await client.query("a/select", [("q", "(")])
    assert r.status == 400 and "bad" in r.body


@respx.mock
async def test_query_sends_basic_auth_and_params(client):
    route = respx.get(f"{BASE}/a/select").respond(200, text="{}", headers={"content-type": "application/json"})
    r = await client.query("a/select", [("q", "*:*")])
    req = route.calls.last.request
    assert req.headers["authorization"] == "Basic " + base64.b64encode(b"u:p").decode()
    assert req.url.query == b"q=%2A%3A%2A"
    assert r.url == "http://s/solr/a/select?q=%2A%3A%2A" and r.content_type == "application/json"


@respx.mock
async def test_solr_version(client):
    respx.get(f"{BASE}/admin/info/system").respond(json={"lucene": {"solr-spec-version": "9.8.0"}})
    assert await client.solr_version() == "9.8.0"


@respx.mock
async def test_query_url_is_the_sent_url(client):
    respx.get(f"{BASE}/a/select").respond(200, text="{}")
    r = await client.query("a/select", [("q", 'title:"a b" & é #x +y')])
    assert r.url == str(respx.calls.last.request.url)


async def test_aclose_closes_http_client(client):
    await client.aclose()
    assert client._http.is_closed
