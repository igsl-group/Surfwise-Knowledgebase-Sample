from tests.conftest import AUTH, UI_AUTH


async def _first_book_id(client):
    r = await client.get("/api/books", headers=AUTH)
    return r.json()["data"][0]["id"]


async def test_upload_list_download_delete(client):
    book_id = await _first_book_id(client)

    # upload a markdown document
    files = {"file": ("notes.md", b"# Notes\n\nHello **doc**", "text/markdown")}
    up = await client.post(
        "/api/documents/upload", headers=AUTH, data={"book_id": book_id}, files=files
    )
    assert up.status_code == 201
    doc = up.json()
    assert doc["filename"] == "notes.md" and doc["is_file"] is True
    doc_id = doc["id"]

    # it appears in the document list
    listing = (await client.get("/api/documents", headers=AUTH)).json()
    assert any(d["id"] == doc_id for d in listing["data"])

    # text content is indexable via the BookStack markdown export
    md = await client.get(f"/api/pages/{doc_id}/export/markdown", headers=AUTH)
    assert "# Notes" in md.text

    # download returns the original bytes + filename
    dl = await client.get(f"/api/documents/{doc_id}/download", headers=AUTH)
    assert dl.status_code == 200
    assert dl.content == b"# Notes\n\nHello **doc**"
    assert "notes.md" in dl.headers.get("content-disposition", "")

    # delete
    d = await client.delete(f"/api/documents/{doc_id}", headers=AUTH)
    assert d.status_code == 204
    gone = await client.get(f"/api/documents/{doc_id}/download", headers=AUTH)
    assert gone.status_code == 404


async def test_ui_served(client):
    assert (await client.get("/ui")).status_code == 401  # requires Basic auth
    r = await client.get("/ui", headers=UI_AUTH)
    assert r.status_code == 200
    assert "Document Management" in r.text
