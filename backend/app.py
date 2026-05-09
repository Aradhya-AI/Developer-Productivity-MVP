import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from metrics_service import MetricsService


app = Flask(__name__)
CORS(app)

metrics_service = MetricsService()


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/metrics")
def metrics():
    developer_id = request.args.get("developer_id")
    month = request.args.get("month")
    payload = metrics_service.get_dashboard(developer_id=developer_id, month=month)
    return jsonify(payload)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
