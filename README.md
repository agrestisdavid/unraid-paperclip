# Paperclip for Unraid

[![Validate and smoke test](https://github.com/agrestisdavid/unraid-paperclip/actions/workflows/validate.yml/badge.svg)](https://github.com/agrestisdavid/unraid-paperclip/actions/workflows/validate.yml)

A community-maintained Unraid Docker template for [Paperclip](https://github.com/paperclipai/paperclip), an application for managing teams of AI agents, tasks, approvals and budgets.

The template uses **`ghcr.io/paperclipai/paperclip:latest`**, published by Paperclip AI. It runs the dashboard and embedded PostgreSQL in one container. This repository does not build or republish Paperclip and is not an official Paperclip AI or Unraid project.

**CA status:** prepared for submission; not yet submitted or approved. See [submission instructions](docs/CA-SUBMISSION.md) and [validation evidence](docs/VALIDATION.md).

## Install on Unraid

Until Community Applications accepts this repository, install the template manually from an Unraid terminal:

```sh
install -d /boot/config/plugins/dockerMan/templates-user
curl --fail --location --output /boot/config/plugins/dockerMan/templates-user/my-paperclip-upstream.xml \
  https://raw.githubusercontent.com/agrestisdavid/unraid-paperclip/main/templates/paperclip.xml
```

This downloads the template only. In **Docker → Add Container**, select **Paperclip-Upstream** and configure:

| Setting | What to enter |
| --- | --- |
| WebUI port | `3100`, or an unused host port |
| Appdata | A dedicated directory, default `/mnt/user/appdata/paperclip` |
| Public URL | Your actual browser address, such as `http://tower:3100` |
| Authentication secret | Output of `openssl rand -hex 32` |
| Tool action signing secret | Output of a second, separate `openssl rand -hex 32` |

Use local storage for Appdata, preferably an SSD pool. Do not point this template at the data directory of a different Paperclip image or an existing PostgreSQL container. The entrypoint updates ownership within Appdata; it must be a dedicated directory.

Click **Apply**, wait for initialization, and open **WebUI**. The link opens `/auth` directly. Select **Need an account? Create one**, create your account, and complete the first-administrator claim on the setup screen. Existing sessions are redirected into the application. Keep the installation on your trusted private network during initial setup. No model API key is needed to start the dashboard; configure credentials when adding agents.

Enable **Autostart** for the container in the Unraid Docker tab after setup. Unraid then manages startup with the array. This template does not force a separate Docker restart policy. For crash recovery, configure your preferred Unraid monitoring/restart mechanism deliberately.

## Networking and authentication

The template uses bridge networking and publishes only port `3100/tcp`. Embedded PostgreSQL is internal to the container. It does not mount the Docker socket or require privileged mode.

`PAPERCLIP_PUBLIC_URL` must match the browser origin, including a non-default host port, for example `http://tower:3100`. Keep the `/auth` path in the WebUI link only. Unlike the WebUI field, environment variables do not expand Unraid's `[IP]` and `[PORT]` placeholders. Add optional aliases with **Additional hostnames**; the Public URL host is already included.

For a private HTTPS reverse proxy, set Public URL to the HTTPS address and configure the proxy for WebSockets and long-lived event streams. The Unraid WebUI link defaults to the direct HTTP address; edit that field if you use only the proxy. The `private` setting is an application mode, not a firewall. Internet-facing deployments require the separate [upstream public deployment configuration](https://docs.paperclip.ing/reference/deploy/deployment-modes/), including an external database.

**Use HTTPS for normal browser use.** The tested upstream release calls `crypto.randomUUID()` when sending task messages, but browsers do not provide that method on a plain HTTP LAN origin. The sign-in page can work while sending a message silently fails. A temporary, version-checked workaround is documented below; direct HTTP is not yet a fully validated CA deployment path.

## Connect Hermes on another computer

Use Paperclip's built-in **Hermes Gateway** (`hermes_gateway`) adapter. Enable a Hermes API server for the intended profile, make it reachable from the Paperclip container, and store its `API_SERVER_KEY` in Paperclip's secret storage. Prefer HTTPS for a remote endpoint; remote plain HTTP is blocked by the adapter by default.

Use one Paperclip agent per Hermes role/profile and select the corresponding API endpoint. Keep the default issue-scoped session strategy for separate tasks. A Hermes installation on Windows must be running when Paperclip dispatches work to it. A local adapter inside this container cannot launch a Windows CLI on another machine.

See the [Hermes Gateway documentation](https://docs.paperclip.ing/reference/adapters/hermes-gateway/). This template does not copy Hermes profiles, persona files, Honcho memories or credentials into the container.

## Connect a Codex subscription

In Paperclip, start a Codex subscription connection and copy the sign-in command shown for that connection. Open a shell as the application user from the Unraid host terminal:

```sh
docker exec -it --user 1000:1000 Paperclip-Upstream bash
```

Paste Paperclip's command into that shell and complete the device login, then return to the same connection in Paperclip and click **Connect**. Preserve the command's generated `CODEX_HOME`: it identifies this specific sign-in attempt. If you already opened the container console from Docker Manager, run `gosu node bash` before pasting the command.

Docker Manager's container console starts as root in this image. Running the login there as root creates private authentication files that the Paperclip application user cannot read. This can cause subscription verification to fail and `EACCES` errors when cancelling or restarting sign-in. Run the login as `1000:1000`; do not make token files world-readable or run the application as root. See the [official Codex authentication documentation](https://developers.openai.com/codex/auth) for device login and subscription authentication.

## Storage, backup and updates

Everything under `/paperclip` is persisted through Appdata, including embedded PostgreSQL, uploads, workspaces and local encryption material. The application runs with the upstream defaults `USER_UID=1000` and `USER_GID=1000`. Keep these defaults: the tested upstream release cannot initialize embedded PostgreSQL after remapping to Unraid's usual UID 99, because it needs to create native-library symlinks within the image. The entrypoint assigns Appdata ownership to `1000:1000`; no privileged container is needed. The image uses `USER_UID`/`USER_GID`, not `PUID`/`PGID`.

Before an upgrade:

1. Stop the container cleanly.
2. Back up the entire Appdata directory and your configured Unraid template, including the two secrets. Treat both backups as private.
3. Record the current image version/digest and review the [upstream release notes](https://github.com/paperclipai/paperclip/releases).
4. Update through Unraid and verify login, companies and agent configuration.

`latest` tracks upstream stable releases. To hold a tested version, change Repository to an available upstream version tag or immutable digest. Database migrations may prevent a simple image downgrade; restore the matching pre-upgrade data backup when rolling back. Do not copy a running embedded database as a substitute for a consistent backup.

## Troubleshooting

- **Startup fails:** inspect the container log, confirm the two secrets and Public URL are set, and check Appdata permissions and free space. Initial database setup takes longer than later starts.
- **WebUI stays on Loading:** open `/auth` directly, for example `http://tower:3100/auth`. In the tested upstream release, the root route waits for retries of settings requests rejected before login, delaying the setup screen. The template's WebUI link bypasses that initial route. For an existing installation, edit its WebUI field to `http://[IP]:[PORT:3100]/auth` in Advanced View and apply; downloading the updated public template does not change an existing container. Initial asset downloads may also take longer on a slow connection.
- **Send does nothing over LAN HTTP:** use HTTPS. For the tested upstream revision only, run `python3 scripts/http_uuid_compat.py` from a checkout of this repository on the Docker host, then reload the page. This adds a UUID fallback using the browser's cryptographic random generator before the application starts, saves the original HTML in Appdata, and does not restart the container. Restore with `python3 scripts/http_uuid_compat.py --restore`. The workaround survives an ordinary restart, but container recreation or an image update removes it. It only addresses UUID generation; it does not add HTTPS or implement other secure-context browser APIs.
- **Login redirects or origin errors:** check the browser URL against Public URL; update it when changing the host port or proxy address.
- **Permission errors:** keep `USER_UID=1000` and `USER_GID=1000`, and ensure the chosen Appdata path is writable. Do not add `--user` to bypass the upstream entrypoint's permission setup.
- **First administrator already claimed:** sign in using the account that claimed the installation. Do not delete Appdata to repair an account problem.
- **Hermes connection fails:** test reachability from the container, confirm HTTPS and the API key, and make sure the correct profile API is running.

Report template problems in [this repository's issues](https://github.com/agrestisdavid/unraid-paperclip/issues). Include Unraid version, image tag/digest, settings with secrets removed, and relevant redacted logs. Application bugs belong in the [upstream project](https://github.com/paperclipai/paperclip/issues).

## Development

```sh
python scripts/validate.py
python scripts/smoke_test.py
```

The validator uses Python's standard library. The smoke test also needs a Linux Docker engine, internet access and several GB of free disk space. It parses the actual XML, pulls the configured image, uses isolated temporary storage, verifies authentication and database persistence across restart and recreation, and removes only its own containers and volume. It does not call an LLM or connect to a real Hermes installation.

GitHub Actions runs both checks on pushes and pull requests. The smoke test is a Linux Docker check; it does not replace the Unraid UI acceptance steps in [the submission checklist](docs/CA-SUBMISSION.md).

## License and attribution

Template, documentation and validation scripts: [MIT](LICENSE). Paperclip and the bundled upstream icon retain their [upstream MIT license](LICENSES/Paperclip-MIT.txt). See [third-party notices](THIRD-PARTY-NOTICES.md).
