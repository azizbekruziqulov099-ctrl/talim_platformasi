"""Offline AI boundary tests: no provider credentials or live requests needed."""
from copy import deepcopy
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib import error

from modules import presentation_ai as ai


def document(count=2, layout="text"):
    design = {"template": "glass", "background": "paper", "color": "#ffffff", "image": None,
              "overlay": 0, "panel": "solid", "accent": "blue", "text": "dark",
              "font": "sans", "size": "normal", "radius": "round", "transition": "fade"}
    slides = []
    for index in range(count):
        slide = {field: "" for field in ai.TEXT_LIMITS}
        slide.update(id=f"s{index + 1}", title=f"Mavzu {index + 1}", section="Tushuncha",
                     body="Oldingi tushuntirish", image=None, image2=None, layout=layout,
                     design=None, placements={}, elements=[])
        slides.append(slide)
    return {"schema": 2, "title": "Kasrlar", "subject": "Matematika", "audience": "8-sinf",
            "lesson_type": "lecture", "design": design, "slides": slides}


def envelope(slides, finish_reason="stop"):
    return {"choices": [{"finish_reason": finish_reason, "message": {"content": json.dumps({"slides": slides})}}]}


class Stub:
    def __init__(self, change=None):
        self.calls = []
        self.change = change

    def __call__(self, payload, *, api_key, timeout):
        self.calls.append((deepcopy(payload), api_key, timeout))
        plans = json.loads(payload["messages"][1]["content"])["slides"]
        slides = []
        for plan in plans:
            values = {field: r"\frac{1}{2}" if field == "formula" else "Kasr butunning bir qismini bildiradi."
                      for field in plan["limits"]}
            for field in values:
                if field == "section":
                    values[field] = "Tushuncha"
            slides.append({"id": plan["id"], **values})
        result = envelope(slides)
        return self.change(result, len(self.calls)) if self.change else result


