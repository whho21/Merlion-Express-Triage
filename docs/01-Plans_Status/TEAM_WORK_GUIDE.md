# Team 2 work guide — Merlion Express

**Status:** Proposed team working agreement, 15 Nov 2026. Agree this guide at the team sync and update it through a pull request (PR). Times and dates use Singapore time.

## 1. Repository and source of truth

Work in the course submission repository: `https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express`. Application code, deliverables, feature branches, PRs, CI and checkpoint commits belong here. Merge finished work into its `main` before each deadline. In the local clone, the instructor remote is named `instructor`; name it explicitly in commands so there is no ambiguity.

Follow the client brief, checkpoint list and harness checklist in this repository. Use `docs/01-Plans_Status/Capstone_TEAM_PLAN_v0.5.md` for the current proposed plan, `docs/02-Design/contracts.md` for shared interfaces, individual task lists for status and `docs/01-Plans_Status/delivery_RID.md` for risks, issues and decisions. If an accepted decision changes the plan, update the plan or link the decision. Keep client data, keys and client-bearing output out of Git.

## 2. One-time local setup

If you do not have the repository yet, clone it with `git clone -o instructor https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express.git`. In the project folder, confirm the remote with `git remote -v`. Configure your own Git name and an email associated with your GitHub account. Each member must commit substantive work under their own identity; use a `Co-authored-by:` trailer when pairing.

Use local `main` as your read-only base for new work. Do not develop or commit directly on it. If an existing clone's `main` cannot fast-forward from `instructor/main`, reconcile that branch once before following the daily steps; do not reset it or discard commits without examining the difference.

## 3. Daily procedure — start of day to handoff

Run commands from the project root. Replace `<branch-name>`, `<github-login>`, `<PR-number>` and other placeholders before running them. The examples use the `instructor` remote, which points to the course submission repository. GitHub CLI (`gh`) commands require installation and sign-in (`gh auth login`); the same PR actions can be performed on GitHub in a browser.

### Step 1 — Start the day by refreshing instructor main

Check your current branch and unfinished changes:

```bash
git status --short --branch
```

If there are uncommitted changes, save them on their existing task branch before switching. Follow Steps 4–5 to review and commit, or temporarily use `git stash push -u -m "unfinished work before daily refresh"`. A stash stays local; it is not a backup or handoff. Restore it with `git stash pop` only after returning to that task branch in Step 2; resolve any conflicts before continuing.

With a clean working tree:

```bash
git fetch instructor --prune
git switch main
git merge --ff-only instructor/main
```

This brings in teammates' changes already merged into instructor `main`. Work that remains on their branches or open PRs is not included. If fast-forward fails, inspect `git log --oneline --left-right main...instructor/main` and reconcile the difference before continuing; do not reset or force-push `main`.

### Step 2 — Create a new branch or continue yesterday's branch

**New task:** choose the prefix from Section 4 and use a short, descriptive, lowercase topic with hyphens:

```bash
git switch -c feature/order-resolution
```

Other examples: `fix/gps-timezone`, `chore/backend-scaffold`, `docs/john-status-2026-11-17` or `review/package-audit`. Use one branch per reviewable outcome.

**Continuing an unfinished task:** switch to its existing branch and merge current instructor `main`:

```bash
git switch <branch-name>
git merge --no-edit instructor/main
```

If another contributor also pushed to this branch, first merge its remote updates with `git merge --no-edit instructor/<branch-name>`, then merge `instructor/main`. Resolve conflicts and rerun the affected checks. If yesterday's PR is still open, keep updating that PR. If it is already merged, create a new branch from refreshed `main` for follow-up work.

### Step 3 — Implement and check the day's work

Read the current plan (`Capstone_TEAM_PLAN_v0.5.md`), your task list, affected contracts and relevant handoffs. Confirm the deliverable and acceptance checks, then implement on the task branch. Keep instructor baseline Markdown files in the project root unchanged; put team documentation under `docs/` or `scripts/` as appropriate.

Run the checks relevant to the change. For a frontend change, for example:

```bash
npm --prefix frontend run lint
npm --prefix frontend run build
```

