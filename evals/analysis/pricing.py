"""Per-token USD billing rates used by generate_graphs.py.

All rates are USD per 1,000,000 tokens, taken directly from Anthropic's
published pricing page (https://platform.claude.com/docs/en/about-claude/pricing),
fetched 2026-08-12 and re-checked 2026-08-26:

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
1-hour TTL; cache reads at 0.1x. Which TTL a given write used is read out of
the archive, never inferred from when the run happened: CodeScribe records the
provider's own split as cache_write_{5m,1h} per loop phase (and
cumulative_cache_creation_{5m,1h}_tokens in the run manifest) whenever the
provider reports one, and cost() bills exactly what is attributed.

Writes an archive leaves unattributed bill at the 5-minute rate. That is exact
for archives predating the split — every cache_control breakpoint was a plain
{"type": "ephemeral"} 5-minute write then — and it is the right default for a
provider that reports no TTL at all, which is every OpenAI-compatible gateway
here. It is a *floor*, not a certainty, for any archive that mixes TTLs without
saying so: parse_csloop marks each row with cache_write_ttl_attributed so a
run priced on that fallback can be told from one priced on recorded data.

The gateway-hosted gpt56sol / gpt56terra deployments are not Anthropic models
and have no entry here on purpose — cost() raises KeyError for them, and
callers must treat those runs' USD cost as not applicable rather than silently
pricing them off someone else's rate card. The same applies to Kimi K3
(oaic-moonshotai/Kimi-K3), which appears in the archived corpus but not in the
current figure scope.
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
    the archive records one, and must not exceed it. Any remainder the archive
    left unattributed is billed at the 5-minute rate (see module docstring).

    Unknown models raise KeyError rather than silently defaulting — a silent
    fallback would misprice a model nobody priced on purpose.
    """
    rates = PRICING[model]
    total_write = int(cache_write_tokens or 0)
    split_1h = int(cache_write_1h_tokens or 0)
    split_5m = int(cache_write_5m_tokens or 0)
    if split_5m + split_1h > total_write:
        raise ValueError(
            f"{model}: TTL-attributed cache writes ({split_5m} 5m + {split_1h} 1h) "
            f"exceed the recorded cache-write total ({total_write}) — the archive "
            "is inconsistent, and billing it would invent tokens"
        )
    unattributed = total_write - split_5m - split_1h
    return (
        input_tokens * rates["input"]
        + output_tokens * rates["output"]
        + (split_5m + unattributed) * rates["cache_write_5m"]
        + split_1h * rates["cache_write_1h"]
        + cache_read_tokens * rates["cache_read"]
    ) / 1_000_000
