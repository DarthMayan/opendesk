from app import create_app


def test_health_endpoint():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "opendesk"}


def test_index_page():
    app = create_app()
    app.config.update(TESTING=True)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"OpenDesk" in response.data
