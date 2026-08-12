"""Small, offline interactive visuals that explain a lesson relationship.

The first visual is deliberately narrow: a Momentum lab where students change
mass and velocity and immediately see the numerical and directional result.
It does not simulate physics beyond the lesson formula, use a network, or run
an automatic animation loop.  That keeps the visual lightweight, testable,
and focused on learning rather than decoration.
"""

from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk

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


def make_momentum_state(mass: float, velocity: float) -> MomentumState:
    """Create a valid local momentum state without silently changing values."""
    if mass <= 0:
        raise ValueError("Mass must be greater than zero.")
    return MomentumState(float(mass), float(velocity))


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


class MomentumLab(ttk.Frame):
    """An interactive Canvas and slider lab for the Momentum lesson."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, style="Surface.TFrame", padding=(18, 16))
        self.mass = tk.DoubleVar(value=2.0)
        self.velocity = tk.DoubleVar(value=5.0)
        self.mass_text = tk.StringVar()
        self.velocity_text = tk.StringVar()
        self.momentum_text = tk.StringVar()
        self.accessible_description = tk.StringVar()

        ttk.Label(self, text="Momentum explorer", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            self,
            text=(
                "Learning goal: compare how mass and velocity affect momentum. "
                "A negative velocity points left; a positive velocity points right."
            ),
            style="CardBody.TLabel",
            wraplength=620,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 12))

        self.canvas = tk.Canvas(
            self,
            height=240,
            background=PALETTE["surface_soft"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
            bd=0,
        )
        self.canvas.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.canvas.bind("<Configure>", lambda _event: self.refresh_visual())

        controls = ttk.Frame(self, style="Surface.TFrame")
        controls.grid(row=3, column=0, sticky="ew")
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

        summary = ttk.Frame(self, style="Soft.TFrame", padding=(12, 9))
        summary.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 8))
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
        self.mass.trace_add("write", lambda *_args: self.refresh_visual())
        self.velocity.trace_add("write", lambda *_args: self.refresh_visual())
        self.refresh_visual()

    def current_state(self) -> MomentumState:
        """Return the state currently represented by the sliders."""
        return make_momentum_state(self.mass.get(), self.velocity.get())

    def set_values(self, mass: float, velocity: float) -> None:
        """Set values for the lab; useful for reset and GUI tests."""
        state = make_momentum_state(mass, velocity)
        self.mass.set(state.mass)
        self.velocity.set(state.velocity)
        self.refresh_visual()

    def reset(self) -> None:
        """Restore a simple, authored starting example."""
        self.set_values(2.0, 5.0)

    def refresh_visual(self) -> None:
        """Refresh text and drawing immediately after a learner changes a slider."""
        state = self.current_state()
        self.mass_text.set(f"{_format_number(state.mass)} kg")
        velocity = _format_number(abs(state.velocity))
        if state.velocity == 0:
            self.velocity_text.set("0 m/s")
            self.momentum_text.set("Momentum: p = m × v = 0 kg m/s")
        else:
            self.velocity_text.set(f"{velocity} m/s {state.direction}")
            self.momentum_text.set(
                "Momentum: p = m × v = "
                f"{_format_number(abs(state.momentum))} kg m/s {state.direction}"
            )
        self.accessible_description.set(momentum_description(state))
        self._draw(state)

    def _draw(self, state: MomentumState) -> None:
        """Draw a cart and a momentum arrow whose size/direction have meaning."""
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 500)
        height = max(self.canvas.winfo_height(), 240)
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
                text="At rest: no momentum arrow",
                fill=PALETTE["muted"],
                font=("Segoe UI", 11, "bold"),
            )
            return

        arrow_length = 40 + min(210, abs(state.momentum) * 6)
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
                f"Momentum arrow: {_format_number(abs(state.momentum))} kg m/s "
                f"{state.direction}"
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
