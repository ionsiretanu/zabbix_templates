# Ceragon Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: DONE ✅ (2026-06-30)

## Old Zabbix source
- Old template name(s): `ZENTRO_ZBX_TEMPLATE_CERAGON_IP50EXP_RADIO` (ID 39097)
- No IP50CX template found in old Zabbix — all 12 found hosts used IP50EXP template
- Host count in old Zabbix: 12 hosts found with this template ID (32 total in all_hosts.json, some may not be in old Zabbix yet)
- Old template was minimal: 3 hardcoded IF-MIB items at interface .2, no discovery, no radio health

## Template files

| File | Template name | Format | Status |
|---|---|---|---|
| `zbx_export_templates (.Ceragon Generic by SNMP).json` | `.Ceragon Generic by SNMP` | **7.4** | Active — new template |
| `zbx_export_templates (.Ceragon Radio).json` | `.Ceragon Radio` | **7.4** | Active — new template |

## New Zabbix template IDs (https://172.30.20.150)
- `.Ceragon Generic by SNMP`: ID **11110**
- `.Ceragon Radio`: ID **11111**
- Template group `Ceragon` (template groups): ID 102
- Host group `Ceragon` (host groups): ID 103

## Template architecture
**Two-layer model** (same pattern as Siklu):
```
.Generic by SNMP → .Ceragon Generic by SNMP → .Ceragon Radio
```
- `.Ceragon Generic by SNMP` links to `.Generic by SNMP` — inventory items only
- `.Ceragon Radio` links to `.Ceragon Generic by SNMP` — walk masters + LLD discoveries
- No separate role template needed (single-purpose radio device)
- `[network-tool]` block in `.Ceragon Radio` description

## One template covers both IP50EXP and IP50CX
Decision: one `.Ceragon Radio` template for all Ceragon IP50 models.
- Only IP50EXP template existed in old Zabbix (ID 39097) — no separate IP50CX template
- ENTITY-MIB (1.3.6.1.2.1.47.x.x.x) is NOT supported on Ceragon IP50 — no entPhysical data
- OIDs confirmed on IP50EX-P (same enterprise 1.3.6.1.4.1.2281 as all IP50 variants)

## Test device
- IP: **172.16.4.35**
- SNMP community: `oomoomee`
- Model: IP-50EX-P (AO E-band system HP, PoE, AES)
- FW: 13.1.0.0.0.195
- Serial: T096K20415
- Test host in new Zabbix: ID 11112 (`ceragon-test-172.16.4.35`)

## Confirmed OID map (IP50EX-P, FW 13.1.0.0.0.195)

### System inventory (scalar get[], single-instance)

| Item key | OID | Live value |
|---|---|---|
| `system.hw.model` | `1.3.6.1.4.1.2281.10.1.2.3.0` | "IP-50EX-P" |
| `system.hw.serialnumber` | `1.3.6.1.4.1.2281.10.1.2.10.1.1.6.127` | "T096K20415" |
| `system.hw.firmware` | `1.3.6.1.4.1.2281.10.4.1.13.1.1.4.1` | "13.1.0.0.0.195" |
| `sensor.temp.value[ceragonSysTempBoard.0]` | `1.3.6.1.4.1.2281.10.1.1.9.0` | 41-42°C |

**Note on serial:** The table at `.10.1.2.10.1.1.x` is indexed by module/board index. Index 127 is the main chassis board on IP50. If other IP50 models use a different index, this OID must be updated. Column 6 = serial number, column 2 = model, column 5 = HW part number.

**Note on firmware:** Table `.10.4.1.13.1.1.x.{component}` where column 4 = current version, component index 1 = "strm" (main software). Index 1 is constant for the main OS.

### Radio performance (walk indexed by ifIndex)

Radio interface ifIndex: **268451905** (ifDescr="Radio", ifName="Radio: Slot 1, Port 1")

Master walk key `net.wlan.walk` covers:

