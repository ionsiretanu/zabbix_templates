# HPE Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: DONE ✅ (partial — HPE 1920/1910 model lists only, see tracking matrix)

## Old Zabbix sources
- Old template names: `ZENTRO_*_HP_1950_SWITCH`, `ZENTRO_*_HP_1920_SWITCH`, `ZENTRO_*_HP_1910_SWITCH`
- Host count: 1097 (1950) + 368 (1920) + 39 (1910) = 1504
- Old Zabbix group: HPE (ID: 85 on new Zabbix, uuid: `a5cb81878d394b8d98e6b9853b03d98b`)

## Template files

All in `vars/templates/zabbix_templates/HPE/`. Import in this order:

```
zbx_export_templates (.HPE Generic by SNMP).json
zbx_export_templates (.HPE - Optical interfaces by SNMP).json
zbx_export_templates (.HPE Switch).json
```

All HPE templates: groups `HPE`, `ITCare`, `Templates/Network devices`; tag `target: hpe`.

| Template | Description | New Zabbix ID |
|---|---|---|
| `.HPE Generic by SNMP` | CPU, memory, temperature, model/serial via H3C Entity Ext MIB | 11068 |
| `.HPE - Optical interfaces by SNMP` | SFP/DOM via H3C Transceiver MIB; add per-host alongside `.HPE Switch` | 11070 |
| `.HPE Switch` | Role template: inherits Generic + .HPE Generic + .Network Interfaces | 11069 |

`.HPE Switch` [network-tool] matches: manufacturer `HPE`, `H3C`, `HP`; device_types include JG960A, JG961A, JG962A, JL380A-JL386A, JG920A, JG923A, JG924A, JG927A, JE174A-JE177A, JG536A, JG540A, and full `HPE 1950/1920/1910 *` strings.

## H3C Entity Ext MIB OIDs (`1.3.6.1.4.1.25506.2.6.1.1.1.1.*`)

| OID column | Description | Item key |
|---|---|---|
| `.6.{$HPE.ENTITY.MODULE.INDEX}` | CPU usage (5-sec avg, %) | `hpe.cpu.usage` |
| `.8.{$HPE.ENTITY.MODULE.INDEX}` | Memory usage (%) | `hpe.mem.usage` |
| `.12.{$HPE.ENTITY.MODULE.INDEX}` | Temperature (°C); 65535 = sensor N/A | `hpe.temp.module` |

Macro `{$HPE.ENTITY.MODULE.INDEX}` default = `192` (MODULE LEVEL1 on HPE 1950). Override per host if different.

## H3C Transceiver MIB OIDs (`1.3.6.1.4.1.25506.2.70.1.1.1.*`), indexed by ifIndex

| OID column | Description | Note |
|---|---|---|
| `.2` | Transceiver type string | LLD `{#SFP_TYPE}` |
| `.6` | Present: 1=installed, 2=not installed | Filter = `^1$` |
| `.9` | Rx optical power (0.01 dBm units) | 2147483647 = DOM not supported |
| `.10` | Tx optical power (0.01 dBm units) | |
| `.13` | Temperature (°C) | |

**Important:** DOM value `2147483647` means the SFP does not support digital optical monitoring. LLD filter `{#SFP_RXPOWER} NOT_MATCHES ^2147483647$` skips such ports. Tested on HPE 1950 24G 2SFP+ 2XGT (JG960A), Comware 7.1.045.

## Master/Dependent Items Compliance

Audited 2026-06-30 against the Template Design Standard in `../CLAUDE.md`.

### `.HPE Generic by SNMP`

**Layering** ✓ — Does not link to `.Generic by SNMP` (correct: role template handles that link, same as MikroTik/Cisco pattern).

**Key naming** ❌ VIOLATIONS — all items use `hpe.*` vendor prefix:
- `hpe.hw.model` → should be `system.hw.model` (inventory MODEL, should use standard key)
- `hpe.hw.serial` → should be `system.hw.serialnumber` (inventory SERIALNO_A, wrong name and prefix)
- `hpe.system.uptime` → should be `system.hw.uptime` (uses different OID `1.3.6.1.6.3.10.2.1.3.0` (snmpEngineTime) vs `.Generic by SNMP`'s `hrSystemUptime`, so not a duplicate — but key still needs standard name without vendor prefix)
- `hpe.cpu.usage` → should be `system.cpu.util[h3cExtEntMemUsage...]` (standard key + MIB leaf in brackets)
- `hpe.mem.usage` → should be `vm.memory.util[h3cExtEntMemUsage...]`
- `hpe.temp.module` → should be `sensor.temp.value[h3cExtEntTemperature...]`

**Master/Dependent compliance** — N/A for single-instance items:
- All 6 items are standalone `SNMP_AGENT get[...]` — no walk master, no discovery rules
- These are single-instance values addressed via `{$HPE.ENTITY.MODULE.INDEX}` macro (not indexed tables)
- Single-instance GETs are an allowed exception per the standard — pattern is acceptable
- If stackable HPE switches need multi-module support in future, walk+dependent would be required

**Macros** ❌ VIOLATIONS — vendor-prefixed threshold macros:
- `{$HPE.CPU.WARN}` → should be `{$CPU.UTIL.CRIT}` (standard name, enables cross-vendor host overrides)
- `{$HPE.MEM.WARN}` → should be `{$MEMORY.UTIL.MAX}`
- `{$HPE.TEMP.HIGH}` → should be `{$TEMP_CRIT}`
- `{$HPE.ENTITY.MODULE.INDEX}` ✓ — vendor prefix correct here (device-specific parameter, not a threshold)

### `.HPE - Optical interfaces by SNMP`

**Master/Dependent compliance** ✅ FULLY COMPLIANT:
- One walk master `hpe.sfp.walk` (SNMP_AGENT) — vendor prefix acceptable (H3C Transceiver MIB namespace)
- 1 DEPENDENT discovery rule (`hpe.sfp.discovery`)
- 3 DEPENDENT item prototypes: Rx power, Tx power, temperature

### `.HPE Switch`

Empty role template (zero items, zero DRs) — correct per standard. Linkage: `.Generic by SNMP` + `.Network Interfaces by SNMP` + `.HPE Generic by SNMP`.

---

## Known issue: templateLinkage when importing alone

When importing `.HPE Switch` alone (not in the same batch as `.Generic by SNMP`), Zabbix may not resolve the `templateLinkage` for parent templates. Fix via API:

```python
call("template.update", {
    "templateid": "11069",  # .HPE Switch
    "templates": [{"templateid": "10782"}, {"templateid": "10780"}, {"templateid": "11068"}]
    # 10782 = .Generic by SNMP, 10780 = .Network Interfaces by SNMP, 11068 = .HPE Generic by SNMP
})
```
