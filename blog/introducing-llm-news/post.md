---
layout: single
title: "Agent Release: llm-news — AI-Curated Tech News"
date: 2026-03-31
categories: launch
tags: news llm curation agents
description: >
  An AI news curation service that monitors 50+ sources, summarizes and rates articles, clusters
  them into themes, and produces daily digests — all running on a local 14B model.
header:
  teaser: /assets/images/llm-news-intro.png
  og_image: /assets/images/llm-news-intro.png
excerpt: >
  An AI news curation service that monitors 50+ sources, summarizes and rates articles, clusters
  them into themes, and produces daily digests — all running on a local 14B model.
---

Tech news is fragmented across dozens of sources — RSS feeds, aggregators, social media, research
feeds. Keeping up means scanning hundreds of articles daily, most of which are rewritten press
releases or low-substance hype. We wanted a service that does the filtering for us: pull from
everywhere, surface what actually matters, skip the noise.

It's live at <a href="https://news.llm-works.ai" target="_blank" rel="noopener
noreferrer">news.llm-works.ai</a>.

## What It Does

The service runs a pipeline every hour:

1. **Collect** — pulls articles from 50+ RSS feeds and aggregators covering AI, programming,
   finance, crypto, science, and security
2. **Summarize & rate** — each article gets a 2-3 sentence AI summary and a 1-5 star relevance
   score based on significance, novelty, and substance
3. **Cluster** — related articles are grouped into thematic digests using semantic similarity
4. **Daily summary** — top stories condensed into a short daily digest

Every item links back to its original source. Summaries are AI-generated, not pulled from the
source.

## Personas

Not everyone reads the news the same way. The service offers 10 personas — developer, founder,
investor, researcher, executive, designer, marketer, student, journalist, lawyer — each filtering
and ranking the same article pool differently based on what matters to that role.

A developer's feed surfaces technical releases, benchmarks, and open-source launches. A founder's
feed highlights market moves, competitive signals, and funding rounds. Same source pool, different
signal — the articles that matter to you float to the top.

## Runs Local

All AI tasks — summarization, rating, clustering, and digest generation — run on a local Qwen 2.5
14B model. No article data is sent to third-party AI services.

The pipeline processes 300-500 articles per day on a single GPU. Running local keeps costs fixed
and latency predictable — no rate limits, no per-token billing, no third-party data sharing.

## Built on Our Stack

llm-news is built on our open-source stack:
<a href="https://github.com/serendip-ml/llm-saia" target="_blank" rel="noopener
noreferrer">llm-saia</a> for structured LLM operations (summarization, rating, and clustering all
use [typed verbs](/saia-verbs-for-llm-agents/) with output guards),
<a href="https://github.com/serendip-ml/llm-infer" target="_blank" rel="noopener
noreferrer">llm-infer</a> for model-agnostic inference, and
<a href="https://github.com/serendip-ml/appinfra" target="_blank" rel="noopener
noreferrer">appinfra</a> for service lifecycle. The pipeline swaps between local and remote models
without code changes.

## Try It

Pick a persona that matches how you consume news and browse today's digest at
<a href="https://news.llm-works.ai" target="_blank" rel="noopener
noreferrer">news.llm-works.ai</a>.

Feedback welcome at <a href="https://x.com/serendip_ml" target="_blank" rel="noopener
noreferrer">@serendip_ml</a>.
