# Ubuntu setup and verification gates

## Status and prerequisites

The earlier conversation describes an Ubuntu Desktop VMware VM with SSH installed and internet access. These are user-reported context, not independently verified results. This repository records **no completed live VM audit**. Python 3.10+ is required; the audit itself has no external Python dependencies.

## Gate 1: read-only VM and SSH checkpoint

Run these in the Ubuntu VMware console. Review output privately; it can reveal usernames, hostnames and network addresses.

```bash
whoami
hostname
cat /etc/os-release
uname -r
python3 --version
ip -4 -br addr
ip -4 route
df -h /
free -h
systemctl is-active ssh
systemctl is-active ssh.socket
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

An inactive or missing `ssh.socket` is not automatically a fault if `ssh.service` is active. On socket-activated Ubuntu installations the opposite may occur. Confirm a real login rather than inferring reachability from one unit's state.

From Windows PowerShell, replace USER and VM_IP with your guest values:

```powershell
ssh USER@VM_IP
```

Compare the fingerprint shown in Windows to the VM console fingerprint before accepting it. This login can store a known-host entry on Windows and produce normal server login logs. Do not bypass a changed-host-key warning; investigate it from the console. Stop at this gate if the expected fingerprint or destination is uncertain.

## Get the code (creates local files)

Only after confirming SSH, use an ordinary Ubuntu user. Do not run as root. If the directory already exists, inspect it before cloning or pulling; do not overwrite other work.

```bash
git clone https://github.com/KENXTENX/ubuntu-server-foundations.git
cd ubuntu-server-foundations
```

## Gate 2: tests and real audit

From the repository root inside the Ubuntu guest:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
echo "Tests exit code: $?"
PYTHONDONTWRITEBYTECODE=1 python3 -m linux_audit --require-ssh --require-network --json
echo "Audit exit code: $?"
df -B1 /
free -k
systemctl is-active ssh
systemctl is-active ssh.socket
ip -4 route
```

Tests create and clean temporary fixtures. The audit commands inspect the local host and print to the terminal; they do not write a report or alter system configuration. Disk and memory readings may vary between commands. See README for calculation differences from `df`.

**Stop here and confirm actual results with the user.** Share test count/result, audit exit code, warning messages and redacted comparisons. Do not publish raw JSON, hostnames, IPs, usernames or full terminal screenshots. A CI runner result is separate from this VM gate.

## Later changes require a separate gate

Do not enable UFW, change SSH configuration, restart services, update packages or expand disks during these checkpoints. Plan any required change after reviewing actual findings, with working VMware console access and a way to retest a second SSH connection.
