from tests.mavat.test_integration_runner import playwright_tests_enabled


def test_playwright_tests_disabled_by_default(monkeypatch):
    monkeypatch.delenv("RUN_PLAYWRIGHT_TESTS", raising=False)

    assert not playwright_tests_enabled()


def test_playwright_tests_enabled_for_truthy_values(monkeypatch):
    for value in ("1", "true", "yes", "TRUE", "YeS"):
        monkeypatch.setenv("RUN_PLAYWRIGHT_TESTS", value)
        assert playwright_tests_enabled()


def test_playwright_tests_disabled_for_falsy_values(monkeypatch):
    for value in ("0", "false", "no", "", "off"):
        monkeypatch.setenv("RUN_PLAYWRIGHT_TESTS", value)
        assert not playwright_tests_enabled()


def test_custom_environment_mapping(monkeypatch):
    custom_env = {"RUN_PLAYWRIGHT_TESTS": "1"}

    monkeypatch.setenv("RUN_PLAYWRIGHT_TESTS", "0")

    assert playwright_tests_enabled(custom_env)
