# Cisco Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: DONE ✅

## Old Zabbix sources
- Old template names: `ZENTRO_*_CISCO_C2960_C3560`, `ZENTRO_*_CISCO_C4948`, `ZENTRO_*_CISCO_C3750`
- Host count: 4064
- Old Zabbix group: Cisco (ID: 61 on new Zabbix)

## Template files

All in `vars/templates/zabbix_templates/Cisco/`. Import in this order (base templates first):

```
zbx_export_templates (.Cisco Generic by SNMP).json
zbx_export_templates (.Cisco - Optical interfaces by SNMP).json
zbx_export_templates (.Cisco Switch).json
zbx_export_templates (.Cisco Router).json
```

All Cisco templates: groups `Cisco`, `ITCare`, `Templates/Network devices`; tag `target: cisco`.

| Template | Description | `[network-tool]` device_types |
|---|---|---|
| `.Cisco Generic by SNMP` | Cisco-specific system items (CPU, memory, flash via CISCO-PROCESS-MIB) | (no device_types — vendor base) |
| `.Cisco - Optical interfaces by SNMP` | SFP/DOM monitoring via CISCO-ENTITY-SENSOR-MIB | (no device_types — added as extra per-host) |
| `.Cisco Switch` | Role template: inherits Generic + Cisco Generic + Optical | WS-C4948, WS-C3850-*, WS-C3750*, WS-C3560*, WS-C3550*, WS-C2960*, WS-C2950*, C9200L*, C9300*, C9500*, N5K-C5548UP, N5K-C5596UP, N7K-C7010, N7K-C7018, N3K-C3064PQ-10GE, N3K-C3048TP-1GE, N9K-C93\*\* |
| `.Cisco Router` | Role template: inherits Generic + Cisco Generic | ASR\*, ISR\*, CSR1000V |

## `.Cisco - Optical interfaces by SNMP` OID details (CISCO-ENTITY-SENSOR-MIB)

- Uses `walk[ENTITY-MIB.entPhysicalName, ENTITY-SENSOR-MIB.*]` with master key `cisco.entity.sensor.walk`
- `entPhysicalName` (`.47.1.1.1.1.7`) is self-describing: `"Ethernet1/26(Rx-dBm)"`, `"Ethernet1/26(celsius)"`
- `entSensorValue` (`.9.9.91.1.1.1.1.4`): raw sensor value
- `entSensorStatus` (`.9.9.91.1.1.1.1.5`): 1=ok, 2=unavailable, 3=nonoperational
- All NX-OS sensor values use scale=8 (milli) → multiply by 0.001 for dBm/°C
- Macro `{$CISCO.SFP.PHYSNAME_FILTER}` = `\\([RT]x-dBm\\)` — controls which sensors become items
- Tested on: Nexus 5548 (N5K-C5548UP), NX-OS 7.3. **CISCO-DOM-MIB not supported on Nexus 5548.**

---

## Master/Dependent Items Compliance

Audited 2026-06-30 against the Template Design Standard in `../CLAUDE.md`.

### `.Cisco Generic by SNMP`

**Layering** ✓ — Does not link to `.Generic by SNMP` (correct: role templates handle that link directly, same as MikroTik Generic pattern).

**Key naming** ✓ mostly:
- Standard keys used correctly: `system.hw.model` (→MODEL), `system.hw.serialnumber` (→SERIALNO_A), `system.sw.os` (→OS), `system.cpu.util[...]`, `sensor.temp.value[...]`, `vm.memory.free[...]`, `vm.memory.used[...]`, `sensor.fan.status[...]`, `sensor.psu.status[...]`
- `system.descr` duplicates `.Generic by SNMP`'s `system.descr[sysDescr.0]` — same OID `1.3.6.1.2.1.1.1.0`, causes double polling when both templates are linked
- `entSensorThresholdRxTxValueHighWarn[{#SNMPINDEX}]` etc. in `sfp.discovery` — raw MIB leaf names used as item keys instead of normalized names like `sensor.sfp.rx.warn[...]`
- `system.asr9k.chassis` — platform-specific name, acceptable

**Master/Dependent compliance** ⚠️ PARTIAL:
- ✅ COMPLIANT: `sensor.temp.walk` master + `sensor.temp.discovery` DEPENDENT DR + 2 DEPENDENT prototypes
- ✅ COMPLIANT: `system.sw.os` is DEPENDENT (derived via preprocessing)
- ❌ NON-COMPLIANT: 7 SNMP_AGENT discovery rules with standalone SNMP_AGENT prototypes:
  - `cpu.discovery` — `system.cpu.util[{#SNMPINDEX}]` polled independently per CPU core
  - `entity_sn.discovery` — `system.hw.serialnumber[{#SNMPINDEX}]` polled independently
  - `fan.status.discovery` — `sensor.fan.status[{#SNMPINDEX}]`
  - `memory.discovery` — `vm.memory.free[{#SNMPINDEX}]`, `vm.memory.used[{#SNMPINDEX}]`
  - `psu.discovery` — `sensor.psu.status[{#SNMPINDEX}]`
  - `sfp.discovery` — 5 standalone prototypes including raw-named threshold items
  - `temperature.discovery` — `sensor.temp.status[{#SNMPINDEX}]`, `sensor.temp.value[{#SNMPINDEX}]` (duplicates the walk-based discovery)
- Note: `sensor.temp.walk` exists but `temperature.discovery` is a separate SNMP_AGENT DR polling the same OIDs — conflicting implementations

**Macros** ✓ — Uses `{$CPU.UTIL.CRIT}`, `{$MEMORY.UTIL.MAX}`, `{$TEMP_CRIT}`, `{$TEMP_WARN}` — standard names.

### `.Cisco - Optical interfaces by SNMP`

**Master/Dependent compliance** ✅ FULLY COMPLIANT:
- One walk master `cisco.entity.sensor.walk` (SNMP_AGENT) — vendor prefix acceptable (Cisco-specific MIB namespace)
- 2 DEPENDENT discovery rules (`cisco.entity.sfp.power.discovery`, `cisco.entity.sfp.temp.discovery`)
- All item prototypes DEPENDENT on the walk master

### `.Cisco Switch` / `.Cisco Router`

Empty role templates (zero items, zero DRs) — correct per standard. Linkage: `.Generic by SNMP` + `.Network Interfaces by SNMP` + `.Cisco Generic by SNMP`.
