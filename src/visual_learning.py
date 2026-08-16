"""Small, offline interactive visuals that explain a lesson relationship.

The first visual is deliberately narrow: a Momentum lab where students change
mass and velocity and immediately see the numerical and directional result.
It does not simulate physics beyond the lesson formula, use a network, or run
an automatic animation loop.  That keeps the visual lightweight, testable,
and focused on learning rather than decoration.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

from problem_scenario_engine import MomentumCartComparisonVisual
from ui_theme import PALETTE


@dataclass(frozen=True)
class MomentumState:
    """The learner-controlled values and their authored formula result."""

    mass: float
    velocity: float

    @property
    def momentum(self) -> float:
        """Return linear momentum using p = m × v."""
        return self.mass * self.velocity

    @property
    def direction(self) -> str:
        """Return the direction represented by the sign of velocity."""
        if self.velocity > 0:
            return "right"
        if self.velocity < 0:
            return "left"
        return "no direction because it is at rest"


PREDICTION_GREATER = "greater"
PREDICTION_SMALLER = "smaller"
PREDICTION_SAME = "same"
MOMENTUM_PREDICTIONS = {
    PREDICTION_GREATER,
    PREDICTION_SMALLER,
    PREDICTION_SAME,
}


@dataclass(frozen=True)
class MomentumPredictionResult:
    """An honest comparison of a learner's chosen prediction and model result."""

    prediction: str
    actual: str
    correct: bool
    message: str


@dataclass(frozen=True)
class MomentumCartComparisonPredictionResult:
    """A local prediction check for one fixed, authored two-cart model."""

    prediction: str
    actual: str
    supported: bool
    message: str


def compare_momentum_size(reference: MomentumState, candidate: MomentumState) -> str:
    """Compare momentum magnitudes without hiding a possible direction change."""
    reference_size = abs(reference.momentum)
    candidate_size = abs(candidate.momentum)
    if math.isclose(reference_size, candidate_size, rel_tol=1e-9, abs_tol=1e-9):
        return PREDICTION_SAME
    return (
        PREDICTION_GREATER if candidate_size > reference_size else PREDICTION_SMALLER
    )


def evaluate_momentum_prediction(
    prediction: str,
    reference: MomentumState,
    candidate: MomentumState,
) -> MomentumPredictionResult:
    """Check a supplied comparison choice using only the authored formula model.

    This checks the selected *greater/smaller/same* option, not a learner's
    written scientific explanation. The result deliberately distinguishes
    momentum size from direction.
    """
    if not isinstance(prediction, str):
        raise ValueError(
            "Choose whether the momentum size will be greater, smaller, or the same."
        )
    aliases = {
        "greater": PREDICTION_GREATER,
        "more": PREDICTION_GREATER,
        "smaller": PREDICTION_SMALLER,
        "less": PREDICTION_SMALLER,
        "same": PREDICTION_SAME,
        "equal": PREDICTION_SAME,
    }
    normalized_prediction = aliases.get(prediction.strip().lower())
    if normalized_prediction not in MOMENTUM_PREDICTIONS:
        raise ValueError(
            "Choose whether the momentum size will be greater, smaller, or the same."
        )

    actual = compare_momentum_size(reference, candidate)
    candidate_size = _format_number(abs(candidate.momentum))
    reference_size = _format_number(abs(reference.momentum))
    readable_actual = {
        PREDICTION_GREATER: "greater",
        PREDICTION_SMALLER: "smaller",
        PREDICTION_SAME: "the same",
    }[actual]
    correct = normalized_prediction == actual
    prefix = (
        "Your prediction was supported."
        if correct
        else "The model result is different from that prediction."
    )
    message = (
        f"{prefix} The candidate momentum size is {readable_actual} than the reference: "
        f"{candidate_size} kg m/s compared with {reference_size} kg m/s."
    )
    if candidate.direction != reference.direction:
        message += " Its direction is different too; size and direction are separate ideas."
    return MomentumPredictionResult(normalized_prediction, actual, correct, message)


