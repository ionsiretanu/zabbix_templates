# Siklu Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: DONE ✅ (2026-06-30) — 6 templates

### Template files & IDs

| File | Template | New Zabbix ID | Role |
|---|---|---|---|
| `zbx_export_templates (.Siklu Generic by SNMP).json` | `.Siklu Generic by SNMP` | **11077** | Vendor generic: model, serial, MAC, hw.rev |
| `zbx_export_templates (.Siklu EH Radio).json` | `.Siklu EH Radio` | **11074** | EH radio metrics (walk+dependent) |
| `zbx_export_templates (.Siklu MH Radio).json` | `.Siklu MH Radio` | **11073** | MH-T280 radio metrics (HC 64-bit, ^rf- LLD) |
| `zbx_export_templates (.Siklu B100 Radio).json` | `.Siklu B100 Radio` | **11102** | MH-B100 60GHz radio (.31926.27.1/4.* MIB) |
| `zbx_export_templates (.Siklu T200 Radio).json` | `.Siklu T200 Radio` | **11103** | MH-T200 60GHz radio (.31926.27.2.* MIB) |
| `zbx_export_templates (.Siklu System Alarm).json` | `.Siklu System Alarm` | **11078** | EH + B100 alarm table add-on |

### Model → template mapping (verified by live SNMP walk)

| Template | Models | MIB subtree | Counters |
|---|---|---|---|
| `.Siklu EH Radio` | EH-600T/TX, EH-614TX, EH-1200/F/FX/L/TL/TX, EH-2200F/FX, EH-2500F/FX, EH-5500FD, EH-8010FX/L/H | `.31926.2.*` | 32-bit |
| `.Siklu MH Radio` | MH-T280, MH-N366(?), ML2.5-60-35(?) | `.31926.35.*` | HC 64-bit |
| `.Siklu B100 Radio` | MH-B100-CCS-PoE-MWB | `.31926.27.1.*` + `.27.4.*` | 32-bit |
| `.Siklu T200 Radio` | MH-T200-CNN-PoE-MWB, MH-T200-CCC-PoE-MWB | `.31926.27.2.*` | 32-bit |

**MH-N366 and ML2.5-60-35: unverified** — currently assigned to `.Siklu MH Radio`, must confirm `.31926.35.*` OIDs exist on live devices before bulk migration.

### Template inheritance chain

```
.Generic by SNMP
    └── .Siklu Generic by SNMP   ← model, serial, MAC, hw.rev (ENTITY-MIB)
            ├── .Siklu EH Radio   ← EH firmware/bank, temp, voltage, alarms, radio LLD, if LLD (32-bit)
            ├── .Siklu MH Radio   ← MH temp, radio LLD (rf-* filter), if LLD (HC 64-bit)
            ├── .Siklu B100 Radio ← B100 temp/firmware (.31926.1.*), radio (.27.1/4.*), if LLD (32-bit)
            └── .Siklu T200 Radio ← T200 temp/firmware (.31926.1.*), radio (.27.2.*), if LLD (32-bit)

.Siklu System Alarm              ← EH + B100 alarm table add-on; standalone, no parent
```

