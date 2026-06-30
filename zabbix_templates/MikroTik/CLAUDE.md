# CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Zabbix 7.4 monitoring templates (JSON export format) for MikroTik network devices, maintained by ITcare. Each template is a standalone JSON file that can be imported independently into Zabbix.

## Directory layout

```
zbx_export_templates/
├── MikroTik/       ← active work area (all templates here)
├── Juniper/        ← ignore
└── andrena/        ← ignore
```

---

## Template inventory & linkage

Templates are imported as standalone units. After import, link them manually in Zabbix UI:
**Configuration → Templates → (template name) → Linked templates tab → Add**

### Base / shared templates (vendor-agnostic)

```
.ICMP Ping                          (no parents — base)
.Generic by SNMP                    → link: .ICMP Ping
.Network Interfaces by SNMP         (no parents — base, all vendors)
```

### MikroTik feature templates (no parents — standalone feature modules)

```
.MikroTik Generic by SNMP                  system health, memory, CPU, disk, inventory
.MikroTik Network Interfaces by SNMP       MikroTik-only IF errors: FCS (.45) + RxCode (.52)
.MikroTik BGP monitoring by SNMP           BGP peer state via SNMP
.MikroTik OSPF monitoring by SSH           OSPF neighbors via SSH
.MikroTik OSPF monitoring by API           OSPF neighbors via RouterOS REST API (preferred)
.MikroTik Optical interfaces by SNMP       SFP RX/TX power, temperature, vendor
.MikroTik POE monitoring by SNMP           PoE port power delivery
.MikroTik Sentinel by SNMP                 Sentinel script queues, pools, BGP, toggles
```

### Role templates (assigned to actual hosts)

```
.MikroTik Router   → link: .Generic by SNMP
                          .MikroTik Generic by SNMP
                          .Network Interfaces by SNMP
                          .MikroTik Network Interfaces by SNMP
                          .MikroTik BGP monitoring by SNMP
                          .MikroTik OSPF monitoring by API   (or SSH variant)
                   +opt:  .MikroTik Sentinel by SNMP        (only if Sentinel deployed)

.MikroTik Switch   → link: .Generic by SNMP
                          .MikroTik Generic by SNMP
                          .Network Interfaces by SNMP
                          .MikroTik Network Interfaces by SNMP
                          .MikroTik Optical interfaces by SNMP
                          .MikroTik POE monitoring by SNMP
                   +opt:  .MikroTik Sentinel by SNMP        (only if Sentinel deployed)
```

### Optional / standalone templates (not linked to role templates)

```
MikroTik - ARP Monitor     standalone, assign directly to host
MikroTik - MAC Monitor     standalone, assign directly to host
```

Dot-prefix (`.`) = library template, not assigned directly to hosts.
No dot = assigned directly to hosts.

---

## Template groups & tags (all templates)

Every template in `MikroTik/` must have:

| Field | Value |
|---|---|
| Template groups | `ITcare`, `MikroTik`, `Templates/Network devices` |
| Tag | `target: mikrotik` |

Exception: `.Network Interfaces by SNMP` and `.Generic by SNMP` use groups `ITcare` + `Templates/Network devices` (no `MikroTik` group — they are vendor-agnostic).

---

## Template design rules

- `.Network Interfaces by SNMP` is **vendor-agnostic** — only standard IF-MIB / EtherLike-MIB OIDs.
  Do NOT add MikroTik-specific OIDs here.
- `.MikroTik Network Interfaces by SNMP` holds **MikroTik-only** per-interface metrics.
  Item prototypes reference trigger expressions using `/.Network Interfaces by SNMP/net.if.status[...]`
  so the host must also have `.Network Interfaces by SNMP` linked.
- **EtherLike-MIB** (OID `1.3.6.1.2.1.10.7`) is NOT supported on MikroTik RouterOS — returns
  "No Such Object". The EtherLike duplex discovery in `.Network Interfaces by SNMP` discovers
  nothing on MikroTik devices (harmless — no items created).
- **OSPF monitoring**: use `.MikroTik OSPF monitoring by API` (RouterOS REST API) in preference
  to the SSH variant. The API template discovery rule is DEPENDENT on the standalone EXTERNAL item
  (both used to share the same key — fixed by making the DR key `ospf.neighbor.discovery`).
- Role templates carry a `[netbox]` description block for automation — preserve exactly.

---

## Verified MikroTik SNMP OIDs

These OIDs have been tested on RouterOS 7.x (device 10.33.76.144):

| OID | Description | Works |
|---|---|---|
| `1.3.6.1.2.1.2.2.1.7` | ifAdminStatus | ✓ |
| `1.3.6.1.2.1.2.2.1.8` | ifOperStatus | ✓ |
| `1.3.6.1.2.1.2.2.1.9` | ifLastChange (timeticks) | ✓ |
| `1.3.6.1.2.1.31.1.1.1.1` | ifName | ✓ |
| `1.3.6.1.2.1.31.1.1.1.6` | ifHCInOctets | ✓ |
| `1.3.6.1.2.1.31.1.1.1.10` | ifHCOutOctets | ✓ |
| `1.3.6.1.2.1.31.1.1.1.15` | ifHighSpeed | ✓ |
| `1.3.6.1.2.1.31.1.1.1.18` | ifAlias | ✓ |
| `1.3.6.1.4.1.14988.1.1.14.1.1.45` | mtxrInterfaceStatsFCSErrors | ✓ |
| `1.3.6.1.4.1.14988.1.1.14.1.1.52` | mtxrInterfaceStatsRxCodeErrors | ✓ |
| `1.3.6.1.2.1.10.7.2.1.19` | dot3StatsDuplexStatus (EtherLike-MIB) | ✗ Not supported |
| `1.3.6.1.2.1.10.7.2.1.3` | dot3StatsFCSErrors (EtherLike-MIB) | ✗ Not supported |

