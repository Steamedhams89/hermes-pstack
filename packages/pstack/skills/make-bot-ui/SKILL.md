---
name: Make Bot UI
description: >-
  Use when building a custom page, dashboard, or button that should wake a
  Hermes Agent through an authenticated webhook.
---

# How to make a bot UI

<!-- pstack-hermes-adapter:v1 -->
<!-- PATCH-HERMES-MAKE-BOT-UI -->

Build a small browser UI whose local relay sends a narrow JSON event to Hermes. The browser never receives the Hermes webhook secret. The relay is the only component that signs requests.

Load `skill_view(name='webhook-subscriptions')` before acting. Treat the current Hermes webhook documentation at <https://hermes-agent.nousresearch.com/docs/user-guide/messaging/webhooks> as authoritative when it differs from this adapter.

## Inspect before changing anything

Read the live state first:

- `hermes webhook list`
- the intended local listener and port
- `tailscale status`, only when tailnet access is relevant
- existing relay files and service state

Do not create a duplicate subscription or listener. Do not infer credentials, route names, ports, exposure, or delivery targets.

## Approval boundary

Ask for explicit approval before any of these state changes:

- creating, updating, pausing, resuming, or removing a recurring webhook subscription;
- changing Hermes gateway or security configuration;
- installing software or starting, enabling, or changing a service;
- exposing the relay beyond loopback, including tailnet or other non-loopback exposure;
- sending an external message or taking another externally visible action.

A request to design or build the UI does not authorize those changes. Continue the local, read-only, or isolated work that is not blocked.

## Create the Hermes subscription

After approval, use the supported Hermes CLI rather than editing scheduler state directly:

```text
hermes webhook subscribe <name> ...
```

Set the prompt so that the request body is untrusted data. Name the accepted fields and allowed actions. Reject unknown fields and payloads over a small documented size. Constrain the subscription to the minimum required toolsets and delivery target. A button click must not expand the agent's authority.

Read the subscription back with `hermes webhook list`. Record the exact route name and enabled state without printing secrets.

## Keep the secret server-side

The relay config owns the webhook URL and HMAC key. Keep it outside browser assets, chat, command history, source control, and request logs. Store the config with mode `0600` in a directory that is not web-served.

For Generic V2 requests, the relay sends:

- `Content-Type: application/json`
- `X-Webhook-Timestamp: <unix timestamp>`
- `X-Webhook-Signature-V2: <HMAC signature>`

Compute the HMAC over `<timestamp>.<body>` exactly as required by the current Hermes documentation. Serialize the body once and sign those exact bytes. Use a short timeout, one attempt by default, and an idempotency value when the action could be repeated. Never log the key or full signed headers.

## Host locally first

Bind the relay to `127.0.0.1` by default. Serve static assets and the POST endpoint from the same narrowly scoped local process. The browser sends only the documented action fields to that relay. The relay validates them before signing and forwarding the event.

Do not install dependencies implicitly. If the selected implementation requires a missing runtime or package, report the exact dependency and stop at the approval boundary.

## Optional tailnet access

Tailnet access is a separate, security-relevant choice. Inspect `tailscale status` first. If Tailscale is missing or inactive, do not install it or change its service state without approval.

After explicit approval, prefer `tailscale serve` in front of the loopback relay. Do not replace loopback with a wildcard or publicly reachable bind merely to make it reachable. Reuse the existing node identity and expose only the intended path and port. Public Funnel exposure is outside this workflow unless separately requested and approved.

## Verify the real path

Do not call the UI live until every applicable check passes:

1. The relay health endpoint returns success on loopback.
2. Browser assets contain no webhook key, signed header, token, or private config.
3. The relay rejects unknown actions, malformed JSON, stale timestamps, and oversized bodies.
4. `hermes webhook list` reads back the exact subscription and constrained toolsets.
5. A harmless test button produces one authenticated webhook event and one expected agent receipt.
6. Repeating or refreshing does not duplicate a state-changing action.
7. When tailnet access was approved, the exact served route works and no unintended port is exposed.

If an end-to-end probe would itself send an external message or perform a real action, use a no-op test action or ask for that separate approval. Report the actual HTTP result and Hermes receipt; never infer success from a running process alone.
