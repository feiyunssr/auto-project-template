import time

HEADERS = {
    "X-Hub-User-Id": "user-1",
    "X-Hub-User-Name": "Zero",
    "X-Hub-Role": "operator",
}
SERVICE_API_HEADERS = {"Authorization": "Bearer test-service-token"}


def wait_for_status(client, job_id: str, expected: set[str], timeout_sec: float = 5.0):
    started = time.time()
    while time.time() - started < timeout_sec:
        response = client.get(f"/api/v1/tasks/{job_id}", headers=HEADERS)
        assert response.status_code == 200, response.text
        payload = response.json()
        if payload["status"] in expected:
            return payload
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} did not reach {expected} within {timeout_sec}s")


def wait_for_service_api_status(client, job_id: str, expected: set[str], timeout_sec: float = 5.0):
    started = time.time()
    while time.time() - started < timeout_sec:
        response = client.get(f"/api/v1/service-api/tasks/{job_id}", headers=SERVICE_API_HEADERS)
        assert response.status_code == 200, response.text
        payload = response.json()
        if payload["status"] in expected:
            return payload
        time.sleep(0.1)
    raise AssertionError(f"service-api job {job_id} did not reach {expected} within {timeout_sec}s")


def test_create_task_runs_to_success_and_is_idempotent(client):
    payload = {
        "scenario_key": "general",
        "title": "Generate preview",
        "input_payload": {"content": "hello world"},
    }
    first = client.post("/api/v1/tasks", json=payload, headers=HEADERS)
    assert first.status_code == 200, first.text
    second = client.post("/api/v1/tasks", json=payload, headers=HEADERS)
    assert second.status_code == 200, second.text
    assert first.json()["id"] == second.json()["id"]

    detail = wait_for_status(client, first.json()["id"], {"succeeded"})
    assert detail["result_summary"]["result_type"] == "mock_result"
    assert detail["attempts"][0]["status"] == "succeeded"
    assert detail["results"][0]["quality_status"] == "approved"


