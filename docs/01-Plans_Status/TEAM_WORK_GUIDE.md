# Team 2 work guide — Merlion Express

**Status:** Proposed team working agreement, 15 Nov 2026. Agree this guide at the team sync and update it through a pull request (PR). Times and dates use Singapore time.

## 1. Repository and source of truth

Work in the course submission repository: `https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express`. Application code, deliverables, feature branches, PRs, CI and checkpoint commits belong here. Merge finished work into its `main` before each deadline. In the local clone, the instructor remote is named `instructor`; name it explicitly in commands so there is no ambiguity.

Follow the client brief, checkpoint list and harness checklist in this repository. Use `docs/01-Plans_Status/Capstone_TEAM_PLAN_v0.3.md` for the current proposed plan, `docs/02-Design/contracts.md` for shared interfaces, individual task lists for status and `docs/01-Plans_Status/delivery_RID.md` for risks, issues and decisions. If an accepted decision changes the plan, update the plan or link the decision. Keep client data, keys and client-bearing output out of Git.

## 2. One-time local setup

If you do not have the repository yet, clone it with `git clone -o instructor https://github.com/fde-sctp-aieng-FT-Cohort1/team2_merlion_express.git`. In the project folder, confirm the remote with `git remote -v`. Configure your own Git name and an email associated with your GitHub account. Each member must commit substantive work under their own identity; use a `Co-authored-by:` trailer when pairing.

Use local `main` as your read-only base for new work. Do not develop or commit directly on it. If an existing clone's `main` cannot fast-forward from `instructor/main`, reconcile that branch once before following the daily steps; do not reset it or discard commits without examining the difference.

## 3. Daily start of work

1. Check `git status --short --branch`. If there are uncommitted changes, finish, commit or safely set them aside on their existing branch before switching.
2. Run `git switch main`, then `git fetch instructor --prune` and `git merge --ff-only instructor/main`. If fast-forward fails, inspect the divergence and resolve it before starting new work.
3. Create a short-lived task branch with `git switch -c feature/<topic>` (choose the appropriate prefix below). For an existing task, switch to its branch and bring in the latest instructor `main` with `git merge instructor/main`; resolve conflicts and run relevant checks.
4. Read the current plan, your task list, affected contract and applicable handoff. State the deliverable and acceptance check in the task list or PR.

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

Default reviewer is the main consumer of the change; add another affected owner when a PR changes a shared interface. The A–D/name mapping remains subject to team agreement.

| Author role | Default reviewer | Add when the interface is affected |
|---|---|---|
| A — extraction/retrieval | B — loads POD/rate records | C for retrieval-tool or citation contract changes |
| B — data/SQL | C — calls data tools | D for weekly-summary response changes |
| C — API/agent | D — consumes the API | A or B for changes to their tool contracts |
| D — React/HTTP routes/integration | C — supplies and reviews the service contract | B for weekly-view definitions |

B owns candidate-order lookup and structured source identity; C owns clarification and orchestration; D owns thin HTTP routes and validated request/response models. A/B attach verifiable source references and handle source-specific errors; C validates the final answer; D displays the evidence. John coordinates the pitch and checkpoint submission, while D owns the integrated smoke check and demo runbook. These boundaries keep one owner accountable for each handoff.

Open a PR from the branch into the **instructor repository's `main`**. State the outcome, relevant task or RID entry, files affected, checks actually run, evidence, and known limitations. Link related handoffs. Request at least one teammate who did not author the change to review it. For shared contracts or data rules, include the consuming owner. Resolve comments and rerun checks after material changes.

Prefer GitHub's **Create a merge commit** option for team PRs. It preserves the branch's individual commits and authors in `main`, which supports the course's per-person contribution review. Avoid squash merges for substantive multi-author work. Rebase is optional for a developer's own unpublished branch; it rewrites commit IDs and should not be used casually on shared branches. Merge only after the required CI/checks pass, the reviewer approves, and the branch is compatible with current `main`. If branch protection or instructor policy specifies another merge method, follow that policy and preserve authorship where possible.

