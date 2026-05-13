def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_sources_seeded(client):
    response = client.get("/sources")
    assert response.status_code == 200
    assert len(response.json()) >= 1