For backend, ingestion or agent changes, run the applicable tests, count checks or evals provided by those components. Record commands and actual outcomes. Update your task status and any changed RID entry. Mark a task complete only when its acceptance checks pass.

### Step 4 — Stage changes and ask AI to review against the plan

Inspect the changed files before staging everything:

```bash
git status --short
git diff --stat
git add -A
git diff --cached --name-status
git diff --cached --check
```

`git add -A` stages all non-ignored additions, modifications and deletions. Review the staged list and diff for unintended files, client data, secrets and generated output. Remove an unintended file from staging with `git restore --staged -- <path>`; keep sensitive files excluded from the eventual commit.

Ask your AI agent:

> Review all changes on this task branch against instructor/main, including staged and unstaged changes. Use the current capstone plan, my task list, contracts, relevant handoffs and course checklists. Report defects, missing acceptance criteria, integration risks, data or secret leaks, and missing checks with file/line references. Do not edit instructor baseline Markdown files in the project root. Distinguish checks actually run from checks still needed.

For reference, `git diff instructor/main` includes committed branch changes and current tracked edits; `git diff instructor/main...HEAD` alone omits uncommitted work. The developer reviews the AI findings, fixes or explains them, reruns affected checks and stages any fixes:

```bash
git add -A
git diff --cached --check
git diff --cached
```

### Step 5 — Commit the reviewed changes

Use a message describing the outcome; replace the example below:

```bash
git commit -m "feat: add order candidate lookup"
git status --short --branch
```

Only proceed with a clean working tree. Repeat Steps 3–5 for additional reviewable changes during the day. Commit unfinished work honestly on its task branch; it need not be merged into `main` just because the workday ends.

### Step 6 — Refresh others' changes again before pushing

Stay on your task branch:

```bash
git fetch instructor --prune
git merge --no-edit instructor/main
```

For a branch shared with another contributor, also merge `instructor/<branch-name>` before pushing. If Git reports conflicts, use `git status` to identify the files, edit them, then run:

```bash
git add -A
git diff --cached --check
git diff --cached
git merge --continue
```

Use these conflict commands only while a merge is in progress. Review and test the integrated result, including any automatic merge changes. Ask AI to repeat the review if incoming changes affect your work; fix and commit any follow-up changes before pushing. If uncertain how to resolve a merge, `git merge --abort` returns to the state before that merge.

### Step 7 — Push the task branch

```bash
git diff --check
git diff --stat instructor/main...HEAD
git status --short --branch
git push -u instructor HEAD
```

Push only from the named task branch. If rejected because the remote branch advanced, fetch and merge its changes, rerun affected checks and retry. Do not force-push as a shortcut.

### Step 8 — Raise a PR for teammate review

Create the PR in the instructor repository, targeting `main`:

```bash
gh pr create --repo fde-sctp-aieng-FT-Cohort1/team2_merlion_express --base main --head <branch-name> --reviewer <github-login>
```

The command prompts for the title and description. Describe the problem, resulting behaviour, plan/task reference, checks run, remaining limitations and relevant handoff. Choose a reviewer using Section 6. For unfinished work, add `--draft`; update the same PR as work progresses.

Resolve review comments on the same branch, repeat the review/check/commit/refresh/push steps and request another review after material changes. AI review supports the developer and does not replace teammate approval.

### Step 9 — Merge the approved PR, then fast-forward local main

Once a teammate approves the current changes, required checks pass and GitHub permits merging, an authorised merger runs:

```bash
gh pr checks <PR-number> --repo fde-sctp-aieng-FT-Cohort1/team2_merlion_express
gh pr view <PR-number> --repo fde-sctp-aieng-FT-Cohort1/team2_merlion_express --web
```

Check approval and branch compatibility in the PR. If no automated checks are configured, the first command does not establish that testing passed; use the recorded manual results. Merge with **Create a merge commit** in GitHub, or:

```bash
gh pr merge <PR-number> --repo fde-sctp-aieng-FT-Cohort1/team2_merlion_express --merge
```

Follow instructor branch protection and merge policy. If GitHub requires an update, repeat Step 6, push and obtain the required checks/review again. If a merge queue is used, wait for actual merge completion. Confirm the PR state is `MERGED`:

