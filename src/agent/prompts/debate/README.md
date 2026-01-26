# Debate Prompt Templates

This directory contains prompt templates for the stock debate agents module.

## Template Files

| File | Purpose |
|------|---------|
| `opening_buy.txt` | Bull participant's opening statement |
| `opening_avoid.txt` | Bear participant's opening statement |
| `rebuttal.txt` | Response to opponent's opening |
| `summary.txt` | Neutral synthesis of the debate |

## Benefits of Rebuttals

The rebuttal phase serves several important purposes:

### 1. Argument Stress-Testing
Rebuttals force each side to defend against direct challenges. A weak argument that sounds compelling in isolation often crumbles when confronted. This helps filter out:
- Superficial pattern-matching ("stock dropped → buy the dip")
- Cherry-picked evidence that ignores contradicting data
- Confident-sounding but logically flawed reasoning

### 2. Information Surfacing
The rebuttal phase often brings out details that weren't emphasized initially:
- Bull might ignore a risk → Bear's opening forces Bull to address it in rebuttal
- Bear might dismiss a strength → Bull's rebuttal has to make that strength more concrete

This creates a more complete picture than two independent monologues.

### 3. Reader Trust
Arguments that survive challenge feel more credible. A reader seeing "Bull said X, Bear challenged with Y, Bull defended with Z" can assess the quality of reasoning themselves.

### 4. LLM-Specific Benefits
- Gives the model a "second pass" with richer context (opponent's argument included)
- Counteracts the model's tendency to hedge or be overly balanced in a single response
- The adversarial framing can produce sharper, more specific claims

### Potential Downsides

| Concern | Mitigation |
|---------|------------|
| **Cost/Latency** - 2 extra API calls | Make rebuttals toggleable; skip for lower-priority stocks |
| **Diminishing returns** - Rebuttals might just repeat openings | Prompt explicitly: "Address their *specific* points, don't repeat yourself" |
| **Manufactured disagreement** - LLM invents weak counterarguments | Allow participants to concede good points |

---

## Prompting Considerations

### 1. Evidence Grounding

Should participants only cite the provided context, or draw on general knowledge?

| Approach | Pros | Cons |
|----------|------|------|
| **Strict grounding** | Verifiable, no hallucination risk | May miss relevant context |
| **Open knowledge** | Richer arguments | Risk of hallucinated facts |
| **Hybrid** | Best of both | Requires careful prompting |

**Current approach**: Strict grounding (provided data only) for v1. Loosen when tool access is added for fact-checking.

### 2. Concession Allowance

Participants should be allowed to acknowledge valid points from the opponent:

```
"You may concede points that are genuinely strong, but explain why
they don't change your overall conclusion."
```

This prevents artificial disagreement and produces more nuanced output. A Bull who says "Sarah's right that near-term guidance is uncertain, but..." is more credible than one who dismisses everything.

### 3. Confidence Calibration

| Style | When to use |
|-------|-------------|
| **High conviction** | Openings and rebuttals (it's a debate) |
| **Calibrated uncertainty** | Summary (honest synthesis) |

### 4. Persona Intensity

Keep personas as "tendencies" rather than rigid characters:
- Too strong → Caricature, predictable arguments
- Too weak → Bland, interchangeable voices
- Just right → Distinct perspectives without being gimmicky

The style hints approach ("focuses on long-term value", "emphasizes risk") is lighter than forcing a full character.

### 5. Handling Lopsided Cases

When evidence clearly favors one side:
- Force both sides but allow concessions
- Add post-hoc "argument strength" assessment in summary
- Summary identifies "crux" - what would need to be true for each side to be right

### 6. Summary Neutrality

The summary must NOT pick a winner. Instead:
1. Steelman both positions
2. Identify the crux disagreement
3. List what investors should watch for

### 7. Output Length Targets

| Phase | Target Length | Rationale |
|-------|---------------|-----------|
| Opening | 150-250 words | Make your case, don't ramble |
| Rebuttal | 100-200 words | Focused response, not rehash |
| Summary | 150-200 words | Quick synthesis |

**Total**: ~600-900 words per debate. Readable in 3-4 minutes.

---

## Key Prompting Decisions (v1)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Evidence grounding | Strict (provided data only) | Avoid hallucination |
| Concession allowed | Yes (with justification) | More nuanced output |
| Confidence style | Convicted in debate, calibrated in summary | Appropriate per phase |
| Persona intensity | Light (tendencies, not characters) | Avoid caricature |
| Lopsided handling | Force both, allow concessions | Complete picture |
| Summary stance | Neutral with "crux" identification | Help reader decide |

---

## Template Variables

Each template uses these variables (injected at runtime):

| Variable | Description |
|----------|-------------|
| `{ticker}` | Stock symbol (e.g., "AAPL") |
| `{company_name}` | Full company name |
| `{price_change}` | Today's price change (e.g., "-8.2%") |
| `{context}` | Formatted StockContext |
| `{opponent_name}` | Name of opposing participant |
| `{opponent_argument}` | Opponent's statement (for rebuttals) |
| `{debate_transcript}` | Full debate so far (for summary) |
