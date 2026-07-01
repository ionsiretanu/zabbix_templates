# Ubiquiti Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: NOT STARTED ❌ HIGH PRIORITY (~2199 hosts)

## Old Zabbix sources

| Old template | Product line | Hosts |
|---|---|---|
| `ZENTRO_*_UBNT_POWERBEAM_RADIO` | PowerBeam | 733 |
| `ZENTRO_*_UBNT_AF60_RADIO` | AirFiber 60 | 653 |
| `ZENTRO_*_UBNT_AF24_AF11_AF5_AF5X_RADIO` | AirFiber 24/11/5/5X | 493 |
| `ZENTRO_*_UBNT_WAVE_RADIO` | Wave | 224 |
| `ZENTRO_*_UBNT_AF5XHD_RADIO` | AirFiber 5XHD | 74 |
| `ZENTRO_*_UBNT_GBE_RADIO` | GigaBeam | 8 |
| `ZENTRO_*_UBNT_UNIFI_SWITCH` | UniFi Switch | 14 |
| **Total** | | **2199** |

## Planned new Zabbix template(s)
- Name: TBD — likely multiple templates per product line (AirFiber radios share UBNT MIB subtrees; UniFi switches are different)
- Template groups: `Ubiquiti`, `ITcare`, `Templates/Wireless` (radios) / `Templates/Network devices` (switches)
- Tag: `target: ubiquiti`

## Reference implementation
**Read `Aviat/CLAUDE.md` before starting work on radio templates** (PowerBeam, AirFiber, Wave, GBE). Follow the same SNMP bulk walk + LLD pattern, `net.wlan.*` item key namespace, and macro structure. For UniFi Switch, read `Cisco/CLAUDE.md` instead — UniFi switches are fundamentally different from Ubiquiti radios and should follow the switch template pattern.

## MIB / OID research
- Base enterprise OID: `1.3.6.1.4.1.41112.*` (UBNT enterprise MIB)
- Status: not yet verified on a live device

## Test device
- IP: TBD
- SNMP community: TBD
- Model: TBD

## [network-tool] block plan

```ini
[network-tool]
manufacturer = [ "Ubiquiti" ]
device_role = [ "Radio Link" ]
device_types = [ ]   ← TBD after OID research per product line
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

