"""
Shared formatting helpers for CLI and Streamlit output.
"""


def task_emoji(description: str) -> str:
    """Return an emoji that matches the task type based on keywords."""
    desc = description.lower()
    if any(w in desc for w in ["walk", "exercise", "run", "jog", "stroll"]):
        return "🦮"
    if any(w in desc for w in ["feed", "food", "breakfast", "lunch", "dinner", "meal", "eat"]):
        return "🍖"
    if any(w in desc for w in ["med", "medication", "medicine", "pill", "drug", "heartworm", "flea", "tablet", "dose"]):
        return "💊"
    if any(w in desc for w in ["groom", "brush", "bath", "bathe", "clean", "hair", "nail", "trim"]):
        return "✂️"
    if any(w in desc for w in ["play", "enrich", "toy", "fetch", "game"]):
        return "🎾"
    if any(w in desc for w in ["vet", "appoint", "checkup", "doctor", "clinic", "visit"]):
        return "🏥"
    if any(w in desc for w in ["train", "training", "lesson", "teach"]):
        return "🎓"
    return "📋"


def species_emoji(species: str) -> str:
    """Return an emoji for the given pet species."""
    return {"dog": "🐕", "cat": "🐈", "bird": "🐦", "rabbit": "🐇"}.get(species.lower(), "🐾")


def priority_badge_html(priority: str) -> str:
    """Return an HTML span with a colored badge for the given priority."""
    colors = {
        "high":   ("#fff0f0", "#cc0000"),
        "medium": ("#fff8e1", "#b36b00"),
        "low":    ("#f0fff4", "#2e7d32"),
    }
    bg, fg = colors.get(priority, ("#f5f5f5", "#333"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:4px;font-weight:600;font-size:0.85em;">'
        f'{priority.upper()}</span>'
    )


def status_badge_html(completed: bool) -> str:
    """Return an HTML span with a colored status badge."""
    if completed:
        return (
            '<span style="background:#e8f5e9;color:#2e7d32;padding:2px 8px;'
            'border-radius:4px;font-weight:600;font-size:0.85em;">✅ Done</span>'
        )
    return (
        '<span style="background:#e3f2fd;color:#1565c0;padding:2px 8px;'
        'border-radius:4px;font-weight:600;font-size:0.85em;">⏳ Pending</span>'
    )