def test_timeout_task_reaches_final_failure(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "scenario_key": "general",
            "title": "Generate with timeout",
            "input_payload": {"content": "slow", "simulate": "timeout_always"},
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text

    detail = wait_for_status(client, response.json()["id"], {"failed"}, timeout_sec=8.0)
    assert detail["error_code"] == "PROVIDER_TIMEOUT_FINAL"
    assert detail["retryable"] is True
    assert len(detail["attempts"]) == 3


def test_timeout_once_task_recovers_without_stale_retrying_error(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "scenario_key": "general",
            "title": "Generate after timeout retry",
            "input_payload": {"content": "slow once", "simulate": "timeout_once"},
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text

    detail = wait_for_status(client, response.json()["id"], {"succeeded"})
    assert detail["error_code"] is None
    assert detail["error_message"] is None
    assert [attempt["status"] for attempt in detail["attempts"]] == ["timeout", "succeeded"]


def test_profile_timeout_ms_enforces_provider_call_deadline(client):
    profile = client.post(
        "/api/v1/settings/ai-profiles",
        json={
            "profile_key": "timeout-tight",
            "profile_name": "Timeout Tight",
            "scenario_key": "general",
            "is_default": False,
            "is_active": True,
            "provider_name": "mock",
            "model_name": "mock-001",
            "system_prompt": "test",
            "prompt_template": "{{ input_payload }}",
            "temperature": 0.2,
            "max_tokens": 512,
            "timeout_ms": 100,
            "max_retries": 0,
            "concurrency_limit": 1,
        },
        headers=HEADERS,
    )
    assert profile.status_code == 200, profile.text

    response = client.post(
        "/api/v1/tasks",
        json={
            "scenario_key": "general",
            "title": "Timeout by profile",
            "ai_profile_id": profile.json()["id"],
            "input_payload": {"content": "slow by sleep", "delay_ms": 250},
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text

    detail = wait_for_status(client, response.json()["id"], {"failed"}, timeout_sec=5.0)
    assert detail["error_code"] == "PROVIDER_TIMEOUT_FINAL"
    assert detail["error_message"] == "Provider timed out after 100 ms."
    assert detail["attempts"][0]["status"] == "timeout"


def test_frontend_shaped_payload_uses_brief_as_result_source(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "scenario_key": "general",
            "title": "Frontend payload",
            "input_payload": {
                "brief": "spring sale ad copy",
                "asset_urls": ["https://example.com/a.png"],
            },
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text

    detail = wait_for_status(client, response.json()["id"], {"succeeded"})
    assert detail["results"][0]["preview_text"].startswith("spring sale ad copy ::")


def test_task_endpoints_allow_local_access_when_hub_auth_disabled(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["items"] == []


def test_task_endpoints_require_hub_session_when_hub_auth_enabled(auth_required_client):
    response = auth_required_client.get("/api/v1/tasks")
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["code"] == "AUTH_REQUIRED"


def test_ai_profile_endpoints_allow_local_access_when_hub_auth_disabled(client):
    response = client.get("/api/v1/settings/ai-profiles")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload["items"], list)


def test_ai_profile_endpoints_require_hub_session_when_hub_auth_enabled(auth_required_client):
    response = auth_required_client.get("/api/v1/settings/ai-profiles")
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["code"] == "AUTH_REQUIRED"


def test_cors_preflight_allows_local_frontend_origin(client):
    response = client.options(
        "/api/v1/tasks",
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-hub-user-id,x-hub-user-name,x-hub-role",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4173"
    assert "x-hub-user-id" in response.headers["access-control-allow-headers"]


def test_cors_preflight_allows_ip_frontend_origin(client):
    response = client.options(
        "/api/v1/tasks",
        headers={
            "Origin": "http://192.168.1.242:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-hub-user-id,x-hub-user-name,x-hub-role",
        },
    )
    assert response.status_code == 200, response.text
    assert response.headers["access-control-allow-origin"] == "http://192.168.1.242:5173"
    assert "x-hub-user-id" in response.headers["access-control-allow-headers"]


def test_healthz_reports_degraded_when_hub_registration_missing(client):
    response = client.get("/healthz")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] in {"healthy", "degraded"}
    assert payload["checks"]["database"]["status"] == "healthy"
    assert payload["checks"]["hub_registration"]["status"] == "degraded"


def test_service_api_requires_bearer_token(client):
    response = client.post(
        "/api/v1/service-api/tasks",
        json={
            "scenario_key": "general",
            "title": "Missing token",
            "input_payload": {"content": "hello"},
        },
    )
    assert response.status_code == 401, response.text
    payload = response.json()
    assert payload["code"] == "SERVICE_API_AUTH_REQUIRED"


def test_service_api_create_task_runs_to_success_and_returns_result(client):
    response = client.post(
        "/api/v1/service-api/tasks",
        json={
            "scenario_key": "general",
            "title": "Service API task",
            "input_payload": {"content": "service api hello"},
        },
        headers=SERVICE_API_HEADERS,
    )
    assert response.status_code == 202, response.text
    payload = response.json()
    assert payload["status"] == "queued"

    detail = wait_for_service_api_status(client, payload["id"], {"succeeded"})
    assert detail["last_success_result"]["preview_text"].startswith("service api hello ::")

    result = client.get(f"/api/v1/service-api/tasks/{payload['id']}/result", headers=SERVICE_API_HEADERS)
    assert result.status_code == 200, result.text
    result_payload = result.json()
    assert result_payload["status"] == "succeeded"
    assert result_payload["result"]["preview_text"].startswith("service api hello ::")


def test_service_api_result_endpoint_returns_failure_state_without_fake_result(client):
    response = client.post(
        "/api/v1/service-api/tasks",
        json={
            "scenario_key": "general",
            "title": "Service API timeout",
            "input_payload": {"content": "slow", "simulate": "timeout_always"},
        },
        headers=SERVICE_API_HEADERS,
    )
    assert response.status_code == 202, response.text

    wait_for_service_api_status(client, response.json()["id"], {"failed"}, timeout_sec=8.0)
    result = client.get(f"/api/v1/service-api/tasks/{response.json()['id']}/result", headers=SERVICE_API_HEADERS)
    assert result.status_code == 200, result.text
    payload = result.json()
    assert payload["status"] == "failed"
    assert payload["error_code"] == "PROVIDER_TIMEOUT_FINAL"
    assert payload["result"] is None


def test_service_api_cannot_read_frontend_created_task(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "scenario_key": "general",
            "title": "Frontend owned task",
            "input_payload": {"content": "human task"},
        },
        headers=HEADERS,
    )
    assert response.status_code == 200, response.text

    forbidden = client.get(
        f"/api/v1/service-api/tasks/{response.json()['id']}",
        headers=SERVICE_API_HEADERS,
    )
    assert forbidden.status_code == 404, forbidden.text