```bash
gh pr view <PR-number> --repo fde-sctp-aieng-FT-Cohort1/team2_merlion_express --json state,mergeCommit
```

Then, with no uncommitted changes:

```bash
git switch main
git fetch instructor --prune
git merge --ff-only instructor/main
git status --short --branch
```

Do not merge a feature branch directly into local `main` and push it as a substitute for the PR process. If the PR is still awaiting review at day's end, leave it open and record its status; continue that task branch tomorrow.

### Step 10 — Ask AI to draft a dependent-work handoff; developer reviews

When another developer depends on this work, ask the AI agent:

> Draft docs/03-Handoffs/<Name>_<YYYY-MM-DD>-<topic>.md using the existing handoff format. Record sender and receiver, Singapore timestamp, delivered scope, merged PR/commit (or explicitly pending PR), contract/version, setup commands, synthetic example or fixture, checks actually run, remaining gaps and the receiver's next action. Keep client data and secrets out. Do not claim unfinished work is merged or verified.

The developer checks the draft against the code and results and corrects it before sharing. Include a handoff in the original task PR when possible. If it is written after the code merges, create a documentation branch from the refreshed `main`:

```bash
git switch -c docs/<name>-handoff-<topic>-<YYYY-MM-DD>
```

Review and publish the handoff through Steps 4–9 using a documentation commit message, then return to refreshed `main`. Request the dependent developer's review and confirm they can follow the setup and next action. A local file or unmerged PR is not yet part of shared `main`; share its PR link when early coordination is needed. Do not create a second handoff just to describe the handoff-only PR.

