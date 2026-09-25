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
- Unraid Docker Manager install, WebUI, Autostart and backup restore: not yet tested.
- CA portal Validate/Scan: not yet run.
- CA submission: not submitted.

The Unraid runtime check verified authenticated startup, dashboard HTML, rejection of anonymous company access, data ownership, the non-root application process, signup, first-admin claim, company creation, restart persistence, recreation persistence and fresh login. It used an isolated Docker volume and a loopback-bound host port with a simulated LAN hostname. All test containers and volumes were removed afterward; the original 42 running containers remained running.

CI results are available under [Actions](https://github.com/agrestisdavid/unraid-paperclip/actions). A passing Docker smoke test must not be described as a completed Unraid Docker Manager UI or CA moderation test.
