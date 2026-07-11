async def _register_and_login(client, email="alice@example.com", password="supersecret1"):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "first_name": "Alice", "last_name": "A"},
    )
    assert r.status_code == 201, r.text
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def test_register_rejects_invalid_email(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "supersecret1", "first_name": "X", "last_name": "Y"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_register_rejects_short_password(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "b@example.com", "password": "short", "first_name": "X", "last_name": "Y"},
    )
    assert r.status_code == 422


async def test_duplicate_registration_is_conflict_not_500(client):
    await _register_and_login(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "supersecret1",
            "first_name": "Alice",
            "last_name": "A",
        },
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


async def test_login_wrong_password_rejected(client):
    await _register_and_login(client)
    r = await client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "wrongpass"}
    )
    assert r.status_code == 401


async def test_protected_route_requires_token(client):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401


async def test_protected_route_with_valid_token(client):
    token = await _register_and_login(client)
    r = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


async def test_refresh_rotation_and_reuse_detection(client):
    await _register_and_login(client)
    old_refresh_cookie = client.cookies.get("refresh_token")
    assert old_refresh_cookie

    r1 = await client.post("/api/v1/auth/refresh")
    assert r1.status_code == 200, r1.text
    new_refresh_cookie = client.cookies.get("refresh_token")
    assert new_refresh_cookie != old_refresh_cookie

    # Replay the now-revoked OLD refresh token: must be rejected as reuse/theft,
    # not silently accepted.
    client.cookies.set("refresh_token", old_refresh_cookie)
    r2 = await client.post("/api/v1/auth/refresh")
    assert r2.status_code == 401
    assert "reuse" in r2.json()["error"]["message"].lower()

    # Reuse detection must revoke the WHOLE token family — the new token that was
    # just issued should be dead too, not just the replayed old one.
    client.cookies.set("refresh_token", new_refresh_cookie)
    r3 = await client.post("/api/v1/auth/refresh")
    assert r3.status_code == 401


async def test_non_admin_cannot_list_users(client):
    token = await _register_and_login(client)
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"
