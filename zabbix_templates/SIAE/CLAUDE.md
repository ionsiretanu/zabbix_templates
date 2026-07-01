# SIAE Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: DONE ✅ (3 templates, 2026-06-30)

New Zabbix template IDs:
- `.SIAE Generic by SNMP` → ID **11104**
- `.SIAE AlfoPlus80 Radio` → ID **11105** (covers HDX + AlfoPlus2)
- `.SIAE AlfoPlus80HD Radio` → ID **11106** (HD only — completely different MIB subtree)

## Old Zabbix sources

| Old template | Product line | Hosts |
|---|---|---|
| `ZENTRO_*_SIAE_ALFOPLUS80HDX_RADIO` | AlfoPlus80HDX | ~533 |
| `ZENTRO_*_SIAE_ALFOPLUS80HD_RADIO` | AlfoPlus80HD | ~331 |
| `ZENTRO_*_SIAE_ALFOPLUS2_RADIO` | AlfoPlus2 | ~103 |
| **Total** | | **~967 hosts** |

## New Zabbix template structure

```
.SIAE Generic by SNMP          (links to .Generic by SNMP)
  ├── .SIAE AlfoPlus80 Radio   (links to .SIAE Generic by SNMP)  ← HDX + AlfoPlus2
  └── .SIAE AlfoPlus80HD Radio (links to .SIAE Generic by SNMP)  ← HD only
```

Template groups: `SIAE`, `ITcare`, `Templates/Wireless`
Tag: `target: siae`

## Critical MIB discovery: HDX/AlfoPlus2 vs HD use entirely different subtrees

Verified live via SNMP on all 3 test devices. The split mandates 3 templates (not 2).

| Product | Radio MIB subtree | Notes |
|---|---|---|
| AlfoPlus80HDX | `1.3.6.1.4.1.3373.1103.80.*` | Single TRX (index 1) |
| AlfoPlus2 | `1.3.6.1.4.1.3373.1103.80.*` | Dual TRX (indices 1,2) + XPIC (101, excluded) |
| AlfoPlus80HD | `1.3.6.1.4.1.3373.1103.39.*` + `.15.*` | `.80.*` returns NoSuchObject on HD |

SIAE enterprise OID base: `1.3.6.1.4.1.3373`
Common inventory OID prefix: `1.3.6.1.4.1.3373.1103`

## OID map — common inventory (all models, .SIAE Generic by SNMP)

| Item key | OID | Notes |
|---|---|---|
| `system.hw.model` | `1.3.6.1.2.1.1.1.0` (sysDescr) | Returns full model string e.g. "ALFOplus80HDX - SIAE Microelettronica" |
| `system.hw.serialnumber` | `1.3.6.1.4.1.3373.1103.6.2.1.13.1` | rbEqSerialNumber chassis |
| `system.hw.firmware` | `1.3.6.1.4.1.3373.1103.7.2.0` | rbSwBench1Version |
| `siae.sys.alarm` | `1.3.6.1.4.1.3373.1103.4.26.0` | rbSysAlarm — 0=no alarm; trigger HIGH on !=0 |

## OID map — AlfoPlus80HDX and AlfoPlus2 (.SIAE AlfoPlus80 Radio)

Walk master key: `siae.radio.walk`
Walk OIDs: `.80.2.1.2`, `.80.12.1.3`, `.80.12.1.4`, `.80.12.1.5`, `.80.17.1.10.1`, `.80.17.1.7.1`

| Item key | OID | Multiplier | Verified live value |
|---|---|---|---|
| LLD anchor (`{#TRXNAME}`) | `1.3.6.1.4.1.3373.1103.80.2.1.2.{idx}` | — | "TRX" (HDX), "TRX A"/"TRX B" (AP2) |
| `net.wlan.health.[rsl.{#SNMPINDEX}]` | `.80.12.1.3.{idx}` | direct dBm | HDX: -31, AP2: -37/-37 |
| `net.wlan.pow.[txpow.{#SNMPINDEX}]` | `.80.12.1.4.{idx}` | direct dBm | |
| `net.wlan.health.[cinr.{#SNMPINDEX}]` | `.80.12.1.5.{idx}` | ×0.1 | HDX raw=326 → 32.6 dBm |
| `net.wlan.cap.[cap.{#SNMPINDEX}]` | `.80.17.1.10.1.{idx}` | ×1000 → bps | kbps raw |
| `net.wlan.mod.[profile.{#SNMPINDEX}]` | `.80.17.1.7.1.{idx}` | — | Modulation profile ID |
| `net.wlan.rf.freq` | `.80.9.1.4.1` (standalone GET) | ×1000 → Hz | kHz raw, single value per device |

LLD macro: `{#TRXNAME}` from `.80.2.1.2`
LLD filter: `{#TRXNAME}` NOT_MATCHES_REGEX `XPIC`

**AlfoPlus2 dual-TRX:** Walk `.80.2.1.2` returns TRX A (1), TRX B (2), XPIC-1 (101). Filter drops XPIC-1. Stats in `.80.12` exist only for indices 1 and 2.

**Capacity 2D index:** `.80.17` table is indexed `radio.trx` (e.g. `.80.17.1.10.1.1` = radio=1, trx=1). Walking only radio=1 section (`.80.17.1.10.1`) gives entries with trx as last index — matches TRX LLD index correctly.

## OID map — AlfoPlus80HD (.SIAE AlfoPlus80HD Radio)

