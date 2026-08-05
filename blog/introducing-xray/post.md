---
layout: single
title: "xray — Deep Research with a Knowledge Graph"
kicker: Agent Release
date: 2026-08-05
categories: launch
tags: xray deep-research knowledge-graph ontology agents
description: >
  Deep research that builds a knowledge graph as it works. Reports are derived from structured
  evidence rather than summarized from raw text, and every claim traces back to its sources.
header:
  teaser: /assets/images/xray-intro.png
  og_image: /assets/images/xray-intro.png
excerpt: >
  Deep research that builds a knowledge graph as it works. Reports are derived from structured
  evidence rather than summarized from raw text, and every claim traces back to its sources.
---

Deep research tools today tend to give you a page of links or a paragraph that summarizes them.
What's harder to get at is the underlying structure — which entities are involved, how they
connect, and which claims come from where. Without that, you can't easily tell where a report is
confident, where it's guessing, or where sources disagree.

xray builds that structure as it researches, and the report is derived from it. It's live at
<a href="https://xray.llm-works.ai" target="_blank" rel="noopener noreferrer">xray.llm-works.ai</a>.

## What It Does

As xray researches a question, it builds a knowledge graph out of what it reads. Companies,
people, products, events and metrics become typed nodes. Relationships between them (such as
competitor, acquired-by, correlated-with) become typed edges. Claims are anchored to the sources
that support them and, where relevant, to sources that contradict them.

The report at the end is derived from that graph rather than summarized from raw text. The graph
itself is browsable in the UI, so you can pull apart any claim and see what it's built from.

## Structured Extraction

xray works from a fixed ontology of entity and relationship types. The extractor knows what a
"competitor" edge means, what an "acquired" event looks like, what a "revenue-metric" node
contains. Extraction is constrained rather than free-form paraphrase.

Because the graph has a known shape, xray can run its own output back through it as a self-check.
It flags claims not backed by extracted evidence, sources that disagree, and metrics that lack a
source. A separate self-grading pass then scores the report against the same evidence
structure before it's handed over.

## Built on Our Stack

xray runs end-to-end on our open-source stack:
<a href="https://github.com/llm-works/llm-infer" target="_blank" rel="noopener noreferrer">llm-infer</a>
for model-agnostic inference,
<a href="https://github.com/llm-works/llm-saia" target="_blank" rel="noopener noreferrer">llm-saia</a>
for the typed verbs the KG extractor and self-check are built from, and
<a href="https://github.com/llm-works/appinfra" target="_blank" rel="noopener noreferrer">appinfra</a>
for service lifecycle.

## Try It

Sign in at
<a href="https://xray.llm-works.ai" target="_blank" rel="noopener noreferrer">xray.llm-works.ai</a>.
Free credits are available on sign-up. Credit packs are available for heavier use.

xray is the first agent product built on the LLM Works stack. See also our earlier post on
[llm-news](/blog/introducing-llm-news/), and the
[infrastructure series](/blog/building-agent-infrastructure/) for the substrate it runs on.