After merge, switch to `main`, run `git fetch instructor` and `git merge --ff-only instructor/main`, verify the merged commit on the instructor repository, and then start the next branch. Do not delete a branch with unmerged work or force-push to resolve a rejected merge.

## 7. Daily task status, RID and documentation PRs

Each owner updates `docs/01-Plans_Status/Developer-<A-D>_tasklist.md` at the end of the workday: status, what was delivered, PR/evidence link, next step and blocker. Mark ✅ only when the deliverable and its acceptance check exist. John updates cross-team milestones and the course checkpoint list from verified evidence; he does not mark work complete based solely on a status claim.

Anyone who identifies a new risk, active issue or needed decision adds or updates a row in `delivery_RID.md` with owner, date, next action and status. The decision owner records the agreed outcome and date when resolved. Put client questions and answers in `docs/00-Biz_Requirements/client_qa.md`; the RID log links to them rather than copying client data.

A docs-only update may be committed and PR'd before unfinished code is ready. Use a separate worktree so the coding branch and any unfinished code remain untouched. Staging only documentation on a feature branch does not make its PR docs-only if that branch also contains code commits.

### Daily docs-only status procedure

After the documentation scaffold is merged into instructor `main`, set up a docs worktree once from your project folder. Replace `A` and the example date with your role and today's Singapore date:

```bash
git fetch instructor
git worktree add ../team2-docs -b docs/<Your_Name>-status-2026-11-16 instructor/main
```

In `../team2-docs`, follow these steps at the end of each workday:

1. Update your `Developer-<A-D>_tasklist.md`: status, delivered work or PR link, next step and blocker. Update `delivery_RID.md` only when a risk, issue or decision changes.
2. Stage the specific files and inspect the staged diff. Add the RID file only if it changed:

   ```bash
   git status --short
   git add docs/01-Plans_Status/Developer-A_tasklist.md
   # If the RID log changed, also run: git add docs/01-Plans_Status/delivery_RID.md
   git diff --cached
   git diff --cached --check
   ```

3. Ask your AI agent to review the staged changes against the plan, this guide, your task list and any relevant handoff. Resolve findings, then commit. Inspect the full branch diff before pushing:

   ```bash
   git commit -m "docs: update <your name>> task status for 16 Nov"
   git diff --stat instructor/main...HEAD
   git push -u instructor HEAD
   ```

4. Open a PR to the instructor repository's `main`; a teammate reviews and merges it. The push makes status visible in the branch/PR, and the merge makes it part of the shared `main` history.

After that PR merges, start the next day's branch **inside the docs worktree**:

```bash
git fetch instructor
git switch -c docs/<your name>-status-2026-11-17 instructor/main
```

If yesterday's docs PR is still open, continue on that branch and update the existing PR instead of opening another. Keep updates concise and coordinate edits to shared plans, contracts and the RID log to avoid conflicts.

## 8. Handoffs, integration and checkpoints

When another owner depends on your work, add a note in `docs/03-Handoffs/` with sender, receiver, contract/version, branch or PR, fixture or sample, how to run it, checks actually run, unresolved gaps and the next action. Use synthetic examples until the package is available. Interface changes require the affected owner to review the PR and the contract update.

Integrate daily: identify the last end-to-end flow that worked, current failing checks, a blocked interface or source decision, and cumulative API spend. Escalate a blocker to its owner the same day; move a bounded task if one owner is overloaded. Before each course checkpoint, verify the required files and app evidence are **merged in instructor `main`**, update the checkpoint list, and confirm every member's substantive commits are visible there. A pushed branch or open PR alone does not satisfy submission.

Keep local client data under ignored `data/`, generated artifacts under ignored `output/`, and credentials outside Git. Use sanitised or synthetic fixtures for CI and portfolio examples. Before publishing a portfolio version, confirm what course code and materials may be reused. Use separate credentials for any hosted version.

## 9. Version history

| Version | Date | Changes |
|---|---|---|
| TEAM_WORK_GUIDE.md | 15 Nov 2026 | Simplified instructor-repository workflow using local `main` |
