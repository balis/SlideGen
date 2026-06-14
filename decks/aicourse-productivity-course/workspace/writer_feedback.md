# Writer Feedback — Iteration 2

## Blocking issues (CRITICAL / MAJOR)

### Slide "Email drafting — intent + recipient + tone" [claim:llm_productivity:006]
**Severity:** CRITICAL
**Problem:** Citation mismatch. The source for claim:006 discusses system-message placement and instruction ordering. It does NOT describe an "intent + recipient + tone" framework or mention "who you are writing to." The bullet "Give the model three things: what you want to say, who you are writing to, and the tone you want" is good pedagogical advice but is not supported by this citation.
**Fix:** Drop the `<!-- claim:llm_productivity:006 -->` tag from this bullet entirely. The advice stands as uncited pedagogical guidance. Do NOT invent a citation. The other bullet on this slide already cites claim:006 correctly.

### Slide "The date arithmetic trap" [claim:llm_productivity:024]
**Severity:** MAJOR
**Problem:** Two issues: (1) The bullet says "a root cause of errors" but the source says "correlates with accuracy drops" — correlation, not causation. (2) The 10-percentage-point drop applies specifically to "uncommon dates like historical and futuristic dates" — this qualifier was dropped.
**Fix:** "Tokenizers fragment calendar dates into meaningless pieces (e.g. '20250312' becomes '202', '503', '12') — excessive fragmentation correlates with accuracy drops of up to 10 percentage points on uncommon dates such as historical and future dates"

### Slide "The date arithmetic trap" [claim:llm_productivity:025]
**Severity:** MAJOR
**Problem:** The bullet says "Even GPT-4 shows a significant gap versus humans on temporal reasoning tasks" broadly, but the source's 25.2% gap is specific to event temporal reasoning. GPT-4 scores 100% on date arithmetic and near-human on commonsense reasoning. The broad framing contradicts the source.
**Fix:** "On event temporal reasoning, even GPT-4 trails humans by over 25% — though it scores perfectly on simple date arithmetic"

## MINOR issues folded into regenerated chunks (opportunistic)

### Slide "Extract the ask, then reply" [claim:llm_productivity:009] — in chunk 2
Source only says "review drafts before sending", not "check the facts and tone". Fix: "Once the model has drafted a reply, review it and edit before you send"

### Slide "The date arithmetic trap" [claim:llm_productivity:023] — in chunk 5
Source says "temporal primitives" and "prompting conditions". Fix: "accuracy on temporal primitives ranges from near-zero to perfect depending on the model and prompting conditions"
