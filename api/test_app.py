import fakeredis
import pytest

import app as shop


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(shop, "db", fakeredis.FakeRedis(decode_responses=True))
    return shop.app.test_client()


def test_health(client):
    assert client.get("/api/health").json["status"] == "ok"


def test_products(client):
    assert len(client.get("/api/products").json["products"]) == 3


def test_place_and_list_order(client):
    res = client.post("/api/orders", json={"product_id": 2})
    assert res.status_code == 201
    assert res.json["product"] == "Kubernetes Sticker Pack"
    assert client.get("/api/orders").json["orders"][0]["id"] == 1


def test_bad_order(client):
    assert client.post("/api/orders", json={"product_id": 99}).status_code == 400


def test_metrics(client):
    client.get("/api/products")
    assert b"shop_requests_total" in client.get("/metrics").data
