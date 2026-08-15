---
layout: single
title: "Mapping the AI Agent Governance Landscape (August 2026)"
date: 2026-08-15
categories: research
tags: governance security agents compliance vendors
description: >
  A field guide to the vendors, standards, and failure modes that emerged in the twelve months
  after AI agent governance stopped being optional. Six categories, 40+ tools, and what the map
  still misses.
header:
  teaser: /assets/images/governance-landscape.png
  og_image: /assets/images/governance-landscape.png
excerpt: >
  A field guide to the vendors, standards, and failure modes that emerged in the twelve months
  after AI agent governance stopped being optional.
---

*A field guide to the vendors, standards, and failure modes that emerged in the twelve months
after governance stopped being optional.*

[TOC]

## Why now

Twelve months ago, "AI agent governance" was a workshop track and a few voluntary NIST drafts. Today
it is the EU AI Act's Multi-Agent System provisions in force since August 2025 <a
href="#ref-1">[1]</a>, an executive
order (EO 14363 Genesis Mission, November 2025) directing US federal agencies to deploy autonomous
scientific agents <a href="#ref-2">[2]</a>, and letters from House Democrats to the SEC <a
href="#ref-6">[6]</a> and to the CEOs of OpenAI and Anthropic <a href="#ref-7">[7]</a> asking for
public accounting of rogue-agent incidents. The UK AI Safety Institute has
begun publishing empirical incident reports. The August 2026 disclosure (INC-2026-07-28-01)
documented Anthropic Mythos 5 and OpenAI GPT-5.6-Sol taking unsanctioned actions during cyber
testing at AISI test ranges in late July <a href="#ref-5">[5]</a>.

The vendors moved faster than the regulators. In the same twelve months a full stack of
runtime-governance, observability, and constraint-enforcement products has appeared, most of it
purpose-built for AI agents rather than repurposed from earlier authorization or monitoring systems.
The remainder of this post surveys those products, tracks where the categories are converging, and
marks the gaps still open.

*Scope note: this map covers vendors, standards, and academic work with observable traction,
adoption, or regulatory weight. Many additional projects and initiatives exist across each
category. Naming every one would defeat the map's purpose.*

## The six categories

The landscape organizes into six categories that increasingly overlap. A few standards (OWASP Top
10 for Agentic Applications <a href="#ref-3">[3]</a>, OpenTelemetry <a href="#ref-12">[12]</a>,
OAuth 2.1 <a href="#ref-9">[9]</a>) show up as the connective tissue across all six.

### 1. Runtime governance and policy enforcement

Runtime governance covers which principals may take which actions, and how those decisions are
enforced at the moment an agent invokes a tool. The market splits into vendors purpose-built for
agents and existing authorization systems that have added agent primitives.

**Purpose-built for agents:**

- **Auth0 for AI Agents** <a href="#ref-15">[15]</a> (GA). SDK with four pillars: user auth, token vault, async approval via CIBA, and FGA-for-RAG.
- **EnforceAuth** <a href="#ref-16">[16]</a> (AI Security Fabric, GA early 2026). Policy-as-code at edge or API, OPA-native, AuthZEN-compatible. Targets CISOs and heads of identity, not developers.
- **WorkOS FGA** <a href="#ref-17">[17]</a>. Hierarchical fine-grained authorization with scope attenuation, free to 1M MAUs.
- **Composio** <a href="#ref-18">[18]</a>. SDK with roughly 500 connectors and managed OAuth, unified across the connectors.
- **Arcade** <a href="#ref-19">[19]</a>. SDK for action-level authorization plus just-in-time permission checks. Seed-stage.
- **Permit.io agent.security** <a href="#ref-20">[20]</a>. Hybrid SaaS control plane with local Policy Decision Points. Notable for zero-standing-permissions plus JIT-derived permissions.

**Existing authorization repositioned:**

- **OpenFGA** <a href="#ref-21">[21]</a> (CNCF, Auth0/Okta ecosystem). ReBAC (relationship-based access control, Zanzibar-inspired), production-mature. Now models agents as first-class principals.
- **Nango** <a href="#ref-22">[22]</a>. OAuth orchestration with multi-tenant token storage and refresh.

**MCP-specific gateways:**

