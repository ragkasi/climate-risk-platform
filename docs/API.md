# Climate Risk Lens API Documentation

## Overview

The Climate Risk Lens API provides endpoints for accessing real-time climate hazard predictions, managing assets, and configuring alerts. All responses are sanitized to contain only ASCII characters.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses JWT-based authentication with OTP (One-Time Password) verification.

### Request OTP

```http
POST /api/v1/auth/request_otp
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Verification code sent to your email",
  "email": "user@example.com",
  "expires_in": 300
}
```

### Verify OTP

```http
POST /api/v1/auth/verify_otp
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

## Risk Assessment

### Geocode Address

```http
GET /api/v1/risk/geocode?query=San Francisco
Authorization: Bearer <token>
```

**Response:**
```json
{
  "point": {
    "lat": 37.7749,
    "lon": -122.4194
  },
  "admin_areas": ["California", "San Francisco County"]
}
```

### Query Risk

```http
POST /api/v1/risk/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "lat": 37.7749,
  "lon": -122.4194,
  "hazards": ["flood", "heat", "smoke", "pm25"],
  "horizon_hours": 24
}
```

**Response:**
```json
{
  "grid_id": "37_-122",
  "horizon": 24,
  "predictions": [
    {
      "hazard": "flood",
      "p_risk": 0.35,
      "q10": 0.15,
      "q50": 0.35,
      "q90": 0.65,
      "model": "demo-model-v1",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "top_drivers": [
    {
      "feature": "precipitation_24h",
      "contribution": 0.35
    }
  ],
  "brief": "Moderate risk conditions present. Main hazard: heat with 42% probability. Stay informed.",
  "sources": ["NOAA", "USGS", "EPA AirNow", "NASA FIRMS"]
}
```

## Asset Management

### Upload Assets

```http
POST /api/v1/assets/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <CSV or GeoJSON file>
```

**Response:**
```json
{
  "site_ids": ["uuid1", "uuid2"],
  "stats": {
    "total_sites": 2,
    "file_type": "csv"
  }
}
```

### Get Site Risk

```http
GET /api/v1/assets/{site_id}/risk?horizon_hours=24
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "site_id": "uuid1",
    "time": "2024-01-01T24:00:00Z",
    "hazard": "flood",
    "p_risk": 0.35,
    "q10": 0.15,
    "q50": 0.35,
    "q90": 0.65,
    "brief": "Demo risk assessment for flood at Site 1"
  }
]
```

## Alert Management

### Subscribe to Alerts

```http
POST /api/v1/alerts/subscribe
Authorization: Bearer <token>
Content-Type: application/json

{
  "site_ids": ["uuid1", "uuid2"],
  "hazard": "flood",
  "threshold": 0.5,
  "channel": ["email", "webhook"],
  "webhook_url": "https://example.com/webhook"
}
```

**Response:**
```json
{
  "subscription_id": "sub_123"
}
```

### List Alerts

```http
GET /api/v1/alerts/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "alert_123",
    "site_id": "uuid1",
    "hazard_type": "flood",
    "status": "sent",
    "p_risk": 0.65,
    "threshold": 0.5,
    "channel": "email",
    "sent_at": "2024-01-01T12:00:00Z",
    "created_at": "2024-01-01T11:00:00Z"
  }
]
```

## Feedback

### Submit Feedback

```http
POST /api/v1/feedback/
Authorization: Bearer <token>
Content-Type: application/json

{
  "hazard_id": "hazard_123",
  "label": "TP",
  "notes": "Accurate prediction"
}
```

**Response:**
```json
{
  "message": "Feedback submitted successfully",
  "feedback_id": "feedback_123"
}
```

## Admin Endpoints

### System Metrics

```http
GET /api/v1/admin/metrics
Authorization: Bearer <token>
```

**Response:**
```json
{
  "database": {
    "hazard_predictions": 1000,
    "alerts": 50,
    "telemetry_records": 5000
  },
  "redis": {
    "memory_usage": "128MB",
    "connected_clients": 5
  },
  "latency": {
    "data_latency_p50_ms": 150,
    "data_latency_p95_ms": 500
  },
  "cache": {
    "cache_hit_ratio": 0.85
  }
}
```

### Retrain Models

```http
POST /api/v1/admin/retrain?hazard=flood
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Model retraining started for flood",
  "status": "success"
}
```

## Health Checks

### Health Check

```http
GET /api/v1/healthz
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "0.1.0"
}
```

### Readiness Check

```http
GET /api/v1/readyz
```

**Response:**
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- 60 requests per minute per IP
- 10 requests per minute burst allowance
- Rate limit headers included in responses

## ASCII-Only Policy

All API responses are sanitized to contain only ASCII characters:
- No emojis, em dashes, en dashes, or smart quotes
- All text content is ASCII-compliant
- Error messages and user-facing text are sanitized
