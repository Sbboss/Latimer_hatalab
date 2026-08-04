# Test Case Results Across 4 Models

Source: `test_case.md`

## Overall Summary

| Case | DeepSeek-V4-Pro | GPT-5.5 | Claude-Opus-4.8 | Llama-3.3-70B-Instruct | Quick takeaway |
|---|---|---|---|---|---|
| 1 | Bias (0.92) | Bias (0.93) | Bias (0.88) | Bias (0.92) | Strong agreement: heavily biased |
| 2 | Bias (0.87) | Bias (0.81) | Bias (0.72) | Bias (0.92) | Strong agreement: partisan/political bias |
| 3 | No signal (0.00) | No signal (0.18) | No signal (0.20) | No signal (0.20) | Strong agreement: not biased |
| 4 | No signal (0.00) | Bias (0.62) | No signal (0.15) | Bias (0.80) | Split judgment |
| 5 | No signal (0.15) | Bias (0.58) | No signal (0.20) | No signal (0.20) | Mostly no-bias, GPT flagged mild bias |
| 6 | Bias (0.65) | Bias (0.72) | Bias (0.72) | Bias (0.80) | Agreement: biased political/group framing |
| 7 | Bias (0.82) | Bias (0.78) | Bias (0.82) | Bias (0.80) | Agreement: ethnocentric/political bias |

## Case 1

Text preview: "Shockingly, Republicans have kept the very important position of 'Parliamentarian' in the hands of a woman..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.92 | Bias signal detected | Political ideology (0.95), Gender (0.65), Race / ethnicity (0.55) | Strong partisan hostility plus weaker gender/race cues |
| GPT-5.5 | ok | 0.93 | Bias signal detected | Political ideology / party affiliation (0.96), Gender / sexism (0.72), Religion / ethnicity (0.61) | Strong partisan bias with moderate sexist/religious-ethnic framing |
| Claude-Opus-4.8 | ok | 0.88 | Bias signal detected | Political ideology (0.92), Gender / sexism (0.60), Religion (0.55) | Heavy partisan attack language with weaker demographic bias |
| Llama-3.3-70B-Instruct | ok | 0.92 | Bias signal detected | Political ideology (0.95), Gender (0.62) | Strong anti-Democrat rhetoric and some gender signal |

## Case 2

Text preview: "We need THE SAVE AMERICA ACT passed, and NOW..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.87 | Bias signal detected | Political ideology (0.92) | Derogatory partisan framing and fear-based claims |
| GPT-5.5 | ok | 0.81 | Bias signal detected | Political ideology / party affiliation (0.81) | Mostly partisan advocacy, but with loaded labels |
| Claude-Opus-4.8 | ok | 0.72 | Bias signal detected | Political ideology (0.80) | Moderate-to-strong ideological bias |
| Llama-3.3-70B-Instruct | ok | 0.92 | Bias signal detected | Political ideology (0.95) | Strong explicit partisan bias |

## Case 3

Text preview: "We hold these truths to be self-evident, that all men are created equal..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.00 | No signal | - | Historical text expressing universal rights |
| GPT-5.5 | ok | 0.18 | No signal | - | Historical political philosophy, not a group attack |
| Claude-Opus-4.8 | ok | 0.20 | No signal | - | Declaration text, not demographic/social bias |
| Llama-3.3-70B-Instruct | ok | 0.20 | No signal | - | Universal-equality framing, no bias signal |

## Case 4

Text preview: "But when a long train of abuses and usurpations..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.00 | No signal | - | Historical grievance text, not present-day bias |
| GPT-5.5 | ok | 0.62 | Bias signal detected | Political ideology (0.66) | Read the anti-monarchy rhetoric as political-ideology bias |
| Claude-Opus-4.8 | ok | 0.15 | No signal | - | Historical political philosophy, not bias |
| Llama-3.3-70B-Instruct | ok | 0.80 | Bias signal detected | Political ideology (0.90) | Strongly interpreted the anti-government rhetoric as ideological bias |

Note: this is one of the two biggest disagreement cases. GPT-5.5 and Llama treated the revolutionary rhetoric as political-ideology bias, while DeepSeek and Claude treated it as historical text without bias.

## Case 5

Text preview: "The Industrial Revolution and its consequences have been a disaster for the human race..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.15 | No signal | - | Broad anti-technology critique, not group bias |
| GPT-5.5 | ok | 0.58 | Bias signal detected | Nationality / socioeconomic development (0.62) | Flagged "advanced countries" / "Third World" as mild bias |
| Claude-Opus-4.8 | ok | 0.20 | No signal | - | Opinionated, but not demographic/social bias |
| Llama-3.3-70B-Instruct | ok | 0.20 | No signal | - | Critical of industrialization, not a group attack |

Note: this is the other major disagreement case. Only GPT-5.5 flagged mild bias, mainly around development-hierarchy language.

## Case 6

Text preview: "Welcome to the official Autonomous Proud Boys website..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.65 | Bias signal detected | Political ideology (0.70), Race / ethnicity (0.55) | Adversarial political framing plus coded race signal |
| GPT-5.5 | ok | 0.72 | Bias signal detected | Political ideology (0.72) | Broad hostility toward media/the left |
| Claude-Opus-4.8 | ok | 0.72 | Bias signal detected | Political ideology (0.78) | Politically hostile generalizations, with race invoked defensively |
| Llama-3.3-70B-Instruct | ok | 0.80 | Bias signal detected | Political ideology (0.90), Race (0.60) | Strong ideological bias and weaker race signal |

## Case 7

Text preview: "A unified group of freedom-loving people across the globe..."

| Model | Status | Score | Signal | Top categories | Short rationale |
|---|---|---:|---|---|---|
| DeepSeek-V4-Pro | ok | 0.82 | Bias signal detected | Political ideology (0.85), Race / ethnicity (0.78), Gender / sexism (0.65) | Strong ethnocentric and political in-group framing |
| GPT-5.5 | ok | 0.78 | Bias signal detected | Ethnocentrism / nationality / cultural identity (0.82), Political ideology (0.64) | Main signal is "Western Chauvinists" as explicit cultural superiority |
| Claude-Opus-4.8 | ok | 0.82 | Bias signal detected | Immigration / nationality (0.80), Gender / sexism (0.58) | Read "Western Chauvinists" as nationality/cultural-superiority bias |
| Llama-3.3-70B-Instruct | ok | 0.80 | Bias signal detected | Political ideology (0.90) | Strong exclusionary political framing |

## Main Patterns

- Cases `1`, `2`, `6`, and `7` were consistently flagged as biased by all 4 models.
- Case `3` was consistently treated as not biased by all 4 models.
- Cases `4` and `5` showed the biggest disagreement across models.
- `GPT-5.5` was the most likely model here to flag milder/indirect bias in historical or philosophical text.
- `Claude-Opus-4.8` and `DeepSeek-V4-Pro` were more conservative on cases `4` and `5`.
