"""Tests for safe, local JSON Problem Solver scenario support."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from problem_scenario_engine import (
    COMPUTER_MODEL,
    ILLUSTRATIVE_COMPUTER_MODEL,
    NEEDS_REVIEW,
    SCENARIOS_DIR,
    UNAVAILABLE,
    DataProvenance,
    ProblemScenario,
    ProblemScenarioRepository,
    ProblemScenarioSession,
    ScenarioFormatError,
    load_problem_scenarios,
    render_go_deeper,
    render_problem_solver,
)


class ProblemScenarioEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        scenarios = load_problem_scenarios(SCENARIOS_DIR)
        assert len(scenarios) == 3
        cls.scenario = next(
            scenario
            for scenario in scenarios
            if scenario.identifier == "physics.momentum.cart-comparison"
        )

    def _raw_momentum_scenario(self) -> dict[str, object]:
        """Return a fresh editable record for schema-validation tests."""
        return json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )

    def test_authored_model_scenario_loads_with_distinct_source_and_provenance(self) -> None:
        scenario = self.scenario

        self.assertEqual(scenario.identifier, "physics.momentum.cart-comparison")
        self.assertEqual(scenario.scenario_type, COMPUTER_MODEL)
        self.assertEqual(scenario.verification_status, NEEDS_REVIEW)
        self.assertEqual(scenario.data_provenance.kind, ILLUSTRATIVE_COMPUTER_MODEL)
        self.assertFalse(scenario.data_provenance.is_local_measurement)
        self.assertIn("OpenStax", scenario.content_source.citation)
        self.assertIn("illustrative", scenario.data_provenance.statement.lower())
        self.assertNotEqual(scenario.content_source.citation, scenario.data_provenance.statement)

    def test_visual_model_uses_typed_json_inputs_not_scenario_prose(self) -> None:
        """The static visual has explicit model inputs, rather than scraped wording."""
        visual_model = self.scenario.visual_model

        self.assertIsNotNone(visual_model)
        assert visual_model is not None
        self.assertEqual(visual_model.kind, "MOMENTUM_CART_COMPARISON")
        self.assertEqual(
            visual_model.prediction_prompt,
            "Which cart has greater momentum size: Cart A, Cart B, or the same?",
        )
        self.assertEqual(visual_model.available_after_step_id, "cart-b-momentum")
        cart_a, cart_b = visual_model.carts
        self.assertEqual((cart_a.identifier, cart_a.label), ("cart-a", "Cart A"))
        self.assertEqual((cart_b.identifier, cart_b.label), ("cart-b", "Cart B"))
        self.assertEqual((cart_a.mass_kg, cart_a.velocity_m_per_s), (2.0, 3.0))
        self.assertEqual((cart_b.mass_kg, cart_b.velocity_m_per_s), (3.0, 2.0))
        self.assertEqual((cart_a.momentum, cart_b.momentum), (6.0, 6.0))
        self.assertEqual((cart_a.direction, cart_b.direction), ("right", "right"))

        raw = self._raw_momentum_scenario()
        raw["introduction"] = (
            "This deliberately misleading prose says a fictional Cart Z has mass 999 kg "
            "and velocity 888 m/s."
        )
        raw["problem"] = "Do not infer visual inputs from this unrelated sentence: 12345."

        parsed = ProblemScenario.from_mapping(raw)
        assert parsed.visual_model is not None
        self.assertEqual(
            tuple(
                (cart.identifier, cart.mass_kg, cart.velocity_m_per_s)
                for cart in parsed.visual_model.carts
            ),
            (("cart-a", 2.0, 3.0), ("cart-b", 3.0, 2.0)),
        )

    def test_rejects_visual_model_outside_momentum_computer_model_scope(self) -> None:
        raw = self._raw_momentum_scenario()
        raw["topic"] = "force"

        with self.assertRaisesRegex(ScenarioFormatError, "Momentum COMPUTER_MODEL"):
            ProblemScenario.from_mapping(raw)

    def test_rejects_malformed_momentum_visual_carts(self) -> None:
        cases = (
            ("one cart", lambda raw: raw["visual_model"]["carts"].pop()),
            (
                "three carts",
                lambda raw: raw["visual_model"]["carts"].append(
                    {
                        "id": "cart-c",
                        "label": "Cart C",
                        "mass_kg": 4,
                        "velocity_m_per_s": 1,
                    }
                ),
            ),
            (
                "duplicate ids",
                lambda raw: raw["visual_model"]["carts"][1].update({"id": "CART-A"}),
            ),
            (
                "duplicate labels",
                lambda raw: raw["visual_model"]["carts"][1].update({"label": "cart a"}),
            ),
            (
                "non-finite mass",
                lambda raw: raw["visual_model"]["carts"][0].update(
                    {"mass_kg": float("nan")}
                ),
            ),
            (
                "non-finite velocity",
                lambda raw: raw["visual_model"]["carts"][0].update(
                    {"velocity_m_per_s": float("inf")}
                ),
            ),
            (
                "non-finite JSON-number input",
                lambda raw: raw["visual_model"]["carts"][0].update({"mass_kg": 1e309}),
            ),
            (
                "finite inputs with overflowed momentum",
                lambda raw: raw["visual_model"]["carts"][0].update(
                    {"mass_kg": 1e308, "velocity_m_per_s": 1e308}
                ),
            ),
            (
                "at rest",
                lambda raw: raw["visual_model"]["carts"][0].update(
                    {"velocity_m_per_s": 0}
                ),
            ),
            (
                "opposite directions",
                lambda raw: raw["visual_model"]["carts"][1].update(
                    {"velocity_m_per_s": -2}
                ),
            ),
        )

        for case_name, corrupt in cases:
            with self.subTest(case_name=case_name):
                raw = self._raw_momentum_scenario()
                corrupt(raw)
                with self.assertRaises(ScenarioFormatError):
                    ProblemScenario.from_mapping(raw)

    def test_visual_model_is_optional_but_its_learning_step_link_must_exist(self) -> None:
        raw = self._raw_momentum_scenario()
        raw.pop("visual_model")
        self.assertIsNone(ProblemScenario.from_mapping(raw).visual_model)

        raw = self._raw_momentum_scenario()
        raw["visual_model"]["available_after_step_id"] = "missing-step"
        with self.assertRaisesRegex(ScenarioFormatError, "installed guided step"):
            ProblemScenario.from_mapping(raw)

    def test_visual_model_can_describe_two_left_moving_carts_without_changing_scope(self) -> None:
        """The initial model permits a shared left direction as well as right."""
        raw = self._raw_momentum_scenario()
        raw["visual_model"]["carts"][0]["velocity_m_per_s"] = -3
        raw["visual_model"]["carts"][1]["velocity_m_per_s"] = -2

        visual_model = ProblemScenario.from_mapping(raw).visual_model
        assert visual_model is not None
        self.assertEqual(tuple(cart.direction for cart in visual_model.carts), ("left", "left"))

    def test_renderer_marks_draft_and_illustrative_values_before_problem_steps(self) -> None:
        sections = render_problem_solver(self.scenario)
        text = "\n".join(f"{section.title}\n{section.body}" for section in sections)

        self.assertEqual(sections[0].title, "CONTENT STATUS")
        self.assertIn("needs review", sections[0].body.lower())
        self.assertEqual(sections[1].title, "MODEL DATA")
        self.assertIn("not local measurements", sections[1].body.lower())
        self.assertIn("not local measurements", text.lower())
        self.assertIn("STEP 1", sections[4].title)
        self.assertNotIn("Sindhudurg", text)
        self.assertNotIn("Konkan", text)

    def test_session_requires_attempt_or_hints_before_solution_and_progresses_by_step(self) -> None:
        session = ProblemScenarioSession(self.scenario)

        self.assertFalse(session.reveal_solution().available)
        self.assertIsNotNone(session.current_step_section())
        wrong = session.submit_attempt("9")
        self.assertFalse(wrong.correct)
        self.assertEqual(session.attempts, 1)
        self.assertTrue(session.reveal_solution().available)

        first = session.submit_attempt("6 kg m/s")
        self.assertTrue(first.correct)
        self.assertEqual(session.current_step_index, 1)
        self.assertTrue(session.has_completed_step("cart-a-momentum"))
        self.assertFalse(session.has_completed_step("cart-b-momentum"))
        self.assertNotEqual(session.hint(), session.hint())
        self.assertTrue(session.submit_attempt("6").correct)
        self.assertTrue(session.has_completed_step("cart-b-momentum"))
        final = session.submit_attempt("Both are equal")
        self.assertTrue(final.correct)
        self.assertTrue(final.is_complete)
        self.assertTrue(session.is_complete)
        self.assertIsNone(session.current_step)
        self.assertIn("completed", session.submit_attempt("anything").message.lower())

    def test_declared_numeric_rule_accepts_safe_formats_but_not_guesses(self) -> None:
        """Calculation steps accept declared decimal/unit forms, not arbitrary prose."""
        cart_a, cart_b, comparison = self.scenario.guided_steps

        self.assertIsNotNone(cart_a.numeric_answer)
        self.assertTrue(cart_a.matches_answer("6.0"))
        self.assertTrue(cart_a.matches_answer("6.0 kg m/s"))
        self.assertTrue(cart_a.matches_answer("p = 6 kg*m/s"))
        self.assertTrue(cart_a.matches_answer("p = 6 kg × m/s"))
        self.assertTrue(cart_a.matches_answer("momentum = 6 kg m/s"))
        self.assertFalse(cart_a.matches_answer("6 kg"))
        self.assertFalse(cart_a.matches_answer("6 m/s"))
        self.assertFalse(cart_a.matches_answer("6 kg/m*s"))
        self.assertFalse(cart_a.matches_answer("6 kg^m/s"))
        self.assertFalse(cart_a.matches_answer("6 kg--m/s"))
        self.assertFalse(cart_a.matches_answer("6 kg..m/s"))
        self.assertFalse(cart_a.matches_answer("6.5 kg m/s"))
        self.assertFalse(cart_a.matches_answer("the answer is 6 kg m/s"))
        self.assertFalse(cart_a.matches_answer("force = 6 kg m/s"))
        self.assertIsNone(comparison.numeric_answer)
        self.assertFalse(comparison.matches_answer("6.0"))

        session = ProblemScenarioSession(self.scenario)
        self.assertTrue(session.submit_attempt("p = 6.0 kg*m/s").correct)
        self.assertTrue(session.submit_attempt("6.0 kg m/s").correct)

    def test_empty_answer_does_not_count_as_a_student_attempt(self) -> None:
        session = ProblemScenarioSession(self.scenario)

        feedback = session.submit_attempt("   ")

        self.assertIsNone(feedback.correct)
        self.assertEqual(session.attempts, 0)
        self.assertFalse(session.can_reveal_solution())

    def test_go_deeper_includes_hypothesis_labelled_data_analysis_and_reflection(self) -> None:
        sections = render_go_deeper(self.scenario)
        titles = [section.title for section in sections]
        data_section = next(section for section in sections if section.title == "DATA / OBSERVATION")

        self.assertEqual(
            titles,
            [
                "GO DEEPER: RESEARCH QUESTION",
                "HYPOTHESIS",
                "DATA / OBSERVATION",
                "ANALYSIS",
                "PROPOSE A SOLUTION",
                "REFLECT",
            ],
        )
        self.assertIn("Illustrative computer-model values", data_section.body)
        self.assertIn("Velocity (m/s)", data_section.body)
        self.assertIn("|", data_section.body)

    def test_rejects_any_local_measurement_in_computer_model_schema(self) -> None:
        with self.assertRaisesRegex(ScenarioFormatError, "does not accept local measurements"):
            DataProvenance.from_mapping(
                {
                    "kind": ILLUSTRATIVE_COMPUTER_MODEL,
                    "statement": "Incorrectly claimed local data.",
                    "is_local_measurement": True,
                }
            )

    def test_rejects_malformed_rows_and_duplicate_step_ids(self) -> None:
        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["go_deeper"]["data_rows"][0].pop()
        with self.assertRaisesRegex(ScenarioFormatError, "exactly 4 values"):
            ProblemScenario.from_mapping(raw)

        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["guided_steps"][1]["id"] = raw["guided_steps"][0]["id"].upper()
        with self.assertRaisesRegex(ScenarioFormatError, "identifiers must be unique"):
            ProblemScenario.from_mapping(raw)

        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["guided_steps"][0]["numeric_answer"]["value"] = 7
        with self.assertRaisesRegex(ScenarioFormatError, "must match every numeric"):
            ProblemScenario.from_mapping(raw)

        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["guided_steps"][0]["numeric_answer"]["allow_unit_omission"] = False
        with self.assertRaisesRegex(ScenarioFormatError, "must match every numeric"):
            ProblemScenario.from_mapping(raw)

        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["guided_steps"][0]["accepted_answers"] = ["6"]
        raw["guided_steps"][0]["numeric_answer"]["unit"] = None
        with self.assertRaisesRegex(ScenarioFormatError, "unit must be a non-empty string"):
            ProblemScenario.from_mapping(raw)

        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["guided_steps"][0]["numeric_answer"]["value"] = "6"
        with self.assertRaisesRegex(ScenarioFormatError, "value must be a finite number"):
            ProblemScenario.from_mapping(raw)

        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["guided_steps"][0]["numeric_answer"]["accepted_symbols"] = [None]
        with self.assertRaisesRegex(ScenarioFormatError, "must contain only strings"):
            ProblemScenario.from_mapping(raw)

    def test_repository_lookup_is_explicit_and_file_errors_name_the_file(self) -> None:
        repository = ProblemScenarioRepository([self.scenario])
        self.assertIs(repository.get("PHYSICS.MOMENTUM.CART-COMPARISON"), self.scenario)
        self.assertEqual(repository.for_topic("Momentum"), (self.scenario,))
        self.assertEqual(repository.for_topic("gravity"), ())

        with tempfile.TemporaryDirectory() as temporary_directory:
            scenario_path = Path(temporary_directory) / "broken.json"
            scenario_path.write_text("{not valid JSON", encoding="utf-8")
            with self.assertRaisesRegex(ScenarioFormatError, "broken.json"):
                load_problem_scenarios(Path(temporary_directory))

    def test_repository_scopes_student_activities_to_subject_and_hides_unavailable(self) -> None:
        wrong_subject = replace(
            self.scenario,
            identifier="computer-science.momentum.wrong-subject",
            subject="Computer Science",
            title="Wrong subject",
        )
        unavailable = replace(
            self.scenario,
            identifier="physics.momentum.unavailable",
            verification_status=UNAVAILABLE,
        )
        repository = ProblemScenarioRepository([wrong_subject, unavailable, self.scenario])

        self.assertEqual(
            repository.for_topic("momentum", subject="Physics"),
            (self.scenario,),
        )
        self.assertEqual(
            repository.for_topic("momentum", subject="Computer Science"),
            (wrong_subject,),
        )
        self.assertNotIn(unavailable, repository.for_topic("momentum"))
        self.assertFalse(unavailable.is_student_available)
        self.assertIn("unavailable", unavailable.content_status_notice.lower())

    def test_rejects_non_https_concept_source_url(self) -> None:
        raw = json.loads(
            (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                encoding="utf-8"
            )
        )
        raw["content_source"]["url"] = "http://example.invalid/source"

        with self.assertRaisesRegex(ScenarioFormatError, "https URL"):
            ProblemScenario.from_mapping(raw)


class ForceScenarioTests(unittest.TestCase):
    """The second authored scenario reuses the same schema for a new topic."""

    @classmethod
    def setUpClass(cls) -> None:
        scenarios = load_problem_scenarios(SCENARIOS_DIR)
        cls.scenario = next(
            scenario
            for scenario in scenarios
            if scenario.identifier == "physics.force.model-comparison"
        )

    def test_scenario_loads_with_distinct_source_and_provenance_and_no_visual(self) -> None:
        scenario = self.scenario

        self.assertEqual(scenario.topic, "force")
        self.assertEqual(scenario.scenario_type, COMPUTER_MODEL)
        self.assertEqual(scenario.verification_status, NEEDS_REVIEW)
        self.assertEqual(scenario.data_provenance.kind, ILLUSTRATIVE_COMPUTER_MODEL)
        self.assertFalse(scenario.data_provenance.is_local_measurement)
        self.assertIn("OpenStax", scenario.content_source.citation)
        self.assertIn("illustrative", scenario.data_provenance.statement.lower())
        self.assertNotEqual(scenario.content_source.citation, scenario.data_provenance.statement)
        self.assertIsNone(scenario.visual_model)

    def test_renderer_marks_draft_and_illustrative_values_before_problem_steps(self) -> None:
        sections = render_problem_solver(self.scenario)
        text = "\n".join(f"{section.title}\n{section.body}" for section in sections)

        self.assertEqual(sections[0].title, "CONTENT STATUS")
        self.assertIn("needs review", sections[0].body.lower())
        self.assertEqual(sections[1].title, "MODEL DATA")
        self.assertIn("not local measurements", sections[1].body.lower())
        self.assertNotIn("Sindhudurg", text)
        self.assertNotIn("Konkan", text)

    def test_session_progresses_through_two_calculations_then_a_comparison(self) -> None:
        session = ProblemScenarioSession(self.scenario)

        wrong = session.submit_attempt("3")
        self.assertFalse(wrong.correct)
        self.assertTrue(session.reveal_solution().available)

        first = session.submit_attempt("2 m/s2")
        self.assertTrue(first.correct)
        self.assertEqual(session.current_step_index, 1)
        self.assertTrue(session.has_completed_step("block-a-acceleration"))

        second = session.submit_attempt("4")
        self.assertTrue(second.correct)
        self.assertTrue(session.has_completed_step("block-b-acceleration"))

        final = session.submit_attempt("Block B")
        self.assertTrue(final.correct)
        self.assertTrue(final.is_complete)
        self.assertTrue(session.is_complete)

    def test_go_deeper_includes_hypothesis_labelled_data_analysis_and_reflection(self) -> None:
        sections = render_go_deeper(self.scenario)
        titles = [section.title for section in sections]
        data_section = next(section for section in sections if section.title == "DATA / OBSERVATION")

        self.assertEqual(
            titles,
            [
                "GO DEEPER: RESEARCH QUESTION",
                "HYPOTHESIS",
                "DATA / OBSERVATION",
                "ANALYSIS",
                "PROPOSE A SOLUTION",
                "REFLECT",
            ],
        )
        self.assertIn("Illustrative computer-model values", data_section.body)
        self.assertIn("Acceleration (m/s2)", data_section.body)
        self.assertIn("|", data_section.body)

    def test_repository_scopes_the_new_scenario_to_its_own_topic(self) -> None:
        repository = ProblemScenarioRepository.from_directory(SCENARIOS_DIR)

        self.assertEqual(repository.for_topic("force"), (self.scenario,))
        self.assertNotIn(self.scenario, repository.for_topic("momentum"))


class MotionRealLifeScenarioTests(unittest.TestCase):
    """A real-life-framed scenario must stay illustrative, not a factual claim."""

    @classmethod
    def setUpClass(cls) -> None:
        scenarios = load_problem_scenarios(SCENARIOS_DIR)
        cls.scenario = next(
            scenario
            for scenario in scenarios
            if scenario.identifier == "physics.motion.water-carrying-journey"
        )

    def test_scenario_loads_with_distinct_source_and_provenance_and_no_visual(self) -> None:
        scenario = self.scenario

        self.assertEqual(scenario.topic, "motion")
        self.assertEqual(scenario.scenario_type, COMPUTER_MODEL)
        self.assertEqual(scenario.verification_status, NEEDS_REVIEW)
        self.assertEqual(scenario.data_provenance.kind, ILLUSTRATIVE_COMPUTER_MODEL)
        self.assertFalse(scenario.data_provenance.is_local_measurement)
        self.assertIn("OpenStax", scenario.content_source.citation)
        self.assertIsNone(scenario.visual_model)

    def test_introduction_never_claims_a_real_household_or_place(self) -> None:
        """A relatable frame must not slide into an unverified factual claim."""
        sections = render_problem_solver(self.scenario)
        text = "\n".join(f"{section.title}\n{section.body}" for section in sections)

        self.assertIn("not a measurement of any real household", self.scenario.introduction)
        self.assertIn("not local measurements", sections[1].body.lower())
        self.assertNotIn("Sindhudurg", text)
        self.assertNotIn("Konkan", text)

    def test_session_progresses_through_two_calculations_then_a_reasoning_step(self) -> None:
        session = ProblemScenarioSession(self.scenario)

        wrong = session.submit_attempt("100")
        self.assertFalse(wrong.correct)
        self.assertTrue(session.reveal_solution().available)

        first = session.submit_attempt("250 s")
        self.assertTrue(first.correct)
        self.assertTrue(session.has_completed_step("one-way-time"))

        second = session.submit_attempt("500")
        self.assertTrue(second.correct)
        self.assertTrue(session.has_completed_step("round-trip-time"))

        final = session.submit_attempt("more time")
        self.assertTrue(final.correct)
        self.assertTrue(final.is_complete)

    def test_go_deeper_data_supports_the_slower_return_speed_hypothesis(self) -> None:
        sections = render_go_deeper(self.scenario)
        data_section = next(section for section in sections if section.title == "DATA / OBSERVATION")

        self.assertIn("Illustrative computer-model output", data_section.body)
        self.assertIn("Total round-trip time (s)", data_section.body)

    def test_repository_scopes_the_new_scenario_to_its_own_topic(self) -> None:
        repository = ProblemScenarioRepository.from_directory(SCENARIOS_DIR)

        self.assertEqual(repository.for_topic("motion"), (self.scenario,))
        self.assertNotIn(self.scenario, repository.for_topic("force"))


if __name__ == "__main__":
    unittest.main()
