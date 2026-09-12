"""Read one Claude Code assistant message's `usage` block into the field names
the csloop parser already normalizes to.

Both Claude Code harnesses (ccworkflow, ccloop) and per_file_effort read usage
out of the same transcript shape, so the mapping lives here once rather than
three times.

WHY THIS EXISTS RATHER THAN A DICT ACCESS. The transcript records strictly more
than the corpus was reading, and the parts it was dropping are exactly the
parts csloop records explicitly — so the two harnesses looked less comparable
than they are:

  cache-write TTL split
      `usage.cache_creation.ephemeral_{5m,1h}_input_tokens`. pricing.cost bills
      any unattributed cache write at the 5-minute rate, documented as "a
      floor, not a certainty" for an archive that mixes TTLs without saying so.
      The Claude Code archives do say so, on every message. Verified across all
      13,978 assistant messages in the corpus: `ephemeral_5m + ephemeral_1h`
      equals `cache_creation_input_tokens` exactly, every time, and 1h is zero
      throughout — so attributing the split changes no number today. It changes
      the PROVENANCE: `cache_write_ttl_attributed` now means the same thing for
      a ccworkflow row as it already did for a csloop one, and a future run that
      does use 1-hour writes (billed at 2x base rather than 1.25x) is priced
      from the archive instead of from the fallback.

  reasoning tokens
      `usage.output_tokens_details.thinking_tokens` — 4.08M across ccworkflow
      and 462k across ccloop, previously unread, where parse_csloop has always
      surfaced `usage.reasoning`. This is a BREAKDOWN of output_tokens, not an
      addition to them: Anthropic bills thinking inside output. It is reported,
      never added to a cost.

  service tier
      `usage.service_tier`. pricing.py has to ASSUME a tier for the
      OpenAI-compatible runs (see its docstring on why "standard" is the only
      defensible default there). The Anthropic archives record it, so for those
      runs it is a reading and can be checked rather than assumed.
"""


def cc_usage(message):
    """One assistant message's `message` dict -> normalized usage fields.

    Field names match parse_csloop's row keys so a caller can treat a
    ccworkflow, ccloop or csloop row the same way.
    """
    usage = message.get("usage") or {}
    split = usage.get("cache_creation") or {}
    write_5m = split.get("ephemeral_5m_input_tokens", 0) or 0
    write_1h = split.get("ephemeral_1h_input_tokens", 0) or 0
    details = usage.get("output_tokens_details") or {}

    return {
        "input_tokens": usage.get("input_tokens", 0) or 0,
        "output_tokens": usage.get("output_tokens", 0) or 0,
        "cache_write_tokens": usage.get("cache_creation_input_tokens", 0) or 0,
        "cache_read_tokens": usage.get("cache_read_input_tokens", 0) or 0,
        "cache_write_5m_tokens": write_5m,
        "cache_write_1h_tokens": write_1h,
        # False when the message carried no `cache_creation` sub-object at all,
        # in which case pricing falls back to the 5-minute rate exactly as it
        # does for a csloop phase that predates the split.
        "cache_write_ttl_attributed": bool(split),
        "reasoning_tokens": details.get("thinking_tokens", 0) or 0,
        "service_tier": usage.get("service_tier"),
    }


ACCUMULATED_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_write_tokens",
    "cache_read_tokens",
    "cache_write_5m_tokens",
    "cache_write_1h_tokens",
    "reasoning_tokens",
)
