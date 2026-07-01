# CyberPower Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: NOT STARTED ❌ HIGH PRIORITY (450 hosts)

## Old Zabbix source
- Old template name(s): `ZENTRO_BAI_*_CYBER_CYxxxx`
- Host count: 450
- Old Zabbix group: TBD

## Planned new Zabbix template(s)
- Name: TBD (e.g. `.CyberPower UPS by SNMP` — follow Aviat/Siklu radio pattern adapted for UPS)
- Template groups: `CyberPower`, `ITcare`, `Templates/Network devices` (or a `Templates/UPS` group)
- Tag: `target: cyberpower`

## Reference implementation
No existing UPS template to reference. **Read `APC/CLAUDE.md`** — APC (SNMP) is the other large UPS vendor (406 hosts) and should be built in parallel. Coordinate so both UPS templates share the same group conventions and macro naming pattern.

## MIB / OID research
- Base enterprise OID: `1.3.6.1.4.1.3808.*` (CyberPower enterprise MIB — POWERNET-MIB)
- Status: not yet verified on a live device

## Test device
- IP: TBD
- SNMP community: TBD (check `vars/cisco_vars.yml` or device config — community may be `oomoomee`)
- Model: TBD (CY prefix — check old Zabbix template name for model details)

## Related
- `scripts/cyberpower_ups.sh` — shell script for CyberPower UPS management (check for OID hints)

## [network-tool] block plan

```ini
[network-tool]
manufacturer = [ "CyberPower" ]
device_role = [ "UPS" ]
device_types = [ ]   ← TBD after OID research
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

