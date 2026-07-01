#!/usr/bin/env python3
"""
MikroTik OSPF monitoring via RouterOS API (port 8728)
Zabbix external script — called by Zabbix server directly.

Usage:
    mikrotik_ospf_api.py <host> <username> <password> [port]

Returns JSON object keyed by index (0, 1, 2 ...) with OSPF data.

Matching logic (in priority order):
  1. neighbor.area == template.area AND neighbor.instance == template.instance  (exact)
  2. Subnet match: neighbor IP falls inside interface IP subnet              (fallback)

This handles:
  - Environments with `networks=` configured on templates
  - Environments WITHOUT networks configured (engineers forgot / ptp links)
  - OSPFv2 and OSPFv3 running on same interface (different areas) — no cross-contamination
"""

import json
import sys
from ipaddress import ip_interface, ip_network

try:
    from librouteros import connect
    from librouteros.exceptions import LibRouterosError
except ImportError:
    print(json.dumps({"error": "librouteros not installed. Run: pip install librouteros"}))
    sys.exit(1)


def get_ospf_data(host, username, password, port=8728):
    try:
        api = connect(
            host=host,
            username=username,
            password=password,
            port=int(port),
            use_ssl=False,
            timeout=10,
        )
    except Exception as e:
        return {"error": f"Connection failed: {e}"}

    try:
        templates  = list(api.path("/routing/ospf/interface-template"))
        neighbors  = list(api.path("/routing/ospf/neighbor"))
        all_ips    = list(api.path("/ip/address"))
        areas      = list(api.path("/routing/ospf/area"))
    except LibRouterosError as e:
        return {"error": f"API query failed: {e}"}

    # Map area name -> instance name  e.g. "backbone-v2" -> "default-v2"
    area_to_instance = {a.get("name", ""): a.get("instance", "") for a in areas}

    result = {}

    for idx, tmpl in enumerate(templates):
        iface         = tmpl.get("interfaces", "")
        networks_raw  = tmpl.get("networks", "")
        cost          = tmpl.get("cost", "")
        area          = tmpl.get("area", "")
        tmpl_instance = area_to_instance.get(area, "")
        disabled      = "1" if tmpl.get("disabled") == "true" else "0"
        inactive      = "2" if tmpl.get("inactive") == "true" else ""
        flags         = disabled + inactive

        # Build subnet list
        # Priority: use configured networks; fallback to interface assigned IPs
        subnets = []
        if networks_raw:
            if isinstance(networks_raw, str):
                subnets = [n.strip() for n in networks_raw.split(",") if n.strip()]
            else:
                subnets = [str(networks_raw)]
        else:
            # No networks= configured — use IP addresses assigned to this interface
            for ip_entry in all_ips:
                if ip_entry.get("interface") == iface:
                    addr = ip_entry.get("address", "")
                    if addr:
                        subnets.append(addr)

        has_neighbor = 0
        info = {}

        for nbr in neighbors:
            naddr        = nbr.get("address", "")
            nbr_area     = nbr.get("area", "")
            nbr_instance = nbr.get("instance", "")

            if not naddr:
                continue

            matched = False

            # PRIMARY: exact area + instance match
            # This is the correct way — RouterOS neighbor object carries area and instance
            if nbr_area and nbr_instance:
                if nbr_area == area and nbr_instance == tmpl_instance:
                    # Also confirm IP is reachable via this interface's subnets (when subnets known)
                    if subnets:
                        try:
                            nip = ip_interface(naddr).ip
                            if any(
                                nip in ip_network(sn if "/" in sn else sn + "/32", strict=False)
                                for sn in subnets
                            ):
                                matched = True
                        except Exception:
                            pass
                    else:
                        # No subnets to verify — trust area+instance match alone
                        matched = True

            # FALLBACK: neighbor object has no area/instance (older RouterOS or stripped fields)
            # Use subnet matching only
            if not matched and not nbr_area and subnets:
                try:
                    nip = ip_interface(naddr).ip
                    if any(
                        nip in ip_network(sn if "/" in sn else sn + "/32", strict=False)
                        for sn in subnets
                    ):
                        matched = True
                except Exception:
                    pass

            if not matched:
                continue

            has_neighbor = 1
            info = {
                "ADDRESS":      naddr,
                "ROUTERID":     nbr.get("router-id", ""),
                "STATEOSPF":    nbr.get("state", ""),
                "ADJACENCY":    nbr.get("adjacency", ""),
                "STATECHANGES": str(nbr.get("state-changes", "")),
            }
            break  # one neighbor per template entry

        entry = {
            "INTERFACE":   iface,
            "NETWORKS":    networks_raw,
            "COST":        str(cost),
            "AREA":        area,
            "FLAGS":       flags,
            "HASNEIGHBOR": "1" if has_neighbor else "0",
        }
        if has_neighbor:
            entry.update(info)

        result[str(idx)] = entry

    return result


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: mikrotik_ospf_api.py <host> <user> <password> [port]"}))
        sys.exit(1)

    host     = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    port     = int(sys.argv[4]) if len(sys.argv) > 4 else 8728

    data = get_ospf_data(host, username, password, port)
    print(json.dumps(data, indent=2))

