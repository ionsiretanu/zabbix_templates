# APC Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: NOT STARTED ❌ HIGH PRIORITY (445 hosts)

## Old Zabbix sources

| Old template | Type | Hosts |
|---|---|---|
| `ZENTRO_*_APC_SNMP_GLOBAL` | SNMP-polled | 406 |
| `ZENTRO_*_APC_CLOUD_GLOBAL` | Cloud-managed | 39 |
| **Total** | | **445** |

## Planned new Zabbix template(s)
- Name: TBD (e.g. `.APC UPS by SNMP` for SNMP devices; cloud devices may need a different approach)
- Template groups: `APC`, `ITcare`, `Templates/Network devices` (or `Templates/UPS`)
- Tag: `target: apc`

## Reference implementation
No existing UPS template to reference. **Read `CyberPower/CLAUDE.md`** — CyberPower is the other large UPS vendor (450 hosts) and should be built in parallel. Coordinate so both UPS templates share the same group conventions and macro naming pattern. Note: cloud-managed APC devices (39 hosts) may need a separate approach — investigate SNMP availability first.

## MIB / OID research
- Base enterprise OID: `1.3.6.1.4.1.318.*` (APC / Schneider Electric — PowerNet-MIB)
- Status: not yet verified on a live device
- Note: Cloud-managed APC devices (39 hosts) may not support SNMP — investigate separately

## Test device
- IP: TBD
- SNMP community: TBD
- Model: TBD

## [network-tool] block plan

```ini
[network-tool]
manufacturer = [ "APC", "Schneider Electric" ]
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

