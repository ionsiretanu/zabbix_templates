# Zabbix Templates — Directory Index

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory or any vendor subdirectory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

Zabbix 7.4 monitoring templates (JSON export format). All template files must be 7.4 format — 7.0 templates cannot be imported into Zabbix 7.4.

## Validate any template before importing

```bash
python3 -m json.tool "path/to/template.json" > /dev/null && echo "valid"
```

## Directory layout

```
vars/templates/zabbix_templates/
├── MikroTik/       ← active — see MikroTik/CLAUDE.md (import order, OIDs, design rules)
├── Aviat/          ← active — see Aviat/CLAUDE.md (WTM4880 OID map, item prototypes)
├── Cisco/          ← active — see Cisco/CLAUDE.md (import order, ENTITY-SENSOR-MIB OIDs)
├── HPE/            ← active — see HPE/CLAUDE.md (H3C MIB OIDs, templateLinkage fix)
├── Siklu/          ← DONE ✅ (5 templates: Generic, EH Radio, MH Radio, B100 Radio, System Alarm) — see Siklu/CLAUDE.md
├── Juniper/        ← NOT STARTED ❌ CRITICAL (3166 hosts) — see Juniper/CLAUDE.md
├── Ubiquiti/       ← NOT STARTED ❌ HIGH (~2199 hosts) — see Ubiquiti/CLAUDE.md
├── SIAE/           ← NOT STARTED ❌ HIGH (~1020 hosts) — see SIAE/CLAUDE.md
├── CyberPower/     ← NOT STARTED ❌ HIGH (450 hosts) — see CyberPower/CLAUDE.md
├── APC/            ← NOT STARTED ❌ HIGH (445 hosts) — see APC/CLAUDE.md
├── Aruba/          ← NOT STARTED ❌ (119 hosts) — see Aruba/CLAUDE.md
├── Positron/       ← NOT STARTED ❌ (93 hosts) — see Positron/CLAUDE.md
├── TripLite/       ← NOT STARTED ❌ (25 hosts) — see TripLite/CLAUDE.md
├── Ceragon/        ← NOT STARTED ❌ (32 hosts) — see Ceragon/CLAUDE.md
├── Raisecom/       ← NOT STARTED ❌ (14 hosts) — see Raisecom/CLAUDE.md
├── Ignite/         ← NOT STARTED ❌ (81 hosts) — see Ignite/CLAUDE.md
├── Alcoma/         ← NOT STARTED ❌ (16 hosts) — see Alcoma/CLAUDE.md
├── Ruckus/         ← (not in migration tracking matrix — status unknown)
├── andrena/        ← ignore
└── README.md
```

For cross-vendor import infrastructure (migration script, RULES dict, Python import snippet, required template groups, new Zabbix credentials), see `/etc/ansible/CLAUDE.md` → "Zabbix migration — old → new".

---

## Template Design Standard — Naming, Keys, and Master/Dependent Items

The reference implementation is **`.MikroTik Generic by SNMP`** in `MikroTik/`. When building a new vendor template, read `MikroTik/CLAUDE.md` alongside this section.

### 1. Template layering

Three-layer model for managed network devices (switches, routers):

| Layer | Naming pattern | Purpose |
|---|---|---|
| Base | `.Generic by SNMP` | Vendor-agnostic: sysName, sysDescr, sysContact, SNMP availability, ICMP (via `.ICMP Ping` link) |
| Vendor Generic | `.<Vendor> Generic by SNMP` | Vendor-specific system metrics: CPU, memory, temperature, hardware model, serial, firmware |
| Role | `.<Vendor> Switch` / `.<Vendor> Router` | Thin shell — only template links, zero items |

**Role template links (mandatory order):** `.Generic by SNMP` + `.Network Interfaces by SNMP` + `.<Vendor> Generic by SNMP`.

The Vendor Generic does **not** link to `.Generic by SNMP` — the role template handles that link directly. This is the reference pattern from MikroTik.

**Single-purpose devices (radio, UPS):** one combined template linking to `.Generic by SNMP` is acceptable — no need for a separate Vendor Generic. This is the Aviat pattern.

**Add-on templates** (`.Cisco - Optical interfaces by SNMP`, `.HPE - Optical interfaces by SNMP`) are standalone, attached per-host as needed alongside the role template.

### 2. Key naming convention

Use the MikroTik Generic keys as the canonical set. No vendor prefix on cross-comparable metrics.

| Metric | Key pattern | Inventory link |
|---|---|---|
| Hardware model | `system.hw.model` | `MODEL` |
| Serial number | `system.hw.serialnumber` | `SERIALNO_A` |
| Firmware/OS version | `system.hw.firmware` or `system.sw.os[<mibLeaf>.0]` | `OS` |
| Per-CPU utilization | `system.cpu.util[<mibLeaf>.{#SNMPINDEX}]` | — |
| Temperature sensor | `sensor.temp.value[<mibLeaf>.{#SNMPINDEX}]` | — |
| Memory total / used | `vm.memory.total[<mibLeaf>]` / `vm.memory.used[<mibLeaf>]` | — |
| Memory utilization | `vm.memory.util[<mibLeaf>]` (CALCULATED) | — |
| Storage | `vfs.fs.total[...]` / `vfs.fs.used[...]` / `vfs.fs.pused[...]` | — |
| Radio metrics | `net.wlan.<category>[<name>.{#SNMPINDEX}]` | — |
| Interface metrics | `net.if.*` (via `.Network Interfaces by SNMP`) | — |
| Walk master items | `<domain>.<scope>.walk` (e.g. `system.cpu.walk`, `sensor.temp.walk`) | — |

