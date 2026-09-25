# Unraid 7.2.4 runtime smoke result

Recorded from the isolated automated test. No credentials or private host addresses are included.

```json
{
  "startedAt": "2026-09-25T19:16:38.155023+00:00",
  "image": "ghcr.io/paperclipai/paperclip:latest",
  "checks": [
    "Authenticated startup using the XML settings",
    "Dashboard HTML is served",
    "Anonymous access to company data is denied",
    "Fresh persistent storage receives the configured UID/GID",
    "Application process runs as the configured non-root user",
    "First account can sign up",
    "Private deployment supports browser first-admin claim",
    "Authenticated administrator can create a company",
    "Account session and company persist across restart",
    "Account session and company persist across container recreation",
    "Fresh login works against the persisted database"
  ],
  "success": true,
  "imageId": "sha256:61d20a50453c2535d0707a0656b0e4d9e7c094ac75d1077e8e6be8525f4e4622",
  "repoDigests": [
    "ghcr.io/paperclipai/paperclip@sha256:a02ac35ac41df911af477422ea0e781cf41d2b2c600c66f0a5ac9d8c63f52c2c"
  ],
  "architecture": "amd64",
  "sourceRevision": "d554c4789ed3930f8a53ac9fdf6503b3187097da",
  "cleanupErrors": [],
  "finishedAt": "2026-09-25T19:17:32.689956+00:00",
  "hostPlatform": "Unraid 7.2.4 / Docker 27.5.1",
  "templateCommit": "5aeaefe"
}
```
