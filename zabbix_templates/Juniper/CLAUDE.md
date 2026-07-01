# Juniper Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: NOT STARTED ❌ CRITICAL (3166 hosts)

## Old Zabbix source
- Old template name(s): `ZENTRO_*_JUNIPER_GLOBAL`
- Host count: 3166
- Old Zabbix group: Juniper (ID: 26 on new Zabbix)

## Planned new Zabbix template(s)
- Name: TBD (e.g. `.Juniper Generic by SNMP`, `.Juniper Switch`, `.Juniper Router` — follow the per-device-class pattern used by Cisco/HPE)
- Template groups: `Juniper`, `ITCare`, `Templates/Network devices`
- Tag: `target: juniper`

## Reference implementation
**Read `Cisco/CLAUDE.md` before starting work on this template.** Juniper switch/router templates should follow the same structure: `.Juniper Generic by SNMP` (vendor base) + role templates (`.Juniper Switch`, `.Juniper Router`). Use the same `[network-tool]` block format and template group conventions as Cisco. Note: Juniper uses NETCONF in playbooks — SNMP template metrics are separate from how playbooks connect.

## MIB / OID research
- Base enterprise OID: `1.3.6.1.4.1.2636.*` (Juniper Networks MIB)
- Status: not yet verified on a live device

## Test device
- IP: TBD (check tmp.ini for an active Juniper device)
- SNMP community: `oomoomee` (default per `vars/juniper_vars.yml`)
- Model: TBD

## [network-tool] block plan

```ini
[network-tool]
manufacturer = [ "Juniper" ]
device_role = [ "Core Router", "Edge Router", "Access Switch" ]
device_types = [ ]   ← TBD after confirming hardware model strings from old Zabbix
```

## Template Design Standard — build requirements

Before writing any items, read the **Template Design Standard** in `../CLAUDE.md` (section "Template Design Standard — Naming, Keys, and Master/Dependent Items"). Required:
- Walk + DEPENDENT pattern for all discoverable metrics — no standalone SNMP_AGENT discovery rules
- Standard key names: `system.hw.model`, `system.hw.serialnumber`, `sensor.temp.value[...]`, `system.cpu.util[...]`, `vm.memory.*`, `net.wlan.*` — no vendor prefix on threshold-bearing items
- Standard threshold macros: `{$TEMP_CRIT}`, `{$TEMP_WARN}`, `{$CPU.UTIL.CRIT}`, `{$MEMORY.UTIL.MAX}`
- Before editing any template already live in new Zabbix, apply the sync-back rule (fetch live first)

## Import checklist

- [ ] JSON validates: `python3 -m json.tool "*.json" > /dev/null && echo valid`
- [ ] Imported to new Zabbix (https://172.30.20.150) with `templateLinkage: createMissing: true`
- [ ] `[network-tool]` block present in template description (migration script auto-selection)
- [ ] Template groups created and assigned
- [ ] Test host confirmed collecting — check items/data in Zabbix UI
- [ ] Master/dependent pattern used for all discoverable metrics — no standalone SNMP items in discovery rules
- [ ] Key names follow standard convention (vendor-agnostic where possible)

