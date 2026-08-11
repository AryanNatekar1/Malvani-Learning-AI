"""Small visual specifications for concepts where a diagram aids learning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSpec:
    """A simple diagram description that a GUI can render without image files."""

    topic: str
    title: str
    description: str


VISUALS = {
    "gravity": VisualSpec(
        topic="gravity",
        title="Gravity: falling object",
        description="A ball with a downward arrow toward Earth.",
    ),
    "momentum": VisualSpec(
        topic="momentum",
        title="Momentum: mass and velocity",
        description="A moving cart with an arrow showing its velocity.",
    ),
    "force": VisualSpec(
        topic="force",
        title="Force: push or pull",
        description="A box with a force arrow acting on it.",
    ),
    "newton": VisualSpec(
        topic="newton",
        title="Newton's second law",
        description="A force arrow acts on a mass and produces acceleration.",
    ),
}


def get_visual(topic: str) -> VisualSpec | None:
    """Return a useful diagram specification, if the topic has one."""
    return VISUALS.get(topic)