def make_momentum_state(mass: float, velocity: float) -> MomentumState:
    """Create a valid local momentum state without silently changing values."""
    try:
        numeric_mass = float(mass)
        numeric_velocity = float(velocity)
    except (TypeError, ValueError) as error:
        raise ValueError("Mass and velocity must be numbers.") from error
    if not math.isfinite(numeric_mass) or numeric_mass <= 0:
        raise ValueError("Mass must be a finite number greater than zero.")
    if not math.isfinite(numeric_velocity):
        raise ValueError("Velocity must be a finite number.")
    return MomentumState(numeric_mass, numeric_velocity)


def momentum_description(state: MomentumState) -> str:
    """Return a text alternative for the current visual state."""
    mass = _format_number(state.mass)
    velocity = _format_number(abs(state.velocity))
    momentum = _format_number(abs(state.momentum))
    if state.velocity == 0:
        return (
            f"The {mass} kg cart is at rest. Its velocity is 0 m/s, so its momentum is 0 kg m/s."
        )
    return (
        f"The {mass} kg cart moves {state.direction} at {velocity} m/s. "
        f"Its momentum is {momentum} kg m/s {state.direction}."
    )


def momentum_prediction_pending_description(
    reference: MomentumState,
    candidate: MomentumState,
) -> str:
    """Provide a text alternative before the visual reveals the candidate result."""
    reference_size = _format_number(abs(reference.momentum))
    candidate_mass = _format_number(candidate.mass)
    candidate_speed = _format_number(abs(candidate.velocity))
    return (
        f"Prediction pending. The reference cart has momentum size {reference_size} kg m/s. "
        f"The new cart has mass {candidate_mass} kg and moves {candidate.direction} at "
        f"{candidate_speed} m/s. Choose greater, smaller, or same before revealing its momentum."
    )


def compare_momentum_cart_sizes(visual_model: MomentumCartComparisonVisual) -> str:
    """Return which named cart has the greater *momentum size*, or ``same``.

    The scenario schema permits this visual only when both carts move in the
    same non-zero direction.  That makes the later student-facing result safe
    to describe as both the same size and the same direction for this narrow
    computer model.
    """
    first, second = visual_model.carts
    first_size = abs(first.momentum)
    second_size = abs(second.momentum)
    if math.isclose(first_size, second_size, rel_tol=1e-9, abs_tol=1e-9):
        return PREDICTION_SAME
    return first.identifier if first_size > second_size else second.identifier


def evaluate_momentum_cart_comparison_prediction(
    prediction: str,
    visual_model: MomentumCartComparisonVisual,
) -> MomentumCartComparisonPredictionResult:
    """Check one explicit visual prediction using only the authored model.

    This does not evaluate written reasoning, change a Problem Solver step,
    or make a claim about student mastery.  It is deliberately local to the
    visual and is not a persistence or progress event.
    """
    if not isinstance(prediction, str):
        raise ValueError("Choose Cart A, Cart B, or the same momentum size first.")
    first, second = visual_model.carts
    aliases = {
        first.identifier.casefold(): first.identifier,
        second.identifier.casefold(): second.identifier,
        first.label.casefold(): first.identifier,
        second.label.casefold(): second.identifier,
        "same": PREDICTION_SAME,
        "equal": PREDICTION_SAME,
    }
    normalized_prediction = aliases.get(prediction.strip().casefold())
    if normalized_prediction is None:
        raise ValueError("Choose Cart A, Cart B, or the same momentum size first.")

    actual = compare_momentum_cart_sizes(visual_model)
    supported = normalized_prediction == actual
    prefix = (
        "Your prediction was supported by this computer model."
        if supported
        else "This computer model gives a different comparison."
    )
    first_value = _format_number(abs(first.momentum))
    second_value = _format_number(abs(second.momentum))
    first_speed = _format_number(abs(first.velocity_m_per_s))
    second_speed = _format_number(abs(second.velocity_m_per_s))
    if actual == PREDICTION_SAME:
        comparison = (
            f"Both carts have the same momentum size: {first_value} kg m/s. "
            f"They also both move {first.direction} in this model."
        )
    else:
        greater = first if actual == first.identifier else second
        comparison = f"{greater.label} has the greater momentum size in this model."
    message = (
        f"{prefix} {first.label}: p = {_format_number(first.mass_kg)} kg × "
        f"{first_speed} m/s = {first_value} kg m/s {first.direction}. "
        f"{second.label}: p = {_format_number(second.mass_kg)} kg × "
        f"{second_speed} m/s = {second_value} kg m/s {second.direction}. "
        f"{comparison}"
    )
    return MomentumCartComparisonPredictionResult(
        prediction=normalized_prediction,
        actual=actual,
        supported=supported,
        message=message,
    )


