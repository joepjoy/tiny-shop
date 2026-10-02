"""Tiny Shop API: lists products and stores orders in Redis."""
import json
import os
import socket
import time

import redis
from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

PRODUCTS = [
    {"id": 1, "name": "Cloud Mug", "price": 9.99},
    {"id": 2, "name": "Kubernetes Sticker Pack", "price": 4.50},
    {"id": 3, "name": "DevOps Hoodie", "price": 29.00},
]

# Metrics that Prometheus scrapes from /metrics
REQUESTS = Counter("shop_requests_total", "HTTP requests", ["endpoint", "status"])
ORDERS = Counter("shop_orders_total", "Orders placed")
LATENCY = Histogram("shop_request_seconds", "Request latency", ["endpoint"])


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        LATENCY.labels(request.path).observe(time.time() - request.start_time)
        REQUESTS.labels(request.path, response.status_code).inc()
    return response


@app.get("/api/health")
def health():
    """Kubernetes calls this to check the app is alive."""
    try:
        db.ping()
        return jsonify(status="ok", pod=socket.gethostname())
    except redis.exceptions.ConnectionError:
        return jsonify(status="redis unavailable"), 503


@app.get("/api/products")
def products():
    return jsonify(products=PRODUCTS, served_by=socket.gethostname())


@app.post("/api/orders")
def create_order():
    body = request.get_json(silent=True) or {}
    product = next((p for p in PRODUCTS if p["id"] == body.get("product_id")), None)
    if product is None:
        return jsonify(error="unknown product_id"), 400
    order_id = db.incr("order_counter")
    order = {"id": order_id, "product": product["name"], "price": product["price"]}
    db.rpush("orders", json.dumps(order))
    ORDERS.inc()
    return jsonify(order), 201


@app.get("/api/orders")
def list_orders():
    orders = [json.loads(o) for o in db.lrange("orders", -20, -1)]
    return jsonify(orders=list(reversed(orders)))


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
