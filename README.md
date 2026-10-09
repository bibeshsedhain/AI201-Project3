# TakeMeter — r/TrueFilm Discourse Classifier

TakeMeter is a text-classification project for AI201. It classifies public
r/TrueFilm posts and comments into three discourse categories:
`analysis`, `opinion`, and `discussion_question`.

## Community Choice

I chose **r/TrueFilm** because its discussions contain a useful mix of interpretation,
criticism, personal evaluation, and open-ended questions. This makes it a good setting
for testing whether a classifier can distinguish the purpose and structure of film
discourse rather than only recognizing film-related vocabulary.

## Label Taxonomy

### `analysis`
The main purpose is to explain, interpret, or argue something about film using
meaningful reasoning, examples, observations, filmmaking techniques, narrative
structure, historical context, or comparisons.

Examples:
- A post explaining how repeated framing choices reinforce a character's isolation.
- A comment arguing that an ending works because it completes a pattern established earlier in the story.

### `opinion`
The main purpose is expressing a judgment, preference, or evaluation about a movie,
filmmaker, actor, performance, genre, or filmmaking choice without substantially
developing the reasoning.

Examples:
- “I think this is easily Nolan's weakest film.”
- “That was the best performance in the movie.”

### `discussion_question`
The primary purpose is asking the community to explain, interpret, compare, recommend,
or debate something related to film.

Examples:
- “Why is 2001: A Space Odyssey considered one of the most important films ever made?”
- “Should horror films be evaluated differently from dramas when discussing character development?”

### Decision rule

Labels are assigned according to the **primary communicative purpose** of the text.
A question mark alone does not make a post a discussion question, and evaluative
language does not make a post an opinion when developed interpretation is the main
substance.

## Data Collection

Public r/TrueFilm posts and comments were collected from the **Arctic Shift public
Reddit archive**. The collection script is included in
`scripts/truefilm_dataset_collector.py`.

I used automated preliminary labels to speed up annotation, then reviewed and corrected
the data according to the label rules. The final dataset used for model training is:

`data/labeled_data_final.csv`

| Label | Count | Percentage |
|---|---:|---:|
| analysis | 94 | 41.8% |
| opinion | 45 | 20.0% |
| discussion_question | 86 | 38.2% |
| **Total** | **225** | **100%** |

## Difficult Annotation Cases

The hardest boundary was `analysis` vs. `opinion`, because film criticism naturally
mixes judgment with explanation. I classified examples according to the **primary
communicative purpose** of the full text rather than punctuation or isolated keywords.

### Case 1 — question-shaped title, analytical body
**Example:** “Is One Battle After Another a critique of state violence?”

Possible labels: `analysis` / `discussion_question`

**Final label:** `analysis`

**Decision:** Although the title is phrased as a question, the body develops the
author's own interpretation that the film critiques militarization and state violence.
The post mainly presents an argument rather than asking other users to supply one.

### Case 2 — personal evaluation ending with a question
**Example:** a post about Avatar's variable frame-rate presentation that says the
switching between frame rates was distracting and nearly ruined the viewing experience.

Possible labels: `opinion` / `discussion_question`

**Final label:** `opinion`

**Decision:** The author ends by asking whether others found the effect distracting,
but most of the post is a personal evaluation of the viewing experience. The judgment
is the main substance.

### Case 3 — asks for feedback after doing real analysis
**Example:** “First Time Doing a Scene Analysis—Looking for Feedback! (The Little Prince 2015)”

Possible labels: `analysis` / `discussion_question`

**Final label:** `analysis`

**Decision:** The writer asks for feedback, but the body is a developed scene analysis
using composition, point of view, camera work, and animation choices. The analytical
content is the primary substance.

Two additional difficult cases are documented in `reports/dataset_qc_report.txt`,
including a Bugonia interpretation containing rhetorical questions and a The Forgiven
post that mixes evaluation with a genuine request for community analysis.

## Train / Validation / Test Split

The notebook uses a stratified 70/15/15 split with `random_state=42`.

- Train: 157
- Validation: 34
- Test: 34

The test set was treated as locked after the split.

## Models

### Zero-shot baseline

The specification originally requested
`meta-llama/llama-4-scout-17b-16e-instruct`. That model was unavailable through Groq
at evaluation time, so I used the available Groq model:

`openai/gpt-oss-120b`

The baseline was run on the **same locked 34-example test set** later used for
DistilBERT evaluation. Each test example was sent independently to Groq with no
task-specific training.

The prompt used was:

