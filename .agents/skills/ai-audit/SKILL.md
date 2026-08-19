---
name: ai-audit
description: Export available AI-user conversations to an input-provided AI_Audit.md file or the default ./AI_Audit.md, creating the standard Group 04 report when the target is missing and appending verbatim, numbered audit artifacts with GMT+7 timestamps, agents, file modifications, and review TODOs. Use when asked to log, export, audit, record, append, or save AI interactions or when a workflow requires audit documentation for AI-produced file edits.
---

# AI Audit

Export the available conversation through one workflow that resolves, initializes, and appends to the audit document.

## Workflow

1. Resolve the target audit document:
   - If the user input includes an `AI_Audit.md` file or an explicit path to one, use that file.
   - Otherwise, use `./AI_Audit.md` in the current working directory.
   - If the resolved target does not exist, read [references/initialization-template.md](references/initialization-template.md), create the target from that exact template, and replace `[Current Date in GMT+7]` with the actual current date in GMT+7.
   - If the resolved target exists, skip initialization without changing its existing header and continue to step 2 immediately.
2. Identify every completed user prompt and corresponding AI response available in the current conversation context, in chronological order. Include the whole available conversation, not only the latest completed turn. Do not invent a response for the current in-progress turn.
3. Capture the current date and time in GMT+7.
4. Read the resolved audit document, count the existing `### Artifact` headings, and choose the next artifact number. Start with `### Artifact 1` when none exist.
5. Read [references/artifact-template.md](references/artifact-template.md) and create one artifact block from that exact template for each available user/AI pair. Increment artifact numbers in chronological order.
6. Determine whether each AI response created, edited, appended to, deleted content from, replaced content in, or deleted any file. Record those details in the corresponding artifact; otherwise use `None`.
7. Append all completed artifact blocks to the resolved audit document.

## Document file modifications

For each modified file, provide concise, explicit bullets under `File Modifications`:

- `File:` exact path.
  - `Action:` created, edited, appended, deleted content, replaced content, or deleted file.
  - `Deleted:` exact removed content, or `None`.
  - `Replaced With:` exact replacement content, or `None`.
  - `Appended:` exact appended content, or `None`.

If exact changed text is too large to include safely, give the path, known line numbers or section names, and a faithful summary. Never invent file changes that are not visible in the conversation or tool output.

## Preserve audit integrity

- Copy each prompt and AI response verbatim. Do not summarize, paraphrase, or compress them.
- Export each available completed interaction as a separate artifact. Do not collapse multiple prompts into one artifact.
- Append only artifact blocks after initialization; do not add another report header or student table.
- Preserve the `TODO` placeholders for verdict, reasoning, and student fixes.
- Use quadruple backticks with the `markdown` language identifier around prompts and outputs.
- If exact prompts or responses are unavailable, export only exact completed interactions that are available. Do not fabricate missing content.
- After appending, state `Artifacts [first]-[last] successfully appended to [resolved audit document path]`. If some interactions were unavailable, add that limitation to the same one-sentence response.
