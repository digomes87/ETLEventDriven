import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_ingest_event_creates_processed_record(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "source_name": "test-source",
            "payload": {"value": 10},
        }
        # Assuming the ingest process also creates the source if not exists
        # Or we might need to create the source first depending on the logic
        response = await client.post("/api/ingest", json=payload)
        
        # If the API returns 500, we should print the body to debug
        if response.status_code != 201:
            print(f"Error response: {response.json()}")

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "SUCCESS"
        assert body["raw_event_id"] is not None


@pytest.mark.asyncio
async def test_list_sources_returns_created_source(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "source_name": "source-list",
            "payload": {"value": 5},
        }
        response_ingest = await client.post("/api/ingest", json=payload)
        
        if response_ingest.status_code != 201:
            print(f"Error ingest response: {response_ingest.json()}")
            
        assert response_ingest.status_code == 201

        response_sources = await client.get("/api/sources")
        assert response_sources.status_code == 200
        sources = response_sources.json()
        names = {item["name"] for item in sources}
        assert "source-list" in names