class PresentationAITests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"PRESENTATION_AI_ENABLED": "true", "GROQ_API_KEY": "test-key",
                                         "PRESENTATION_AI_MODEL": ai.DEFAULT_MODEL}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)

    def generate(self, doc=None, stub=None, **kwargs):
        return ai.generate_content(doc or document(), {"audience": "8-sinf", "instructions": "Sodda misol keltiring."},
                                   transport=stub or Stub(), **kwargs)

    def assert_invalid(self, transform, code="invalid_response"):
        source = document()
        before = deepcopy(source)
        def change(result, _count):
            data = json.loads(result["choices"][0]["message"]["content"])
            transform(data)
            result["choices"][0]["message"]["content"] = json.dumps(data)
            return result
        with self.assertRaises(ai.PresentationAIError) as caught:
            self.generate(source, Stub(change))
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(source, before)

    def test_configuration_disabled_missing_key_and_unsupported_model(self):
        for overrides in ({"PRESENTATION_AI_ENABLED": "false"}, {"GROQ_API_KEY": ""},
                          {"PRESENTATION_AI_MODEL": "untrusted-secret-model"}, {"GROQ_API_KEY": "bad\nheader"}):
            with self.subTest(overrides=overrides), patch.dict(os.environ, overrides):
                stub = Stub()
                self.assertFalse(ai.get_ai_capabilities()["available"])
                with self.assertRaises(ai.PresentationAIError) as caught:
                    self.generate(stub=stub)
                self.assertEqual(caught.exception.status_code, 503)
                self.assertEqual(stub.calls, [])
                self.assertNotIn("test-key", json.dumps(ai.get_ai_capabilities()))
                self.assertNotIn("untrusted-secret-model", json.dumps(ai.get_ai_capabilities()))

    def test_validation_happens_without_provider_or_configuration(self):
        with patch.dict(os.environ, {"PRESENTATION_AI_ENABLED": "false"}):
            result = ai.validate_generation_request(document(), {"instructions": "Maqsad"}, ["s2", "s1"])
        self.assertEqual(result, {"brief": {"audience": "8-sinf", "instructions": "Maqsad"}, "slide_ids": ["s1", "s2"]})

    def test_invalid_selection_and_brief_are_rejected_before_transport(self):
        for selection in ([], ["missing"], ["s1", "s1"], "s1", [True], [{}]):
            with self.subTest(selection=selection), self.assertRaises(ai.PresentationAIError):
                self.generate(slide_ids=selection)
        for brief in ({"instructions": "x" * 2001}, {"audience": "x" * 121}, {"api_key": "secret"}, [], None):
            with self.subTest(brief=brief), self.assertRaises(ai.PresentationAIError):
                ai.validate_generation_request(document(), brief)

    def test_one_selected_slide_changes_only_native_active_fields(self):
        source = document(3)
        source["slides"][1].update(body2="Yashirin uzun matn", image="data:image/png;base64,private-pixels",
                                    elements=[{"id": "x", "kind": "text", "text": "Private student details"}],
                                    placements={"body": {"x": 80, "y": 240, "w": 1000, "h": 300}})
        before = deepcopy(source)
        result = self.generate(source, slide_ids=["s2"])
        self.assertEqual(source, before)
        self.assertEqual(result["generated_count"], 1)
        self.assertEqual(result["document"]["slides"][0], before["slides"][0])
        self.assertEqual(result["document"]["slides"][2], before["slides"][2])
        self.assertEqual(result["document"]["design"], before["design"])
        for field in set(source["slides"][1]) - {"title", "body"}:
            self.assertEqual(result["document"]["slides"][1][field], before["slides"][1][field])

    def test_response_order_cannot_reorder_document(self):
        def reorder(result, _count):
            data = json.loads(result["choices"][0]["message"]["content"])
            data["slides"][0]["body"] = "Birinchi mavzu."
            data["slides"][1]["body"] = "Ikkinchi mavzu."
            data["slides"].reverse()
            result["choices"][0]["message"]["content"] = json.dumps(data)
            return result
        result = self.generate(stub=Stub(reorder))["document"]
        self.assertEqual([slide["id"] for slide in result["slides"]], ["s1", "s2"])
        self.assertEqual(result["slides"][0]["body"], "Birinchi mavzu.")
        self.assertEqual(result["slides"][1]["body"], "Ikkinchi mavzu.")

    def test_unknown_duplicate_and_missing_ids_fail_atomically(self):
        self.assert_invalid(lambda data: data["slides"][0].update(id="outside"))
        self.assert_invalid(lambda data: data["slides"][1].update(id="s1"))
        self.assert_invalid(lambda data: data["slides"].pop())
        self.assert_invalid(lambda data: data["slides"].append(deepcopy(data["slides"][0])))

    def test_unexpected_fields_and_hidden_text_cannot_be_overwritten(self):
        self.assert_invalid(lambda data: data["slides"][0].update(image="https://example.invalid/a.png"))
        self.assert_invalid(lambda data: data["slides"][0].update(body2="Hidden replacement"))
        self.assert_invalid(lambda data: data["slides"][0].update(design={"color": "#ff0000"}))
        self.assert_invalid(lambda data: data.update(warnings=["provider secret"]))

    def test_overlong_empty_html_controls_and_excess_lines_are_not_clipped(self):
        for value in ("a" * 601, " ", "<script>alert(1)</script>", "bad\x00text", "line\n" * 30,
                      "https://example.invalid/private", "```code```", None, 42):
            with self.subTest(value=str(value)[:30]):
                self.assert_invalid(lambda data, v=value: data["slides"][0].update(body=v))

    def test_malformed_duplicate_json_and_truncated_provider_results(self):
        for raw in ("not JSON", '{"slides":[],"slides":[]}', '{"slides":NaN}'):
            def broken(result, _count):
                result["choices"][0]["message"]["content"] = raw
                return result
            with self.subTest(raw=raw), self.assertRaises(ai.PresentationAIError):
                self.generate(stub=Stub(broken))
        for reason in ("length", "tool_calls", None):
            def incomplete(result, _count):
                result["choices"][0]["finish_reason"] = reason
                return result
            with self.subTest(reason=reason), self.assertRaises(ai.PresentationAIError) as caught:
                self.generate(stub=Stub(incomplete))
            self.assertEqual(caught.exception.code, "incomplete_response")

    def test_refusal_is_readable_without_raw_provider_message(self):
        def refusal(result, _count):
            result["choices"][0]["message"]["refusal"] = "secret internal reason"
            return result
        with self.assertRaises(ai.PresentationAIError) as caught:
            self.generate(stub=Stub(refusal))
        self.assertEqual(caught.exception.code, "refused")
        self.assertNotIn("secret", str(caught.exception))

    def test_failed_later_batch_cannot_mutate_any_original_slide(self):
        source = document(8)
        before = deepcopy(source)
        def break_second(result, count):
            if count == 2:
                return {"choices": []}
            return result
        stub = Stub(break_second)
        with self.assertRaises(ai.PresentationAIError):
            self.generate(source, stub)
        self.assertEqual(len(stub.calls), 2)
        self.assertEqual(source, before)

    def test_40_slides_use_10_bounded_sequential_requests(self):
        stub = Stub()
        result = self.generate(document(40), stub)
        self.assertEqual(result["generated_count"], 40)
        self.assertEqual(len(stub.calls), 10)
        for payload, _key, timeout in stub.calls:
            self.assertEqual(len(json.loads(payload["messages"][1]["content"])["slides"]), 4)
            self.assertLessEqual(timeout, 25)
            self.assertLessEqual(payload["max_completion_tokens"], 3500)
            self.assertTrue(payload["response_format"]["json_schema"]["strict"])
            self.assertFalse(payload["stream"])
            self.assertNotIn("tools", payload)
        with self.assertRaises(ai.PresentationAIError):
            self.generate(document(41), Stub())

    def test_provider_receives_only_selected_lesson_content(self):
        source = document(3)
        source["owner"] = {"email": "private@example.invalid", "user_id": 919191919}
        source["design"]["image"] = "data:image/png;base64,PRIVATE_BACKGROUND"
        source["slides"][0]["body"] = "NEVER_SEND_UNSELECTED"
        source["slides"][1]["body"] = "Savol: student@example.com yoki +998 90 123 45 67"
        source["slides"][1]["body2"] = "NEVER_SEND_HIDDEN"
        source["slides"][1]["elements"] = [{"text": "NEVER_SEND_ELEMENTS"}]
        stub = Stub()
        self.generate(source, stub, slide_ids=["s2"])
        payload = json.dumps(stub.calls[0][0], ensure_ascii=False)
        for value in ("PRIVATE_BACKGROUND", "NEVER_SEND", "student@example.com", "+998 90 123 45 67", "private@example.invalid", "user_id", "test-key"):
            self.assertNotIn(value, payload)

    def test_layout_specific_fields_and_native_formulas(self):
        for layout, fields in (("two_columns", {"body", "body2"}), ("three_cards", {"body", "body2", "body3"}),
                               ("steps", {"body", "body2", "body3"}), ("formula", {"body", "formula", "example"}),
                               ("two_images", {"body", "body2", "image_prompt", "image2_prompt", "image_caption", "image2_caption"})):
            stub = Stub()
            with self.subTest(layout=layout):
                result = self.generate(document(1, layout), stub)
                plan = json.loads(stub.calls[0][0]["messages"][1]["content"])["slides"][0]
                self.assertEqual(set(plan["limits"]), fields | {"title"})
                self.assertIsNone(result["document"]["slides"][0]["image"])
                if layout == "formula":
                    self.assertEqual(result["document"]["slides"][0]["formula"], r"\frac{1}{2}")

    def test_scientific_numbers_survive_contact_redaction(self):
        text = r"N = 1000000000; c = 299792458 m/s; t = 1000000000-2000000000; 1.25e12; x_123456789"
        self.assertEqual(ai._sanitize_text(text), text)
        self.assertNotIn("+998 90 123 45 67", ai._sanitize_text("Aloqa: +998 90 123 45 67"))
        self.assertNotIn("+14155552671", ai._sanitize_text("Aloqa: +14155552671"))

    def test_every_batch_has_the_shared_title_section_outline(self):
        source = document(9)
        source["slides"][8]["section"] = "Xulosa"
        stub = Stub()
        self.generate(source, stub)
        expected = [[slide["title"], slide["section"]] for slide in source["slides"]]
        for payload, _key, _timeout in stub.calls:
            user = json.loads(payload["messages"][1]["content"])
            self.assertEqual(user["outline"], expected)
            self.assertLessEqual(len(user["slides"]), 4)

    def test_formula_must_fit_its_preserved_placement(self):
        source = document(1, "formula")
        source["slides"][0]["placements"] = {"formula": {"x": 100, "y": 350, "w": 20, "h": 20}}
        with self.assertRaises(ai.PresentationAIError) as caught:
            self.generate(source)
        self.assertEqual(caught.exception.code, "content_does_not_fit")

    def test_existing_images_and_captions_are_not_invented_or_replaced(self):
        source = document(1, "image")
        source["slides"][0].update(image="data:image/png;base64,PRIVATE_PIXELS", image_caption="Asl tavsif")
        stub = Stub()
        result = self.generate(source, stub)
        slide = result["document"]["slides"][0]
        self.assertEqual(slide["image"], source["slides"][0]["image"])
        self.assertEqual(slide["image_caption"], "Asl tavsif")
        self.assertNotIn("PRIVATE_PIXELS", json.dumps(stub.calls[0][0]))

    def test_unsupported_tex_is_rejected_before_applying_content(self):
        def bad_formula(result, _count):
            data = json.loads(result["choices"][0]["message"]["content"])
            data["slides"][0]["formula"] = r"\input{secret}"
            result["choices"][0]["message"]["content"] = json.dumps(data)
            return result
        source = document(1, "formula")
        before = deepcopy(source)
        with self.assertRaises(ai.PresentationAIError) as caught:
            self.generate(source, Stub(bad_formula))
        self.assertEqual(caught.exception.code, "content_does_not_fit")
        self.assertEqual(source, before)

    def test_tiny_custom_placement_fails_before_provider_call(self):
        source = document(1)
        source["slides"][0]["placements"] = {"body": {"x": 100, "y": 300, "w": 10, "h": 10}}
        stub = Stub()
        with self.assertRaises(ai.PresentationAIError) as caught:
            self.generate(source, stub)
        self.assertEqual(caught.exception.code, "slot_too_small")
        self.assertFalse(stub.calls)

    def test_final_pixel_fit_check_rejects_wide_text_without_clipping(self):
        source = document(1)
        source["slides"][0]["placements"] = {"body": {"x": 100, "y": 300, "w": 240, "h": 65}}
        def wide_text(result, _count):
            data = json.loads(result["choices"][0]["message"]["content"])
            data["slides"][0]["body"] = "W" * 32
            result["choices"][0]["message"]["content"] = json.dumps(data)
            return result
        with self.assertRaises(ai.PresentationAIError):
            self.generate(source, Stub(wide_text))

    def test_http_errors_timeout_and_transport_secrets_are_safe(self):
        cases = [(429, 429, "rate_limited"), (401, 503, "provider_auth"), (403, 503, "provider_auth"),
                 (500, 502, "provider_unavailable"), (400, 502, "provider_request"), (302, 502, "provider_unavailable")]
        for code, status, name in cases:
            def fail(_payload, **_kwargs):
                raise error.HTTPError(ai.ENDPOINT, code, "secret api key", {}, io.BytesIO(b"provider private body"))
            with self.subTest(code=code), self.assertRaises(ai.PresentationAIError) as caught:
                self.generate(stub=fail)
            self.assertEqual((caught.exception.status_code, caught.exception.code), (status, name))
            self.assertNotIn("secret", str(caught.exception))
            self.assertNotIn("private", str(caught.exception))
        for exception in (TimeoutError("secret"), error.URLError("secret"), RuntimeError("secret")):
            def fail(_payload, **_kwargs):
                raise exception
            with self.subTest(exception=exception), self.assertRaises(ai.PresentationAIError) as caught:
                self.generate(stub=fail)
            self.assertNotIn("secret", str(caught.exception))

    def test_deadline_stops_additional_batches(self):
        stub = Stub()
        with patch.object(ai.time, "monotonic", side_effect=[0, 1, 181]):
            with self.assertRaises(ai.PresentationAIError) as caught:
                self.generate(document(8), stub)
        self.assertEqual(caught.exception.code, "timeout")
        self.assertEqual(len(stub.calls), 1)

    def test_http_uses_fixed_endpoint_and_refuses_redirects(self):
        response = io.BytesIO(json.dumps(envelope([])).encode())
        class Opener:
            def open(self, req, timeout):
                self.req, self.timeout = req, timeout
                return response
        opener = Opener()
        with patch.object(ai.request, "build_opener", return_value=opener) as build:
            ai._groq_transport({"model": ai.DEFAULT_MODEL}, api_key="test-key", timeout=1)
        self.assertEqual(opener.req.full_url, ai.ENDPOINT)
        self.assertEqual(opener.req.method, "POST")
        self.assertEqual(opener.req.get_header("Authorization"), "Bearer test-key")
        self.assertTrue(any(isinstance(handler, ai._NoRedirect) for handler in build.call_args.args))
        self.assertIsNone(ai._NoRedirect().redirect_request(None, None, 302, None, {}, "https://evil.invalid"))

    def test_oversized_http_body_is_bounded(self):
        response = io.BytesIO(b"x" * (ai.MAX_RESPONSE_BYTES + 1))
        class Opener:
            def open(self, req, timeout):
                return response
        with patch.object(ai.request, "build_opener", return_value=Opener()):
            with self.assertRaises(ai.PresentationAIError) as caught:
                ai._groq_transport({}, api_key="test-key", timeout=1)
        self.assertEqual(caught.exception.code, "invalid_response")


if __name__ == "__main__":
    unittest.main()
