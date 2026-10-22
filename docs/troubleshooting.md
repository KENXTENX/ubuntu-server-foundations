# Troubleshooting notebook

Record the **actual error**, cause, fix and verification for each incident. Do not invent incidents.

| Symptom | Read-only investigation | Potential remedy |
| --- | --- | --- |
| Windows SSH times out | Check VM NAT adapter, guest IP, route, UFW, `systemctl is-active ssh` | Resolve interface or firewall issue before retrying |
| SSH host key unknown | Compare fingerprint in Windows with the VM console | Accept only when fingerprints match |
| Report says SSH inactive | `systemctl status ssh` | Ensure OpenSSH Server is installed and active if needed |
| No default IPv4 route | `ip route` | Examine VMware virtual NIC and guest DHCP settings |
| High disk usage alert | `df -h /` and `du` on explicitly selected paths | Expand VM disk or remove disposable files after backup |
| Unexpected OS details | `cat /etc/os-release` | Check whether running on expected VM |

## Incident record template

- **Date:**
- **Symptoms:**
- **What I expected:**
- **Commands and observations:**
- **Root cause:**
- **Remediation:**
- **Retest evidence:**
- **Prevention:**