Walk master key: `siae.radio.hd.walk`
Walk OIDs: `.39.2.1.2`, `.39.2.1.17`, `.39.2.1.50`, `.39.2.1.53`, `.39.2.1.54`, `.15.4.1.17`, `.15.4.1.20`

| Item key | OID | Multiplier | Verified live value |
|---|---|---|---|
| LLD anchor | `1.3.6.1.4.1.3373.1103.39.2.1.53.{idx}` | — | RSSI column used for carrier discovery |
| `net.wlan.health.[rsl.{#SNMPINDEX}]` | `.39.2.1.53.{idx}` | ×0.1 | raw=-333 → -33.3 dBm |
| `net.wlan.pow.[txpow.{#SNMPINDEX}]` | `.39.2.1.54.{idx}` | ×0.1 | |
| `net.wlan.health.[cinr.{#SNMPINDEX}]` | `.39.2.1.17.{idx}` | ×0.1 | raw=296 → 29.6 dBm |
| `net.wlan.cap.[cap.{#SNMPINDEX}]` | `.15.4.1.17.{idx}` | ×1000 → bps | kbps raw |
| `net.wlan.rf.freq[{#SNMPINDEX}]` | `.39.2.1.2.{idx}` | ×1000 → Hz | kHz raw |
| `net.wlan.rf.chanwidth[{#SNMPINDEX}]` | `.39.2.1.50.{idx}` | ×1000 → Hz | kHz raw |
| `net.wlan.mod.[profile.{#SNMPINDEX}]` | `.15.4.1.20.{idx}` | — | Modulation profile ID |

## Trigger thresholds (from old Zabbix + live verification)

| Macro | Value | Source |
|---|---|---|
| `{$RSL.LOW}` | -42 | Old Zabbix trigger threshold, consistent across all 3 model templates |
| `{$RSL.HIGH}` | -24 | Old Zabbix trigger threshold |
| `{$CINR.LOW}` | 22 | Old Zabbix trigger threshold |
| `{$HEALTH_TRIGGER_INT}` | 15m | Old Zabbix trigger avg window |
| `{$RADIO_POLL_INT}` | 1m | Standard |
| `{$HEALTH_POLL_INT}` | 1m | Standard |

HD uses ×0.1 multiplier on RSL and CINR — thresholds in dBm are the same because stored value is already in dBm after preprocessing.

## Test hosts (new Zabbix)

| Host | IP | Model | hostid | Template |
|---|---|---|---|---|
| TEST-SIAE-HDX | 172.16.0.116 | ALFOplus80HDX | 11107 | .SIAE AlfoPlus80 Radio |
| TEST-SIAE-HD | 172.16.10.12 | ALFOplus80HD | 11108 | .SIAE AlfoPlus80HD Radio |
| TEST-SIAE-AP2 | 10.12.229.92 | AlfoPlus2 | 11109 | .SIAE AlfoPlus80 Radio |

SNMP community: `EWsnmp420` (all devices — found via host.get on old Zabbix; template macro `oomoomee` is wrong)
Proxy group: PROXY-CA (proxy_groupid=1, monitored_by=2)

## [network-tool] block strings

`.SIAE AlfoPlus80 Radio`:
```ini
device_types = [ "ALFOplus80HDX - SIAE Microelettronica", "ALFOplus2 - SIAE Microelettronica" ]
```

`.SIAE AlfoPlus80HD Radio`:
```ini
device_types = [ "ALFOplus80HD - SIAE Microelettronica" ]
```

These strings come from `sysDescr` (inventory.hardware column) of live devices, which is what the migration script matches against.

## Import checklist

- [x] JSON validates: `python3 -m json.tool "*.json" > /dev/null && echo valid`
- [x] SIAE template group created (templategroup ID 100, hostgroup ID 101)
- [x] Imported to new Zabbix (https://172.30.20.150) with `templateLinkage: createMissing: true`
- [x] `[network-tool]` block present in template descriptions with verified device_types strings
- [x] Template groups assigned (SIAE, ITcare, Templates/Wireless)
- [x] Test hosts created (11107, 11108, 11109) in new Zabbix
- [x] Master/dependent pattern used for all discoverable metrics
- [x] Key names follow standard convention (vendor-agnostic where possible)
- [x] Test hosts confirmed collecting data (2026-06-30, all 3 hosts verified):
  - HDX: RSL=-31 dBm, CINR=32.5 dBm, cap=10 Gbps, freq=72 GHz, 1 TRX ✅
  - HD: RSL=-33.2 dBm, CINR=29.6 dBm, cap=2 Gbps, freq=71.25 GHz, chanwidth=250 MHz ✅
  - AP2: RSL=-37/-37 dBm (2 TRX), CINR=43.6/43 dBm, cap=650/650 Mbps, freq=11.075 GHz ✅
- [ ] Migration script RULES updated with SIAE templates

## Notes / Lessons learned

**lld_macro_paths fix (2026-06-30):** SNMP_WALK_TO_JSON first parameter must be a plain string, NOT an LLD macro (`{#TRXNAME}`). Zabbix interprets `{#...}` as a macro reference and tries to resolve it, causing "Cannot process LLD macro" error. Fix: use `NAME` as the parameter, map `$.NAME` → `{#TRXNAME}` in lld_macro_paths. This applies to any custom LLD macro name. `{#SNMPVALUE}` works as a special built-in exception.

## Files

```
SIAE/
├── CLAUDE.md                                              ← this file
├── zbx_export_templates (.SIAE Generic by SNMP).json
├── zbx_export_templates (.SIAE AlfoPlus80 Radio).json
└── zbx_export_templates (.SIAE AlfoPlus80HD Radio).json
```