def momentum_cart_comparison_description(
    visual_model: MomentumCartComparisonVisual,
    revealed: bool = False,
) -> str:
    """Return an accessible description without leaking a pending result."""
    first, second = visual_model.carts
    first_speed = _format_number(abs(first.velocity_m_per_s))
    second_speed = _format_number(abs(second.velocity_m_per_s))
    description = (
        "Illustrative computer model, not a real measurement. "
        f"{first.label} has mass {_format_number(first.mass_kg)} kg and moves "
        f"{first.direction} at {first_speed} m/s. "
        f"{second.label} has mass {_format_number(second.mass_kg)} kg and moves "
        f"{second.direction} at {second_speed} m/s. "
        "Cart width and velocity-arrow length are schematic visual cues, not exact scale. "
    )
    if not revealed:
        return (
            description
            + "The model calculation and final comparison are still hidden. "
            "Choose a prediction, then test it."
        )
    first_value = _format_number(abs(first.momentum))
    second_value = _format_number(abs(second.momentum))
    comparison = compare_momentum_cart_sizes(visual_model)
    calculation_text = (
        f"{first.label}: p = {_format_number(first.mass_kg)} kg × {first_speed} m/s = "
        f"{first_value} kg m/s {first.direction}. "
        f"{second.label}: p = {_format_number(second.mass_kg)} kg × {second_speed} m/s = "
        f"{second_value} kg m/s {second.direction}. "
    )
    if comparison == PREDICTION_SAME:
        outcome = (
            f"Revealed result: {calculation_text}Both carts have the same momentum size and both "
            f"move {first.direction} in this model."
        )
    else:
        greater = first if comparison == first.identifier else second
        outcome = (
            f"Revealed result: {calculation_text}{greater.label} has the greater momentum size "
            "in this model."
        )
    return f"{description}{outcome}"


