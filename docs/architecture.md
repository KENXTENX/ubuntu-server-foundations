# Architecture and trust boundaries

The audit runs on one Linux host. Python reads `/etc/os-release`, `/proc/meminfo`, `/proc/uptime` and `/proc/net/route`, queries filesystem capacity through `shutil.disk_usage`, and invokes `systemctl is-active ssh` with fixed arguments and a timeout. No shell executes report data.

```text
[Administrator SSH client]
             |
             v
[Linux host: sshd + Python audit]
                  |    |    |
               /proc  disk  systemd
                  \    |    /
                [stdout report]
                       |
               [private review]
```

The owner's planned deployment is an Ubuntu Desktop guest in VMware on a Windows host. A VMware NAT connection may support host-to-guest SSH without public port forwarding. Verify the actual adapter, guest address and route at the checkpoint. The code does not require VMware, Windows or particular household equipment.

The auditor does not alter services, install packages, edit configuration or open listening sockets. Hostnames, OS/kernel metadata and a user-supplied path can appear in output and must be reviewed before publication. SSH access and the local system utilities are trusted parts of the environment.

GitHub Actions runs deterministic tests and an audit smoke check on a separate disposable Ubuntu runner. That validates the code path, not the owner's VM or network. A smoke check can legitimately report warnings; it accepts exit 0 or 1 and verifies the JSON/status agreement. Execution errors fail CI. No runner report is uploaded.

Future fleet monitoring or advanced cloud architecture belongs in a later, separately scoped project.
