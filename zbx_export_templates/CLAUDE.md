# CLAUDE.md

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

```
.ICMP Ping                          (no parents — base)
.Generic by SNMP                    → link: .ICMP Ping
.Network Interfaces by SNMP              (no parents — base)
.MikroTik Generic by SNMP               (no parents — base)
.MikroTik - BGP monitoring by SNMP      (no parents — feature)
.MikroTik - OSPF monitoring by SSH      (no parents — feature)
.MikroTik - Optical interfaces by SNMP  (no parents — feature)
.MikroTik - POE monitoring by SNMP      (no parents — feature)
.MikroTik - Sentinel by SNMP            (no parents — feature, add if Sentinel deployed)
Mikrotik - LDP by SSH                   (no parents — feature)
MikroTik - ARP Monitor                  (no parents — standalone)
MikroTik - MAC Monitor                  (no parents — standalone)

.MikroTik Router   → link: .Generic by SNMP
                          .MikroTik Generic by SNMP
                          .Network Interfaces by SNMP
                          .MikroTik - BGP monitoring by SNMP
                          .MikroTik - OSPF monitoring by SSH
                   +opt:  .MikroTik - Sentinel by SNMP

.MikroTik Switch   → link: .Generic by SNMP
                          .MikroTik Generic by SNMP
                          .Network Interfaces by SNMP
                          .MikroTik - Optical interfaces by SNMP
                          .MikroTik - POE monitoring by SNMP
                   +opt:  .MikroTik - Sentinel by SNMP
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

### Simple import (recommended — link manually after)

```python
import json, subprocess

API   = "https://<zabbix>/api_jsonrpc.php"
TOKEN = "<api-token>"          # User → API tokens in Zabbix UI
BASE  = "MikroTik"

RULES = {
    "templates":          {"createMissing": True, "updateExisting": True},
    "items":              {"createMissing": True, "updateExisting": True, "deleteMissing": False},
    "discoveryRules":     {"createMissing": True, "updateExisting": True, "deleteMissing": False},
    "triggers":           {"createMissing": True, "updateExisting": True, "deleteMissing": False},
    "graphs":             {"createMissing": True, "updateExisting": True, "deleteMissing": False},
    "valueMaps":          {"createMissing": True, "updateExisting": False},
    "templateDashboards": {"createMissing": True, "updateExisting": True, "deleteMissing": False},
}

# Import in this order (base templates before composites)
FILES = [
    "zbx_export_templates (ICMP Ping).json",
    "zbx_export_templates (Generic by SNMP).json",
    "zbx_export_templates (Network Interfaces by SNMP).json",
    "zbx_export_templates (MikroTik - Generic by SNMP).json",
    "zbx_export_templates (MikroTik - BGP monitoring by SNMP).json",
    "zbx_export_templates (MikroTik - OSPF monitoring by SSH).json",
    "zbx_export_templates (MikroTik - Optical interfaces by SNMP).json",
    "zbx_export_templates (MikroTik - POE monitoring by SNMP).json",
    "zbx_export_templates (MikroTik - LDP by SSH).json",
    "zbx_export_templates (MikroTik - Sentinel by SNMP).json",
    "zbx_export_templates (MikroTik - ARP Monitor).json",
    "zbx_export_templates (MikroTik - MAC Monitor).json",
    "zbx_export_templates (MikroTik - Router).json",
    "zbx_export_templates (MikroTik - Switch).json",
]

for fname in FILES:
    source = open(f"{BASE}/{fname}").read()
    payload = json.dumps({
        "jsonrpc": "2.0", "method": "configuration.import", "id": 1,
        "params": {"format": "json", "rules": RULES, "source": source}
    }).encode()
    proc = subprocess.run(
        ["curl", "-s", "-X", "POST", API,
         "-H", "Content-Type: application/json",
         "-H", f"Authorization: Bearer {TOKEN}",
         "-d", "@-"],
        input=payload, capture_output=True
    )
    resp = json.loads(proc.stdout)
    status = "OK" if resp.get("result") == True else resp.get("error", {}).get("data")
    print(f"  {status:4}  {fname}")
```

### Prerequisites on a fresh Zabbix instance

The following template groups must exist before import (create via
**Configuration → Template groups → Create**, or via `templategroup.create` API):

- `ITcare`
- `MikroTik`
- `Templates/Network devices` ← usually exists by default

### After import — manual linking order

Link in the UI in this order to avoid dependency errors:

1. `.Generic by SNMP` → add `.ICMP Ping`
2. `.MikroTik Router` → add the 5 parents listed above
3. `.MikroTik Switch` → add the 5 parents listed above

> **Note:** When linking `.ICMP Ping` to `.Generic by SNMP` the UI may warn
> about the trigger dependency ("No SNMP data collection" depends on
> "Unavailable by ICMP ping"). If it blocks, temporarily remove the dependency
> on that trigger, complete the link, then re-add it.

---

## Validating a template file

```bash
python3 -m json.tool "MikroTik/zbx_export_templates (MikroTik - Router).json" > /dev/null \
  && echo "valid"
```

## Checking SNMP OIDs on a device

```bash
# Standard IF-MIB
snmpwalk -v2c -c <community> <ip> 1.3.6.1.2.1.2.2.1.9     # ifLastChange

# MikroTik proprietary interface error counters
snmpwalk -v2c -c <community> <ip> 1.3.6.1.4.1.14988.1.1.14.1.1.45  # FCS errors
snmpwalk -v2c -c <community> <ip> 1.3.6.1.4.1.14988.1.1.14.1.1.52  # Rx code errors
```
