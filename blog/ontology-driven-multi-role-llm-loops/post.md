---
layout: single
title: "Ontology-driven multi-role LLM loops in production"
date: 2026-09-07
categories: design
tags: xray ontology agents llm-loops research
description: >
  Field notes from running an ontology-driven multi-role LLM research loop in xray for over a
  month. What works, where ontology non-determinism at generation time bites, and where
  mitigation is heading.
header:
  teaser: /assets/images/teaser.png
  og_image: /assets/images/teaser.png
excerpt: >
  Field notes from running an ontology-driven multi-role LLM research loop in xray for over a
  month. What works, where ontology non-determinism at generation time bites, and where
  mitigation is heading.
---

For over a month, we have been running an ontology-driven multi-role LLM research loop in our
xray production agent. It delivers structured, typed extraction and cleanly composable
multi-role synthesis. It also surfaces the hard engineering problem of ontology non-determinism
at the generation step.

## Introduction

Frank Coyle at UC Berkeley recently gave a talk called
["Why Agentic Systems Need Ontologies"](https://www.youtube.com/watch?v=Sir59K8ZDPU). His broader
argument is neuro-symbolic, pairing a probabilistic LLM with formal ontology reasoning as a
guardrail, and he summed the idea up in one line: *"Pydantic at the door, ontology at the ledger."*

We have been running the lighter, schema-based version of this (typed schema, not the full
RDFS/OWL formalism) as part of our research agent at [xray.llm-works.ai][xray].

## What an ontology is (in this context)

In practice, an ontology is nothing more than a schema of typed entities, their attributes, and
how those entities relate to each other. To make that concrete, consider a query like:

> *What are the current pricing tiers for OpenAI, Anthropic, and Google's flagship API models?*

An ontology for it might look like:

```
Provider: name
Model: name, input_cost_per_1M_tokens, output_cost_per_1M_tokens, context_window
Relationship: Model belongs-to Provider
```

The typed structure earns its keep downstream. Every step past ontology generation gets to
work against the same explicit contract instead of against free-form text, which means
extraction preserves distinctions that plain-prompt approaches routinely collapse (three
related dollar amounts stay separate), and synthesis produces output whose structure any
downstream consumer can rely on programmatically.

## The 5-step loop

Our loop has five steps, all of which are realized through LLM calls:

1. **Ontology generation.** The LLM proposes an ontology based on the input prompt. This turns
   a generic research request into a structure the rest of the loop can work against.
2. **Planning.** The LLM breaks the problem into a set of concrete queries against the ontology.
   Each query targets a specific attribute on a specific entity.
3. **Inner reasoning loop.** Each planned query runs an inner reasoning loop with a set of
   tools, gathering the evidence needed to answer that query. The plan drives the outer
   sequence, and the ontology drives the plan.
4. **Typed extraction.** Results are extracted into the ontology. Values land in named
   attributes on named entities, not in a free-form blob.
5. **Synthesis.** The final summary reads the filled ontology and produces an answer that matches
   its structure.

Realizing every step through an LLM call is deliberate. The different steps carry different
quality-cost tradeoffs, which makes model-per-role a natural configuration. The role separation
also makes each step independently debuggable and replaceable. A single monolithic prompt buys
none of that.

## Implementation

The 5-step loop above is intentionally abstract. A few details from the production version
matter before the analysis below.

**Constrain the ontology-generation step.** Step 1 runs at low temperature behind schema
guardrails and retries. That catches malformed or off-target ontologies before they reach the
planner, but it does not remove run-to-run drift in attribute and type names. Structured-output
constraints on this step are the next thing to try.

**Model per role, not one model for everything.** Extraction and per-query planning tolerate
weaker models cleanly. Ontology generation and final synthesis benefit significantly from a
stronger model. Running the whole loop against a single frontier model works but is wasteful, and
running it against a single weaker model degrades ontology quality in ways that cascade.

**Tools fail, so the loop has to degrade gracefully.** Web search, fetch, and DB queries all
have transient failure rates that show up at scale. This is handled by retries that live at
multiple layers of the stack (inference-side in [llm-infer](/platform/), guard-side in
[llm-saia](/platform/)). When
retries do exhaust, the affected attributes are marked unresolved and synthesis notes the gap
without aborting the run.

**A wrong ontology is expensive.** If step 1 misreads the query, every downstream call is wasted
work. We therefore use the strongest model and the tightest constraints for ontology generation.

**The ontology stays smaller than people expect.** Most queries we have seen resolve into
ontologies with 3 to 8 entity types and somewhere between 5 and 20 attributes in total. Deeper
ontologies are possible, but extraction cost grows roughly linearly in the attribute count per
source, so there is a natural pull toward keeping the schema tight.

## What works well in production

**The planner is purpose-driven.** Because the plan is derived from a typed ontology and not
from the prompt directly, iteration chases exactly the attributes the ontology defines. Drift
into tangents is less likely, and so is premature stopping while attributes are still empty.

**Extraction preserves structure.** Without an ontology, an LLM asked "what's the deal size?"
happily collapses `$X valuation`, `$Y to founders`, and `$Z to investors` into a single number.
With an ontology, those become three distinct attributes on their respective entities, and
downstream code
can actually use them.

**Synthesis composes.** Because the synthesis role knows the ontology, its output follows the
ontology's structure even if the wording varies. That makes multi-role composition
more effective, since any downstream stage can consume the output programmatically, e.g.,
feeding a visualization, chaining another ontology-driven loop, or anything else that processes
the results.

Debugging and tracing also get easier. Because every value lives on a named slot, wrong answers
trace cleanly back to the extraction step that produced them.

## What still needs work

**Ontology non-determinism.** Step 1 produces a different ontology every time, even for the
same prompt. Attribute names and type names drift between runs, and sometimes the number of
types themselves changes. This is the real hard problem, because everything downstream that
assumed a stable schema does not get that stability. A stored artifact from yesterday might not
match
today's ontology for the same query.

**Cost overhead is meaningful but bounded.** Adding ontology generation, planning, typed
extraction, and synthesis on top of a generic tool-loop runs roughly 20 to 30% more expensive at
comparable iteration depth. In our workload the inner tool loop (search + fetch + read) still
dominates, so the cost overhead is manageable. Workloads with cheaper inner loops will feel it
more prominently.

## Where mitigation is heading

Beyond the guardrails mentioned above, a number of further directions came from discussions
with the wider practitioner community. None is a finished answer, but taken together, they point
toward a registry-anchored architecture that quarantines and versions candidates before use.

**Stable registry + novel residue.** A more ambitious direction is to maintain a stable registry
of predicates and types, followed by a deterministic lookup for known classes on every query,
and only invoke the LLM for the *novel residue*. Against a mature registry, most queries would
never touch the model at all. The catch is that queries are arbitrary, and a slightly different
phrasing can map to an entirely new ontology, so the lookup becomes a classification problem
that is expensive to build well. Caching the first ontology generated for a query pattern is
the naive form of the same idea, and buys the same stability at the cost of freezing whatever
the model produced first, validated or not.

**Quarantine and promote.** When the LLM does propose a new class, it does not go straight into
the registry. It sits in quarantine until it passes an admission test, e.g., generate the
candidate, run one extraction round, check that fields fill stably, and only then promote it. A
fill-round-trip is a cheap way to catch a candidate that looked plausible but was actually
incoherent.

**Version + compat.** Each ontology can be treated as a versioned artifact with stable
identifiers and explicit compatibility rules to its downstream consumers. Later queries map
into a version or propose a versioned change; they don't silently redefine the structure that
extraction and synthesis depend on.

**Fixed schema for known domains.** Where the domain is known in advance, the schema can be
written by hand and the generation step dropped entirely. The LLM fills slots but never defines
them, which removes drift at the source. The open case remains the arbitrary query, where the
domain is not known until the request arrives.

What these directions share is a gradual withdrawal of direct LLM authority over schema
generation, towards schemas that are validated, versioned, and reused across queries rather than
generated per query.

## Conclusion

Ontologies are a powerful primitive that elevates the output quality of traditional LLM loops,
by giving them more structure and guarantees. Techniques like multi-role composition,
model-per-role, and slot-level debugging become more reliable when a typed schema is in play,
since planning, extraction, and synthesis all operate against a shared explicit contract. In
our setup, we've observed a ~20-30% cost overhead across the ontology generation, planning,
extraction, and synthesis steps, and this pays for itself in extraction quality. Interest in
ontology-driven design is growing across the practitioner community, and non-determinism at
generation time is where much of the near-term engineering will happen.

## See also

- [xray.llm-works.ai][xray]
- [r/LLMDevs discussion][thread]

[xray]: https://xray.llm-works.ai
[thread]:
https://www.reddit.com/r/LLMDevs/comments/1w4nee4/ontologydriven_multirole_llm_loops_in_production