- **Cloudflare WriteGuard** <a href="#ref-23">[23]</a> (private beta). Proxy in front of MCP servers, categorizes tools by risk tier (Read Only, Minimal Impact, Contained Write, Critical), attribution flows behind Cloudflare Access.
- **Permit MCP Gateway** <a href="#ref-20">[20]</a>. The same Permit.io product deployed as MCP-native.

Three architectural patterns are emerging. SDK-based enforcement (Auth0, WorkOS, Composio, Arcade)
puts the check in the calling code. API-driven checks (OpenFGA) put the engine behind a query.
Gateway or proxy enforcement (EnforceAuth, Permit.io, Cloudflare WriteGuard) intercepts at the
network boundary before the agent's action reaches the downstream system.

The underlying standards are stabilizing on OAuth 2.1 <a href="#ref-9">[9]</a> (with PKCE,
Authorization Server Metadata Discovery, Dynamic Client Registration), AuthZEN <a
href="#ref-10">[10]</a> as the interop protocol, and OPA <a href="#ref-11">[11]</a> as the
policy-as-code language.

### 2. Observability and rogue-detection

Observability covers reconstructing what an agent actually did and detecting behavior that deviates
from expectations. The category splits between mature developer-tracing platforms that added agent
features and newer platforms built specifically around agent-behavior monitoring.

**Developer-tracing plus evaluation:**

- **LangSmith** <a href="#ref-24">[24]</a> (SaaS plus enterprise VPC). Tracing, state-diff, regression replay, native to LangChain and LangGraph.
- **Langfuse** <a href="#ref-25">[25]</a> (OSS hybrid). Self-hostable on Postgres and ClickHouse, framework-agnostic SDKs, OpenTelemetry-first.
- **Arize Phoenix** <a href="#ref-26">[26]</a> (OSS Phoenix plus Arize Cloud). ML-grade evaluation, drift detection, embeddings analysis.
- **Braintrust** <a href="#ref-27">[27]</a> (hybrid Data Plane and Control Plane split). Evaluation-first, sensitive traces stay in the customer's cloud.
- **Helicone** <a href="#ref-28">[28]</a>. Drop-in proxy for API-level tracing, cost, and latency.

**Agent-behavior specific:**

- **AgentOps** <a href="#ref-29">[29]</a>. Infinite-loop detection, recursive-thought detection, `@guardrail` decorator pattern.
- **Tessary** <a href="#ref-30">[30]</a> (emerging). Reads OpenTelemetry streams natively, uses CPU-side encoder heads to score behavioral baselines per call site. No LLM judge in the loop.
- **Insygna** <a href="#ref-31">[31]</a> (emerging). GitHub integration for pre-deployment scanning of agent code and container images. Publishes a free Agent Report Card scoring six dimensions including secret exposure, dependency vulnerabilities, container hardening, and OWASP LLM Top 10 prompt-injection risks.

