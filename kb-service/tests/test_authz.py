from tests.conftest import AUTH


async def test_readonly_token_cannot_write(client):
    # admin creates a read-only token
    created = await client.post(
        "/api/tokens", headers=AUTH, json={"name": "connector", "is_admin": False}
    )
    assert created.status_code == 201
    t = created.json()
    ro = {"Authorization": f"Token {t['token_id']}:{t['secret']}"}

    # read-only token CAN read
    assert (await client.get("/api/pages", headers=ro)).status_code == 200
    assert (await client.get("/api/books", headers=ro)).status_code == 200

    # ...but CANNOT write
    assert (await client.post("/api/books", headers=ro, json={"name": "X"})).status_code == 403
    up = await client.post(
        "/api/documents/upload", headers=ro,
        data={"book_id": 1}, files={"file": ("x.md", b"# x", "text/markdown")},
    )
    assert up.status_code == 403
    # ...and cannot mint tokens
    assert (await client.post("/api/tokens", headers=ro, json={"name": "y"})).status_code == 403
