"""Safety rules for displaying local and cultural learning context.

The project can store drafts for review, but students must not be shown an
unverified regional claim as if it were an established fact.
"""

from lesson_models import ContextEntry


VERIFIED = "VERIFIED"
COMMUNITY_PROVIDED = "COMMUNITY_PROVIDED"
NEEDS_REVIEW = "NEEDS_REVIEW"


def is_verified_for_student_display(context: ContextEntry) -> bool:
    """Return True only for source-backed context approved for student output."""
    return context.verification_status == VERIFIED and bool(context.source)


def student_context_text(context: ContextEntry | None) -> str | None:
    """Return safe context text, hiding drafts and unverified claims."""
    if context is None or not is_verified_for_student_display(context):
        return None

    source_note = f" Source: {context.source}." if context.source else ""
    return f"{context.text}{source_note}"


def context_availability_notice(context: ContextEntry | None) -> str | None:
    """Give students a useful availability note without exposing draft metadata."""
    if context is None or is_verified_for_student_display(context):
        return None
    return "A verified Sindhudurg or Konkan connection is not available for this lesson yet."
