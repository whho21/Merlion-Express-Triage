"""Model client + cache tests. A fake transport stands in for the endpoint: no network, no spend."""
import json
import tempfile
import unittest
from pathlib import Path

from backend.unstructured import llm
from backend.unstructured.cache import ExtractionCache, cache_key


def ok_response(answer, prompt_tokens=100, completion_tokens=20):
    return 200, json.dumps({"choices": [{"message": {"content": json.dumps(answer)}}],
                            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}}).encode()


class FakeTransport:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []

    def __call__(self, url, headers, body, timeout):
        self.calls.append(json.loads(body))
        return self.responses.pop(0)


def call(transport, telemetry=None, **kw):
    return llm.vision_json(b"\xff\xd8fake", "image/jpeg", "read it", api_key="test-key", model="m", tool="t",
                           source_id="pod:v1:1", prompt_version="p1", telemetry_path=telemetry, transport=transport,
                           sleep=lambda s: None, **kw)


class VisionJsonTests(unittest.TestCase):
    def test_success_returns_answer_and_usage_and_logs_no_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            tel = Path(tmp) / "telemetry.jsonl"
            answer, usage = call(FakeTransport(ok_response({"order_ref": "V1-20001"})), tel)
            line = json.loads(tel.read_text(encoding="utf-8"))
        self.assertEqual(answer, {"order_ref": "V1-20001"})
        self.assertEqual(usage, {"prompt_tokens": 100, "completion_tokens": 20})
        self.assertEqual((line["status"], line["prompt_tokens"], line["cache"]), ("ok", 100, "miss"))
        self.assertNotIn("V1-20001", json.dumps(line))

    def test_request_shape(self):
        fake = FakeTransport(ok_response({}))
        call(fake)
        body = fake.calls[0]
        self.assertEqual((body["temperature"], body["response_format"]), (0, {"type": "json_object"}))
        self.assertTrue(body["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))

    def test_retries_on_429_then_succeeds(self):
        fake = FakeTransport((429, b"{}"), ok_response({"a": 1}))
        answer, _ = call(fake)
        self.assertEqual((answer, len(fake.calls)), ({"a": 1}, 2))

    def test_gives_up_after_three_attempts(self):
        fake = FakeTransport((503, b""), (503, b""), (503, b""))
        with self.assertRaises(llm.LLMError) as ctx:
            call(fake)
        self.assertEqual((ctx.exception.code, ctx.exception.retryable, len(fake.calls)), ("HTTP_503", True, 3))

    def test_does_not_retry_401(self):
        fake = FakeTransport((401, b""))
        with self.assertRaises(llm.LLMError) as ctx:
            call(fake)
        self.assertEqual((ctx.exception.code, len(fake.calls)), ("HTTP_401", 1))

    def test_bad_json_answer_is_an_error(self):
        bad = (200, json.dumps({"choices": [{"message": {"content": "not json"}}]}).encode())
        with self.assertRaises(llm.LLMError) as ctx:
            call(FakeTransport(bad))
        self.assertEqual(ctx.exception.code, "BAD_RESPONSE")

    def test_no_key_never_calls(self):
        fake = FakeTransport()
        with self.assertRaises(llm.LLMError) as ctx:
            llm.vision_json(b"x", "image/jpeg", "p", api_key=None, model="m", tool="t", source_id="s",
                            prompt_version="p", transport=fake)
        self.assertEqual((ctx.exception.code, fake.calls), ("NO_API_KEY", []))


class CostTests(unittest.TestCase):
    def test_estimate_cost(self):
        self.assertEqual(llm.estimate_cost("gpt-4o-mini", 1_000_000, 1_000_000), 0.75)
        self.assertIsNone(llm.estimate_cost("unknown-model", 10, 10))


class SettingsTests(unittest.TestCase):
    def test_reads_only_the_repo_root_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            (parent / ".env").write_text("OPENAI_API_KEY=class-key\n", encoding="utf-8")
            repo = parent / "repo"
            repo.mkdir()
            (repo / ".env").write_text("# comment\nOPENAI_API_KEY=\nA_VISION_MODEL=gpt-test\n", encoding="utf-8")
            import os
            saved = {k: os.environ.pop(k, None) for k in ("OPENAI_API_KEY", "A_VISION_MODEL", "OPENAI_BASE_URL")}
            try:
                cfg = llm.settings(repo)
            finally:
                for k, v in saved.items():
                    if v is not None:
                        os.environ[k] = v
        self.assertIsNone(cfg["api_key"])  # the parent folder's class key is never picked up
        self.assertEqual(cfg["model"], "gpt-test")


class CacheTests(unittest.TestCase):
    def test_key_changes_with_prompt_or_model(self):
        self.assertNotEqual(cache_key("abc", "p1", "m"), cache_key("abc", "p2", "m"))
        self.assertNotEqual(cache_key("abc", "p1", "m"), cache_key("abc", "p1", "m2"))
        self.assertEqual(cache_key("abc", "p1", "m"), cache_key("abc", "p1", "m"))

    def test_roundtrip_and_damaged_file_is_a_miss(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = ExtractionCache(Path(tmp))
            self.assertIsNone(cache.get("k"))
            cache.put("k", {"answer": {"x": 1}})
            self.assertEqual(cache.get("k"), {"answer": {"x": 1}})
            (Path(tmp) / "k.json").write_text("{broken", encoding="utf-8")
            self.assertIsNone(cache.get("k"))


if __name__ == "__main__":
    unittest.main()
