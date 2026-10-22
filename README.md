# Ubuntu Server Foundations — Linux System Audit

**Portfolio project 01 | Linux • Python • SSH • GitHub Actions**

A read-only Linux host health auditor written with Python's standard library. It collects disk pressure, memory usage, SSH service state and default IPv4 route availability without installing an agent or changing system configuration.

> **Verification status:** Starter code, automated tests and a clearly labeled synthetic example are included. The owner's Ubuntu VM deployment and real audit evidence remain **pending user verification**. GitHub runner checks do not prove the owner's VM is healthy.

## Business problem and scope

A technician investigating a slow or unreachable Linux host needs repeatable basic health facts. This CLI provides a small local snapshot suitable for triage and learning. It is a foundation project, not a production monitoring platform, security certification or advanced cloud deployment.

## Architecture

```text
Administrator's SSH client -> Linux host / Ubuntu VM
                                        |
                              python3 -m linux_audit
                                 |      |      |
                               /proc  disk   systemd
                                  \     |     /
                                    JSON / text
                                        |
                                 private review
```

The owner's planned lab uses Windows PowerShell and an Ubuntu Desktop VMware guest. Any supported Linux host can run the audit; VMware and Windows are not requirements. See [architecture](docs/architecture.md).

## Quick start

Requirements: Linux, Python 3.10+, no third-party packages, no sudo required. Run inside Ubuntu, from the repository root:

```bash
git clone https://github.com/KENXTENX/ubuntu-server-foundations.git
cd ubuntu-server-foundations
python3 --version
python3 -m unittest discover -s tests -v
python3 -m linux_audit
python3 -m linux_audit --require-ssh --require-network --json
echo "Audit exit code: $?"
```

Cloning creates a local directory. Audit and test commands do not change host configuration; tests use temporary fixture files and Python may create bytecode caches. For a checkpoint requiring no file writes, use `PYTHONDONTWRITEBYTECODE=1 python3 -m linux_audit` from an existing checkout.

Options: `--disk-path /`, `--disk-warn 85`, `--memory-warn 90`, `--require-ssh`, `--require-network`, `--json`.

Exit codes: **0** = no configured warnings and memory verified; **1** = warning(s), including unavailable memory; **2** = invalid arguments or execution error. Thresholds are inclusive, from 1 through 100. A warning is a finding to investigate, not a command failure to conceal.

## Validate on a real host

1. Follow the [read-only SSH checkpoint](docs/setup.md). Verify host fingerprints from the VM console before accepting a new SSH host key.
2. Run tests and the audit, recording actual exit codes.
3. Compare disk bytes to `df -B1 /` and memory to `free -k`. Disk pressure is `(total - free available to this user) / total`, rounded to one decimal. `df` can show a different percentage because it accounts for reserved blocks differently. Memory is `(MemTotal - MemAvailable) / MemTotal`, not simply `MemFree`; readings change between commands.
4. Optionally try `--disk-warn 1`. Exit 1 is expected only if measured usage reaches 1% (or another warning occurs); it is not a guaranteed synthetic failure. Tests cover the exact threshold deterministically without filling the disk or stopping SSH.
5. Record only genuine findings and resolutions. Stop for user confirmation before making changes to services, firewall or storage.

## Documentation and evidence

- [Architecture and boundaries](docs/architecture.md)
- [Setup and verification gates](docs/setup.md)
- [Troubleshooting notebook](docs/troubleshooting.md)
- [Evidence and publishing checklist](docs/evidence.md)
- [Synthetic example JSON](examples/synthetic-report.json) — invented demonstration values, never live evidence
- [Automated checks](.github/workflows/test.yml) — Python 3.10 and 3.12 unit tests and runner smoke checks

## Security and limitations

- No sudo, configuration changes, network scanning, remote calls or credential collection. The subprocess call uses a fixed argument list without a shell, with a five-second timeout.
- Reports hostname, OS/kernel metadata and the supplied disk path. Review and redact all output before sharing. Never commit private host information, credentials, tokens, keys or `.env` files. `.gitignore` is a guardrail, not a secret scanner.
- Requires Linux. Missing memory produces a warning. Optional SSH and route checks may report `unknown`/`null`; they warn when their `--require-*` flag is selected.
- `--require-network` checks for an UP IPv4 default route with a zero mask in `/proc/net/route`. It does not test reachability, DNS, firewall policy or IPv6-only networks.
- `--require-ssh` checks `systemctl is-active ssh`, as used on Ubuntu. It does not test authentication, key configuration or remote login. Socket-activated SSH can be reachable while `ssh.service` is inactive; inspect `ssh.socket` separately. Other Linux distributions may name their service `sshd`.
- No fleet management, continuous monitoring, kernel vulnerability scanning, patch compliance or malware detection. An `ok` report covers only configured checks at that moment.

## Roadmap

- [ ] User verifies SSH and audit results on the actual Ubuntu guest.
- [ ] Add redacted real evidence after review and user confirmation.
- [ ] Consider a separate firewall verification/change plan with console recovery access.
- [ ] Add optional metrics export and disposable-VM integration testing.

License not yet selected. Publication alone does not grant a general reuse license.
