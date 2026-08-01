from fastapi.testclient import TestClient
import pytest

from app.dependencies import get_repository
from app.main import app
from app.models import PlaylistRequest


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


def test_cluster_target_penalty_uses_feature_centroid() -> None:
    repository = get_repository()
    target_cluster = next(iter(repository._cluster_centroids))
    track = next(track for track in repository._tracks if track.cluster_id != target_cluster)
    request = PlaylistRequest.model_validate(
        {
            "seed_track_id": track.track_id,
            "target_type": "cluster",
            "target_value": str(target_cluster),
            "algorithm": "astar",
            "playlist_length": 3,
            "constraints": {},
        }
    )
    target = repository._cluster_centroids[target_cluster]
    point = repository._feature_point(track)
    expected = sum((point[index] - target[index]) ** 2 for index in range(3)) ** 0.5
    assert repository._target_penalty(track, request) == pytest.approx(expected)