```text
You are classifying discourse from the r/TrueFilm Reddit community.

Choose exactly ONE label:

analysis:
The main purpose is to explain, interpret, or argue something about film
using meaningful reasoning, examples, observations, themes, filmmaking
techniques, narrative structure, historical context, or comparisons.

opinion:
The main purpose is expressing a judgment, preference, or evaluation about
a movie, filmmaker, actor, performance, genre, or filmmaking choice without
substantially developing the reasoning.

discussion_question:
The primary purpose is asking the community to explain, interpret, compare,
recommend, or debate something related to film.

Decision rules:
If reasoning or interpretation is the main substance, choose analysis.
If the judgment itself is the main substance and reasoning is minimal, choose opinion.
If the primary goal is getting responses from others, choose discussion_question,
even if the author includes their own opinion.

Return ONLY one of:
analysis
opinion
discussion_question
```

Predictions were collected for all test examples and compared against the same gold
labels used for the fine-tuned model. The notebook records the accuracy, per-class
precision/recall/F1, and confusion matrix.

### Fine-tuned classifier

Base model:

`distilbert-base-uncased`

Training setup:

- epochs: 3
- learning rate: `2e-5`
- batch size: 16
- validation after each epoch
- best checkpoint loaded at the end

**Hyperparameter decision:** I kept the starter/default settings of 3 epochs,
`2e-5` learning rate, and batch size 16 because the training set is small (157 examples).
Using conservative defaults reduced the risk of overfitting while keeping the run
comparable to the course's recommended setup. I did not tune on the test set.

The complete executed pipeline is in `notebooks/TakeMeter_TrueFilm.ipynb`.

## Evaluation

### Overall results

| Model | Accuracy | Macro F1 |
|---|---:|---:|
| Zero-shot baseline | **0.8824** | **0.87** |
| Fine-tuned DistilBERT | **0.5882** | **0.42** |

The zero-shot baseline substantially outperformed the small DistilBERT fine-tune.

### Per-class metrics

| Model | Label | Precision | Recall | F1 | Support |
|---|---|---:|---:|---:|---:|
| Baseline | analysis | 1.00 | 0.79 | 0.88 | 14 |
| Baseline | opinion | 0.75 | 0.86 | 0.80 | 7 |
| Baseline | discussion_question | 0.87 | 1.00 | 0.93 | 13 |
| DistilBERT | analysis | 0.61 | 1.00 | 0.76 | 14 |
| DistilBERT | opinion | 0.00 | 0.00 | 0.00 | 7 |
| DistilBERT | discussion_question | 0.55 | 0.46 | 0.50 | 13 |

### Fine-tuned confusion matrix

| Actual \ Predicted | analysis | opinion | discussion_question |
|---|---:|---:|---:|
| analysis | 14 | 0 | 0 |
| opinion | 2 | 0 | 5 |
| discussion_question | 7 | 0 | 6 |

The most important result is that DistilBERT **never predicted `opinion`** on the test
set. All seven opinion examples were assigned to either analysis or discussion_question.
The model also overpredicted analysis, assigning seven true discussion questions to it.

A rendered copy is available at `results/confusion_matrix.png`.

## Error Analysis

### Error 1 — long question misread as analysis

**Excerpt:** “What do you guys consider a cinephile?”

- True label: `discussion_question`
- Fine-tuned prediction: `analysis`

The post contains a long explanation of the author’s viewing habits and many film
references before asking the community how to define a cinephile. The length and
film-specific detail likely looked analytical to DistilBERT, even though the primary
purpose was to solicit an answer. More long discussion-question examples would help
teach the model that detailed setup can still lead to a response-seeking post.

### Error 2 — comparative judgment misread as analysis

**Excerpt:** “Both had perfect casting.”

- True label: `opinion`
- Fine-tuned prediction: `analysis`

The post compares two adaptations and mentions their casts, so it contains vocabulary
that resembles analytical comparison. However, its main substance is an evaluation of
which film and performances were better. The model appears to equate comparison with
analysis too readily.

### Error 3 — personal evaluation misread as discussion question

**Excerpt:** “It’s an absolutely gorgeous and effective film.”

- True label: `opinion`
- Fine-tuned prediction: `discussion_question`

This is a short evaluative response rather than a request for community input. The
mistake suggests that the opinion class did not receive enough distinct training signal;
the confusion matrix confirms that the model failed to predict opinion anywhere in the
test set.

See `results/wrong_predictions.csv` for all 14 fine-tuned mistakes.

## Sample Classifications

The following examples were exported from the fine-tuned DistilBERT model using the
saved test-set logits.

