from fastapi.testclient import TestClient


def test_search_results_history_and_favorites(client: TestClient, auth_headers: dict[str, str]):
    create_response = client.post(
        "/search",
        headers=auth_headers,
        json={
            "query": "Телефон Samsung",
            "marketplaces": ["ozon", "wildberries"],
            "filters": {"minRating": 4.7, "minReviews": 100, "maxPrice": 50000},
            "sort": "best_value",
        },
    )
    assert create_response.status_code == 200
    search_id = create_response.json()["searchId"]

    results_response = client.get(f"/search/{search_id}/results", headers=auth_headers)
    assert results_response.status_code == 200
    payload = results_response.json()
    assert payload["status"] == "completed"
    assert len(payload["results"]) > 0
    assert payload["results"][0]["score"] > 0
    assert payload["results"][0]["scoreReasons"]

    history_response = client.get("/search/history", headers=auth_headers)
    assert history_response.status_code == 200
    assert history_response.json()[0]["id"] == search_id

    logs_response = client.get(f"/search/{search_id}/logs", headers=auth_headers)
    assert logs_response.status_code == 200
    assert logs_response.json()

    csv_response = client.get(f"/search/{search_id}/results.csv", headers=auth_headers)
    assert csv_response.status_code == 200
    assert "marketplace,title,price" in csv_response.text

    offer_id = payload["results"][0]["id"]
    favorite_response = client.post("/favorites", headers=auth_headers, json={"offerId": offer_id})
    assert favorite_response.status_code == 200
    assert favorite_response.json()["offerId"] == offer_id

    favorites_response = client.get("/favorites", headers=auth_headers)
    assert favorites_response.status_code == 200
    assert len(favorites_response.json()) == 1
