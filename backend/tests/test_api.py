from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["dataset"]["track_count"] >= 1


def test_track_listing() -> None:
    response = client.get("/tracks", params={"query": "amber"})
    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert any("Amber" in track["title"] for track in payload)


def test_playlist_generation() -> None:
    seed_track_id = client.get("/tracks").json()[0]["track_id"]
    response = client.post(
        "/playlists/generate",
        json={
            "seed_track_id": seed_track_id,
            "target_type": "genre",
            "target_value": "synthwave",
            "algorithm": "astar",
            "playlist_length": 5,
            "constraints": {
                "artist_repeat_limit": 1,
                "explicit_filter": True,
                "tempo_policy": "lift",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["playlist_id"]
    assert len(payload["steps"]) >= 3
