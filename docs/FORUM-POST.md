# Optional forum support post draft

Suggested title: `[Support] agrestisdavid - Paperclip (upstream image)`

This is a draft for the maintainer to post after completing the Unraid acceptance test. Do not state that CA has accepted the app until it has.

---

This Unraid template runs Paperclip, an open-source application for coordinating AI agents, tasks, approvals and budgets, using the official upstream Docker image.

- Repository and installation: https://github.com/agrestisdavid/unraid-paperclip
- Container image: `ghcr.io/paperclipai/paperclip:latest`
- Upstream project: https://github.com/paperclipai/paperclip
- Template issues: https://github.com/agrestisdavid/unraid-paperclip/issues

The container includes embedded PostgreSQL. Set an Appdata directory, the browser-facing Public URL and two independently generated secrets before starting. Create your account and claim the first administrator through the WebUI. Autostart is enabled separately in Unraid's Docker tab.

Remote Hermes installations can connect through Paperclip's Hermes Gateway adapter. Agent credentials are configured after installation; the dashboard does not need a model API key to start.

This is a community template for the upstream image. It is independent of Paperclip AI and does not automatically migrate installations from the deprecated BitCryptic package.

When reporting a problem, include the Unraid version, image tag/digest and redacted container logs. Remove passwords, API keys, session cookies and claim/invite links before posting.
