# Alcoma Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: NOT STARTED ❌ Low priority (16 hosts)

## Old Zabbix source
- Old template name(s): `ZENTRO_*_ALCOMA_*` (11/18/24/6 GHz variants)
- Host count: 16
- Old Zabbix group: TBD

## Planned new Zabbix template(s)
- Name: TBD (e.g. `.Alcoma Radio by SNMP` — determine if all frequency bands share same MIB)
- Template groups: `Alcoma`, `ITcare`, `Templates/Wireless`
- Tag: `target: alcoma`

## Reference implementation
**Read `Aviat/CLAUDE.md` before starting work on this template.** Follow the same SNMP bulk walk + LLD pattern, `net.wlan.*` item key namespace, and macro structure. Adapt OIDs once confirmed on a live device.

## MIB / OID research
- Base enterprise OID: TBD — confirm via snmpwalk on a live device first
- Status: not yet verified on a live device

## Test device
- IP: TBD
- SNMP community: TBD
- Model: TBD (check old Zabbix for which frequency band has devices available)

## [network-tool] block plan

```ini
[network-tool]
manufacturer = [ "Alcoma" ]
device_role = [ "Radio Link" ]
device_types = [ ]   ← TBD after OID research (include all GHz variants)
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

