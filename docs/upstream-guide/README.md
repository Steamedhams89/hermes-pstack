# The pstack guide

Upstream context: pstack 0.14.5 was originally authored for Cursor. This guide describes the complete Hermes-native port.

pstack works best when you state the result and the evidence, then let the matched playbook supply the procedure. Load a qualified skill with `skill_view("pstack:<name>")`. For a multi-step job, `skill_view("pstack:poteto-mode")` selects one of 22 routed playbooks, copies its steps into `todo`, loads narrower skills when needed, and reports the receipts.

The complete product has three parts. The `pstack` content plugin holds all 45 first-class skills: 24 workflows and 21 principles, including `pstack:make-bot-ui`. `pstack-runtime` is optional role-config/state/health support and does not gate Hermes built-in tools such as `delegate_task`, `todo`, `clarify`, `session_search`, and `terminal`. `pstack-benny` preserves three dormant automation procedures. It stays outside the default pack unless the operator separately authorizes and proves an event integration. The two preserved agent prompts are `poteto-agent` and `comment-sicko`; the optional runtime companion can use them as role briefs.

Install the versioned, commit-pinned plugin pack using [Set up pstack](./01-setup.md). Review the pack before installation; installing or enabling a plugin changes the active Hermes profile and is never implied by loading this guide.

Here's what you'll learn:

1. [Set up pstack](./01-setup.md). Inspect the staged packages, understand the role settings, and run a content-only task without changing a live profile.
2. [Route work through `pstack:poteto-mode`](./02-poteto-mode.md). Give it a goal and let it select a playbook.
3. [Understand the code](./03-understand.md). Use `pstack:how`, `pstack:why`, `pstack:teach`, and `pstack:recall` before you edit anything.
4. [Design the change](./04-design.md). Use `pstack:architect`, `pstack:arena`, `pstack:swarm`, and `pstack:interrogate` before code locks in a shape.
5. [Build and clean the change](./05-build-and-clean.md). Follow the build playbooks, `pstack:tdd`, `pstack:unslop`, and `pstack:no-comments`.
6. [Verify and ship](./06-verify-and-ship.md). Prove behavior on the real app, then prepare external delivery without crossing an approval boundary.
7. [Run work while you sleep](./07-overnight.md). Use a bounded contract, a decision log, and an authorized durable schedule when the work must outlive the session.
8. [Steer with principle names](./08-principles.md). Use the 21 first-class principles to redirect an agent mid-task.
9. [Make it yours](./09-make-it-yours.md). Draft your own mode, capture lessons, and test a skill change.
10. [Recipes and pitfalls](./10-recipes-and-pitfalls.md). Copy Hermes-native prompts and avoid the common mistakes.

Read the pages in order the first time. After that, each page stands alone.

Local reading, analysis, reversible edits, and verification stay within the task's stated scope. An external message, commit, push, PR creation or merge, deployment, credential change, deletion, live-profile change, recurring automation, or non-loopback exposure requires explicit current authorization. A playbook name never supplies that authorization.

## If you only remember one thing

Give the agent a goal and a check, in your own words:

```text
skill_view("pstack:poteto-mode")
Goal: the export writes duplicate rows when a retry lands mid-run.
Evidence: reproduce it first, then fix it and show the retry output.
```

You do not need to name a playbook or list skills. The defect and the check are enough routing signal. `pstack:poteto-mode` matches `bug-fix`, puts the playbook steps in `todo`, and loads the required skills as each step begins. If the route needs independent work, Hermes uses `delegate_task`. If an approved `pstack-runtime` route alias exists, the playbook may use `delegate_with_route` instead.

Next: [Set up pstack](./01-setup.md).
