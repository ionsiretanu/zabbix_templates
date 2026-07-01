# Aviat Templates — CLAUDE.md

> **Always read `/etc/ansible/CLAUDE.md` at the start of any session in this directory** — it contains required project-wide context (migration script logic, `syn_vars.yml` keys, import `RULES` pattern) and does NOT auto-load here due to the symlink at `vars/templates` (`templates` → `/home/ion_siretanu/zabbix_templates`).

## Status: DONE ✅

## Old Zabbix source
- Old template name(s): `ZENTRO_*_AVIAT_WTM4880_RADIO`
- Host count: 613
- Old Zabbix group: Aviat

## Template files

| File | Template name | Format | Status |
|---|---|---|---|
| `Aviat/zbx_export_templates (.Aviat by SNMP).json` | `.Aviat by SNMP` | **7.4** | Active — new template |
| `Aviat/zbx_export_templates (ZENTRO_ZBX_TEMPLATE_AVIAT_WTM4880_RADIO).json` | `ZENTRO_ZBX_TEMPLATE_AVIAT_WTM4880_RADIO` | 7.0 | Reference only — do not update |

`.Aviat by SNMP` groups: `Aviat`, `ITcare`, `Templates/Wireless`; tag `target: aviat`; parent: `.Generic by SNMP`.

**Architecture:** Uses SNMP bulk walk (`net.if.walk`, `net.wlan.walk`) + LLD for dynamic carrier discovery — no hardcoded interface indices (unlike old template which hardcoded index `.63`).

## Wireless Interface Discovery item prototypes (all DEPENDENT on `net.wlan.walk`)

| Key | Name | Notes |
|---|---|---|
| `net.wlan.cap.[rxcap.{#SNMPINDEX}]` | Rx Capacity | bps |
| `net.wlan.cap.[txcap.{#SNMPINDEX}]` | Tx Capacity | bps |
| `net.wlan.health.[rsl.{#SNMPINDEX}]` | RSL | dBm; has RSL High / RSL Low trigger prototypes |
| `net.wlan.health.[snr.{#SNMPINDEX}]` | SNR | dBm |
| `net.wlan.health.[BER.{#SNMPINDEX}]` | BER | raw |
| `net.wlan.health.[fademar.{#SNMPINDEX}]` | Fade Margin | dB |
| `net.wlan.health.[rxsync.{#SNMPINDEX}]` | Rx Sync Loss | seconds/s |
| `net.wlan.mod.[rxmod.{#SNMPINDEX}]` | Rx Modulation | valuemap: Modulation State |
| `net.wlan.mod.[txmod.{#SNMPINDEX}]` | Tx Modulation | valuemap: Modulation State |
| `net.wlan.pow.[txpow.{#SNMPINDEX}]` | Output Power | dBm |
| `net.wlan.status.[status.{#SNMPINDEX}]` | Carrier Status | valuemap: IF-MIB::ifOperStatus |
| `net.wlan.rf.[chanwidth.{#SNMPINDEX}]` | Channel Width | valuemap: Aviat Channel Width |

## Key macros

| Macro | Value | Purpose |
|---|---|---|
| `{$RSL.HIGH}` | `-24` | RSL high alert threshold (dBm) |
| `{$RSL.LOW}` | `-42` | RSL low alert threshold (dBm) |
| `{$HEALTH_TRIGGER_INT}` | `15m` | Averaging window for health triggers |
| `{$SFP_HIGH_LIGHT}` | `-1` | SFP overload threshold (dBm) |
| `{$SFP_LOW_LIGHT}` | `-18` | SFP sensitivity threshold (dBm) |
| `{$RADIO_POLL_INT}` | `1m` | Radio metrics poll interval |

## Aviat WTM4880 confirmed OID map

