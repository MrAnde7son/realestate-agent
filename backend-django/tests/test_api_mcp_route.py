import json

import pytest


@pytest.mark.django_db
def test_mcp_route_initializes_session(client):
    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "0.0.0"},
            "protocolVersion": "2024-11-05",
        },
    }

    response = client.post(
        "/mcp",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_ACCEPT="application/json, text/event-stream",
    )

    assert response.status_code == 200
    assert response.has_header("mcp-session-id")
    body = b"".join(response.streaming_content)
    response.close()

    assert b"event: message" in body
    assert b"protocolVersion\":\"2024-11-05" in body


def test_mcp_route_requires_accept_header(client):
    response = client.get("/mcp")
    assert response.status_code == 406
