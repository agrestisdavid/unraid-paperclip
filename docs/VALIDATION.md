# Validation record

Prepared on September 25, 2026.

## Upstream provenance

- Stable release: `v2026.916.1`
- Image: `ghcr.io/paperclipai/paperclip:latest`
- OCI index digest observed: `sha256:a02ac35ac41df911af477422ea0e781cf41d2b2c600c66f0a5ac9d8c63f52c2c`
- Image source revision: `d554c4789ed3930f8a53ac9fdf6503b3187097da`
- Published platforms observed: `linux/amd64`, `linux/arm64`
- Template runtime test target: Linux AMD64. Unraid installation support is scoped to its x86-64 Docker environment.

The registry was queried anonymously. The image's entrypoint, default environment and stable source were inspected for UID/GID mapping, embedded database storage and authenticated setup. `latest` is mutable; each CI smoke run records the image it actually tested.

## Compatibility finding

An initial runtime test on Unraid 7.2.4 and GitHub's Linux runner exposed an upstream limitation when setting `USER_UID=99` and `USER_GID=100`: embedded PostgreSQL could not create a native-library symlink under `/app/node_modules` (`EACCES`). The template therefore keeps the upstream `1000:1000` defaults. It does not work around this by granting privileged mode or changing application-file permissions at runtime.

## Results

- Local XML/repository validation: passed on September 25, 2026.
- Unraid 7.2.4 / Docker 27.5.1 runtime smoke test: passed with 11 checks; see [the recorded result](validation/unraid-7.2.4-smoke.md).
- GitHub-hosted Linux Docker authentication and persistence smoke test: passed with 11 checks on September 25, 2026 ([successful workflow run](https://github.com/agrestisdavid/unraid-paperclip/actions/runs/36178771145)).
- Native Unraid Docker Manager installation, saved WebUI metadata and Autostart configuration: verified as described below. A planned array/server reboot and backup restoration remain untested.
- CA portal Validate/Scan: not yet run.
- CA submission: not submitted.

The Unraid runtime check verified authenticated startup, dashboard HTML, rejection of anonymous company access, data ownership, the non-root application process, signup, first-admin claim, company creation, restart persistence, recreation persistence and fresh login. It used an isolated Docker volume and a loopback-bound host port with a simulated LAN hostname. All test containers and volumes were removed afterward; the original 42 running containers remained running.

CI results are available under [Actions](https://github.com/agrestisdavid/unraid-paperclip/actions). A passing Docker smoke test must not be described as a completed Unraid Docker Manager UI or CA moderation test.

## Native Unraid installation

On September 25, 2026, the template was also installed persistently on Unraid 7.2.4 using Docker Manager's own `xmlToCommand` compiler. The saved user template, `dockerman` management label, WebUI link, appdata bind mount and native Autostart entry were verified. The authenticated WebUI was reachable from another LAN computer, and a clean restart and container recreation preserved the data directory and settings. First-account setup remains an interactive operator step.

Docker Manager caches icons as PNG files, so the template now references the original upstream PNG asset. The cached file's PNG signature was verified. This integration check does not replace a visual browser check or a physical server/array reboot test.

## Browser follow-up

The first browser check exposed a gap in the HTTP smoke test: a successful HTML response does not prove that the interface has rendered. On the tested upstream release, a fresh unauthenticated visit to `/` initially displays `Loading…` while the experimental-settings query retries HTTP 403 responses. The setup screen eventually appears after those retries; large initial asset downloads can add further delay.

The template now opens `/auth` directly. On September 25, 2026, Playwright Chromium and WebKit 26.5 rendered that sign-in page successfully over a LAN HTTP connection. WebKit with an iPhone 13 viewport also switched to the registration form with no JavaScript page errors; the resulting screenshot was inspected. This is browser-engine emulation, not a test on a physical iPhone. No production account was created during the browser check.

The installed Unraid template and container WebUI label were updated together. The image, environment, storage, port mappings and native Autostart entry were preserved. The public URL remains the origin without `/auth`. These checks cover entry into the authentication UI; the existing API smoke test separately covers signup, the first-admin claim and persistence.

## Codex subscription sign-in

An operator's successful device login from the root container console created private root-owned files in Paperclip's isolated sign-in directory. The application user (`1000:1000`) could not read `auth.json`, and cancellation/retry requests failed with `EACCES`. Changing ownership only within the affected sign-in directory, while preserving permission modes and file contents, restored access. Both `codex login status` and Paperclip's own `readVerifiedLocalAiCredential("openai", ...)` check then passed as the application user. The latter includes the upstream account/quota check; no agent task was run for this verification.

The README now requires running the generated sign-in command as `1000:1000` and retaining its attempt-specific `CODEX_HOME`. This is an operator workflow requirement; the template does not change the default user of Docker Manager's console.
