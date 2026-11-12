import pytest_asyncio

from solr_tui.client import SolrClient

BASE = "http://s/solr"


@pytest_asyncio.fixture
async def client():
    c = SolrClient(BASE, "u", "p")
    yield c
    await c.aclose()
