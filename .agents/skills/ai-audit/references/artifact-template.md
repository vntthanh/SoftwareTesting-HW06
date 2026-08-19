# Artifact Template

Use this exact template for every completed user/AI interaction. Replace bracketed instructions with actual content and preserve the review TODOs.

`````markdown
### Artifact [X]

- **User:** [Insert the exact, verbatim user name or identifier who initiated the interaction here. If unknown, use "TODO: Unknown".]
- **Date and Time:** [Insert Current Date and Time, GMT+7]
- **Model Used:** [Identify the model(s) involved in the interaction. If multiple models were involved, list them all. If no specific model can be identified, use "TODO: Unknown".]
- **Skill Used:**  [Identify the agent skill(s) involved in the interaction. If multiple skills were involved, list them all. If no specific skill can be identified, use "TODO: Unknown".]
- **Prompt:**

````markdown
[Insert the exact, verbatim user prompt here. Do not paraphrase or summarize.]
````

- **AI Output:**

````markdown
[Insert the exact, verbatim AI response here, preserving all original markdown formatting, lists, and code blocks.]
````

- **File Modifications:** [Use `None` if the AI output did not modify files. Otherwise, insert the required file modification details.]
- **Verdict:** TODO: VALID / INVALID / INCOMPLETE
- **Reasoning:** TODO: Your reasoning here
- **Student Fixes:** TODO: Your fixes here
`````
