# Ollama Secure Gateway

A FastAPI-based proxy middleware that supports:

* JWT authentication
* Request logging
* Per-user rate limiting
* Secure proxying to a backend server

---

## 1. Authentication

Clients obtain a JWT by sending a `POST` request to `/token` with their username and password.

All protected routes (e.g., the proxy endpoint) require the `Authorization: Bearer <token>` header.

```bash
curl -X POST https://localhost:8000/token \
  -d "username=user1&password=password1" \
  -k
```

The `-k` option tells `curl` to ignore certificate verification. This is acceptable for local development with a self-signed certificate but should not be used in production.

---

## 2. Request Logging

The middleware logs each request to a file defined by the `LOGGING_FILE` constant. Logged information includes:

* Username (or `Anonymous` if unauthenticated)
* Request method and endpoint
* Timestamp
* Request duration in seconds

---

## 3. Rate Limiting

Implemented using the `slowapi` library.

* Each authenticated user is limited to 5 requests per minute per route
* Limits are enforced per path and per user

---

## 4. Proxying Requests

Requests to unmatched paths are forwarded to a target server specified by the `TARGET_SERVER` constant.

Features:

* Preserves HTTP method, headers, and request body
* Forwards the request to the target server
* Returns the raw response content

Example request:

```bash
curl -X GET https://localhost:8000/your/target/endpoint \
  -H "Authorization: Bearer <your_token>" \
  -k
```

---

## 5. Access Control

Access to proxied routes is restricted to authenticated and active users using:

```python
Depends(get_current_active_user)
```

User accounts are stored in a JSON file (path defined by `DB_FILE`).
New users can self-register via `/users`, but must be manually activated (`is_active = true`).

---

## Running the Application with HTTPS

To run the FastAPI app securely over HTTPS:

### Step 1: Generate a Self-Signed Certificate (Development Only)

```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

> For production, replace with a valid certificate from a certificate authority.

### Step 2: Run with Uvicorn and SSL

```bash
uvicorn middleware:app --reload \
  --host 0.0.0.0 --port 8000 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

---

## API Summary

| Endpoint    | Method | Description                               |
| ----------- | ------ | ----------------------------------------- |
| `/token`    | POST   | Login and receive JWT token               |
| `/users`    | POST   | Register a new user (inactive by default) |
| `/users/me` | GET    | Retrieve current authenticated user       |
| `/{path}`   | ANY    | Forward authenticated requests to target  |

---

## Considerations

* **Security**: Use HTTPS in production and securely store secret keys.
* **Timeouts**: Requests to the target server use configurable timeouts.
* **Error Handling**: Unexpected errors from the target server are propagated to the client.
* **Scalability**: Supports easy extension with caching, auditing, or load balancing mechanisms.
