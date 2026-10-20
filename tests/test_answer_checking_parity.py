"""The browser and the desktop app must accept exactly the same answers.

This is the highest-stakes duplication in the project. The website reimplements
`problem_scenario_engine` in JavaScript, and that code decides whether a
student's answer is marked right. A divergence does not crash or log anything:
a learner types a correct answer, is told it is wrong, and concludes they do
not understand the physics.

Every other port in this repository is checked by reading the source for the
right substrings. That is too weak here, so these run the real JavaScript in a
headless browser against the same cases as the Python, and compare verdicts.
When no browser is available the comparison skips rather than failing — it is
a cross-check, and it must not become a reason CI cannot run.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from problem_scenario_engine import ScenarioStep

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

# Taken from the real momentum scenario, so the cases exercise a rule a
# student actually meets rather than one invented for the test.
STEP = {
    "id": "cart-a-momentum",
    "prompt": "What is Cart A's momentum?",
    "success_feedback": "Correct. Cart A has momentum 2 kg x 3 m/s = 6 kg m/s.",
    "accepted_answers": ["6", "6 kg m/s"],
    "numeric_answer": {
        "value": 6,
        "unit": "kg m/s",
        "allow_unit_omission": True,
        "accepted_symbols": ["p", "momentum"],
    },
}

# Chosen to cover what a student actually types, and the places where a
# sloppy port diverges: spacing, symbols, units written three ways, a wrong
# value, a right value with the wrong unit, and division where the rule says
# multiplication.
ANSWERS = [
    "6",
    "6.0",
    " 6 ",
    "6 kg m/s",
    "6 kg*m/s",
    "6 kg m / s",
    "p = 6",
    "p = 6 kg m/s",
    "momentum = 6 kg m/s",
    "P = 6 KG M/S",
    "6kg m/s",
    "+6 kg m/s",
    "6.000 kg m/s",
    "7",
    "6 m/s",
    "6 kg/m/s",
    "6 kg m s",
    "six",
    "6 kg m/s approximately",
    "x = 6 kg m/s",
    "",
    "the momentum is 6",
]

# Quiz answers are what every student touches, where only some reach a
# Problem Solver step, so the same comparison covers both.
QUIZ = {
    "id": "waves-what-travels",
    "correct_answers": ["Energy, carried by the disturbance", "2"],
}
QUIZ_ANSWERS = [
    "Energy, carried by the disturbance",
    "energy carried by the disturbance",
    "ENERGY, CARRIED BY THE DISTURBANCE",
    "  energy,  carried   by the disturbance  ",
    "energy-carried-by-the-disturbance",
    "2",
    " 2 ",
    "The water itself",
    "energy",
    "",
    "3",
]

JS_START = "/* ============ answer checking"
JS_END = "/* ============ data ============ */"


def find_chrome() -> str | None:
    for candidate in (
        os.environ.get("CHROME_PATH"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "google-chrome",
        "chromium-browser",
        "chromium",
    ):
        if not candidate:
            continue
        if os.path.sep in candidate:
            if Path(candidate).exists():
                return candidate
        else:
            found = shutil.which(candidate)
            if found:
                return found
    return None


class AnswerCheckingParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")
        self.step = ScenarioStep.from_mapping(STEP)

    def python_verdicts(self) -> list[bool]:
        return [self.step.matches_answer(answer) for answer in ANSWERS]

    @staticmethod
    def python_quiz_verdicts() -> list[bool]:
        from quiz_engine import _normalize_answer

        accepted = {_normalize_answer(a) for a in QUIZ["correct_answers"]}
        return [_normalize_answer(answer) in accepted for answer in QUIZ_ANSWERS]

    def test_the_javascript_block_can_be_located(self) -> None:
        """If these markers move, the harness silently tests nothing."""
        self.assertIn(JS_START, self.html)
        self.assertIn(JS_END, self.html)
        self.assertLess(self.html.index(JS_START), self.html.index(JS_END))

    def test_python_accepts_the_answers_a_student_would_write(self) -> None:
        verdicts = dict(zip(ANSWERS, self.python_verdicts()))
        for accepted in ("6", "6.0", "6 kg m/s", "6 kg*m/s", "p = 6 kg m/s"):
            with self.subTest(answer=accepted):
                self.assertTrue(verdicts[accepted])
        for rejected in ("7", "six", "", "6 kg/m/s", "x = 6 kg m/s"):
            with self.subTest(answer=rejected):
                self.assertFalse(verdicts[rejected])

    def test_browser_and_python_agree_on_every_answer(self) -> None:
        chrome = find_chrome()
        if chrome is None:
            self.skipTest("no Chrome or Chromium available for the cross-check")

        start = self.html.index(JS_START)
        logic = self.html[start : self.html.index(JS_END)]
        harness = (
            "<!doctype html><title>parity</title><body><pre id=out></pre>\n"
            "<script>\n"
            + logic
            + "\nconst STEP = "
            + json.dumps(STEP)
            + ";\nconst ANSWERS = "
            + json.dumps(ANSWERS)
            + ";\nconst QUIZ = "
            + json.dumps(QUIZ)
            + ";\nconst QUIZ_ANSWERS = "
            + json.dumps(QUIZ_ANSWERS)
            + ";\n"
            "document.getElementById('out').textContent = JSON.stringify({"
            "step: ANSWERS.map(a => stepMatches(STEP, a)),"
            "quiz: QUIZ_ANSWERS.map(a => quizMatches(QUIZ, a))});\n"
            "</script>"
        )

        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "parity.html"
            page.write_text(harness, encoding="utf-8")
            try:
                completed = subprocess.run(
                    [
                        chrome,
                        "--headless",
                        "--disable-gpu",
                        "--no-sandbox",
                        "--virtual-time-budget=4000",
                        "--dump-dom",
                        page.as_uri(),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
            except (subprocess.TimeoutExpired, OSError) as error:
                self.skipTest(f"browser could not run: {error}")

        dom = completed.stdout
        marker = '<pre id="out">'
        self.assertIn(marker, dom, "the harness produced no output")
        rendered = dom[dom.index(marker) + len(marker) :]
        rendered = rendered[: rendered.index("</pre>")]
        self.assertTrue(rendered.strip(), "the JavaScript produced no verdicts")
        browser = json.loads(rendered)

        for label, answers, python in (
            ("problem step", ANSWERS, self.python_verdicts()),
            ("quiz", QUIZ_ANSWERS, self.python_quiz_verdicts()),
        ):
            with self.subTest(checking=label):
                js = browser[{"problem step": "step", "quiz": "quiz"}[label]]
                self.assertEqual(len(js), len(python))
                disagreements = [
                    (answer, expected, actual)
                    for answer, expected, actual in zip(answers, python, js)
                    if expected != actual
                ]
                self.assertEqual(
                    disagreements,
                    [],
                    f"the two apps mark the same {label} answer differently: "
                    + "; ".join(
                        f"{answer!r} python={expected} browser={actual}"
                        for answer, expected, actual in disagreements
                    ),
                )


if __name__ == "__main__":
    unittest.main()
