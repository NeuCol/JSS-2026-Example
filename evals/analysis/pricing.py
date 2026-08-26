"""Per-token USD billing rates used by generate_graphs.py.

All rates are USD per 1,000,000 tokens, taken directly from Anthropic's
published pricing page (https://platform.claude.com/docs/en/about-claude/pricing),
fetched 2026-08-12:

  Claude Opus 5:   $5 / MTok input,  $25 / MTok output,
                    $6.25 / MTok 5m-cache-write, $10.00 / MTok 1h-cache-write,
                    $0.50 / MTok cache read
  Claude Sonnet 5: $2 / MTok input,  $10 / MTok output,
                    $2.50 / MTok 5m-cache-write, $4.00 / MTok 1h-cache-write,
                    $0.20 / MTok cache read
                    ($2/$10 input/output is Sonnet 5's standing price, not
                    introductory pricing — the previously-scheduled increase
                    to $3/$15 on 2026-09-01 was cancelled.)

Cache writes bill at 1.25x base input for the 5-minute TTL and 2x for the
1-hour TTL. Which one applies depends on the CodeScribe revision a run was
executed under:

  before 2026-08-26 15:09 local  all three cache_control breakpoints were
                                 plain {"type": "ephemeral"} — 5-minute TTL
                                 throughout, so every write bills at 1.25x.
                                 Covers every run through 08-26 14:55.
  from  2026-08-26 15:09 local   the system prompt and the tool schemas carry
                                 ttl "1h" (2x) while the rolling message
                                 breakpoint stays at the 5-minute default.

Runs archived before that revision carry only a single cache_write total with
no TTL split, so cost() treats an unattributed write as a 5-minute write —
exact for those archives, and the right default for any provider that reports
no TTL at all. Runs from the newer revision record
cumulative_cache_creation_{5m,1h}_tokens and are priced exactly.

Kimi K3 (model id oaic-moonshotai/Kimi-K3; the run directory is named
codescribe-kimi-k3-5, which is a naming slip -- the model is K3, not K3.5) and
the gateway-hosted gpt56sol / gpt56terra deployments are not Anthropic models
and have no entry here on purpose — cost() raises KeyError for them, and
callers must treat those runs' USD cost as not applicable rather than silently
pricing them off someone else's rate card.
"""

PRICING = {
    "claude-opus-5": {
        "input": 5.00,
        "output": 25.00,
        "cache_write_5m": 6.25,
        "cache_write_1h": 10.00,
        "cache_read": 0.50,
    },
    "claude-sonnet-5": {
        "input": 2.00,
        "output": 10.00,
        "cache_write_5m": 2.50,
        "cache_write_1h": 4.00,
        "cache_read": 0.20,
    },
}


def cost(
    model,
    input_tokens=0,
    output_tokens=0,
    cache_write_tokens=0,
    cache_read_tokens=0,
    cache_write_5m_tokens=0,
    cache_write_1h_tokens=0,
):
    """Return USD cost for the given token counts under `model`'s rate card.

    cache_write_tokens is the total; the 5m/1h arguments are the TTL split when
    the archive records one. Any remainder is billed at the 5-minute rate.

    Unknown models raise KeyError rather than silently defaulting — a silent
    fallback would misprice a model nobody priced on purpose.
    """
    rates = PRICING[model]
    split_1h = int(cache_write_1h_tokens or 0)
    split_5m = int(cache_write_5m_tokens or 0)
    unattributed = max(0, int(cache_write_tokens or 0) - split_5m - split_1h)
    return (
        input_tokens * rates["input"]
        + output_tokens * rates["output"]
        + (split_5m + unattributed) * rates["cache_write_5m"]
        + split_1h * rates["cache_write_1h"]
        + cache_read_tokens * rates["cache_read"]
    ) / 1_000_000
