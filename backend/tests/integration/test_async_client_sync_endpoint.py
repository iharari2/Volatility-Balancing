import pytest


@pytest.mark.anyio
async def test_async_client_healthz(async_client):
    response = await async_client.get("/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