class MomentumCartComparisonLab(ttk.Frame):
    """Fixed two-cart scenario visual with a local prediction-before-reveal gate.

    Unlike :class:`MomentumLab`, this component has no sliders and takes its
    data only from a validated ``MomentumCartComparisonVisual``.  It is a
    visual explanation inside one Problem Solver scenario, not a general
    simulation or a student assessment.
    """

    def __init__(
        self,
        parent: tk.Misc,
        visual_model: MomentumCartComparisonVisual,
        on_close: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=(16, 14))
        self.visual_model = visual_model
        self._on_close = on_close
        self.prediction = tk.StringVar(value="")
        self.prediction_feedback = tk.StringVar(
            value="Use the visible input values, choose a prediction, then test it."
        )
        self.accessible_description = tk.StringVar()
        self._result_revealed = False
        self.close_button: ttk.Button | None = None

        ttk.Label(
            self,
            text="Use the supplied mass and velocity values. This visual does not change the model steps.",
            style="Subtitle.TLabel",
            wraplength=650,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 7))

        self.canvas = tk.Canvas(
            self,
            height=160,
            background=PALETTE["surface_soft"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            bd=0,
        )
        self.canvas.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        prediction_frame = ttk.LabelFrame(
            self,
            text="Predict the comparison",
            style="Card.TLabelframe",
            padding=(10, 5),
        )
        prediction_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 7))
        for column in range(3):
            prediction_frame.columnconfigure(column, weight=1)
        ttk.Label(
            prediction_frame,
            text=self.visual_model.prediction_prompt,
            style="Surface.TLabel",
            wraplength=650,
            justify="left",
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        first, second = self.visual_model.carts
        options = (
            (f"{first.label} greater", first.identifier),
            (f"{second.label} greater", second.identifier),
            ("Same size", PREDICTION_SAME),
        )
        for column, (label, value) in enumerate(options):
            ttk.Radiobutton(
                prediction_frame,
                text=label,
                value=value,
                variable=self.prediction,
                style="Surface.TRadiobutton",
            ).grid(row=1, column=column, sticky="w", pady=(3, 0))
        ttk.Button(
            prediction_frame,
            text="Test prediction",
            style="Primary.TButton",
            command=self.test_prediction,
        ).grid(row=2, column=0, sticky="w", pady=(5, 0))
        ttk.Button(
            prediction_frame,
            text="Reset prediction",
            style="Secondary.TButton",
            command=self.reset_prediction,
        ).grid(row=2, column=1, sticky="w", pady=(5, 0))
        ttk.Label(
            prediction_frame,
            textvariable=self.prediction_feedback,
            style="SurfaceMuted.TLabel",
            wraplength=650,
            justify="left",
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5, 0))

        summary = ttk.Frame(self, style="Soft.TFrame", padding=(10, 8))
        summary.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 7))
        ttk.Label(
            summary,
            text="Text description",
            style="CardTitle.TLabel",
        ).pack(anchor="w", pady=(0, 1))
        ttk.Label(
            summary,
            textvariable=self.accessible_description,
            style="Soft.TLabel",
            wraplength=650,
            justify="left",
        ).pack(anchor="w")

        footer = ttk.Frame(self, style="Surface.TFrame")
        footer.grid(row=4, column=0, columnspan=3, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            text="p = mass × velocity. This visual does not assess, record, or save a prediction.",
            style="SurfaceMuted.TLabel",
            wraplength=500,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        if self._on_close is not None:
            self.close_button = ttk.Button(
                footer,
                text="Close visual",
                style="Secondary.TButton",
                command=self._on_close,
            )
            self.close_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

        for column in range(3):
            self.columnconfigure(column, weight=1)
        self.refresh_visual()

    @property
    def result_revealed(self) -> bool:
        """Tell tests/UI whether this local visual result is currently shown."""
        return self._result_revealed

    def reset_prediction(self) -> None:
        """Hide the comparison and invite a fresh local prediction."""
        self.prediction.set("")
        self._result_revealed = False
        self.prediction_feedback.set(
            "Prediction reset. Choose an option, then test it to reveal this model comparison."
        )
        self.refresh_visual()

    def test_prediction(self) -> MomentumCartComparisonPredictionResult | None:
        """Reveal the fixed model comparison after an explicit prediction choice."""
        chosen_prediction = self.prediction.get().strip()
        if not chosen_prediction:
            self.prediction_feedback.set(
                "Choose Cart A, Cart B, or the same momentum size before testing your prediction."
            )
            self.refresh_visual()
            return None
        result = evaluate_momentum_cart_comparison_prediction(
            chosen_prediction,
            self.visual_model,
        )
        self._result_revealed = True
        self.prediction_feedback.set(result.message)
        self.refresh_visual()
        return result

    def refresh_visual(self) -> None:
        """Refresh static labels and Canvas without changing scenario progress."""
        self.accessible_description.set(
            momentum_cart_comparison_description(
                self.visual_model,
                revealed=self._result_revealed,
            )
        )
        self._draw()

    def _draw(self) -> None:
        """Draw two labelled velocity cues; their lengths are not exact scale."""
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 560)
        height = max(self.canvas.winfo_height(), 160)
        max_mass = max(cart.mass_kg for cart in self.visual_model.carts)
        max_speed = max(abs(cart.velocity_m_per_s) for cart in self.visual_model.carts)
        colors = (("#76C893", "#386641"), ("#90CAF9", "#1565C0"))
        for index, (cart, colors_for_cart) in enumerate(zip(self.visual_model.carts, colors)):
            fill, outline = colors_for_cart
            lane_top = 10 + index * 67
            ground_y = lane_top + 40
            cart_width = 76 + (cart.mass_kg / max_mass) * 44
            cart_height = 30
            cart_left = 80 if cart.velocity_m_per_s > 0 else width - 80 - cart_width
            cart_top = ground_y - cart_height
            self.canvas.create_line(36, ground_y + 13, width - 36, ground_y + 13, fill="#94A3B8", width=2)
            self.canvas.create_rectangle(
                cart_left,
                cart_top,
                cart_left + cart_width,
                ground_y,
                fill=fill,
                outline=outline,
                width=2,
            )
            self.canvas.create_oval(cart_left + 12, ground_y - 2, cart_left + 29, ground_y + 14, fill="#334155")
            self.canvas.create_oval(
                cart_left + cart_width - 29,
                ground_y - 2,
                cart_left + cart_width - 12,
                ground_y + 14,
                fill="#334155",
            )
            self.canvas.create_text(
                cart_left + cart_width / 2,
                cart_top + cart_height / 2,
                text=f"{cart.label}\n{_format_number(cart.mass_kg)} kg",
                fill=PALETTE["text"],
                font=("Segoe UI", 9, "bold"),
                justify="center",
            )
            arrow_length = 55 + (abs(cart.velocity_m_per_s) / max_speed) * 105
            if cart.velocity_m_per_s > 0:
                arrow_start = cart_left + cart_width + 20
                arrow_end = min(width - 42, arrow_start + arrow_length)
                label_x = min(width - 18, arrow_end + 8)
                label_anchor = "w"
            else:
                arrow_start = cart_left - 20
                arrow_end = max(42, arrow_start - arrow_length)
                label_x = max(18, arrow_end - 8)
                label_anchor = "e"
            self.canvas.create_line(
                arrow_start,
                cart_top + cart_height / 2,
                arrow_end,
                cart_top + cart_height / 2,
                fill=outline,
                width=4,
                arrow=tk.LAST,
                tags=("velocity-arrow", cart.identifier),
            )
            self.canvas.create_text(
                label_x,
                cart_top + cart_height / 2,
                text=f"{_format_number(abs(cart.velocity_m_per_s))} m/s {cart.direction}",
                fill=outline,
                anchor=label_anchor,
                font=("Segoe UI", 9, "bold"),
            )
        self.canvas.create_text(
            width / 2,
            height - 8,
            text="Schematic cues only: cart width shows mass and arrow length shows velocity.",
            fill=PALETTE["muted"],
            font=("Segoe UI", 9),
        )


