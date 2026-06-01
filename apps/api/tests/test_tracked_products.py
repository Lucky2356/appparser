from fastapi.testclient import TestClient


def test_create_list_delete_tracked_product(client: TestClient, auth_headers: dict[str, str]):
    create_response = client.post(
        "/tracked-products",
        headers=auth_headers,
        json={
            "marketplace": "ozon",
            "title": "Телефон Samsung",
            "productUrl": "https://example.com/product",
            "targetPrice": 40000,
            "lastPrice": 45000,
        },
    )
    assert create_response.status_code == 200
    tracked_id = create_response.json()["id"]
    assert create_response.json()["externalId"] is None

    list_response = client.get("/tracked-products", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == tracked_id

    delete_response = client.delete(f"/tracked-products/{tracked_id}", headers=auth_headers)
    assert delete_response.status_code == 204


def test_track_offer_history_and_refresh(client: TestClient, auth_headers: dict[str, str]):
    create_search = client.post(
        "/search",
        headers=auth_headers,
        json={
            "query": "Наушники",
            "marketplaces": ["ozon"],
            "filters": {"minRating": 4.5, "minReviews": 100},
            "sort": "best_value",
        },
    )
    assert create_search.status_code == 200
    search_id = create_search.json()["searchId"]
    results = client.get(f"/search/{search_id}/results", headers=auth_headers).json()["results"]
    assert results

    track_response = client.post(
        "/tracked-products/from-offer",
        headers=auth_headers,
        json={"offerId": results[0]["id"], "targetPrice": results[0]["price"] + 500},
    )
    assert track_response.status_code == 200
    tracked_id = track_response.json()["id"]
    assert track_response.json()["lastPrice"] == results[0]["price"]
    assert track_response.json()["externalId"] == results[0]["externalId"]

    history_response = client.get(f"/tracked-products/{tracked_id}/price-history", headers=auth_headers)
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1

    refresh_response = client.post(f"/tracked-products/{tracked_id}/refresh", headers=auth_headers)
    assert refresh_response.status_code == 200

    refreshed_history = client.get(f"/tracked-products/{tracked_id}/price-history", headers=auth_headers)
    assert len(refreshed_history.json()) >= 2

    refresh_all = client.post("/tracked-products/refresh-all", headers=auth_headers)
    assert refresh_all.status_code == 200
    assert refresh_all.json()["refreshed"] == 1

    notifications = client.get("/notifications", headers=auth_headers)
    assert notifications.status_code == 200
    assert notifications.json()[0]["type"] == "target_price_reached"

    unread = client.get("/notifications/unread-count", headers=auth_headers)
    assert unread.json()["count"] == 1

    notification_id = notifications.json()[0]["id"]
    mark_read = client.post(f"/notifications/{notification_id}/read", headers=auth_headers)
    assert mark_read.status_code == 200
    assert mark_read.json()["isRead"] is True
