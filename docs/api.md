# API

Base URL in Docker through the web container: `/api`.

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

Auth endpoints return:

```json
{
  "accessToken": "jwt",
  "tokenType": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

## Search

- `POST /search`
- `GET /search/{searchId}`
- `GET /search/{searchId}/results`
- `GET /search/{searchId}/results.csv`
- `GET /search/{searchId}/logs`
- `GET /search/history`

Create search:

```json
{
  "query": "телефон samsung",
  "marketplaces": ["ozon", "wildberries"],
  "filters": {
    "minRating": 4.7,
    "minReviews": 100,
    "minPrice": null,
    "maxPrice": 50000
  },
  "sort": "best_value"
}
```

## Favorites

- `POST /favorites`
- `GET /favorites`
- `DELETE /favorites/{favoriteOrOfferId}`

## Notifications

- `GET /notifications`
- `GET /notifications/unread-count`
- `POST /notifications/{notificationId}/read`
- `DELETE /notifications/{notificationId}`

## Settings

- `GET /settings`
- `PUT /settings`
- `POST /settings/test-telegram`

## Tracked products

- `POST /tracked-products`
- `POST /tracked-products/from-offer`
- `GET /tracked-products`
- `GET /tracked-products/{trackedProductId}/price-history`
- `POST /tracked-products/{trackedProductId}/refresh`
- `POST /tracked-products/refresh-all`
- `DELETE /tracked-products/{trackedProductId}`

## Marketplaces

- `GET /marketplaces`

Response items include `isMock` and `sourceMode`. `sourceMode` mirrors `PARSER_MODE` (`real`, `hybrid`, or `mock`) so the frontend can show whether a marketplace is running live-only collection, live collection with fallback, or deterministic development data.