**Note:** `.Siklu Generic by SNMP` does NOT link to `.Generic by SNMP` at import time — it already had this link from first import (templateLinkage createMissing doesn't remove links). All Radio templates link only to `.Siklu Generic by SNMP`; `.Generic by SNMP` is inherited transitively.

### Import checklist
- [x] `.Siklu Generic by SNMP` created (ID 11077) — `system.hw.model`, `system.hw.serialnumber`, `siklu.hw.rev`, `siklu.mac`
- [x] `.Siklu EH Radio` redesigned — master/dependent walk pattern, `net.wlan.radio.walk` + `net.if.walk`
- [x] `.Siklu MH Radio` redesigned — walk+LLD, radio DR filtered on `^rf-` ifName, HC 64-bit counters
- [x] `.Siklu System Alarm` created (ID 11078) — alarm table walk LLD (EH + B100)
- [x] `.Siklu B100 Radio` created (ID 11102) — B100 60GHz, .31926.27.1/4.* MIB, 32-bit if counters
- [x] `.Siklu T200 Radio` created (ID 11103) — T200 60GHz, .31926.27.2.* MIB, 32-bit if counters
- [x] All 6 imported to new Zabbix with standard RULES (templateLinkage createMissing)
- [x] `Siklu` template group created (ID 89)
- [x] `[network-tool]` blocks updated in all templates with model mapping comment

### Live verification (2026-06-30)

**EH test host: `366W-675W-SK2G` (10.12.236.220, `EWsnmp420`) — EH-2500FX**
- model=EH-2500FX, serial=F625193321, hw.rev=A0, mac=0:24:a4:6:97:60 ✓
- temperature=38°C ✓
- RSSI=-38dBm, CINR=28dB, TX power=11dBm, modulation=6, freq=81875MHz (81.875GHz) ✓
- Radio state=1 (active) ✓, 2 active alarms ✓, voltage=54 ✓
- Firmware returns `1` (EH2500 bank index quirk — documented)
- Interface LLD: 6 interfaces (32-bit counters), collecting bps ✓

**MH test host: `171A-209M-T280` (10.12.225.188, `oomoomee`) — MH-T280**
- model=MH-T280, serial=FC20597790, hw.rev=A1 ✓
- temperature=30°C ✓
- RSSI=-54dBm, CINR=10dB, TX/RX cap=2050Mbps (2050000000 bps) ✓, modulation=9 ✓
- Interface LLD: 5 interfaces (ifIndex 101-105, HC 64-bit), radio at .105 collecting ✓
- `siklu.mac` NO DATA — known gap: Generic uses ifPhysAddress.1 but MH CPU MAC is at .104

**B100 test host: `2142-2147-SKB100` (10.12.234.235, hostid 11091) — MH-B100-CCS-PoE-MWB**
- model=MH-B100-CCS-PoE-MWB, serial=F018386529, firmware=MH-2.3.0.26881 (via `.31926.1.5.0`) ✓
- temperature=33°C (via `.31926.1.2.0`, same OID as EH series) ✓
- RSSI=-50dBm, CINR=12dB, TX/RX MCS=8, state=1 (active) ✓
- Radio OIDs: `.31926.27.4.*` (peer table) for RSSI/CINR, `.31926.27.1.*` (link table) for TX power
- Radio LLD: discovers from `.27.4.1.10` (peer operational state), index .1 confirmed
- Interface LLD: 5 Ethernet interfaces (Host/Eth1/Eth2/Eth3/Eth-tu1), NO radio in IF-MIB
- 32-bit counters (ifHCInOctets returns "No Such Object" on B100)
- Alarm table `.31926.11.*` confirmed present (2 active alarms on test date) — attach `.Siklu System Alarm`
- `siklu.mac` at ifPhysAddress.1 = "00 24 A4 14 F4 69" (Host interface) ✓

**T200 test host: `1705-2333-SKT200` (10.12.244.70, hostid 11093) — MH-T200-CNN-PoE-MWB**
- model=MH-T200-CNN-PoE-MWB, serial=F931334644, hw.rev=A2 ✓
- firmware=MH-2.2.0.25894 2019-03-17 15:08 (via `.31926.1.5.0`) ✓
- temperature=32°C (via `.31926.1.2.0`, same OID as EH/B100) ✓
- RSSI=-68dBm, MCS=7, `.31926.27.2.1.12`=30 (TX power?), state=2 (connected) ✓
- Radio OIDs: `.31926.27.2.*` — DIFFERENT from B100 (`.27.1/4.*`) and T280 (`.35.*`)
- Radio LLD: discovers from `.27.2.1.17` (RSSI column), index .1 confirmed
- Interface LLD: 3 Ethernet interfaces (Host/Eth-bu1/Eth1), NO radio in IF-MIB
- 32-bit counters (ifHCInOctets returns "No Such Object" on T200)
- Alarm table `.31926.11.*` present (5 alarms on test date) — attach `.Siklu System Alarm`
- No CINR column visible in `.27.2.*` walk — T200 MIB does not expose SNR/CINR
- `siklu.mac` at ifPhysAddress.1 = "0:24:a4:13:b1:91" (Host interface) ✓

### Template group IDs
- `Siklu` → ID 89 (created)
- `ITcare` → ID 23
- `Templates/Wireless` → ID 36

## Key design decisions (2026-06-30)

### Walk master pattern (mandatory)
Both EH and MH use master/dependent pattern — no standalone SNMP_AGENT radio items:
- `net.wlan.radio.walk` (SNMP_AGENT walk[...]) → `net.wlan.radio.discovery` (DEPENDENT DR) → item prototypes (DEPENDENT)
- `net.if.walk` (SNMP_AGENT walk[...]) → `net.if.discovery` (DEPENDENT DR) → interface item prototypes

### MH radio LLD (confirmed 2026-06-30)
MH radio interface is **discoverable via LLD** (not hardcoded):
- `ifName` at ifIndex 105 = `"rf-209171a"` — pattern `^rf-` matches the radio interface
- Discovery rule `net.wlan.radio.discovery` (DEPENDENT on `net.if.walk`) with filter `{#IFNAME} MATCHES_REGEX ^rf-`
- Item prototypes use `net.wlan.radio.walk` as master (MH .31926.35.* subtree)
- Old hardcoded approach (ifIndex 105 direct OID) was replaced by this LLD

### MH alarm table (confirmed absent)
`1.3.6.1.4.1.31926.11.*` returns "No Such Object" on live MH-T280. The `.Siklu System Alarm` template is EH-ONLY. Do not attach it to MH hosts.

### EH traffic counters
64-bit `ifHCInOctets`/`ifHCOutOctets` NOT supported on EH series. Template uses 32-bit `ifInOctets`/`ifOutOctets` via `net.if.walk`. MH uses HC 64-bit (confirmed working at ifIndex 105).

### Temperature sensor placement
- EH: single sensor at `.31926.1.2.0` — direct SNMP_AGENT item (no LLD needed)
- MH: sensor in radio table at `.31926.35.1.1.3.1.1.13.{ifIndex}` — direct SNMP_AGENT at hardcoded ifIndex 105 (temperature not discoverable from radio walk in MH)

### Trigger dependencies
Item-level trigger dependencies fail during fresh template import (Zabbix bug/limitation). Warn/Critical temp triggers are currently independent (no dependency). Set dependencies manually in Zabbix UI after import if needed.

## Trigger threshold comparison (old templates → new macros)

| Model | RSSI Low | RSSI High | CINR Low | Source |
|---|---|---|---|---|
| EH-1200FX | **-43** | **-31** | **20** | `ZENTRO_ZBX_TEMPLATE_SIKLU_EH1200_RADIO` |
| EH-2200FX | -42 | -33 | 22 | `ZENTRO_ZBX_TEMPLATE_SIKLU_EH2200_RADIO` |
| EH-2500FX | -42 | -33 | 22 | `ZENTRO_ZBX_TEMPLATE_SIKLU_EH2500_RADIO` |
| EH-5500FD | -42 | -35 | 22 | `ZENTRO_ZBX_TEMPLATE_SIKLU_EH5500_RADIO` |
| EH-8010FX-L/H | -42 | **-24** | 22 | `ZENTRO_ZBX_TEMPLATE_SIKLU_EH8010_RADIO` |
| MH-T280 | -42 | -33 | 22 | `ZENTRO_ZBX_TEMPLATE_SIKLU_MH_RADIO` |

Per-model overrides implemented as **context-specific macros** in `.Siklu EH Radio`:
- `{$RSL.HIGH}` = -33 (default: EH-2200FX/2500FX/MH)
- `{$RSL.HIGH:"EH-1200FX"}` = -31
- `{$RSL.HIGH:"EH-5500FD"}` = -35
- `{$RSL.HIGH:"EH-8010FX"}` = -24 (bare model, no suffix)
- `{$RSL.HIGH:"EH-8010FX-L"}` = -24
- `{$RSL.HIGH:"EH-8010FX-H"}` = -24
- `{$RSL.LOW}` = -42 (default)
- `{$RSL.LOW:"EH-1200FX"}` = -43
- `{$CINR.LOW}` = 22 (default)
- `{$CINR.LOW:"EH-1200FX"}` = 20

## `.Siklu Generic by SNMP` items

| Item | Key | OID | Inventory |
|---|---|---|---|
| Hardware model name | `system.hw.model` | `1.3.6.1.2.1.1.1.0` (sysDescr) | MODEL |
| Hardware serial number | `system.hw.serialnumber` | `1.3.6.1.2.1.47.1.1.1.1.11.1` (ENTITY-MIB) | SERIALNO_A |
| Hardware revision | `siklu.hw.rev` | `1.3.6.1.2.1.47.1.1.1.1.8.1` (ENTITY-MIB) | — |
| MAC address | `siklu.mac` | `1.3.6.1.2.1.2.2.1.6.1` (ifPhysAddress.1) | MACADDRESS_A |

## `.Siklu EH Radio` items (EH-specific)

| Item | Key | OID | Notes |
|---|---|---|---|
| Firmware version | `system.hw.firmware` | `1.3.6.1.4.1.31926.1.7.0` | Returns int 1 on EH2500 (bank index) |
| SW Bank 1 version | `siklu.sw.bank1` | `1.3.6.1.4.1.31926.1.5.0` | |
| SW Bank 2 version | `siklu.sw.bank2` | `1.3.6.1.4.1.31926.1.6.0` | |
| SW Bank 2 running | `siklu.sw.bank2.running` | `1.3.6.1.4.1.31926.1.8.0` | Returns 2 on EH2500 (bank 2 active) |
| Temperature | `sensor.temp.value[rbSysTemperature.0]` | `1.3.6.1.4.1.31926.1.2.0` | Direct item (single sensor) |
| Voltage | `siklu.system.voltage` | `1.3.6.1.4.1.31926.1.1.0` | mV |
| Alarm count | `siklu.alarms.count` | `1.3.6.1.4.1.31926.11.1.2.0` | Also in .Siklu System Alarm |
| Radio walk | `net.wlan.radio.walk` | `walk[.31926.2.1.1.3,4,17,18,19,42,46 + .31926.2.2.1.9]` | Walk master |
| Interface walk | `net.if.walk` | `walk[ifName,ifDescr,ifAdminStatus,ifOperStatus,ifInOctets,ifOutOctets,ifInErrors,ifOutErrors]` | 32-bit |

**Radio LLD (`net.wlan.radio.discovery`)** item prototypes: state, RSSI, CINR, TX power, modulation, frequency, channel width, RX error packets.

## `.Siklu MH Radio` items (MH-specific)

| Item | Key | OID | Notes |
|---|---|---|---|
| Temperature | `sensor.temp.value[rbSysTemperature.0]` | `1.3.6.1.4.1.31926.35.1.1.3.1.1.13.105` | Hardcoded ifIndex 105 |
| Radio walk | `net.wlan.radio.walk` | `walk[.31926.35.1.1.3.1.1.7,8,9,10,14,15]` | RSSI/CINR/RXmod/TXmod/TXcap/RXcap |
| Interface walk | `net.if.walk` | `walk[ifName,ifDescr,ifAdminStatus,ifOperStatus,ifHCInOctets,ifHCOutOctets,ifInErrors,ifOutErrors]` | HC 64-bit |

**Radio LLD (`net.wlan.radio.discovery`)** filtered on `{#IFNAME} MATCHES_REGEX ^rf-` — discovers rf interface (ifIndex 105 on MH-T280).

## `.Siklu B100 Radio` items (MH-B100-specific)

| Item | Key | OID | Notes |
|---|---|---|---|
| Temperature | `sensor.temp.value[rbSysTemperature.0]` | `1.3.6.1.4.1.31926.1.2.0` | Same OID as EH! Confirmed 33°C |
| Firmware | `system.hw.firmware` | `1.3.6.1.4.1.31926.1.5.0` | Returns full version string (not int) |
| Radio walk | `net.wlan.radio.walk` | `walk[.27.1.1.7,8,10 + .27.4.1.7,10,12,13,14]` | `.27.1.*` local, `.27.4.*` peer |
| Interface walk | `net.if.walk` | `walk[ifName,ifDescr,ifAdminStatus,ifOperStatus,ifInOctets,ifOutOctets,ifInErrors,ifOutErrors]` | 32-bit (HC not supported) |

**Radio LLD (`net.wlan.radio.discovery`)** discovers from `.31926.27.4.1.10` (peer operational state). Index `.1` = single peer. Item prototypes: state, RSSI (`.27.4.1.12`), CINR (`.27.4.1.13`), TX power (`.27.1.1.10`), TX MCS (`.27.1.1.8`), RX MCS (`.27.4.1.7`).

**No radio in IF-MIB** — B100 Ethernet interfaces are Host/Eth1/Eth2/Eth3/Eth-tu1.
**Alarm table** `.31926.11.*` is present — attach `.Siklu System Alarm` to B100 hosts (same as EH).

## `.Siklu T200 Radio` items (MH-T200-specific)

| Item | Key | OID | Notes |
|---|---|---|---|
| Temperature | `sensor.temp.value[rbSysTemperature.0]` | `1.3.6.1.4.1.31926.1.2.0` | Same OID as EH/B100! Confirmed 32°C |
| Firmware | `system.hw.firmware` | `1.3.6.1.4.1.31926.1.5.0` | Full version string: "MH-2.2.0.25894 2019-03-17 15:08" |
| Radio walk | `net.wlan.radio.walk` | `walk[.27.2.1.5,.27.2.1.8,.27.2.1.9,.27.2.1.12,.27.2.1.17]` | Combined link table |
| Interface walk | `net.if.walk` | `walk[ifName,ifDescr,ifAdminStatus,ifOperStatus,ifInOctets,ifOutOctets,ifInErrors,ifOutErrors]` | 32-bit (HC not supported) |

**Radio LLD (`net.wlan.radio.discovery`)** discovers from `.31926.27.2.1.17` (RSSI column). Item prototypes: state (`.27.2.1.8`), RSSI (`.27.2.1.17`), TX power (`.27.2.1.12`, assumed), MCS (`.27.2.1.9`).

**No CINR column** — `.31926.27.2.*` MIB does not expose SNR/CINR on T200.  
**No radio in IF-MIB** — T200 Ethernet interfaces are Host/Eth-bu1/Eth1 (3 total).  
**Alarm table** `.31926.11.*` is present — attach `.Siklu System Alarm` to T200 hosts.

**Key difference from B100:** B100 uses `.27.1.*` (local link) + `.27.4.*` (peer) split tables; T200 uses single `.27.2.*` combined table. OIDs are incompatible — they cannot share a template.

## Consolidation analysis

**Old Zabbix:** 6 per-model templates + 2 shared (SYSTEM_ALARM, WIRELESS_TRAFFIC) covering ~2363 hosts.
**Result: 6 new templates** — Generic (shared), EH Radio, MH Radio, B100 Radio, T200 Radio, System Alarm (EH+B100+T200 add-on).

## Old Zabbix sources

| Old template | Model(s) | Hosts |
|---|---|---|
| `ZENTRO_*_SIKLU_EH8010_RADIO` | EH-8010FX-L/H | 963 |
| `ZENTRO_*_SIKLU_EH1200_RADIO` | EH-1200FX | 354 |
| `ZENTRO_*_SIKLU_EH2200_RADIO` | EH-2200FX | 276 |
| `ZENTRO_*_SIKLU_EH5500_RADIO` | EH-5500FD | 214 |
| `ZENTRO_*_SIKLU_EH2500_RADIO` | EH-2500FX | 75 |
| `ZENTRO_*_SIKLU_MH_RADIO` | MH-T280, ML2.5-60-35 | 481 |
| **Total** | | **2363** |

## [network-tool] blocks (in template descriptions)

```ini
# .Siklu EH Radio
[network-tool]
manufacturer = [ "Siklu" ]
device_role = [ "Radio Link" ]
device_types = [ "EH-600T", "EH-600TX", "EH-614TX", "EH-1200", "EH-1200F", "EH-1200FX", "EH-1200L", "EH-1200TL", "EH-1200TX", "EH-2200F", "EH-2200FX", "EH-2500F", "EH-2500FX", "EH-5500FD", "EH-8010FX", "EH-8010FX-L", "EH-8010FX-H" ]
```

```ini
# .Siklu MH Radio — MH-N366 and ML2.5-60-35 are UNVERIFIED (no live SNMP walk done yet)
[network-tool]
manufacturer = [ "Siklu" ]
device_role = [ "Radio Link" ]
device_types = [ "MH-T280", "MH-N366", "ML2.5-60-35" ]
```

```ini
# .Siklu B100 Radio
[network-tool]
manufacturer = [ "Siklu" ]
device_role = [ "Radio Link" ]
device_types = [ "MH-B100-CCS-PoE-MWB" ]
```

```ini
# .Siklu T200 Radio
[network-tool]
manufacturer = [ "Siklu" ]
device_role = [ "Radio Link" ]
device_types = [ "MH-T200-CNN-PoE-MWB", "MH-T200-CCC-PoE-MWB" ]
```
