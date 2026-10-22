# Evidence and publishing checklist

Live Ubuntu VM verification is partially documented from owner-reported results below; Gate 3 remains open. Mark an item complete only after the user actually performs and confirms it. Synthetic examples and GitHub runner output are not VM deployment evidence.

- [ ] Verify the SSH host fingerprint from the VM console and complete a Windows-to-guest login.
- [ ] Record actual SSH service/socket state and explain any socket activation difference.
- [x] Record the actual test count, result and exit code on the guest (owner-reported; see Gate 3 below).
- [ ] Record the actual audit exit code and warnings; compare disk and memory readings to `df -B1 /` and `free -k`.
- [ ] If tried, record observed behavior of `--disk-warn 1`; a warning depends on measured usage.
- [ ] Adapt the architecture diagram to the actual environment.
- [ ] Record a genuine troubleshooting incident if one occurs; do not invent one.
- [ ] Review report text, screenshots and changed files for secrets and personal host/network details before publishing.
- [ ] Confirm automated checks separately from the user's VM verification.

## Gate 3: reported live Ubuntu validation

**Status: partial; Gate 3 remains open.** The owner supplied the live results below. The VM, terminal output and raw audit JSON were not independently inspected. The repository source and the arithmetic applied to the supplied values were independently checked; that does not independently verify the underlying measurements. The original checklist remains open where confirmation is incomplete.

### Owner-reported results

| Check | Reported result | Evidence limitation |
| --- | --- | --- |
| Python | 3.14.4 | Version reported by the owner; interpreter output not independently inspected. |
| SSH service | Active | Service state reported; socket state and host fingerprint verification were not supplied. |
| Remote SSH | Windows-to-Ubuntu login successful | Login reported by the owner; no terminal transcript published. |
| Unit tests on Ubuntu | 25 passed; exit code 0 | Live run reported by the owner; separate from GitHub Actions. |
| Audit on Ubuntu | Exit code 0; no warnings; disk pressure 27.4%; memory utilization 26.6% | Results reported by the owner, not independently inspected against raw audit JSON. |
| IPv4 default route | Present: yes | Route presence reported; does not establish internet access or DNS resolution. |

### Disk measurements and comparison limit

The owner reported these fields from `df -B1 /`:

| Field | Reported value |
| --- | --- |
| Used | 11206606848 bytes |
| Avail | 36587536384 bytes |
| Size (total) | Not supplied |

In [the audit source](../linux_audit/audit.py), `collect_report()` uses `shutil.disk_usage()`, and `used_percent()` calculates `round(100 * (total - available) / total, 1)`. On Linux, the disk free value represents space available to the calling user. The matching comparison needs `df` Size and Avail for the same filesystem and user context.

Used and Avail alone cannot reproduce this calculation. Do not infer Size by adding them: reserved filesystem space can make that sum differ from total. The owner subsequently reported `disk.used_percent = 27.4%`, while `df` displayed 24% usage at a different observation. These percentages use different filesystem accounting methods and are not directly equivalent. An exact independent recalculation remains pending because the filesystem Size was not supplied; the raw audit output was not inspected.

### Memory and swap calculations

The owner reported these values from `free -k`:

| Field | Reported value |
| --- | --- |
| MemTotal | 5489228 KiB |
| Used | 1429296 KiB |
| Free | 2035820 KiB |
| MemAvailable | 4059932 KiB |
| Swap total | 4194300 KiB |
| Swap free | 4194300 KiB |

The source reads `MemTotal` and `MemAvailable` from `/proc/meminfo`; it does not use MemFree to calculate memory pressure. Arithmetic on the supplied figures gives:

- `5489228 - 4059932 = 1429296 KiB`, which agrees with the reported Used value.
- `(5489228 - 4059932) / 5489228 * 100 ≈ 26.04%`; the source's one-decimal rounding would yield **26.0% for these inputs**.
- Swap consumed: `4194300 - 4194300 = 0 KiB`. This is a calculation from the reported `free` values; the auditor does not report swap usage.

These checks establish arithmetic consistency with the methodology. The owner subsequently reported `memory.used_percent = 26.6%` from the live audit; earlier `free -k` figures calculate to 26.0%. Such a difference is consistent with memory changing between samples, but the raw audit output was not independently inspected.

### Network limitation and unresolved incident

The audit checks for an UP IPv4 default route with a zero destination and mask in `/proc/net/route`. It does not test external reachability or DNS. The previously reported NAT internet/DNS failures remain **unresolved and not retested** in the supplied evidence. A successful SSH login and a present default route do not close that incident; no root cause or fix is claimed.

### Next read-only verification checkpoint

1. On the same Ubuntu guest, run `df -B1 /` and the audit close together. Supply the root filesystem's **Size**, Used and Avail in bytes, with device identifiers removed.
2. Run `PYTHONDONTWRITEBYTECODE=1 python3 -m linux_audit --require-ssh --require-network --json` from the existing repository checkout and record the exit code immediately. Review the full output privately. Share only redacted `disk.used_percent` and `memory.used_percent`, plus `disk.total_bytes`, `disk.free_bytes`, `memory.total_kib` and `memory.available_kib` if needed to reconcile readings taken at different moments. Retain the flags, exit code and any sanitized warning text.
3. Compare disk pressure using Size and Avail, and compare memory using the audit's own total/available pair and one-decimal rounding. Record timing differences instead of forcing exact agreement between separate samples.
4. Review this evidence update and the separate automated checks before marking the disk/memory comparison complete. Gate 3 cannot fully close from the current data: **df Size is still missing for independent disk-pressure reconciliation**. The owner has now reported the audit disk and memory percentages (27.4% and 26.6%), but their raw JSON values were not independently inspected.

The remaining original checklist items still require their own evidence, including host fingerprint confirmation, socket state where relevant, architecture review and any optional threshold experiment. Internet/DNS recovery needs separate read-only retest evidence. Any security, network or storage configuration changes require a separate gate.

## Safe evidence record

A sanitized summary may include date, Python/Ubuntu versions, test count, exit codes, warning text and an explanation of comparisons. Remove usernames, real hostnames, IPs, personal paths, keys and credentials. Save raw reports privately outside the repository; `reports/` is ignored as a secondary guardrail. Do not rely on ignore rules or a pattern scan to prove absence of secrets.

Redacted screenshots can later go in `docs/screenshots/`, after explicit review. Do not attach full terminal transcripts automatically.

## Resume wording — only after user-verified deployment

> Developed and tested a read-only Linux health-audit CLI in Python to assess disk, memory, SSH service status and default IPv4 route availability; verified it on an Ubuntu lab through remote SSH administration, with separate GitHub Actions checks.

Until then, describe the implementation and automated tests only; do not claim the Ubuntu deployment or operational outcome is complete.