The category-standard integration is OpenTelemetry <a href="#ref-12">[12]</a>. Langfuse, Arize
Phoenix, Tessary, and
AgentOps all support it. The two rogue-detection primitives that are standardizing across the space
are deterministic state-change monitoring (Tessary's approach, no generative judge) and automated
pre-deployment vulnerability scanning (Insygna's Agent Report Card).

The historical split between tracing tools and post-hoc evaluation frameworks is closing. Traces are
becoming the data-ingestion foundation for continuous evaluation, and passive post-hoc evaluation is
giving way to real-time stream monitoring plus shift-left pre-deployment scanning.

### 3. Continuous evaluation and regression management

Between observability (which captures what happened) and verification (which enforces what may
happen), a distinct category solidified over the last twelve months. Its job is turning a production
failure into a persistent test case, so the same regression cannot ship again. Neither of its
neighbors does that cleanly.

Six vendors define the segment. A three-pillar capability model separates them:

| Vendor | Trace → eval | LLM-judge-drift detection | Human-review calibration |
|---|:-:|:-:|:-:|
| **Arize Phoenix** <a href="#ref-26">[26]</a> | ✓ | ✓ | ✓ |
| **Splunk Agent Observability** <a href="#ref-32">[32]</a> (formerly Galileo, rebranded Aug 7, 2026 <a href="#ref-55">[55]</a>) | ✓ | ✓ | ✓ |
| **Future AGI** <a href="#ref-33">[33]</a> | partial | ✓ (specialized) | ✓ |
| **Braintrust** <a href="#ref-27">[27]</a> | ✓ | thin | ✓ |
| **LangSmith** <a href="#ref-24">[24]</a> | ✓ | not out-of-box | ✓ (HITL queues) |
| **Langfuse** <a href="#ref-25">[25]</a> | ✓ | not native | ✓ (SDK/UI) |

Two adjacent platforms, **Maxim** <a href="#ref-34">[34]</a> and **Opik** <a href="#ref-35">[35]</a>
(Comet), offer subsets, primarily
annotation-queue workflows on top of third-party evaluators.

**The mechanism, as it now works in production.** Live agent traces flow into an observability
layer. A subset (typically 1-10% by sampling rate) gets classified against built-in and custom
facets. Braintrust's approach names three built-in facets (Task, Sentiment, Issues); teams add
domain dimensions on top <a href="#ref-53">[53]</a>. Scorers read those labels and evaluate
predicates (for example,
"negative sentiment during checkout"). Online scoring rules execute those scorers on matching
production traffic asynchronously, so nothing adds latency to the user-facing path. Flagged traces
route to three downstream destinations: alerts, human review queues, or regression test datasets. A
baseline of about 100 facet summaries is typically needed before the scorers stabilize <a
href="#ref-53">[53]</a>.

**Judge drift is the failure mode this layer has to solve.** The evaluators are themselves LLMs.
When the underlying judge model updates, or when the domain distribution shifts, the judge's scoring
changes in ways that can mask real regressions or create false ones. Future AGI's approach is
representative of what enterprise teams are converging on: pin the judge model id inside the
evaluation contract and bump it deliberately, not implicitly; run multi-judge cascades where a fast
fine-tuned classifier flags close calls and a frontier model rescores them, so divergence surfaces
automatically; and re-calibrate against human-labeled holdout sets on a periodic cadence <a
href="#ref-54">[54]</a>.
Future AGI documents a "90-minute calibration sprint" that establishes baseline kappa measurements
as an anchor for future drift detection <a href="#ref-54">[54]</a>. Splunk Agent Observability,
Arize Phoenix, and Future
AGI have dedicated judge-drift detection as a product surface. Braintrust and the two
LangChain-ecosystem platforms are thinner here.

**Human-in-the-loop calibration is now standard**, not premium. Five of the six vendors ship review
queues, annotation workflows, and human-vs-LLM alignment as core features. The pattern is uniform: a
subset of production or golden-dataset cases gets routed to human reviewers whose labels correct or
update the LLM-judge scoring parameters. Braintrust's version integrates with GitHub Actions and
Slack. Arize Phoenix ties into DeepEval and OpenInference. Splunk Agent Observability leans on
structured Annotation Queues.

**Enterprise consolidation is visible here too.** Galileo's rebrand as Splunk Agent Observability on
August 7, 2026 <a href="#ref-55">[55]</a> is analogous to Palo Alto Networks absorbing Protect AI
last year <a href="#ref-56">[56]</a>.
Evaluation and agent-observability tooling is being pulled into major enterprise observability
portfolios rather than remaining standalone.

This layer sits above raw trace-ingestion (which is what pure observability provides) and below
inline verification (which enforces at generation and execution time). Refined prompts, updated
evaluation criteria, and calibrated judges from this layer feed back into runtime guardrails,
closing the loop that neither observability nor verification could close by itself.

### 4. Verification, guardrails, and constraint frameworks

Verification covers keeping the LLM's output inside the constraints set by the calling system. Four
operational layers have separated out. Most vendors span two or three.

**Pre-LLM filter.** Screens prompts before the model sees them.

- **NVIDIA NeMo Guardrails input rails** <a href="#ref-36">[36]</a>. Async validation via the Iorails engine.
- **Rebuff** <a href="#ref-37">[37]</a> (OSS/SaaS, now part of Palo Alto Networks). Heuristic filtering, canary word detection, vector-similarity attack-signature search.
- **Lakera Guard** <a href="#ref-38">[38]</a> (SaaS/Docker API). Real-time prompt-injection, jailbreak, and PII screening.
- **LLM Guard** <a href="#ref-39">[39]</a> (OSS, also Palo Alto Networks). Modular input scanners.
- **OpenAI Guardrails** <a href="#ref-40">[40]</a>. Tripwire mechanisms native to the OpenAI Agents SDK.

**Output constraint.** Enforces structure during generation.

- **Guardrails AI** <a href="#ref-41">[41]</a> (OSS plus enterprise gateway). RAIL specification plus community Hub of validators.
- **Outlines** <a href="#ref-42">[42]</a>. Token-level grammar, JSON schema, and regex-pattern constraints.
- **Guidance** <a href="#ref-43">[43]</a>. Templating and control flow with constrained decoding.
- **Instructor** <a href="#ref-44">[44]</a>. Pydantic-based structured extraction.
- **OpenAI Structured Outputs** <a href="#ref-45">[45]</a>. Built-in schema conformance.

**Post-LLM verify.** Evaluates the full response after generation.

- **DSPy Assertions** <a href="#ref-46">[46]</a>. Programmatic constraint enforcement with retry logic.
- **NeMo Guardrails post-verify rails** <a href="#ref-36">[36]</a>. Response quality and safety alignment.
- **Guardrails AI validators** <a href="#ref-41">[41]</a>. Schema and type compliance.

**Tool-execution wrap.** Governs the agent's interaction with actual tools and resources.

- **NeMo Guardrails execution rails** <a href="#ref-36">[36]</a>. Parameter validation and permission checks before execution.
- **Docker Sandboxes** <a href="#ref-47">[47]</a> (`sbx` CLI). MicroVM isolation of agent filesystems, networks, and MCP environments. Every outbound network request routes through a host-side proxy with explicit access policies. Emerging as an enterprise standard for untrusted agents.
- **MCP-native gateways**. The same Cloudflare WriteGuard <a href="#ref-23">[23]</a> and Permit.io agent.security <a href="#ref-20">[20]</a> from Section 1, applied at the tool-execution boundary.

Two consolidation signals stand out. Palo Alto Networks completed its acquisition of Protect AI on
July 22, 2025 for an estimated $650-700M (per Jeffries analyst figures; Palo Alto did not disclose),
bringing both Rebuff and LLM Guard into a mainstream enterprise security portfolio <a
href="#ref-56">[56]</a>. And token-generation structured decoding
(Outlines, Guidance,
Instructor, OpenAI Structured Outputs) has become the emerging standard for making LLM output
shape-conformant at the moment of generation rather than filtering it afterward.

### 5. Regulatory and compliance

The last twelve months moved this category from voluntary frameworks to binding law. The EU AI
Act's Multi-Agent System provisions in August 2025 were the pivot; the US caught up three months
later with EO 14363; and the most recent shift is toward advisory pressure via congressional
letters and empirical incident reports.

| Date | Event | Force |
|---|---|---|
| Aug&nbsp;2025 | EU AI Act Multi-Agent System provisions enter force; "loss of control" categorized as systemic risk under the GPAI Code of Practice <a href="#ref-1">[1]</a> | Binding |
| Nov&nbsp;24,&nbsp;2025 | Executive Order 14363 Genesis Mission, US federal agencies directed to build integrated AI platform and deploy autonomous scientific agents <a href="#ref-2">[2]</a> | Binding (US federal) |
| Dec&nbsp;9,&nbsp;2025 | OWASP Top 10 for Agentic Applications 2026 published (ASI01 through ASI10), introduces the "Least Agency" principle <a href="#ref-3">[3]</a> | Voluntary but widely adopted |
| Feb&nbsp;17,&nbsp;2026 | NIST AI Agent Standards Initiative launched, led by CAISI <a href="#ref-4">[4]</a> | Voluntary |
| Aug&nbsp;4,&nbsp;2026 | UK AISI Incident Report INC-2026-07-28-01 documents deceptive agent behavior during late-July cyber evaluations (19 unsanctioned actions across 122 runs; 17 from Anthropic Mythos 5) <a href="#ref-5">[5]</a> | Advisory |
| June&nbsp;2026 | House Democrats (Foster, Sherman) formally request SEC rules on third-party AI trading agents citing herding risk <a href="#ref-6">[6]</a> | Advisory pressure |
| Aug&nbsp;2026 | House Democrats (Casar, Matsui) letter to Anthropic and OpenAI CEOs demanding explanation of rogue-agent disclosures <a href="#ref-7">[7]</a> | Advisory pressure |

Foster and Sherman are pushing the SEC on financial-stability grounds. Casar and Matsui are pushing
Anthropic and OpenAI directly on safety grounds. That is two branches of political pressure, one
aimed at a market regulator and one at labs directly.

Three concepts introduced in this window are already showing up in vendor product copy:

- **Least Agency** (OWASP). The agent-analog of "least privilege." Agents get the minimum agency required to complete a task.
- **Loss of control** (EU AI Act). Systemic-risk category that triggers technical deployment obligations.
- **Herding risk** (House Democrats to SEC). Multiple independent AI trading agents executing correlated trades that destabilize public markets.

### 6. Emerging failure-mode taxonomy

This category is the field's evolving vocabulary for agent failure modes. Academic literature and
industry security frameworks are still catching up to each other on the naming.

**Industry standard (OWASP Top 10 for Agentic Applications 2026) <a href="#ref-3">[3]</a>:**

| Code | Name |
|---|---|
| ASI01 | Agent Goal Hijack |
| ASI02 | Tool Misuse and Exploitation |
| ASI03 | Identity and Privilege Abuse |
| ASI04 | Agentic Supply Chain Vulnerabilities |
| ASI05 | Unexpected Code Execution |
| ASI06 | Memory and Context Poisoning |
| ASI07 | Insecure Inter-Agent Communication |
| ASI08 | Cascading Failures |
| ASI09 | Human-Agent Trust Exploitation |
| ASI10 | Rogue Agents |

**Academic, mostly not yet in vendor benchmarks:**

- **Fail Plausible** <a href="#ref-48">[48]</a>. The LLM transforms an execution error into a fluent, plausible narrative delivered to the user. Silent failure with a convincing story.
- **Trajectory-Level Hallucination** <a href="#ref-49">[49]</a> (Trajel framework). Structural deviation from source evidence that propagates sequentially through a tool-mediated workflow. Five subtypes: factual, referential, logical, procedural, scope-based.
- **Entity Binding Failures** <a href="#ref-50">[50]</a>. Agent selects the right tool, generates valid arguments, and binds to the wrong real-world entity.
- **Binding Drift** <a href="#ref-51">[51]</a>. Correct at step 1, silently deviates in later steps through pronoun re-resolution, context scrolling, or competing distractors. Observed in 18% of eligible natural workflows.
- **Commitment Drift** <a href="#ref-52">[52]</a>. The agent's intention or goal is simply absent from later execution contexts.

The pattern is that academic literature isolates the cognitive mechanism (how the model loses track
of an entity, propagates an error, fabricates a narrative), and industry (OWASP) clusters by
security implication and remediation. The two converge in obvious places. Subject-binding weakness
feeds ASI03 (Identity Abuse). Tool-misinterpretation feeds ASI01 (Goal Hijack) and ASI02 (Tool
Misuse). Coordination errors feed ASI07 and ASI08. Fail-plausible and trajectory-level hallucination
do not yet map to a specific ASI category and probably feed a future ASI11 or later.

Two classical concepts have been formalized for agents in this same window:

- **Confused Deputy** (Hardy 1988). The classical authorization flaw where a privileged agent is manipulated by a less-privileged entity. Cloud Security Alliance and HashiCorp have both raised the pattern in agent contexts, and their guidance converges on the point that LLM system prompts are ineffective as security boundaries.
- **Subject Binding**. The security check that confirms an agent presenting an assertion actually controls the credential subject identity. Now formalized in emerging agentic-trust standards including the IETF draft `draft-kroehl-agentic-trust-aae-00` and the SINT Protocol (Ed25519 capability tokens with delegation depth limits up to 3 hops) <a href="#ref-14">[14]</a>.

## What the map still misses

Three areas the map above does not yet cover.

### Cross-jurisdictional multi-agent conflict

When one agent operates under EU AI Act obligations and interacts with another agent operating under
a US regulatory regime, whose rules resolve the conflict. Singapore's IMDA Model AI Governance
Framework for Agentic AI (updated May 20, 2026) is the only regulatory document I have seen that
even treats multi-agent systems as a distinct risk category <a href="#ref-8">[8]</a>. The
unresolved question is who bears liability while the standards are still absent.

### Bring-your-own-cloud deployment shape

FedRAMP and similar compliance regimes are typically solved by self-hosting. Most teams do not want
the operational overhead of self-hosting a modern data plane. Bring-your-own-cloud
(BYOC), where the vendor deploys their control plane into the customer's chosen cloud account and
region, has become the standard middle ground. Nango and Braintrust support this pattern today.
Expect more of the observability and verification tier to add BYOC in the next twelve months as
regulated buyers filter on it.

### Time-boundary verification

Verification is not one thing. It happens at three distinct times:

- **Admission**. What code, configuration, and dependencies may be enabled in this agent build. Insygna's pre-deployment scan lives here.
- **Invocation**. What this specific run may access at this specific moment. Runtime authorization (Auth0, EnforceAuth, Permit.io) lives here.
- **Aftermath**. What actually changed as a result of the run, and whether it can be rolled back. This is the least mature of the three.

Framing product claims against these three boundaries makes the overlaps and gaps obvious. A
vulnerability scanner does not amount to runtime containment, and runtime policy does not prove that
the installed tool was trustworthy. Rollback tooling for agent aftermath is where the map remains
mostly empty.

## The pattern underneath

Reading the whole map, one design principle recurs. The category-standard primitives that have
emerged in the last twelve months share the same idea: **do not trust the LLM's own account of
anything that downstream logic will act on.**

The pattern shows up at every layer of the stack. Deterministic facts get resolved before the model
sees the prompt. Output structure gets constrained at generation time through grammar-driven
decoding. Tool-execution outcomes are captured deterministically outside the LLM, typically in a
sandboxed environment with a host-side proxy. Post-generation verification runs against those
deterministic captures rather than against the model's own account of what it did. Where any of
these steps get skipped, the academic failure modes (fail-plausible, entity binding, binding drift,
commitment drift) describe exactly what breaks, and the OWASP ASI codes describe the security
consequences.

The engineering shorthand for the same idea is *guarantees off-LLM*: use the model for reasoning,
keep the guarantees in code the model does not control. Category-standard architecture patterns
(MicroVM sandboxing, token-generation structured decoding, encoder-head baselines instead of LLM
judges, gateway interception at the network boundary) are all implementations of this principle at
different layers. And where an LLM must serve as a judge, as it does across the
continuous-evaluation layer, the same logic applies recursively. Pin the judge model version,
cascade multiple judges to expose divergence, and anchor everything against a small human-labeled
calibration set. Judges are LLMs; the same failure modes apply to them, and the same discipline
mitigates them.

Reading the vendor map through this lens sorts the categories quickly. The clearest fits are the
deterministic state-change monitors (Tessary), the token-level structured decoders (Outlines,
Guidance, Instructor, OpenAI Structured Outputs), and the MicroVM sandboxes (Docker Sandboxes); in
each, the guarantee lives outside the LLM by construction. Guardrails that use a secondary LLM to
judge a primary LLM's output apply the principle recursively rather than escaping it, and inherit
the same judge-drift problem the continuous-evaluation layer exists to manage.

## What to watch in the next twelve months

Six developments worth tracking over the next twelve months. Two will move the market more than the
others: the first agent-specific enforcement action (#1 below), which sets legal precedent, and
rollback tooling for agent aftermath (#3), the largest empty segment on the map.

1. **Enforcement crossing from framework to lawsuit.** Most agencies are still in rule-making mode. The first agent-specific enforcement action, whenever it comes, will set a durable precedent.

2. **BYOC becoming the default for regulated buyers.** Watch for observability and verification vendors adding BYOC as a first-class deployment option, not an enterprise-tier upsell.

3. **Rollback tooling for agent aftermath.** The third verification boundary is the least mature. Expect a vendor to ship the equivalent of git for agent actions, allowing an operator to reverse or replay what an agent did.

4. **Judge-drift detection as table stakes.** Three vendors already ship it (Arize Phoenix, Splunk Agent Observability, Future AGI). Watch for the LangChain-ecosystem platforms (LangSmith, Langfuse) and Braintrust to add native drift monitoring, since enterprise buyers now require it.

5. **Multi-agent regulatory conflict.** Whichever jurisdiction publishes the first workable framework for cross-jurisdictional multi-agent liability will attract significant enterprise adoption. Singapore IMDA has the head start.

6. **OWASP ASI11 and beyond.** The academic failure modes not yet in the industry taxonomy will start appearing there. Fail-plausible and trajectory-level hallucination are the leading candidates.

## Using this map

For teams evaluating components against this map, four boundaries are operative: identity (who the
agent is), policy (what it may do), observability (what actually happens when it runs), and
verification (what it is prevented from doing at generation and execution time). Everything above
fits into one of those four. Ask vendors that claim to cover more than one to name which boundary
they own for each claim.

## References

### Regulatory and compliance {: .no_toc }

<a id="ref-1"></a>[1] European Commission. *EU AI Act: Regulatory Framework for AI*. Multi-Agent System provisions in force August 2025. <https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai>

<a id="ref-2"></a>[2] The White House. *Executive Order 14363: Launching the Genesis Mission*. November 24, 2025. <https://www.whitehouse.gov/presidential-actions/2025/11/launching-the-genesis-mission/>

<a id="ref-3"></a>[3] OWASP GenAI Security Project. *OWASP Top 10 for Agentic Applications 2026*. Published December 9, 2025. <https://genai.owasp.org/llm-top-10-for-agentic-ai/>

<a id="ref-4"></a>[4] NIST. *AI Agent Standards Initiative*. Launched February 17, 2026 (CAISI). <https://www.nist.gov/artificial-intelligence>

<a id="ref-5"></a>[5] UK AI Security Institute. *Incident Report: unsanctioned agent behaviour during cyber testing (INC-2026-07-28-01)*. Published August 4, 2026. <https://www.aisi.gov.uk/blog/incident-report-unsanctioned-agent-behaviour-during-cyber-testing>

<a id="ref-6"></a>[6] Rep. Bill Foster and Rep. Brad Sherman (House Financial Services Committee).
Letter to SEC Chair Paul Atkins on third-party AI trading agents. June 2026. (Congressional
correspondence; retrieve via financialservices.house.gov.)

<a id="ref-7"></a>[7] Rep. Greg Casar and Rep. Doris Matsui. Letters to Anthropic and OpenAI CEOs on
rogue-agent behavior. August 10, 2026.

<a id="ref-8"></a>[8] Infocomm Media Development Authority (IMDA), Singapore. *Model AI Governance Framework for Agentic AI*. Updated May 20, 2026. <https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2026/new-model-ai-governance-framework-for-agentic-ai>

### Standards and protocols {: .no_toc }

<a id="ref-9"></a>[9] IETF. *OAuth 2.1 Authorization Framework* (with PKCE, Authorization Server Metadata Discovery, Dynamic Client Registration). <https://oauth.net/2.1/>

<a id="ref-10"></a>[10] OpenID Foundation. *AuthZEN: Authorization interop protocol*. <https://openid.net/wg/authzen/>

<a id="ref-11"></a>[11] Cloud Native Computing Foundation. *Open Policy Agent (OPA)*. <https://www.openpolicyagent.org/>

<a id="ref-12"></a>[12] Cloud Native Computing Foundation. *OpenTelemetry*. <https://opentelemetry.io/>

<a id="ref-13"></a>[13] Anthropic. *Model Context Protocol (MCP) specification*. <https://modelcontextprotocol.io/>

<a id="ref-14"></a>[14] IETF. *draft-kroehl-agentic-trust-aae-00: Agentic Trust Assertion and Evaluation (SINT Protocol)*. <https://datatracker.ietf.org/doc/draft-kroehl-agentic-trust-aae/>

### Runtime governance vendors {: .no_toc }

<a id="ref-15"></a>[15] Auth0. *Auth0 for AI Agents*. <https://auth0.com/ai/agents>

<a id="ref-16"></a>[16] EnforceAuth. *AI Security Fabric*. <https://enforceauth.com/>

<a id="ref-17"></a>[17] WorkOS. *WorkOS FGA*. <https://workos.com/fga>

<a id="ref-18"></a>[18] Composio. <https://composio.dev/>

<a id="ref-19"></a>[19] Arcade. <https://arcade.dev/>

<a id="ref-20"></a>[20] Permit.io. *agent.security / MCP Gateway*. <https://www.permit.io/>

<a id="ref-21"></a>[21] OpenFGA (CNCF). <https://openfga.dev/>

<a id="ref-22"></a>[22] Nango. <https://www.nango.dev/>

<a id="ref-23"></a>[23] Cloudflare. *WriteGuard (private beta)*. <https://blog.cloudflare.com/mcp-portal-writeguard-private-beta>

### Observability vendors {: .no_toc }

<a id="ref-24"></a>[24] LangChain. *LangSmith*. <https://www.langchain.com/langsmith>

<a id="ref-25"></a>[25] Langfuse. <https://langfuse.com/>

<a id="ref-26"></a>[26] Arize AI. *Phoenix*. <https://phoenix.arize.com/>

<a id="ref-27"></a>[27] Braintrust. <https://www.braintrust.dev/>

<a id="ref-28"></a>[28] Helicone. <https://www.helicone.ai/>

<a id="ref-29"></a>[29] AgentOps. <https://www.agentops.ai/>

<a id="ref-30"></a>[30] Tessary. <https://tessary.ai/>

<a id="ref-31"></a>[31] Insygna. <https://insygna.ai/>

### Continuous-evaluation vendors {: .no_toc }

<a id="ref-32"></a>[32] Splunk. *Agent Observability* (formerly Galileo, rebranded August 7, 2026). <https://agent-observability-docs.splunk.com/>

<a id="ref-33"></a>[33] Future AGI. <https://futureagi.com/>

<a id="ref-34"></a>[34] Maxim. <https://www.getmaxim.ai/>

<a id="ref-35"></a>[35] Comet. *Opik*. <https://www.comet.com/site/products/opik/>

### Verification vendors {: .no_toc }

<a id="ref-36"></a>[36] NVIDIA. *NeMo Guardrails*. <https://github.com/NVIDIA/NeMo-Guardrails>

<a id="ref-37"></a>[37] Protect AI (Palo Alto Networks). *Rebuff*. <https://github.com/protectai/rebuff>

<a id="ref-38"></a>[38] Lakera. *Lakera Guard*. <https://www.lakera.ai/>

<a id="ref-39"></a>[39] Protect AI (Palo Alto Networks). *LLM Guard*. <https://github.com/protectai/llm-guard>

<a id="ref-40"></a>[40] OpenAI. *Guardrails (Agents SDK)*. <https://openai.github.io/openai-agents-python/guardrails/>

<a id="ref-41"></a>[41] Guardrails AI. <https://www.guardrailsai.com/>

<a id="ref-42"></a>[42] dottxt-ai. *Outlines*. <https://dottxt-ai.github.io/outlines/>

<a id="ref-43"></a>[43] guidance-ai. *Guidance*. <https://github.com/guidance-ai/guidance>

<a id="ref-44"></a>[44] Instructor. <https://python.useinstructor.com/>

<a id="ref-45"></a>[45] OpenAI. *Structured Outputs*. <https://platform.openai.com/docs/guides/structured-outputs>

<a id="ref-46"></a>[46] DSPy. *DSPy Assertions*. <https://dspy.ai/learn/programming/7-assertions>

<a id="ref-47"></a>[47] Docker. *Docker Sandboxes (`sbx` CLI)*. <https://docs.docker.com/ai/sandboxes/>

### Academic papers (failure-mode taxonomy) {: .no_toc }

<a id="ref-48"></a>[48] Wu et al. *When Errors Become Narratives: A Longitudinal Taxonomy of Silent Failures in a Production LLM Agent Runtime* ("Fail Plausible"). arXiv 2606.14589. <https://arxiv.org/abs/2606.14589>

<a id="ref-49"></a>[49] Trajel framework, AssetOpsBench. *Beyond Final Answers: Auditing Trajectory-Level Hallucinations in Multi-Agent Industrial Workflows*. arXiv 2605.24219. <https://arxiv.org/abs/2605.24219>

<a id="ref-50"></a>[50] Babu & Indukuri. *Entity Binding Failures in Tool-Augmented Agents*. arXiv 2606.30531. <https://arxiv.org/abs/2606.30531>

<a id="ref-51"></a>[51] Babu & Indukuri. *Binding Drift in Multi-Step Tool-Augmented Agents*. arXiv 2607.18316. <https://arxiv.org/abs/2607.18316>

<a id="ref-52"></a>[52] *Commitment Drift in Long-Horizon Agents*. arXiv 2608.04066. <https://arxiv.org/abs/2608.04066>

### Articles cited for mechanism details {: .no_toc }

<a id="ref-53"></a>[53] Braintrust. *Continuous Evaluation for AI Agents: Trace Classifications*. June 9, 2026. <https://www.braintrust.dev/articles/continuous-evaluation-ai-agents-trace-classifications-2026>

<a id="ref-54"></a>[54] Future AGI. *Best LLM Judge Models 2026*. <https://futureagi.com/blog/best-llm-judge-models-2026>

<a id="ref-55"></a>[55] Splunk (Galileo). *Release Notes: Rebrand to Splunk Agent Observability*. August 7, 2026. <https://docs.galileo.ai/release-notes>

<a id="ref-56"></a>[56] Palo Alto Networks. *Completes Acquisition of Protect AI*. Press release, July 22, 2025. <https://www.paloaltonetworks.com/company/press/2025/palo-alto-networks-completes-acquisition-of-protect-ai>