| OID suffix (base: `1.3.6.1.4.1.2509.9`) | Description | Multiplier |
|---|---|---|
| `3.2.1.1.1` | Channel bandwidth | — (valuemap: 1=7MHz, 2=14MHz, 3=28MHz, 4=56MHz) |
| `3.2.1.1.11` | Tx Capacity | ×1000 bps |
| `3.2.1.1.12` | Rx Capacity | ×1000 bps |
| `3.2.1.1.13` | Rx Modulation | — |
| `3.2.1.1.14` | Tx Modulation | — |
| `3.2.4.1.2` | Carrier Status | — |
| `5.2.1.1.1` | Tx Frequency | ×1000 Hz |
| `5.2.1.1.2` | Rx Frequency | ×1000 Hz |
| `5.2.2.1.2` | Fade Margin | ×0.1 dB |
| `15.2.2.1.4` | RSL | ×0.1 dBm |
| `15.2.2.1.8` | BER | — |
| `15.2.2.1.11` | Rx Sync Loss | seconds |
| `33.2.2.1.3` | SNR | ×0.1 dBm |
| `33.2.2.1.7` | Output Power | ×0.1 dBm |
| `1.3.6.1.2.1.99.1.1.1.4.77` | SFP1 light (mW) | ×0.001 → log10 for dBm |
| `1.3.6.1.2.1.99.1.1.1.4.82` | SFP2 light (mW) | ×0.001 → log10 for dBm |

---

## Master/Dependent Items Compliance

Audited 2026-06-30 against the Template Design Standard in `../CLAUDE.md`.

### `.Aviat by SNMP`

**Layering** ✓ — Single combined template (no separate Vendor Generic) linking to `.Generic by SNMP`. Correct pattern for single-purpose radio devices.

**Key naming** ❌ VIOLATIONS:
- `device.model` → should be `system.hw.model` (inventory MODEL)
- `serial.number` → should be `system.hw.serialnumber` (inventory SERIALNO_A)
- `Aviat_Rx_Frequency_Carrier1`, `Aviat_Tx_Frequency_Carrier1`, `Aviat_Rx_Frequency_Carrier2`, `Aviat_Tx_Frequency_Carrier2` — CapWords_with_underscore format, vendor prefix, hardcoded carrier index in key name; should be `net.wlan.rf.[rxfreq.carrier1]` or similar dot-separated lowercase
- `Aviat_Rx_Light_mW_SFP1`, `Aviat_Rx_Light_mW_SFP2` — same format issue; should be `net.sfp.rx.power.mw[sfp1]` or included in `net.wlan.walk` LLD
- `Aviat_Rx_Light_dBm_SFP1`, `Aviat_Rx_Light_dBm_SFP2` — calculated items derived from mW, same naming issue
- ✓ `net.wlan.*` prototype keys follow the standard pattern correctly

**Master/Dependent compliance** ⚠️ PARTIAL:
- ✅ COMPLIANT: `net.if.walk` master + `net.if.discovery` DEPENDENT DR + 11 DEPENDENT interface prototypes
- ✅ COMPLIANT: `net.wlan.walk` master + `net.wlan.discovery` DEPENDENT DR + 12 DEPENDENT radio prototypes
- ❌ NON-COMPLIANT: 6 standalone `SNMP_AGENT get[...]` items:
  - `Aviat_Rx/Tx_Frequency_Carrier1/2` — hardcoded to specific OID instances (only 2 carriers; walk+dependent would work but is optional for fixed-count metrics)
  - `Aviat_Rx_Light_mW_SFP1/2` — standalone GETs for 2 fixed SFP indices; same argument applies
  - `device.model`, `serial.number` — single-instance GETs ✓ (allowed exception per standard)

**Preprocessing** ✓ — JavaScript used for SFP mW→dBm log10 conversion. Native MULTIPLIER cannot do logarithmic math; JavaScript is the correct choice here per standard rule 4. The dBm items derive from the mW items as DEPENDENT calculated items.

**Macros** ✓ — Radio-specific macros (`{$RSL.HIGH}`, `{$RSL.LOW}`, `{$HEALTH_TRIGGER_INT}`, `{$RADIO_POLL_INT}`, `{$SFP_HIGH_LIGHT}`, `{$SFP_LOW_LIGHT}`) have no standard equivalents — vendor prefix not applicable. These names should be reused for SIAE, Siklu, Ubiquiti radio templates.
