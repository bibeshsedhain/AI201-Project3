# TakeMeter — Project Planning

## Community

I chose **r/TrueFilm**, a Reddit community focused on detailed discussion of movies, filmmakers, film history, interpretation, criticism, and filmmaking techniques. The community is a good fit for a discourse-classification task because posts and comments vary in purpose: some develop film analysis, some mainly express evaluations, and others ask the community to explain or debate a topic.

## Labels

### `analysis`
A post or comment whose main purpose is to explain, interpret, or argue something about film using meaningful reasoning, examples, observations, themes, filmmaking techniques, narrative structure, historical context, or comparisons.

Examples:
- A post explaining how repeated framing choices reinforce a character's isolation.
- A comment arguing that an ending works because it completes a pattern established earlier in the story.

### `opinion`
A post or comment whose main purpose is expressing a judgment, preference, or evaluation about a movie, filmmaker, actor, performance, genre, or filmmaking choice without substantially developing the reasoning.

Examples:
- “I think this is easily Nolan's weakest film.”
- “That was the best performance in the movie.”

### `discussion_question`
A post or comment whose primary purpose is asking the community to explain, interpret, compare, recommend, or debate something related to film.

Examples:
- “Why is 2001: A Space Odyssey considered one of the most important films ever made?”
- “Should horror films be evaluated differently from dramas when discussing character development?”

## Decision Rules

### Analysis vs. Opinion
If the reasoning or interpretation is the main substance of the text, use `analysis`. If the judgment itself is the main substance and reasoning is minimal, use `opinion`.

### Opinion vs. Discussion Question
If the primary goal is getting responses from other users, use `discussion_question`, even if the author includes their own opinion.

### Analysis vs. Discussion Question
If the author mainly develops their own interpretation, use `analysis`. If the text ultimately exists mainly to solicit answers, interpretations, recommendations, or debate, use `discussion_question`.

## Hard Edge Cases

The hardest boundary is `analysis` vs. `opinion`, because film criticism naturally mixes judgment and interpretation. I use the following rule: if removing the judgment would still leave meaningful reasoning or interpretation, the example is usually `analysis`; if very little remains, it is `opinion`.

A second difficult case is a long post that contains substantial analysis but ends by asking the community a question. In those cases I classify based on the primary communicative purpose of the full text rather than punctuation alone.

## Data Collection Plan

I collected public r/TrueFilm posts and comments using the Arctic Shift Reddit archive. I first sampled community content to test whether the labels fit real discourse, then collected a larger candidate pool and reviewed the resulting annotations.

The final dataset contains **225 examples**. The reviewed distribution is:

| Label | Count |
|---|---:|
| analysis | 94 |
| opinion | 45 |
| discussion_question | 86 |
| **Total** | **225** |

The dataset is stored as one CSV and is split into train, validation, and test sets inside the notebook.

## Evaluation Metrics

I use overall accuracy plus per-class precision, recall, and F1. Accuracy gives a simple overall measure, but per-class metrics are necessary because the labels are not perfectly balanced and the main challenge is understanding which label boundaries the model fails to learn. I also use a confusion matrix to identify directional error patterns, especially `analysis` vs. `opinion`.

## Definition of Success

A useful result would have overall accuracy around 75% or better, macro F1 around 0.70 or better, and no class with extremely poor performance. Because this is a subjective classification task with a small dataset, the evaluation should focus not only on accuracy but also on what kinds of examples the model consistently gets wrong.

## AI Tool Plan

### Label stress-testing
I used AI to generate and reason through borderline examples between the three labels. This helped refine the primary-purpose decision rules before final annotation.

### Annotation assistance
AI-assisted heuristics were used to pre-label the collected examples. I then reviewed and corrected the labels during a quality-control pass. The final dataset used for training is `data/labeled_data_final.csv`.

### Failure analysis
After evaluation, I use AI to help surface recurring patterns in the model's wrong predictions, then verify those patterns manually before including them in the README.
