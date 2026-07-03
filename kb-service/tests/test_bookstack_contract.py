from tests.conftest import AUTH


async def test_requires_token(client):
    r = await client.get("/api/pages")
    assert r.status_code == 401


async def test_list_pages_shape(client):
    r = await client.get("/api/pages", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert "data" in body and "total" in body
    assert body["total"] >= 1
    page = body["data"][0]
    for field in ("id", "name", "slug", "book_id", "book_slug", "created_at", "updated_at"):
        assert field in page


async def test_page_detail_and_markdown_export(client):
    listing = (await client.get("/api/pages", headers=AUTH)).json()
    pid = listing["data"][0]["id"]

    detail = await client.get(f"/api/pages/{pid}", headers=AUTH)
    assert detail.status_code == 200
    assert "markdown" in detail.json()

    md = await client.get(f"/api/pages/{pid}/export/markdown", headers=AUTH)
    assert md.status_code == 200
    assert "# Onboarding" in md.text


async def test_updated_at_filter(client):
    future = "2999-01-01"
    r = await client.get(
        "/api/pages",
        headers=AUTH,
        params={"filter[updated_at:gt]": future, "sort": "-updated_at"},
    )
    assert r.json()["total"] == 0

    past = "2000-01-01"
    r = await client.get(
        "/api/pages", headers=AUTH, params={"filter[updated_at:gt]": past}
    )
    assert r.json()["total"] >= 1


async def test_book_detail_contents(client):
    books = (await client.get("/api/books", headers=AUTH)).json()
    bid = books["data"][0]["id"]
    detail = await client.get(f"/api/books/{bid}", headers=AUTH)
    assert detail.status_code == 200
    assert "contents" in detail.json()
    assert len(detail.json()["contents"]) >= 1
