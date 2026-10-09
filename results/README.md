# Evaluation Results

## Headline results

| Model | Accuracy | Macro F1 |
|---|---:|---:|
| Zero-shot baseline (`openai/gpt-oss-120b`) | 0.8824 | 0.87 |
| Fine-tuned DistilBERT | 0.5882 | 0.42 |

## Zero-shot baseline

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| analysis | 1.00 | 0.79 | 0.88 | 14 |
| opinion | 0.75 | 0.86 | 0.80 | 7 |
| discussion_question | 0.87 | 1.00 | 0.93 | 13 |

Confusion matrix:

| True \ Predicted | analysis | opinion | discussion_question |
|---|---:|---:|---:|
| analysis | 11 | 2 | 1 |
| opinion | 0 | 6 | 1 |
| discussion_question | 0 | 0 | 13 |

## Fine-tuned DistilBERT

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| analysis | 0.61 | 1.00 | 0.76 | 14 |
| opinion | 0.00 | 0.00 | 0.00 | 7 |
| discussion_question | 0.55 | 0.46 | 0.50 | 13 |

Confusion matrix:

| True \ Predicted | analysis | opinion | discussion_question |
|---|---:|---:|---:|
| analysis | 14 | 0 | 0 |
| opinion | 2 | 0 | 5 |
| discussion_question | 7 | 0 | 6 |

## Main error pattern

The fine-tuned model never predicted `opinion`. All 7 true opinion examples were
absorbed by either `analysis` (2) or `discussion_question` (5). It also overpredicted
`analysis`, labeling 7 discussion questions as analysis.

This suggests the small training set was insufficient for DistilBERT to learn the
semantic boundary between evaluation, developed interpretation, and response-seeking
questions. The zero-shot baseline handled those distinctions much better because it
could reason directly from the written label definitions.


## Sample classifications

See `sample_classifications.csv` for 5 exported test examples with true label, predicted label, and model confidence.