| Item key | OID column | Live value | Notes |
|---|---|---|---|
| `net.wlan.health.[rsl.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.1.1.2.{ifIndex}` | -35 dBm | Integer dBm, no multiplier |
| `net.wlan.pow.[txpow.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.1.1.3.{ifIndex}` | 14 dBm | Integer dBm, no multiplier |
| `net.wlan.rf.[txfreq.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.2.1.3.{ifIndex}` | 82125000000 Hz | kHz → ×1000 → Hz |
| `net.wlan.rf.[rxfreq.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.2.1.4.{ifIndex}` | 72125000000 Hz | kHz → ×1000 → Hz |
| `net.wlan.cap.[cap.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.2.1.16.{ifIndex}` | 600000000 bps | raw=600, assumed Mbps → ×1,000,000 |
| `net.wlan.mod.[txmod.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.2.1.19.{ifIndex}` | 3 (→16QAM) | Valuemap unverified, see below |
| `net.wlan.mod.[rxmod.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.2.1.21.{ifIndex}` | 3 (→16QAM) | Same valuemap |
| `net.wlan.health.[rsl.mimo.{#SNMPINDEX}]` | `1.3.6.1.4.1.2281.10.5.2.1.22.{ifIndex}` | -68 dBm | Likely XPIC/diversity channel |

**Unverified items (need MIB documentation confirmation):**
- Capacity OID `.10.5.2.1.16` — assumed Mbps based on live value 600; plausible for 16QAM at 2 GHz E-band channel
- Modulation valuemap codes: 1=BPSK, 2=QPSK, 3=16QAM, 4=32QAM, 5=64QAM, 6=128QAM, 7=256QAM, 8=512QAM, 9=1024QAM — assumed from industry convention; current device shows 3 at RSL -35 dBm
- RSL MIMO `.10.5.2.1.22` = -68 dBm while main RSL = -35 dBm — 33 dB difference suggests inactive XPIC port or orthogonal polarization with weak cross-pol signal

### Interface discovery (IF-MIB via net.if.walk)
Three interfaces discovered on test IP50EX-P:
- ifIndex 268443714: Ethernet GE (ifType=6, 10 Gbps)
- ifIndex 268451905: Radio (ifType=1/other, ~9.9 Gbps reported in IF-MIB, carrying traffic)
- ifIndex 268460097: Ethernet GE (ifType=6, 1 Gbps)

HC counters (ifHCInOctets, ifHCOutOctets) confirmed supported.

## Master/Dependent Compliance

**Layering** ✓ — Two-layer model (Generic + Radio). Correct pattern for single-purpose radio devices.

**Key naming** ✓ — All items use standard unprefixed keys:
- `system.hw.model`, `system.hw.serialnumber`, `system.hw.firmware` ✓
- `sensor.temp.value[...]` ✓
- `net.if.*`, `net.wlan.*` ✓

**Master/Dependent** ✓ — Full compliance:
- `net.if.walk` → `net.if.discovery` (DEPENDENT) → 9 item prototype types (DEPENDENT)
- `net.wlan.walk` → `net.wlan.discovery` (DEPENDENT) → 8 item prototypes (DEPENDENT)
- Scalar GETs for single-instance items (model, serial, firmware, temperature) — allowed exception

**Macros** ✓ — All standard threshold macros present: `{$TEMP_CRIT}`, `{$TEMP_WARN}`, `{$RSL.HIGH}`, `{$RSL.LOW}`, `{$HEALTH_TRIGGER_INT}`, `{$HEALTH_POLL_INT}`, `{$INVENTORY_INT}`

**Trigger thresholds** — Old template had NO radio health triggers. RSL thresholds (`{$RSL.HIGH}=-24`, `{$RSL.LOW}=-42`) carried over from Aviat as reasonable starting values; adjust per link budget.

## Import checklist

- [x] JSON validates: `python3 -m json.tool "*.json" > /dev/null && echo valid`
- [x] Imported to new Zabbix (https://172.30.20.150) with `templateLinkage: createMissing: true`
- [x] `[network-tool]` block present in `.Ceragon Radio` description
- [x] Template groups created and assigned (Ceragon group ID 102)
- [x] Test host confirmed collecting — all system items + 8 radio items + 27 IF-MIB items
- [x] Master/dependent pattern used for all discoverable metrics — no standalone SNMP items in discovery rules
- [x] Key names follow standard convention (vendor-agnostic where possible)

## Pending / future work
- Verify modulation valuemap codes against actual Ceragon IP50 MIB documentation
- Verify capacity OID `.10.5.2.1.16` unit (assumed Mbps, plausible)
- Verify RSL MIMO/diversity OID `.10.5.2.1.22` meaning (XPIC? diversity RX? cross-pol?)
- Adjust `{$RSL.LOW}` per actual link budget for each site
- Run migration script to move all 32 Ceragon hosts from old Zabbix to new Zabbix with `.Ceragon Radio` template
