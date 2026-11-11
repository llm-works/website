---
layout: single
title: "llm-news gets an AI editor for hourly briefings"
kicker: Agent Release
date: 2026-11-11
categories: engineering
tags: news llm agents briefing
description: >
  llm-news now reads 70+ sources every hour and writes a briefing of the day on top of
  its rated feed, with a local model as the editor.
header:
  teaser: /assets/images/news-front.png
  og_image: /assets/images/news-front.png
excerpt: >
  llm-news now reads 70+ sources every hour and writes a briefing of the day on top of
  its rated feed, with a local model as the editor.
---

In March we [launched llm-news](/blog/introducing-llm-news/) as a rated feed: articles from 50+
sources, each with a star rating and a short summary.

Today llm-news reads 70+ sources every hour, around 750 articles on a busy weekday, and writes a
briefing of the day on top of them. The rating, the summaries and the briefing all run on
a local Qwen3.8 27B model.

A briefing written by a model has to earn trust. Most of the work in this release went into keeping
opinion apart from fact, attributing disputed figures to whoever reported them, and building in
safeguards.

## The new front page

The front page at [llm-news.ai](https://llm-news.ai) opens with the stories that carried the day.
The briefing develops through the day as one edition, and the top spot goes to what is new.

**Top story** leads with the day's biggest news. When outlets report different numbers, each
version appears with its outlet. Forecasts and claims are attributed to their source, as in
"Barclays expects" or "the company says".

**Findings** collects research and security write-ups that rarely make the headlines, such as a
study showing that editing fewer than ten neurons can backdoor an LLM.

**By the numbers** pulls the day's figures out of the coverage and puts them side by side, from the
valuation of an upcoming IPO to the count of vulnerabilities in a patch release.

**Tensions** sets two framings of the same story against each other, such as a company's revenue
claims next to leaked documents showing heavy losses.

**Who moved** shows which companies the coverage treated favorably or unfavorably that day. It
reflects the tone of the news, not stock prices.

**The day in short** closes the briefing with a single paragraph that tells the whole day, with
forecasts and claims attributed the same way.

Below the briefing comes every article with its rating. A 💎 marks a gem, a well-rated story that
few outlets picked up, with a short note on its significance.

## Editorial process

The editor works in several passes, and a story makes the briefing only when it holds up across
them. The top story and the day in short get a closer review before publication. If a review fails,
the briefing keeps the previous version.

Every item is checked against the articles it cites before it appears. Analyst notes and vendor
posts count as views.

Everything runs on our own hardware, without any outside AI service.

## Platform

llm-news runs on the [LLM Works platform](/platform/), using
[llm-saia](https://github.com/llm-works/llm-saia),
[llm-infer](https://github.com/llm-works/llm-infer),
[llm-gent](https://github.com/llm-works/llm-gent) and
[appinfra](https://github.com/llm-works/appinfra).

## Availability

[llm-news.ai](https://llm-news.ai) is free. Errors in the briefing can be reported to
[@serendip_ml](https://x.com/serendip_ml) on X.
