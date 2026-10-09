# Demo Video Guide

**Required length:** 3–5 minutes

**Video link:** TODO — paste your final recording link here.

## Suggested script

### 0:00–0:25 — Introduce the project
“Hi, this is my TakeMeter project for r/TrueFilm. The classifier assigns one of
three discourse labels: analysis, opinion, or discussion_question. I collected and
reviewed 225 public r/TrueFilm examples and compared a zero-shot Groq baseline with
a fine-tuned DistilBERT classifier.”

### 0:25–0:55 — Explain the labels
- `analysis`: developed reasoning or interpretation is the main substance.
- `opinion`: the main substance is a judgment or preference with limited development.
- `discussion_question`: the main purpose is getting explanation, comparison,
  recommendation, or debate from the community.

### 0:55–1:55 — Show 3–5 model classifications
Show the notebook’s sample-classification output. Make sure predicted label and
confidence are visible. Explain at least one correct prediction.

### 1:55–2:35 — Show one incorrect prediction
A useful example is the “What is a Cinephile?” post. Its true label is
`discussion_question`, while DistilBERT predicted `analysis`. The body is long and
contains detailed film discussion, so the model appears to have treated length and
film-specific detail as evidence for analysis even though the author’s main goal was
to ask the community how to define a cinephile.

### 2:35–3:25 — Evaluation
“The zero-shot baseline achieved 88.24% accuracy. Fine-tuned DistilBERT achieved
58.82%. DistilBERT’s biggest failure was the opinion class: it had 0 precision,
0 recall, and 0 F1 because the model never predicted opinion on the test set.”

Show the confusion matrix.

### 3:25–4:00 — Reflection
“The main lesson was that label design and data coverage mattered more than the
training loop. The baseline could directly reason from the definitions, while a
small DistilBERT fine-tune learned stronger surface shortcuts. With more time, I
would collect more opinion examples and more difficult boundary examples.”
