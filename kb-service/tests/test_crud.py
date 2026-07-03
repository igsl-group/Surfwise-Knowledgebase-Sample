from tests.conftest import AUTH


async def test_full_crud_flow(client):
    # create a book
    b = await client.post("/api/books", headers=AUTH, json={"name": "Docs", "description": "x"})
    assert b.status_code == 201
    book_id = b.json()["id"]

    # create a page
    p = await client.post(
        "/api/pages",
        headers=AUTH,
        json={"book_id": book_id, "name": "Intro", "markdown": "# Intro\n\nbody"},
    )
    assert p.status_code == 201
    page_id = p.json()["id"]
    assert p.json()["slug"] == "intro"

    # it shows up in the connector listing
    listing = (await client.get("/api/pages", headers=AUTH)).json()
    assert any(pg["id"] == page_id for pg in listing["data"])

    # update
    u = await client.put(
        f"/api/pages/{page_id}", headers=AUTH, json={"markdown": "# Intro\n\nupdated"}
    )
    assert u.status_code == 200
    md = await client.get(f"/api/pages/{page_id}/export/markdown", headers=AUTH)
    assert "updated" in md.text

    # delete
    d = await client.delete(f"/api/pages/{page_id}", headers=AUTH)
    assert d.status_code == 204
    gone = await client.get(f"/api/pages/{page_id}", headers=AUTH)
    assert gone.status_code == 404
