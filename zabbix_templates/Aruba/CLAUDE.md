# Aruba Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: NOT STARTED ❌ (119 hosts)

## Old Zabbix source
- Old template name(s): `ZENTRO_*_ARUBA_1930_SWITCH`
- Host count: 119
- Old Zabbix group: TBD

## Planned new Zabbix template(s)
- Name: TBD (e.g. `.Aruba Switch` — follow the per-device-class pattern used by Cisco/HPE)
- Template groups: `Aruba`, `ITCare`, `Templates/Network devices`
- Tag: `target: aruba`

## Reference implementation
**Read `HPE/CLAUDE.md` before starting work on this template.** Aruba 1930 is now an HPE brand — the H3C Entity Ext MIB may overlap. Start by testing the same OIDs used in `.HPE Generic by SNMP` on an Aruba 1930 before assuming a separate MIB is needed. If OIDs differ, follow the same template structure (Generic base + Switch role).

## MIB / OID research
- Base enterprise OID: `1.3.6.1.4.1.14823.*` (Aruba Networks / HPE Aruba)
- Status: not yet verified on a live device

## Test device
- IP: TBD
- SNMP community: TBD
- Model: Aruba 1930 (JL684A / JL685A / JL686A / JL687A)

## [network-tool] block plan

```ini
[network-tool]
manufacturer = [ "Aruba" ]
device_role = [ "Access Switch" ]
device_types = [ ]   ← TBD after OID research (Aruba 1930 model strings)
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

