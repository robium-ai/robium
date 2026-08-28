# Robium product-lab editorial system

## The voice

Write like an engineer explaining a result to another capable engineer. The
reader should feel that someone made choices, encountered constraints, and can
say what happened without turning the article into a lab report or a launch
announcement.

- Lead with the result, tension, or decision that makes this app worth reading.
- Prefer concrete nouns and active verbs.
- Use first-person plural only for choices, mistakes, and observations made by
  the team.
- Define a term when it first carries meaning. Do not re-explain it later.
- State run conditions next to the result they qualify.
- Say what a result does not cover once, in the limitations section.
- Keep one short quick start. The README owns exhaustive commands.

## What to avoid

- No em dashes.
- No generic transitions such as “in today’s landscape,” “delve into,” “at its
  core,” or “it is important to note.”
- No inflated adjectives such as “seamless,” “robust,” “revolutionary,” or
  “game-changing” when a measurable description exists.
- No absolute language such as “proves,” “guarantees,” “always,” or “100%” for
  a bounded run.
- Do not repeat the deck in the opening or summarize every section again at the
  end.
- Do not give every article identical headings. The required spine is an edit
  checklist, not visible boilerplate.
- Do not scatter “Robium skills used” callouts through the article. Explain once
  how the guidance changed a decision, test, or boundary.

## The required spine

Each article must answer these questions, in an order that suits the story:

1. What did the application do?
2. Why was this task, policy, simulator, or stack chosen?
3. How do the important parts connect?
4. What is the shortest tested path to run or try it?
5. What happened in the recorded run, and under which conditions?
6. Where did Robium change the implementation or reasoning?
7. What remains limited, expensive, simulated, or untested?

## Natural result language

Prefer:

> The recorded set completed 20 of 20 attempts on LIBERO-Goal task 8. The run
> does not describe other tasks, edited instructions, or a physical Panda.

Avoid:

> This evidence definitively proves that the robust VLA solution achieved
> complete success.

Prefer:

> Seed 1001 reached the simulator's terminal transfer stage with the 100-action
> execution horizon.

Avoid:

> The policy flawlessly solved the task.

## Headlines, decks, and captions

- A headline names the interesting action or decision. Avoid keyword lists.
- A deck adds the reader benefit or boundary. It must not restate the headline.
- Alt text describes what is visible. A caption explains why the image matters,
  whether it is simulated or recorded, and any condition needed to read it.
- Label conceptual work as “Conceptual illustration.” Never make the alt text
  sound like a captured run.

## Final editing pass

Read the article aloud once. Then remove:

1. Any paragraph that repeats the one before it.
2. Any section whose useful sentence can move into another section.
3. Any adjective that claims more than the attached noun.
4. Any first-person sentence that does not describe a real team action.
5. Any em dash, canned transition, or conclusion that only restates the deck.