| Text excerpt | True Label | Predicted Label | Confidence |
|---|---|---|---:|
| I love PTA but didn't really think his latest film is all that is being made Just saw One Battle After Another and even though the cinematography is … | analysis | analysis | 0.524 |
| i'm a 'find the central metaphor' guy. but i'm enjoying the op's perspective and questions. one thing, though. you and op both talk about 'reducing' … | analysis | analysis | 0.490 |
| 70's New Hollywood and the failure of the promise of streaming revolution Despite being subscribed to 4-5 of the most common major streaming platform… | analysis | analysis | 0.551 |
| What is a Cinephile? What do you guys consider a cinephile? Many people here seem to watch more than 350+ movies a year and to me that’s really hard … | discussion_question | analysis | 0.526 |
| Dangerous Liaisons (1988) and Valmont (1989). One is better and more Dangerous than the other. Both had perfect casting. I wish people would talk abo… | opinion | analysis | 0.507 |

The first three examples were classified correctly as `analysis`. The last two show
the model's main failure pattern: it predicts `analysis` even when the primary purpose
is a `discussion_question` or an `opinion`. The confidence values are all close to
0.5, which also shows that the model is uncertain rather than strongly calibrated on
these difficult cases.

## Reflection: What the Model Learned vs. What I Intended

The intended distinction was semantic: `analysis` should be identified by developed
reasoning, `opinion` by primarily evaluative language, and `discussion_question` by
response-seeking purpose.

The fine-tuned model learned part of the `analysis` category very strongly: recall for
analysis was 1.00. However, that came at the cost of overpredicting analysis. It failed
to learn a usable opinion decision boundary at all, producing 0.00 precision, recall,
and F1 for that class.

This suggests the model learned surface patterns such as post length, comparison
language, and film-specific detail more easily than the intended communicative-purpose
boundary. The zero-shot baseline performed much better because it could reason directly
from the written definitions at inference time.

If I continued the project, I would collect substantially more opinion examples and more
hard examples where long posts are still questions or where comparisons remain primarily
evaluative. I would also test longer-context models because some r/TrueFilm posts are
long enough that truncation can remove important context.

## Spec Reflection

The planning document helped by forcing the label definitions and ambiguity rules to be
written before final model evaluation. Those rules were especially useful during dataset
QC, where many automatically labeled examples had to be corrected according to their
primary purpose.

The implementation diverged from the initial plan in two main ways. First, manual review
produced a naturally imbalanced final distribution rather than the planned 75/75/75
split. I kept the corrected labels rather than forcing examples into categories just to
balance the counts. Second, the originally requested Groq baseline model was unavailable,
so I documented the change and used `openai/gpt-oss-120b`.

## AI Usage

### 1. Label stress-testing
I used ChatGPT to generate and reason through borderline examples between `analysis`,
`opinion`, and `discussion_question`. I used these cases to refine the primary-purpose
decision rule.

### 2. Annotation assistance
The collection workflow produced automated preliminary labels. I used AI-assisted QC to
surface suspicious rows, then applied the written decision rules to correct the final
dataset. The reviewed `data/labeled_data_final.csv` is the file used for training.

### 3. Failure analysis
I used AI to help organize the wrong predictions into recurring error patterns. I
verified the final claims against the actual confusion matrix and misclassified examples
from the completed notebook.

## Repository Structure

```text
ai201-project3-takemeter/
├── README.md
├── planning.md
├── requirements.txt
├── DEMO.md
├── data/
│   └── labeled_data_final.csv
├── notebooks/
│   └── TakeMeter_TrueFilm.ipynb
├── scripts/
│   └── truefilm_dataset_collector.py
├── reports/
│   ├── dataset_qc_report.txt
│   └── dataset_summary.txt
└── results/
    ├── evaluation_results.json
    ├── wrong_predictions.csv
    ├── confusion_matrix.png
    ├── baseline_confusion_matrix.png
    ├── sample_classifications.csv
    ├── SAMPLE_CLASSIFICATIONS.md
    └── README.md
├── FINAL_SUBMISSION_CHECKLIST.md
```

## Running the Project

### Dataset collection

```bash
python scripts/truefilm_dataset_collector.py
```

The reviewed dataset is already included, so recollection is not required to reproduce
training.

### Model training and evaluation

Open `notebooks/TakeMeter_TrueFilm.ipynb` in Google Colab, select a T4 GPU, add
`GROQ_API_KEY` to Colab Secrets, and run the notebook from top to bottom.


**Video link:** (https://drive.google.com/file/d/156CQVOOJhIZ-igWcW1pm9f-7hDzbVt3l/view?usp=sharing)