The MikroTik interface stats table (`1.3.6.1.4.1.14988.1.1.14.1.1`) is **sparse** — only columns
1 (index), 45 (FCS), and 52 (RxCode) are confirmed. Columns 2–44 and others do not exist.
Do not assume dense column layout; test each OID individually before adding to a template.

---

## Netbox auto-assignment

Role templates (`.MikroTik Router`, `.MikroTik Switch`) carry a `description` block used by automation to assign templates based on Netbox device attributes. Preserve it exactly:

```
[netbox]
manufacturer = [ "MikroTik" ]
device_type  = [ "CCR2004-16G-2S+", "CHR" ]
device_role  = [ "Core Router", "Edge Router", ... ]
```

---

## Importing templates into Zabbix

### Import script (run in order — base before composites)

```python
import json, subprocess

API   = "https://172.30.20.150/api_jsonrpc.php"
TOKEN = "ede75a3101207a59de7c7e6e60b222a8a57f2f5bd4817c3a7b9b6d18f3b7fd10"
BASE  = "/etc/ansible/vars/templates/zabbix_templates/MikroTik"

RULES = {
    "templates":          {"createMissing": True, "updateExisting": True},
    "items":              {"createMissing": True, "updateExisting": True, "deleteMissing": True},
    "discoveryRules":     {"createMissing": True, "updateExisting": True, "deleteMissing": True},
    "triggers":           {"createMissing": True, "updateExisting": True, "deleteMissing": True},
    "graphs":             {"createMissing": True, "updateExisting": True, "deleteMissing": False},
    "valueMaps":          {"createMissing": True, "updateExisting": False},
    "templateDashboards": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
}

# Import in this order (base before composites)
FILES = [
    "zbx_export_templates (.ICMP Ping).json",
    "zbx_export_templates (.Generic by SNMP).json",
    "zbx_export_templates (.Network Interfaces by SNMP).json",
    "zbx_export_templates (.MikroTik Generic by SNMP).json",
    "zbx_export_templates (.MikroTik Network Interfaces by SNMP).json",
    "zbx_export_templates (.MikroTik BGP monitoring by SNMP).json",
    "zbx_export_templates (.MikroTik OSPF monitoring by SSH).json",
    "zbx_export_templates (.MikroTik OSPF monitoring by API).json",
    "zbx_export_templates (.MikroTik Optical interfaces by SNMP).json",
    "zbx_export_templates (.MikroTik POE monitoring by SNMP).json",
    "zbx_export_templates (.MikroTik Sentinel by SNMP).json",
    "zbx_export_templates (MikroTik - ARP Monitor).json",
    "zbx_export_templates (MikroTik - MAC Monitor).json",
    "zbx_export_templates (.MikroTik Router).json",
    "zbx_export_templates (.MikroTik Switch).json",
]

for fname in FILES:
    path = f"{BASE}/{fname}"
    with open(path) as f:
        source = f.read()
    payload = json.dumps({
        "jsonrpc": "2.0", "method": "configuration.import", "id": 1,
        "params": {"format": "json", "rules": RULES, "source": source}
    }).encode()
    proc = subprocess.run(
        ["curl", "-sk", "-X", "POST", API,
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {TOKEN}",
         "-d", "@-"],
        input=payload, capture_output=True
    )
    resp = json.loads(proc.stdout)
    status = "OK" if resp.get("result") is True else resp.get("error", {}).get("data", "ERROR")
    print(f"  {status:4}  {fname}")
```

### Prerequisites on a fresh Zabbix instance

The following template groups must exist before import (create via
**Configuration → Template groups → Create**, or via `templategroup.create` API):

- `ITcare`   (uuid: `3bd32e85c5624a0687cbe3e58e2c5f2a`)
- `MikroTik` (uuid: `fb49cc980e6a4d06956c8bdab91afcc4`)
- `Templates/Network devices` (uuid: `36bff6c29af641f6a474e5e61de68816`) ← usually exists by default

### After import — manual linking order

Link in the Zabbix UI in this order to avoid dependency errors:

1. `.Generic by SNMP` → add `.ICMP Ping`
2. `.MikroTik Router` → add all 6 parents listed above
3. `.MikroTik Switch` → add all 6 parents listed above

> **Note:** When linking `.ICMP Ping` to `.Generic by SNMP` the UI may warn
> about the trigger dependency ("No SNMP data collection" depends on
> "Unavailable by ICMP ping"). If it blocks, temporarily remove the dependency
> on that trigger, complete the link, then re-add it.

---

## Validating a template file

```bash
python3 -m json.tool "MikroTik/zbx_export_templates (.MikroTik Router).json" > /dev/null \
  && echo "valid"
```

## Checking SNMP OIDs on a device

```bash
# Always test OIDs before adding to a template — MikroTik is sparse/non-standard
snmpwalk -v2c -c <community> <ip> <oid>

# Key OIDs to verify on new RouterOS versions:
snmpwalk -v2c -c oomoomee <ip> 1.3.6.1.2.1.2.2.1.9       # ifLastChange
snmpwalk -v2c -c oomoomee <ip> 1.3.6.1.4.1.14988.1.1.14.1.1.45  # MikroTik FCS errors
snmpwalk -v2c -c oomoomee <ip> 1.3.6.1.4.1.14988.1.1.14.1.1.52  # MikroTik RxCode errors
```