Command references: [Git merge and fast-forward behaviour](https://git-scm.com/docs/git-merge), [GitHub PR creation](https://cli.github.com/manual/gh_pr_create), [GitHub PR merge](https://cli.github.com/manual/gh_pr_merge).

## 4. Branches and commits

- Create 1 branch for 1 reviewable outcome.

### Branch name convention

| Prefix | Use | Example |
|---|---|---|
| `feature/` | New application behaviour | `feature/order-resolution` |
| `fix/` | Correct a defect | `fix/gps-timezone` |
| `chore/` | Setup, dependencies or tooling | `chore/backend-scaffold` |
| `docs/` | Plan, task status or other documentation only | `docs/john-status-2026-11-17` |
| `review/` | A bounded review or audit with a committed report | `review/package-audit` |
| `issue/` | Work tied to a numbered issue when another prefix is unsuitable | `issue/42-citation-locator` |

### Commit descriptions

- Use a descriptive commit message such as `feat: add order candidate lookup`, `fix: preserve GPS timezone`, or `docs: update checkpoint audit`.
- Keep commits small enough to review.
- Do not mix generated data, dependencies, secrets or unrelated formatting into a task commit.
- A branch may have several commits; preserve their authorship.

A **detached HEAD** is a Git state reached when checking out a commit rather than a branch. It is not part of this workflow. If it happens, create or switch to a named branch before making work you intend to keep.

## 5. Before every push: human and AI review

1. Run the checks relevant to the change (for example frontend lint/build, backend tests, ingestion counts or eval cases). Record the actual commands and outcomes in the PR; do not claim a planned check passed.
2. Ask your AI agent to review the full branch diff against `instructor/main`, specifically using the current capstone plan, this guide, your developer task list, applicable handoff, contracts and course checklist. Ask for defects, missing requirements, privacy leaks and test gaps with file/line references. Treat its findings as review input; the developer resolves or explains them.
3. Inspect `git status`, `git diff --check`, `git diff --stat instructor/main...HEAD`, and the staged file list. Check for client data, API keys, OCR text, indexes, traces and generated output. Confirm each source citation or numeric claim in committed evidence is sanitised and supportable.
4. Push the named branch explicitly: `git push -u instructor HEAD`. Never use `--force` on `main`. If a branch was rebased and needs replacement, coordinate with its collaborators first; prefer a merge when in doubt.

The developer owns the final review and test result even when an agent wrote or reviewed the change.

## 6. PR review and merge

Default reviewer is the main consumer of the change; add another affected owner when a PR changes a shared interface. Named owners: A/Ralph, B/Jenn Fang, C/John, D/Jeffrey and E/Ho Wai Hong; see the v0.5 plan for scope.

| Author role | Default reviewer | Add when the interface is affected |
|---|---|---|
| A — extraction/retrieval | B — loads POD/rate records | C for retrieval-tool or citation contract changes |
| B — data/SQL | C — calls data tools | D for weekly-summary response changes |
| C — API/agent | D — consumes the API; E verifies integration | A or B for changes to their tool contracts |
| D — React/customer journey | C — supplies and reviews the API contract | B for weekly-view definitions; E for integration evidence |
| E — setup/evals/integration/runbook | C — reviews runner and API checks | A/B/D for their cases and setup/journey details |

B owns candidate-order lookup and structured source identity; C owns HTTP routes/models, clarification and orchestration. A/B attach verifiable source references and handle source-specific errors; C validates the final answer; D owns the React journey and displays evidence. E maintains the shared runner, integrated smoke check and demo runbook using C’s starter and owner-supplied cases. Jeffrey leads the pitch, business narrative and client-facing demo, and helps frame client questions. John validates/sends/logs official emails, coordinates submission and leads technical Q&A. Case owners define expectations and fix their own component; E consolidates results. Ralph owns chunking, embeddings/indexing and cited retrieval. Choose the UI operator/backup during rehearsal. These boundaries keep one owner accountable for each handoff.

Open a PR from the branch into the **instructor repository's `main`**. State the outcome, relevant task or RID entry, files affected, checks actually run, evidence, and known limitations. Link related handoffs. Request at least one teammate who did not author the change to review it. For shared contracts or data rules, include the consuming owner. Resolve comments and rerun checks after material changes.

Prefer GitHub's **Create a merge commit** option for team PRs. It preserves the branch's individual commits and authors in `main`, which supports the course's per-person contribution review. Avoid squash merges for substantive multi-author work. Rebase is optional for a developer's own unpublished branch; it rewrites commit IDs and should not be used casually on shared branches. Merge only after the required CI/checks pass, the reviewer approves, and the branch is compatible with current `main`. If branch protection or instructor policy specifies another merge method, follow that policy and preserve authorship where possible.

After merge, switch to `main`, run `git fetch instructor` and `git merge --ff-only instructor/main`, verify the merged commit on the instructor repository, and then start the next branch. Do not delete a branch with unmerged work or force-push to resolve a rejected merge.



If yesterday's docs PR is still open, continue on that branch and update the existing PR instead of opening another. Keep updates concise and coordinate edits to shared plans, contracts and the RID log to avoid conflicts.

## 7. Handoffs, integration and checkpoints

When another owner depends on your work, add a note in `docs/03-Handoffs/` with sender, receiver, contract/version, branch or PR, fixture or sample, how to run it, checks actually run, unresolved gaps and the next action. Use synthetic examples in committed handoffs; the package is now available locally and remains ignored. Interface changes require the affected owner to review the PR and the contract update.

Integrate daily: identify the last end-to-end flow that worked, current failing checks, a blocked interface or source decision, and cumulative API spend. Escalate a blocker to its owner the same day; move a bounded task if one owner is overloaded. Checkpoint 1 is Fri 20 Nov 2026, 17:00 SGT; Checkpoint 2 remains Mon 23 Nov, 09:00 SGT. Before each course checkpoint, verify the required files and app evidence are **merged in instructor `main`**, update the checkpoint list, and confirm every member's substantive commits are visible there. A pushed branch or open PR alone does not satisfy submission.

Keep local client data under ignored `data/`, generated artifacts under ignored `output/`, and credentials outside Git. Use sanitised or synthetic fixtures for CI and portfolio examples. Before publishing a portfolio version, confirm what course code and materials may be reused. Use separate credentials for any hosted version.

## 8. Version history

| Version | Date | Changes |
|---|---|---|
| TEAM_WORK_GUIDE.md | 15 Nov 2026 | Simplified instructor-repository workflow using local `main` |
| TEAM_WORK_GUIDE.md | 16 Nov 2026 | Synced v0.5 ownership: C API, D React, E setup/evals/runbook; Ralph retrieval pipeline and Jeffrey presentation lead; retained daily commands and instructor baseline protection |