**Vendor prefix is allowed only for vendor-specific OID namespaces with no standard equivalent** — walk master keys for truly proprietary MIBs (`cisco.entity.sensor.walk`, `hpe.sfp.walk`) are acceptable exceptions. Threshold-bearing items (CPU, memory, temp) must never carry a vendor prefix.

### 3. Master/dependent walk pattern — mandatory for all discoverable metrics

Every set of metrics that requires SNMP discovery (table walk, indexed values) must use this three-piece structure:

**Master item** (one per MIB subtree):
- Type: `SNMP_AGENT`
- OID: `walk[<oid1>,<oid2>,...]`
- Key: ends in `.walk` (e.g. `system.cpu.walk`)
- `value_type: TEXT`, `history: 0` (raw JSON, never store it)

**Discovery rule** (DEPENDENT on the master):
- Type: `DEPENDENT`
- `master_item.key`: the walk item key
- Preprocessing: `SNMP_WALK_TO_JSON`

**Item prototypes** (DEPENDENT on the master, not on the DR):
- Type: `DEPENDENT`
- `master_item.key`: same walk item key
- Preprocessing: `SNMP_WALK_VALUE` to extract the indexed column

**Allowed exception:** single-instance metrics (one fixed value per device, no index) may use a standalone `SNMP_AGENT get[<oid>]` without a walk master. Example: `vm.memory.total`, `system.hw.model`, `system.hw.firmware`.

**Non-compliant pattern — do not use:** `SNMP_AGENT` discovery rule (polls the device independently for every discovered instance). Replaced by the walk+dependent pattern above.

### 4. Preprocessing engine choice

1. Try native Zabbix steps first: `SNMP_WALK_VALUE`, `MULTIPLIER`, `DISCARD_UNCHANGED_HEARTBEAT`, `JSONPATH`, `REGEX`, `CHANGE_PER_SECOND`
2. Use JavaScript only when native cannot do it — log10 conversion for dBm from mW is a valid case
3. If JavaScript is used, put the reason in the preprocessing step name (e.g. `"JS: native cannot do log10"`)

### 5. Trigger pattern

- Triggers on discovered items go in `trigger_prototypes` under the item prototype, never as standalone triggers referencing `{#SNMPINDEX}` from outside
- Include `{#SNMPINDEX}` or `{#NAME}` in the trigger name so each instance is uniquely named
- Define `dependencies` to suppress cascade alerts (e.g. "interface down" depends on "device unreachable"; warn threshold depends on critical threshold)
- Severity guide: `DISASTER` = device offline, `HIGH` = critical operational failure (radio link down, UPS on battery), `AVERAGE` = degraded/threshold breach, `WARNING` = warn threshold

### 6. Macro naming

Threshold macros — use **these exact names across all vendors** so host-level overrides work uniformly:

| Macro | Purpose | Default |
|---|---|---|
| `{$TEMP_CRIT}` | Temperature critical threshold (°C) | 60 |
| `{$TEMP_WARN}` | Temperature warning threshold (°C) | 50 |
| `{$CPU.UTIL.CRIT}` | CPU utilization critical (%) | 90 |
| `{$MEMORY.UTIL.MAX}` | Memory utilization max (%) | 90 |
| `{$HEALTH_POLL_INT}` | Poll interval for health/sensor items | 1m |
| `{$INVENTORY_INT}` | Poll interval for slow-changing inventory items | 1h |

Vendor-specific context macros (`{$HPE.ENTITY.MODULE.INDEX}`, `{$CISCO.SFP.PHYSNAME_FILTER}`) are allowed for per-host override of device-specific parameters. Vendor prefix is required there to avoid collision.

**Wrong:** `{$HPE.CPU.WARN}`, `{$HPE.MEM.WARN}`, `{$HPE.TEMP.HIGH}` — these cannot be overridden at host level cross-vendor and break the standard macro contract.

---

### Live Zabbix as source of truth — sync-back rule

When working on a template that is **already imported into new Zabbix**, the live template state is authoritative — the local JSON file may lag behind UI-applied fixes.

**Step 1 — Fetch live template:**
```python
result = call("template.get", {
    "filter": {"name": ".Vendor Template Name"},
    "selectItems": "extend",
    "selectDiscoveryRules": {
        "selectItemPrototypes": "extend",
        "selectTriggerPrototypes": "extend",
        "selectLLDMacroPaths": "extend",
        "selectFilter": "extend"
    },
    "selectTriggers": "extend",
    "selectMacros": "extend",
    "selectParentTemplates": "extend",
    "selectTags": "extend",
    "selectValueMaps": "extend",
    "selectGroups": "extend"
})
```

**Step 2 — Compare live vs local JSON** for:
- Template name, parent template links, template groups, tags
- Item keys, OIDs, preprocessing steps and parameters, update intervals, value types
- Discovery rules: type (`DEPENDENT` vs `SNMP_AGENT`), master_item, LLD filter, macro paths
- Item prototype keys, types, master_item references, preprocessing
- Trigger expressions, severity, dependencies
- Macro names and values, value maps

**Step 3 — If they match:** say so explicitly. No edits needed.

**Step 4 — If they differ:** live Zabbix is the source of truth for intentional changes. Apply live state back to local JSON. Update vendor CLAUDE.md with a dated note (what changed, why). Flag any standard violations found — note them as future fixes, not overrides.

**Step 5 — Validate** the updated local JSON:
```bash
python3 -m json.tool "vars/templates/zabbix_templates/Vendor/zbx_export_templates (.Name).json" > /dev/null && echo valid
```

This rule applies retroactively to all active templates (MikroTik, Cisco, HPE, Aviat, Siklu) unless the user says "just check local file".
