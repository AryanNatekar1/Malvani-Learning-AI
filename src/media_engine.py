"""Small visual specifications for concepts where a diagram aids learning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualSpec:
    """A local visual resource that a GUI can render without image files."""

    topic: str
    title: str
    description: str
    learning_goal: str
    interaction: str | None = None


VISUALS = {
    "gravity": VisualSpec(
        topic="gravity",
        title="Gravity: falling object",
        description="A ball with a downward arrow toward Earth.",
        learning_goal="Notice that the arrow shows the direction of Earth's pull.",
    ),
    "momentum": VisualSpec(
        topic="momentum",
        title="Momentum: mass and velocity",
        description="Use the mass and velocity controls to compare momentum.",
        learning_goal="See how changing mass or velocity changes momentum and direction.",
        interaction="momentum_lab",
    ),
    "force": VisualSpec(
        topic="force",
        title="Force: push or pull",
        description="A box with a force arrow acting on it.",
        learning_goal="Identify the object and the direction of the applied force.",
    ),
    "newton": VisualSpec(
        topic="newton",
        title="Newton's second law",
        description="A force arrow acts on a mass and produces acceleration.",
        learning_goal="Relate force, mass, and acceleration in one diagram.",
    ),
}


def get_visual(topic: str) -> VisualSpec | None:
    """Return a useful diagram specification, if the topic has one."""
    return VISUALS.get(topic)
