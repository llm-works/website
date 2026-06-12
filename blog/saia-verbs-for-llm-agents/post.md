---
layout: single
title: "A Verb Layer for Agent-LLM Communication"
date: 2026-03-27
categories: design
tags: agents saia llm protocol
description: >
  Agents are code that interacts with LLMs. LLMs speak free-form text. How should this
  communication be structured? Current approaches, trade-offs, and what we're building.
header:
  teaser: /assets/images/teaser.svg
  og_image: /assets/images/teaser.svg
excerpt: >
  Agents are code that interacts with LLMs. LLMs speak free-form text. How should this
  communication be structured?
---

Building agents means asking LLMs to verify claims, critique drafts, decompose tasks—but the only
interface is "send text, get text back." The result is hand-rolled prompts, bespoke response
parsing,
and reimplemented retry logic for every operation. There's a missing layer. Here's how current tools
approach the problem, and what we're building instead.

## Current Approaches

**Raw prompting.** The simplest approach: concatenate strings, send to model, parse the response.
LangChain, most tutorials, and most production agents work this way.

```python
prompt = f"Given this code:\n{code}\n\nDoes it handle null safely? Answer yes or no."
response = await llm.complete(prompt)
is_safe = "yes" in response.lower()
```

**Strengths**: flexible, no abstractions to learn. **Gap**: no structure—every call requires
hand-parsing and reimplemented error handling.

**Tool/function calling.** OpenAI and Anthropic provide structured tool calling: define a schema,
the model returns JSON matching that schema.

```python
tools = [{
    "name": "check_null_safety",
    "parameters": {
        "type": "object",
        "properties": {
            "is_safe": {"type": "boolean"},
            "reason": {"type": "string"}
        }
    }
}]
response = await llm.complete(prompt, tools=tools)
```

**Strengths**: structured output, model understands intent. **Gap**: defines *syntax* not
*semantics*—the JSON is structured, but prompt construction, retries, and provider differences
remain
the caller's problem.

**Structured output libraries.** Instructor, Outlines, and similar libraries allow defining
Pydantic models and getting typed responses.

```python
class SafetyCheck(BaseModel):
    is_safe: bool
    reason: str

result = await client.chat.completions.create(
    response_model=SafetyCheck,
    messages=[{"role": "user", "content": prompt}]
)
```

**Strengths**: type safety, clean API. **Gap**: defines *what shape the answer has*
(`SafetyCheck`) but not *what cognitive operation to perform*. A Pydantic model carries no prompt
strategy, no retry semantics specific to the operation, no validation logic for
yes/no-with-reasoning vs. structured-critique. Prompt crafting and per-call logic remain manual.

**DSPy.** Takes a different approach: define signatures and let the framework optimize prompts.

```python
class CheckSafety(dspy.Signature):
    code: str = dspy.InputField()
    is_safe: bool = dspy.OutputField()
    reason: str = dspy.OutputField()
```

**Strengths**: prompt optimization, composable modules. **Gap**: optimizes prompts but requires
labeled data and adds abstraction layers that can obscure what's happening.

**LangGraph.** Models agent workflows as graphs: nodes are functions, edges define control flow,
state flows through the system.

```python
from langgraph.graph import StateGraph

graph = StateGraph(AgentState)
graph.add_node("check_safety", check_safety_node)
graph.add_node("fix_issues", fix_issues_node)
graph.add_conditional_edges("check_safety", route_based_on_result)
```

**Strengths**: explicit control flow, checkpointing, human-in-the-loop patterns, parallel execution
via `Send`. The `langgraph-prebuilt` package adds helpers like `create_react_agent`, `ToolNode`, and
`ValidationNode`.

**Gap**: orchestrates *workflow*—which node runs next, when to checkpoint, how to fan out—but
inside each node, the LLM call itself is still unstructured: no output validation, no retry on
malformed responses, no typed results.

## A Different Layer

These approaches operate at different levels:

- **Tool calling / Instructor**: *Syntax*—ensuring responses parse correctly
- **DSPy**: *Optimization*—finding prompts that work better
- **LangGraph**: *Control flow*—orchestrating multi-step workflows

We got interested in a different layer: *semantics*—what kind of cognitive operation is being asked
of the LLM.

Consider these operations:

- "Does X satisfy Y?" (verification)
- "What's wrong with X?" (critique)
- "Improve X given feedback Y" (refinement)
- "Break X into subtasks" (decomposition)

Each is a distinct cognitive pattern. A call to `verify()` expects a yes/no with reasoning. A call
to `critique()` expects the strongest counter-argument. These aren't arbitrary function
names—they're
semantic primitives that recur across agent architectures.

With raw prompting, this intent lives in prose. With tool calling, it's expressed as schemas. We
wanted the *operation itself* as a first-class concept.

Not all verbs sit at the same depth. Some—`verify`, `critique`, `refine`—encode genuine cognitive
patterns with operation-specific prompt strategies and retry semantics. Others—`extract`,
`classify`—are closer to structured output with better defaults. The vocabulary spans both: the
value isn't that every verb is equally "semantic," but that the full set composes into reusable
loops.

## Our Approach

We defined a fixed vocabulary of verbs for LLM interactions. The idea draws from SCUMM (1987)—the
adventure game engine that replaced free-form text parsers with a fixed verb vocabulary (`pick up`,
`use`, `talk to`). A constrained verb set made tooling, testing, and composition tractable. The same
principle applies to agent-LLM communication.

Each verb has defined semantics and a typed return value. Here are the core ones:

**`verify`** — Does X satisfy predicate Y? Returns `VerifyResult(passed: bool, reason: str)`.

```python
result = await saia.verify(code, "handles null input safely")
# result.passed = False
# result.reason = "Line 12 dereferences user.name without a null check"
```

**`critique`** — What's the strongest argument against X? Returns
`Critique(counter_argument: str, weaknesses: list[str])`.

```python
critique = await saia.critique(proposal)
# critique.counter_argument = "This assumes network latency is constant..."
# critique.weaknesses = ["No retry budget", "Silent failure on timeout"]
```

**`refine`** — Improve X given feedback Y. Returns the improved artifact.

```python
improved = await saia.refine(proposal, "\n".join(critique.weaknesses))
```

The remaining verbs—`extract`, `complete`, `decompose`, `classify`, `choose`, `ask`, `synthesize`,
`find`, `constrain`, `ground`, `instruct`—follow the same pattern: defined semantics, typed return,
operation-specific prompt strategy and retry logic.
The <a href="https://github.com/serendip-ml/llm-saia#readme" target="_blank" rel="noopener
noreferrer">full reference</a> covers all 14.

### Why These Verbs

We started with ~20 verbs and cut them down. The test: if a verb can be expressed as another verb
with a specific input, it's a variant, not a primitive.

Concrete examples of what we cut:

- **`summarize`** → `extract` with a string return type. The cognitive operation is the same:
  pull structured content from unstructured text. The only difference is the output shape.
- **`compare`** → `verify` with a comparison predicate. "Is A better than B on criterion C?" is
  just verification applied to a pair.
- **`rank`** → `classify` applied repeatedly. Ordering N items is N classification calls
  with a consistent rubric, not a distinct operation.
- **`plan`** → `decompose` followed by `instruct`. Planning is decomposition (break into steps)
  plus instruction generation (define each step). Making it a single verb hid the composability.
- **`validate`** → `verify`. We had both, distinguished by "check format" vs "check correctness."
  In practice, both are predicate checks with different prompts. One verb handles both.

The decision framework was: can the verb be composed from existing ones without losing prompt
strategy or retry semantics? If yes, cut it. If the composition would require the caller to
reimplement prompt logic that should be encapsulated, keep it as a primitive.

We converged on 14 that form composable loops recurring across agent architectures:

- **Validation loop**: `verify` → `critique` → `refine`. Check a claim, find weaknesses, improve
  it. This pattern appears in any agent that iterates on quality.
- **Build loop**: `decompose` → `instruct` → `synthesize`. Break a task apart, execute the pieces,
  combine the results. The standard divide-and-conquer pattern for complex tasks.
- **Structured extraction**: `extract` and `classify` handle pulling typed data from unstructured
  text—the most common operation in production agents.

## How This Relates to LangGraph

LangGraph and SAIA operate at different layers. LangGraph handles *workflow orchestration*—which
node runs next, what state to pass, when to checkpoint. SAIA handles *what happens inside the
node*—the actual LLM operation.

They compose naturally:

```python
# LangGraph node using SAIA verbs
async def review_node(state: AgentState) -> AgentState:
    result = await saia.verify(state["code"], "handles errors correctly")
    if not result.passed:
        critique = await saia.critique(state["code"])
        state["feedback"] = critique.weaknesses
    return state

graph.add_node("review", review_node)
graph.add_conditional_edges("review", lambda s: "fix" if s.get("feedback") else "done")
```

LangGraph decides "run review, then conditionally route to fix or done." SAIA decides "verify the
code, and if it fails, generate a critique." Different concerns, same workflow.

For workflows needing LangGraph's orchestration—checkpointing, parallel branches,
human-in-the-loop—they
compose well. For simpler cases needing only semantic operations, SAIA works standalone.

## Obstacles

**Backend differences.** Anthropic and OpenAI have different APIs, different tool calling formats,
different quirks. Local models via vLLM differ again.

We pushed all provider-specific code into a thin adapter layer. The verb implementations don't know
which model they're talking to. Same agent code works with Claude, GPT-4, or a local Llama.

**Premature completion.** LLMs often claim they're "done" when they're not. We added a confirmation
flow: when the model signals completion, we ask it to confirm. If its response contains
contradictory signals ("done" but also "let me continue"), we catch that and push back.

**Lost tool access.** Sometimes models lose the ability to call tools mid-conversation—they start
writing `read_file(...)` as text instead of invoking the tool. We detect these patterns and nudge
the model to use actual tool calls. Related: we warn when input token counts suggest the server is
ignoring tool definitions entirely.

**Structured output reliability.** Models don't always return valid JSON. When parsing fails, we
retry with the error message as context, which often fixes the issue. For local models, we support
grammar-constrained decoding (xgrammar/outlines) to
guarantee valid output.

**Nudge fatigue.** When models get stuck, repeated correction prompts can make things worse. We
implemented backoff: after nudging, wait N iterations before nudging again. A classifier
(itself an LLM call) determines whether the model is stuck, asking a question, or actually done.

**Balancing structure with flexibility.** Some operations genuinely need free-form output.
`instruct()` exists for open-ended tasks where typed output doesn't make sense.

**Output guards.** Valid JSON isn't enough—models return preambles ("Sure! Here's..."), emoji,
markdown, or exceed length limits. Guards validate after parsing and retry with specific
instructions. Built-in guards handle common cases: `no_preamble`, `no_emoji`, `max_length`,
`english_only`. Custom guards are a validator function plus a retry instruction.

**Token cost of reliability.** Retries, confirmation flows, and nudge classifiers all burn tokens.
In practice, most verb calls succeed on the first attempt with frontier models, but local models
retry more often. We treat this as an acceptable trade-off—a retry that produces correct typed
output
is cheaper than debugging a silently wrong result downstream—but it's a real cost to account for.

## Current API

```python
from llm_saia import SAIA

saia = SAIA.builder().backend(your_backend).build()

# Verify a claim
result = await saia.verify(code, "handles null input safely")

# Chain operations
critique = await saia.critique(claim)
improved = await saia.refine(claim, "\n".join(critique.weaknesses))

# Multi-model: cheap generates, expensive validates
local = SAIA.builder().backend(local_backend).build()
smart = SAIA.builder().backend(anthropic_backend).build()

draft = await local.instruct("Write a function to parse dates")
result = await smart.verify(draft, "handles edge cases correctly")
```

Pure Python, zero framework dependencies, pluggable backends. Same verb calls work across Claude,
GPT-4, and local models via vLLM.

## What's Next

Every verb call already captures inputs, outputs, latency, and token usage—structured operation
traces, not chat transcripts. These traces create (verb, prompt, decision) tuples that map directly
to training examples. We're using them to fine-tune verb-specific adapters: a model trained on
`verify` traces for more consistent verification, another on `critique` traces for sharper
counter-arguments. The first target is `verify`—it has the cleanest signal (boolean outcome +
reason)
and the highest call volume in our current agents. Early direction, not results yet.

## The Code

- Repository: <a href="https://github.com/serendip-ml/llm-saia" target="_blank" rel="noopener noreferrer">github.com/serendip-ml/llm-saia</a>
- Documentation: <a href="https://github.com/serendip-ml/llm-saia#readme" target="_blank" rel="noopener noreferrer">README</a>
