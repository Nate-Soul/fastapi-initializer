from tests.integration.test_auth import _register_and_login


async def test_user_can_view_and_edit_own_profile(client):
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    me = (await client.get("/api/v1/users/me", headers=headers)).json()
    user_id = me["id"]

    r = await client.patch(f"/api/v1/users/{user_id}", json={"first_name": "Updated"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["first_name"] == "Updated"


async def test_user_cannot_view_others_profile(client):
    token_a = await _register_and_login(client, email="a@example.com")
    token_b = await _register_and_login(client, email="b@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    me_a = (
        await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token_a}"})
    ).json()

    r = await client.get(f"/api/v1/users/{me_a['id']}", headers=headers_b)
    assert r.status_code == 403


async def test_soft_delete_then_404_on_subsequent_lookup(client):
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    me = (await client.get("/api/v1/users/me", headers=headers)).json()

    r = await client.delete(f"/api/v1/users/{me['id']}", headers=headers)
    assert r.status_code == 204

    # deleted user's own token is now invalid (is_active check via deleted_at)
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 401


async def test_get_nonexistent_user_as_admin_is_404_not_500(client, db_session):
    import uuid as uuid_mod

    from app.modules.users.models import Role, User

    token = await _register_and_login(client)
    async with db_session() as session:
        from sqlalchemy import select

        me = (await session.execute(select(User))).scalar_one()
        me.role = Role.ADMIN
        await session.commit()

    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get(f"/api/v1/users/{uuid_mod.uuid4()}", headers=headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
