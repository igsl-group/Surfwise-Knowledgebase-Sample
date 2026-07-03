from tests.conftest import AUTH


async def test_token_crud_and_auth(client):
    base = len((await client.get("/api/tokens", headers=AUTH)).json())
    assert base >= 1

    created = await client.post("/api/tokens", headers=AUTH, json={"name": "ci"})
    assert created.status_code == 201
    body = created.json()
    assert body["token_id"] and body["secret"]
    tid = body["id"]

    # the new token authenticates
    newauth = {"Authorization": f"Token {body['token_id']}:{body['secret']}"}
    assert (await client.get("/api/pages", headers=newauth)).status_code == 200

    # list grew by one
    assert len((await client.get("/api/tokens", headers=AUTH)).json()) == base + 1

    # rotate invalidates the old secret
    rot = await client.post(f"/api/tokens/{tid}/rotate", headers=AUTH)
    assert rot.status_code == 200 and rot.json()["secret"] != body["secret"]
    assert (await client.get("/api/pages", headers=newauth)).status_code == 401

    # delete
    assert (await client.delete(f"/api/tokens/{tid}", headers=AUTH)).status_code == 204


async def test_cannot_delete_last_token(client):
    toks = (await client.get("/api/tokens", headers=AUTH)).json()
    for t in toks[1:]:
        await client.delete(f"/api/tokens/{t['id']}", headers=AUTH)
    remaining = (await client.get("/api/tokens", headers=AUTH)).json()
    assert len(remaining) == 1
    d = await client.delete(f"/api/tokens/{remaining[0]['id']}", headers=AUTH)
    assert d.status_code == 400
