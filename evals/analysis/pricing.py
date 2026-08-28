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

The gateway-hosted gpt56sol / gpt56terra deployments run OpenAI's gpt-5.6-sol
and gpt-5.6-terra. Their rates come from OpenAI's published pricing page
(https://developers.openai.com/api/docs/pricing), fetched 2026-08-28, at the
STANDARD service tier and the SHORT context column:

  gpt-5.6-sol:   $4 / MTok input, $20 / MTok output,
                  $5.00 / MTok cache write, $0.40 / MTok cache read
  gpt-5.6-terra: $2 / MTok input, $12 / MTok output,
                  $2.50 / MTok cache write, $0.20 / MTok cache read

Four things about those two choices, since both are assumptions rather than
readings:

  - Service tier. The page documents Standard, Batch, Flex and Fast mode but
    does not say which applies when `service_tier` is omitted. Batch and Flex
    are half Standard and Fast mode is double it, so the choice moves the
    number by 2x in either direction. The loop issues ordinary synchronous
    chat-completion calls and sets no service_tier, and Standard is the only
    tier that does not require asking for it, so Standard is what is billed
    here.
  - Context tier. The page prices short and long context separately but never
    states the boundary for the 5.6 family; the only threshold it names
    anywhere is a 272K annotation on the previous generation. Peak per-request
    context is not archived (the loop records per-phase aggregates, not
    per-request), but it can be bounded: cache reads chain monotonically
    within a phase, so summing them over a phase's N iterations puts the final
    request near 2*sum/N, which across every gpt56sol phase in the corpus tops
    out around 134K tokens. That is below the only boundary the page hints at,
    so the short column is used. If some request did cross into long context,
    these figures are a floor.
  - Cache-write TTL. OpenAI publishes one cache-write rate with no TTL split,
    so cache_write_5m and cache_write_1h are set to the same value below and
    the attribution logic in cost() cannot change the answer for these models.
  - The sol rates are described on the page as discounted "at least through
    November 21, 2026". The runs priced here predate that date, so the
    discounted rate is the correct one to apply to them.

These are list rates for the underlying OpenAI models. The runs reached them
through an OpenAI-compatible gateway whose own margin is not public, so as with
the Anthropic figures these are reference costs for comparison rather than
charges incurred.

Kimi K3 (oaic-moonshotai/Kimi-K3) appears in the archived corpus but not in the
current figure scope, and still has no entry here — cost() raises KeyError for
it, and callers must treat its USD cost as not applicable rather than silently
pricing it off someone else's rate card.
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
    # OpenAI publishes a single cache-write rate, so both TTL slots carry it.
    "oaic-gpt56sol": {
        "input": 4.00,
        "output": 20.00,
        "cache_write_5m": 5.00,
        "cache_write_1h": 5.00,
        "cache_read": 0.40,
    },
    "oaic-gpt56terra": {
        "input": 2.00,
        "output": 12.00,
        "cache_write_5m": 2.50,
        "cache_write_1h": 2.50,
        "cache_read": 0.20,
    },
}

# Rate cards that are not Anthropic's. Callers that describe pricing in prose
# (figure captions, table notes) need to say whose rates a run was priced on,
# and hardcoding a model list in each of them goes stale the moment one is
# added here.
NON_ANTHROPIC = frozenset({"oaic-gpt56sol", "oaic-gpt56terra"})


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
