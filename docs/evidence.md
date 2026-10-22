# Evidence and publishing checklist

Live Ubuntu VM verification is pending. Mark an item complete only after the user actually performs and confirms it. Synthetic examples and GitHub runner output are not VM deployment evidence.

- [ ] Verify the SSH host fingerprint from the VM console and complete a Windows-to-guest login.
- [ ] Record actual SSH service/socket state and explain any socket activation difference.
- [ ] Record the actual test count, result and exit code on the guest.
- [ ] Record the actual audit exit code and warnings; compare disk and memory readings to `df -B1 /` and `free -k`.
- [ ] If tried, record observed behavior of `--disk-warn 1`; a warning depends on measured usage.
- [ ] Adapt the architecture diagram to the actual environment.
- [ ] Record a genuine troubleshooting incident if one occurs; do not invent one.
- [ ] Review report text, screenshots and changed files for secrets and personal host/network details before publishing.
- [ ] Confirm automated checks separately from the user's VM verification.

## Safe evidence record

A sanitized summary may include date, Python/Ubuntu versions, test count, exit codes, warning text and an explanation of comparisons. Remove usernames, real hostnames, IPs, personal paths, keys and credentials. Save raw reports privately outside the repository; `reports/` is ignored as a secondary guardrail. Do not rely on ignore rules or a pattern scan to prove absence of secrets.

Redacted screenshots can later go in `docs/screenshots/`, after explicit review. Do not attach full terminal transcripts automatically.

## Resume wording — only after user-verified deployment

> Developed and tested a read-only Linux health-audit CLI in Python to assess disk, memory, SSH service status and default IPv4 route availability; verified it on an Ubuntu lab through remote SSH administration, with separate GitHub Actions checks.

Until then, describe the implementation and automated tests only; do not claim the Ubuntu deployment or operational outcome is complete.
