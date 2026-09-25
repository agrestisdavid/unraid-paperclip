# Community Applications submission

## Repository details

- Repository: https://github.com/agrestisdavid/unraid-paperclip
- Branch: `main`
- App name: `Paperclip-Upstream`
- Template: `templates/paperclip.xml`
- Repository profile: `ca_profile.xml`
- Support: https://github.com/agrestisdavid/unraid-paperclip/issues
- Image: `ghcr.io/paperclipai/paperclip:latest`
- License: MIT

## Existing listing

The [existing BitCryptic Paperclip listing](https://ca.unraid.net/apps/paperclip-1khajpx0l4tpep) was marked deprecated and unsupported as of September 20, 2026, when checked on September 25, 2026. It uses a separately maintained image and requires external PostgreSQL.

This submission uses the upstream Paperclip AI image and its embedded database, with authenticated private-network setup and Unraid UID/GID defaults. Explain this distinction to reviewers. Acceptance, naming and treatment of the older listing remain decisions for the CA team. This is a fresh-install template, not an automatic migration from that older package.

## Before submission

- [ ] Confirm the latest GitHub Actions validation and container smoke test are green.
- [ ] Complete the Unraid acceptance test below and record the version/results in `docs/VALIDATION.md`.
- [ ] Verify public raw TemplateURL and icon URLs are reachable without signing in.
- [ ] Confirm that GitHub Issues is the support channel you will maintain. A forum announcement draft is provided separately if you prefer forum support; update the XML links only after that thread exists.
- [ ] Confirm the repository is public, active, has its root MIT LICENSE, and contains no credentials or private configuration.

## Unraid acceptance test

1. Download the template as described in README and confirm **Paperclip-Upstream** appears under **Add Container**.
2. Use a new dedicated test Appdata directory and an unused host port. Fill Public URL and both generated secrets.
3. Verify installation, container logs, WebUI, account creation and the first-administrator claim.
4. Create a test company. Restart the container and confirm the company and account survive.
5. Recreate the container with the same Appdata and secrets; confirm that the company and account remain.
6. Check that files use the configured UID/GID and that no database port or Docker socket is exposed.
7. Enable Autostart and verify startup during a planned array/server restart. Do not interrupt an active server just to perform this check.
8. Stop the test container, back up its Appdata and private template, then verify restoration into another isolated test instance.
9. Record the Unraid version, image digest and results. Remove only the disposable test instance and its data when finished.

## Submit

The current authoritative entry point is [ca.unraid.net/submit](https://ca.unraid.net/submit). Follow its [submission help](https://ca.unraid.net/submit/help), add this public repository, then run **Validate** and **Scan**. Resolve reported issues and submit for review yourself.

This repository's validator catches common mistakes but is not the official CA validator and cannot guarantee acceptance. Run the portal's checks again after meaningful XML changes. No CA submission or forum message is sent automatically by this repository.

## Suggested reviewer note

> This community-maintained template installs the official Paperclip AI GHCR image with embedded PostgreSQL. It provides authenticated private-network setup, persistent Appdata, Unraid UID/GID defaults, an English setup guide and automated runtime checks. The older BitCryptic Paperclip listing is marked deprecated; this template uses the upstream-maintained image and a different database layout. We request review as a maintained upstream-image option. Support is provided through the repository's GitHub Issues.

## References

- [CA builder guide](https://ca.unraid.net/submit/help/builders)
- [Repository XML format](https://ca.unraid.net/submit/help/repository-xml)
- [Repository profile requirements](https://ca.unraid.net/submit/help/repository-info-xml)
- [Supported public XML fields](https://ca.unraid.net/submit/help/xml-field-reference)
- [Paperclip Docker documentation](https://docs.paperclip.ing/reference/deploy/docker/)
