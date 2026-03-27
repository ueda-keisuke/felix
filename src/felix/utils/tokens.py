"""Token estimation for context management."""

# Approximate threshold before clearing old tool results (~80k tokens).
# Most models support 128k+; leave headroom for the response.
CONTEXT_THRESHOLD = 80_000

# Number of recent tool-call groups to keep when clearing.
KEEP_RECENT_TOOLS = 5


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English."""
    return len(text) // 4