class MomentumLab(ttk.Frame):
    """An interactive Canvas and slider lab for the Momentum lesson."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=(18, 16))
        self.reference_state = make_momentum_state(2.0, 5.0)
        self.mass = tk.DoubleVar(value=2.0)
        self.velocity = tk.DoubleVar(value=5.0)
        self.prediction = tk.StringVar(value="")
        self.mass_text = tk.StringVar()
        self.velocity_text = tk.StringVar()
        self.momentum_text = tk.StringVar()
        self.accessible_description = tk.StringVar()
        self.prediction_feedback = tk.StringVar(
            value="This starting cart is your reference. Change a value, then make a prediction."
        )
        self._result_revealed = True
        self._suppress_value_change = False

        self.reference_text = tk.StringVar()
        ttk.Label(
            self,
            textvariable=self.reference_text,
            style="Status.TLabel",
            wraplength=620,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 9))

        self.canvas = tk.Canvas(
            self,
            height=155,
            background=PALETTE["surface_soft"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            bd=0,
        )
        self.canvas.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.canvas.bind("<Configure>", lambda _event: self.refresh_visual())

        controls = ttk.Frame(self, style="Surface.TFrame")
        controls.grid(row=2, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Mass", style="Surface.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Scale(
            controls,
            from_=1,
            to=10,
            variable=self.mass,
            orient="horizontal",
        ).grid(row=0, column=1, sticky="ew")
        ttk.Label(controls, textvariable=self.mass_text, style="SurfaceMuted.TLabel").grid(
            row=0, column=2, sticky="e", padx=(10, 0)
        )

        ttk.Label(controls, text="Velocity", style="Surface.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(10, 0)
        )
        ttk.Scale(
            controls,
            from_=-10,
            to=10,
            variable=self.velocity,
            orient="horizontal",
        ).grid(row=1, column=1, sticky="ew", pady=(10, 0))
        ttk.Label(controls, textvariable=self.velocity_text, style="SurfaceMuted.TLabel").grid(
            row=1, column=2, sticky="e", padx=(10, 0), pady=(10, 0)
        )

        prediction_frame = ttk.LabelFrame(
            self,
            text="Predict before revealing the result",
            style="Card.TLabelframe",
            padding=(10, 5),
        )
        prediction_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(14, 8))
        ttk.Label(
            prediction_frame,
            text="Compared with the reference momentum size, the new momentum will be:",
            style="Surface.TLabel",
        ).grid(row=0, column=0, columnspan=4, sticky="w")
        for column, (label, value) in enumerate(
            (
                ("Greater", PREDICTION_GREATER),
                ("Smaller", PREDICTION_SMALLER),
                ("Same", PREDICTION_SAME),
            )
        ):
            ttk.Radiobutton(
                prediction_frame,
                text=label,
                value=value,
                variable=self.prediction,
                style="Surface.TRadiobutton",
            ).grid(row=1, column=column, sticky="w", padx=(0, 12), pady=(5, 0))
        ttk.Button(
            prediction_frame,
            text="Test prediction",
            style="Primary.TButton",
            command=self.test_prediction,
        ).grid(row=1, column=3, sticky="e", pady=(5, 0))
        ttk.Label(
            prediction_frame,
            textvariable=self.prediction_feedback,
            style="SurfaceMuted.TLabel",
            wraplength=620,
            justify="left",
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        summary = ttk.Frame(self, style="Soft.TFrame", padding=(12, 6))
        summary.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(summary, textvariable=self.momentum_text, style="Status.TLabel").pack(anchor="w")
        ttk.Label(
            summary,
            textvariable=self.accessible_description,
            style="Soft.TLabel",
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

        ttk.Button(
            self,
            text="Reset values",
            style="Secondary.TButton",
            command=self.reset,
        ).grid(row=5, column=0, sticky="w")
        ttk.Label(
            self,
            text="This visual demonstrates the lesson relationship; it does not grade an answer.",
            style="SurfaceMuted.TLabel",
            wraplength=420,
            justify="right",
        ).grid(row=5, column=1, sticky="e")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.mass.trace_add("write", lambda *_args: self._on_value_change())
        self.velocity.trace_add("write", lambda *_args: self._on_value_change())
        self.refresh_visual()

    def current_state(self) -> MomentumState:
        """Return the state currently represented by the sliders."""
        return make_momentum_state(self.mass.get(), self.velocity.get())

    @property
    def result_revealed(self) -> bool:
        """Expose whether the candidate momentum result is currently visible."""
        return self._result_revealed

    def set_values(self, mass: float, velocity: float) -> None:
        """Set a candidate state and invite a new prediction before revealing it."""
        state = make_momentum_state(mass, velocity)
        self._suppress_value_change = True
        try:
            self.mass.set(state.mass)
            self.velocity.set(state.velocity)
        finally:
            self._suppress_value_change = False
        self._mark_prediction_needed()
        self.refresh_visual()

    def reset(self) -> None:
        """Restore the visible authored reference example."""
        self._suppress_value_change = True
        try:
            self.mass.set(self.reference_state.mass)
            self.velocity.set(self.reference_state.velocity)
        finally:
            self._suppress_value_change = False
        self.prediction.set("")
        self._result_revealed = True
        self.prediction_feedback.set(
            "Reference restored. Change mass or velocity, then predict before revealing the result."
        )
        self.refresh_visual()

    def _on_value_change(self) -> None:
        """Hide a changed result until the learner deliberately tests a prediction."""
        if self._suppress_value_change:
            return
        self._mark_prediction_needed()
        self.refresh_visual()

    def _mark_prediction_needed(self) -> None:
        self.prediction.set("")
        self._result_revealed = False
        self.prediction_feedback.set(
            "Prediction pending: choose greater, smaller, or same, then test your prediction."
        )

    def test_prediction(self) -> MomentumPredictionResult | None:
        """Reveal the formula result after a learner chooses a comparison prediction."""
        if not self.prediction.get().strip():
            self.prediction_feedback.set(
                "Choose greater, smaller, or same before revealing the model result."
            )
            self.refresh_visual()
            return None
        result = evaluate_momentum_prediction(
            self.prediction.get(),
            self.reference_state,
            self.current_state(),
        )
        self._result_revealed = True
        self.prediction_feedback.set(result.message)
        self.refresh_visual()
        return result

    def refresh_visual(self) -> None:
        """Refresh text and drawing while respecting the prediction-before-reveal rule."""
        state = self.current_state()
        reference_size = _format_number(abs(self.reference_state.momentum))
        self.reference_text.set(
            "Reference cart: "
            f"{_format_number(self.reference_state.mass)} kg at "
            f"{_format_number(abs(self.reference_state.velocity))} m/s "
            f"has momentum size {reference_size} kg m/s."
        )
        self.mass_text.set(f"{_format_number(state.mass)} kg")
        velocity = _format_number(abs(state.velocity))
        if state.velocity == 0:
            self.velocity_text.set("0 m/s")
        else:
            self.velocity_text.set(f"{velocity} m/s {state.direction}")
        if not self._result_revealed:
            self.momentum_text.set(
                "Momentum result hidden: make a prediction, then choose Test prediction."
            )
            self.accessible_description.set(
                momentum_prediction_pending_description(self.reference_state, state)
            )
        elif state.velocity == 0:
            self.momentum_text.set("Momentum: p = m × v = 0 kg m/s")
            self.accessible_description.set(momentum_description(state))
        else:
            self.momentum_text.set(
                "Momentum: p = m × v = "
                f"{_format_number(abs(state.momentum))} kg m/s {state.direction}"
            )
            self.accessible_description.set(momentum_description(state))
        self._draw(state, show_momentum=self._result_revealed)

    def _draw(self, state: MomentumState, show_momentum: bool) -> None:
        """Draw a cart with either a velocity cue or a revealed momentum arrow."""
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 500)
        height = max(self.canvas.winfo_height(), 155)
        centre_x = width / 2
        ground_y = height - 48
        cart_width = 58 + min(62, state.mass * 8)
        cart_height = 52
        cart_left = centre_x - cart_width / 2
        cart_top = ground_y - cart_height

        self.canvas.create_line(42, ground_y + 16, width - 42, ground_y + 16, fill="#94A3B8", width=2)
        self.canvas.create_rectangle(
            cart_left,
            cart_top,
            cart_left + cart_width,
            ground_y,
            fill="#76C893",
            outline="#386641",
            width=2,
        )
        self.canvas.create_oval(cart_left + 12, ground_y - 2, cart_left + 30, ground_y + 16, fill="#334155")
        self.canvas.create_oval(
            cart_left + cart_width - 30,
            ground_y - 2,
            cart_left + cart_width - 12,
            ground_y + 16,
            fill="#334155",
        )
        self.canvas.create_text(
            centre_x,
            cart_top + cart_height / 2,
            text=f"mass = {_format_number(state.mass)} kg",
            fill=PALETTE["text"],
            font=("Segoe UI", 10, "bold"),
        )

        if state.velocity == 0:
            self.canvas.create_text(
                centre_x,
                48,
                text=(
                    "At rest: no momentum arrow"
                    if show_momentum
                    else "At rest: choose a prediction to reveal momentum"
                ),
                fill=PALETTE["muted"],
                font=("Segoe UI", 11, "bold"),
            )
            return

        arrow_length = (
            40 + min(210, abs(state.momentum) * 6)
            if show_momentum
            else 36 + min(160, abs(state.velocity) * 16)
        )
        if state.velocity > 0:
            start_x = cart_left + cart_width + 14
            end_x = min(width - 36, start_x + arrow_length)
        else:
            start_x = cart_left - 14
            end_x = max(36, start_x - arrow_length)
        arrow_y = cart_top + cart_height / 2
        self.canvas.create_line(
            start_x,
            arrow_y,
            end_x,
            arrow_y,
            fill=PALETTE["primary"],
            width=5,
            arrow=tk.LAST,
        )
        self.canvas.create_text(
            centre_x,
            42,
            text=(
                (
                    f"Momentum arrow: {_format_number(abs(state.momentum))} kg m/s "
                    f"{state.direction}"
                )
                if show_momentum
                else (
                    "Velocity arrow: "
                    f"{_format_number(abs(state.velocity))} m/s {state.direction}"
                )
            ),
            fill=PALETTE["primary"],
            font=("Segoe UI", 11, "bold"),
        )


def create_interactive_visual(parent: tk.Misc, topic: str) -> ttk.Frame | None:
    """Create the installed interactive visual for a topic, if one exists."""
    if topic == "momentum":
        return MomentumLab(parent)
    return None


def _format_number(value: float) -> str:
    """Format slider values without distracting trailing decimals."""
    return str(int(value)) if float(value).is_integer() else f"{value:.1f}"
