---
name: append-bug
description: This agent skill streamlines the bug reporting process by scanning a Test Case document for failed test cases, automatically grouping them by root cause into consolidated issues, generating detailed markdown files for GitHub, and logging summaries in the Bug Report document.
---

# Append Bug

When the user provides the inputs for the "Append Bug" skill, you must execute the following steps sequentially and strictly adhere to the formatting constraints.

## Inputs

Expect these three inputs:

- **Test Case document:** (e.g., `Main_Report.md`, which must contain populated Actual Results and 'Failed' statuses)
- **Bug report document:** (e.g., `Bug_Report.md`)
- **Target Feature ID:** (e.g., `FR-01`)

If one of these is missing, ask only for the missing field.

## Workflow

### Step 1: Analyze and Group Failed Test Cases
1. Locate the specified **Target Feature ID** section within the **Test Case document**.
2. Identify all test cases with a `Failed` status or a populated `Actual Result` that indicates a failure.
3. Analyze the failures and group the impacted Test Case IDs logically by their underlying root cause or shared broken constraint (e.g., grouping all missing UI asterisks together, or grouping all missing string trimmers together).
4. For each distinct group, formulate a short `[bug-slug]` (e.g., `whitespace-validation`) and a clear `[Brief Bug Title]`.

### Step 2: Create GitHub Issue Markdown Files
1. For each distinct bug group, create a new file in the `issues` folder named `bug_[feature-id]-[bug-slug].md` (ensure the file name is lowercase, e.g., `issues/bug_fr01-whitespace-validation.md`).
2. Populate each file using the exact template below, consolidating the information from the grouped test cases:

```markdown
  ---
  labels: bug, [feature-id], [severity-level]
  ---

  ## Bug: [Provide a brief, clear title based on the root cause]

  **Impacted Test Case ID(s):** [List all grouped Test Case IDs, e.g., FR01-TC-02, FR01-TC-03]

  ### Description
  [Insert a concise summary of the root cause affecting these test cases.]

  ### Steps to Reproduce
  [Consolidate the test steps from the impacted test cases into a clear, unified sequence.]

  ### Expected Result
  [Summarize the expected system behavior that was violated.]

  ### Actual Result
  [Summarize the actual failing behavior observed across the grouped test cases.]

  ### Environment
  - **Browser/OS:** [Specify the browser and operating system used during testing]
  - **Version:** [Specify the version of the application or system under test]
  ```

3. **Constraint Check:** State exactly what you did. Output the plain text of the file content you appended. Wrap the edited text in quadruple backticks (````).

### Step 3: Update the Bug Report Document
1. Open the **Bug report document**.
2. Locate the corresponding Feature heading (e.g., `## Feature FR-01: Account Registration`).
3. For each distinct bug group, append a new subsection directly under that feature heading using the format: 
   `### [Brief Bug Title]`
   `**Impacted Test Cases:** [List all grouped Test Case IDs]`
4. Write a 1-2 sentence summary of the bug under this new heading.
5. **Constraint Check:** State exactly what you did. Output the plain text of what you appended. Wrap the edited text in quadruple backticks (````).

### Step 4: Call Audit Agent
After all file edits and constraint checks are successfully completed, call the `$ai-export-audit` agent to log the process.

## Editing Rules
- You must not edit any files silently. Every action must be accompanied by an explanation and the quadruple backtick (````) code blocks showing the exact plain text modifications.
- Do not alter any test cases or feature sections outside of the provided Target Feature ID.
- Preserve existing headings, spacing, and feature order.
- Use the exact feature section already present in the bug report.
- Avoid adding timestamps, status labels, or extra metadata unless the report already uses them.