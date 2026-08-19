#!/usr/bin/env python3
"""Runtime API and verification helpers for the production s-ui stack."""

from __future__ import annotations

import base64
import json
import secrets
import subprocess
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


ADMIN_PASSWORD = Path(__file__).resolve().with_name(".admin-password")
SUI_BASE = "http://127.0.0.1:3095/app"
SUI_SUB = "http://127.0.0.1:3096"
PUBLIC_SUB = "https://sub.bigpandas.top"
TLS_SNI = "yuntu.bigpandas.top"
AAITR_IPV4 = "99.88.84.197"
CLASH_TEMPLATE = Path(__file__).resolve().with_name("clash-template.yaml")
DISPLAY_NAMES = {
    "yuntu-aaitr-reality",
    "aaitr-exit-reality",
    "yuntu-aaitr-hy2",
    "aaitr-exit-hy2",
    "yuntu-aaitr-anytls",
    "aaitr-exit-anytls",
    "yuntu-exit-reality",
    "yuntu-exit-hy2",
    "yuntu-exit-anytls",
    "yuntu-aaitr-ss",
    "aaitr-exit-ss",
    "yuntu-exit-ss",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


class SUI:
    def __init__(self) -> None:
        self.jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )

    def request(self, method: str, url: str, data: dict | None = None) -> dict:
        body = None
        headers = {"Host": "sub.bigpandas.top"}
        if data is not None:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=15) as response:
                payload = json.loads(response.read().decode())
        except Exception as exc:  # noqa: BLE001
            fail(f"s-ui API request failed: {method} {url}: {type(exc).__name__}")
        if not payload.get("success", False):
            fail(f"s-ui API rejected {method} {url}: {payload.get('msg', 'unknown error')}")
        return payload

    def login(self) -> None:
        if not ADMIN_PASSWORD.exists():
            fail("admin password file is missing")
        self.request(
            "POST",
            f"{SUI_BASE}/api/login",
            {"user": "suiadmin", "pass": ADMIN_PASSWORD.read_text().strip()},
        )

    def get(self, object_name: str, query: dict | None = None):
        url = f"{SUI_BASE}/api/{object_name}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        obj = self.request("GET", url).get("obj")
        if isinstance(obj, dict) and object_name in obj:
            return obj[object_name]
        return obj

    def save(
        self,
        object_name: str,
        data: dict,
        init_users: str = "",
        action: str = "new",
    ):
        return self.save_raw(
            object_name,
            json.dumps(data, separators=(",", ":")),
            init_users=init_users,
            action=action,
        )

    def save_raw(
        self,
        object_name: str,
        data: str,
        init_users: str = "",
        action: str = "new",
    ):
        form = {"object": object_name, "action": action, "data": data}
        if init_users:
            form["initUsers"] = init_users
        return self.request("POST", f"{SUI_BASE}/api/save", form).get("obj")

    @staticmethod
    def _object(payload: dict):
        obj = payload.get("obj")
        if isinstance(obj, str):
            try:
                return json.loads(obj)
            except json.JSONDecodeError:
                return obj
        return obj

    def link_convert(self, link: str) -> dict:
        obj = self._object(
            self.request("POST", f"{SUI_BASE}/api/linkConvert", {"link": link})
        )
        if isinstance(obj, list) and len(obj) == 1:
            obj = obj[0]
        if isinstance(obj, dict) and isinstance(obj.get("outbound"), dict):
            obj = obj["outbound"]
        if not isinstance(obj, dict) or not obj.get("type"):
            fail("s-ui link conversion returned no outbound")
        return obj

    def check_outbound(self, tag: str) -> dict:
        query = urllib.parse.urlencode(
            {"tag": tag, "link": "https://api.ipify.org"}
        )
        payload = self.request("GET", f"{SUI_BASE}/api/checkOutbound?{query}")
        obj = self._object(payload)
        if not isinstance(obj, dict):
            fail("s-ui outbound check returned no result")
        ok = obj.get("OK")
        if ok is None:
            ok = obj.get("ok")
        if ok is not True:
            fail("s-ui outbound check reported a failed connection")
        return obj

    def delete_outbound(self, tag: str) -> None:
        self.save_raw("outbounds", json.dumps(tag), action="del")


def fetch_subscription(client_name: str, format_name: str = "") -> str:
    encoded_name = urllib.parse.quote(client_name, safe="")
    if format_name in {"clash", "json"}:
        path = f"{PUBLIC_SUB}/{format_name}/{encoded_name}"
    else:
        path = f"{SUI_SUB}/sub/{encoded_name}"
        if format_name:
            path += "?" + urllib.parse.urlencode({"format": format_name})
    request = urllib.request.Request(path, headers={"Host": "sub.bigpandas.top"})
    with urllib.request.urlopen(request, timeout=15) as response:
        if response.status != 200:
            fail(f"subscription returned HTTP {response.status}")
        return response.read().decode()


def subscription_links(client_name: str) -> dict[str, str]:
    links = {}
    for line in subscription_link_lines(client_name):
        scheme = line.split("://", 1)[0].lower()
        links.setdefault(scheme, line)
    return links


def subscription_link_lines(client_name: str) -> list[str]:
    raw = fetch_subscription(client_name)
    decoded = raw
    if "://" not in decoded:
        try:
            decoded = base64.b64decode(raw + "=" * (-len(raw) % 4)).decode()
        except Exception as exc:  # noqa: BLE001
            fail(f"unable to decode raw subscription: {type(exc).__name__}")
    links = []
    for line in decoded.splitlines():
        line = line.strip()
        if "://" not in line:
            continue
        links.append(line)
    return links


def link_route_marker(link: str) -> str:
    parsed = urllib.parse.urlsplit(link)
    hostname = parsed.hostname
    port = parsed.port
    if hostname == "proxy.bigpandas.top":
        return "aaitr-exit"
    if hostname == "yuntu.bigpandas.top" and port in {1443, 2443, 9443, 10444}:
        return "yuntu-exit"
    if hostname == "yuntu.bigpandas.top":
        return "yuntu-aaitr"
    fail(f"unexpected desktop link hostname: {hostname}")


def link_display_name(link: str) -> str:
    return urllib.parse.unquote(urllib.parse.urlsplit(link).fragment)


def clash_template_rules() -> list[str]:
    rules = []
    in_rules = False
    for line in CLASH_TEMPLATE.read_text().splitlines():
        if line == "rules:":
            in_rules = True
            continue
        if in_rules and line.startswith("  - "):
            rules.append(line.removeprefix("  - "))
    if not rules:
        fail("the production Clash template contains no rules")
    return rules


def clash_proxy_groups(clash: str) -> dict[str, dict[str, object]]:
    """Parse the small proxy-group subset without depending on YAML packages."""
    lines = clash.splitlines()
    try:
        start = lines.index("proxy-groups:") + 1
    except ValueError:
        fail("Clash subscription contains no proxy-groups section")
    end = next(
        (
            index
            for index in range(start, len(lines))
            if lines[index]
            and not lines[index][0].isspace()
            and lines[index].endswith(":")
        ),
        len(lines),
    )
    section = lines[start:end]
    item_indents = [
        len(line) - len(line.lstrip())
        for line in section
        if line.lstrip().startswith("- ")
    ]
    if not item_indents:
        fail("Clash subscription contains no proxy groups")
    item_indent = min(item_indents)
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section:
        indent = len(line) - len(line.lstrip())
        item_value = line.lstrip()[1:].strip()
        starts_group = (
            indent == item_indent
            and line.lstrip().startswith("- ")
            and ":" in item_value
        )
        if starts_group:
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        blocks.append(current)

    groups: dict[str, dict[str, object]] = {}
    for block in blocks:
        name = ""
        group_type = ""
        proxies: list[str] = []
        in_proxies = False
        for line in block:
            indent = len(line) - len(line.lstrip())
            value = line.strip()
            dash_value = value[1:].strip() if value.startswith("-") else value
            if (
                in_proxies
                and value.startswith("- ")
                and (indent > item_indent or ":" not in dash_value)
            ):
                proxies.append(dash_value)
                continue
            if indent == item_indent and value.startswith("- "):
                value = dash_value
            in_proxies = value == "proxies:"
            if value.startswith("name: "):
                name = value.removeprefix("name: ")
            elif value.startswith("type: "):
                group_type = value.removeprefix("type: ")
        if name:
            groups[name] = {"type": group_type, "proxies": proxies}
    return groups


def verify_clash_policy(client_name: str, clash: str | None = None) -> None:
    if clash is None:
        clash = fetch_subscription(client_name, "clash")
    lines = clash.splitlines()
    try:
        start = lines.index("rules:") + 1
    except ValueError:
        fail("Clash subscription contains no rules section")
    end = next(
        (
            index
            for index in range(start, len(lines))
            if lines[index]
            and not lines[index][0].isspace()
            and lines[index].endswith(":")
        ),
        len(lines),
    )
    actual = [
        line.strip().removeprefix("- ")
        for line in lines[start:end]
        if line.lstrip().startswith("- ")
    ]
    expected = clash_template_rules()
    if actual != expected:
        fail("Clash subscription routing rules do not match the production policy")
    direct_rules = (
        "DOMAIN-SUFFIX,bigpandas.top,DIRECT",
        "DOMAIN-SUFFIX,shu26.cfd,DIRECT",
        "DOMAIN,ucloud-frp.sometimesnaive.top,DIRECT",
    )
    ai_rule = "GEOSITE,category-ai-!cn,EXIT-MODE"
    cn_rule = "GEOSITE,cn,DIRECT"
    for direct_rule in direct_rules:
        if direct_rule not in actual or actual.index(direct_rule) > actual.index(ai_rule):
            fail(f"the explicit direct rule must take precedence: {direct_rule}")
    if ai_rule not in actual or actual.index(ai_rule) > actual.index(cn_rule):
        fail("the overseas AI rule must take precedence over the CN direct rule")
    if actual[-2:] != ["MATCH,EXIT-MODE", "MATCH,REJECT"]:
        fail("Clash subscription must fail closed after the EXIT-MODE catch-all")
    if "geosite:category-ai-!cn:" not in clash:
        fail("Clash subscription is missing the overseas AI DNS policy")
    direct_dns_policies = {
        "+.bigpandas.top": ("'+.bigpandas.top':", "+.bigpandas.top:"),
        "shu26.cfd": ("shu26.cfd:",),
        "ucloud-frp.sometimesnaive.top": ("ucloud-frp.sometimesnaive.top:",),
    }
    for domain, serialized_forms in direct_dns_policies.items():
        if not any(serialized in clash for serialized in serialized_forms):
            fail(f"Clash subscription is missing the direct DNS policy: {domain}")
    required_sections = ("mode: rule", "dns:", "sniffer:", "tun:", "proxy-groups:")
    missing = [section for section in required_sections if section not in lines]
    if missing:
        fail(f"Clash subscription is missing policy sections: {missing}")
    groups = clash_proxy_groups(clash)
    required_groups = (
        "EXIT-MODE",
        "YUNTU-AAITR",
        "YUNTU-EXIT",
        "AAITR-EXIT",
        "YUNTU-AAITR-AUTO",
        "YUNTU-EXIT-AUTO",
        "AAITR-EXIT-AUTO",
    )
    for group in required_groups:
        if group not in groups:
            fail(f"Clash subscription is missing the {group} proxy group")
    if groups["EXIT-MODE"] != {
        "type": "select",
        "proxies": ["YUNTU-AAITR", "YUNTU-EXIT", "AAITR-EXIT"],
    }:
        fail("Clash subscription has unexpected members in the EXIT-MODE group")
    manual_groups = {
        "YUNTU-AAITR": (
            "YUNTU-AAITR-AUTO",
            "yuntu-aaitr-reality",
            "yuntu-aaitr-hy2",
            "yuntu-aaitr-anytls",
            "yuntu-aaitr-ss",
        ),
        "YUNTU-EXIT": (
            "YUNTU-EXIT-AUTO",
            "yuntu-exit-reality",
            "yuntu-exit-hy2",
            "yuntu-exit-anytls",
            "yuntu-exit-ss",
        ),
        "AAITR-EXIT": (
            "AAITR-EXIT-AUTO",
            "aaitr-exit-reality",
            "aaitr-exit-hy2",
            "aaitr-exit-anytls",
            "aaitr-exit-ss",
        ),
    }
    for group, members in manual_groups.items():
        if groups[group] != {"type": "select", "proxies": list(members)}:
            fail(f"Clash subscription has unexpected members in the {group} group")


def verify_subscriptions(source: dict) -> None:
    raw_expected = {"vless", "hysteria2", "anytls", "ss"}
    json_expected = {"vless", "hysteria2", "anytls", "shadowsocks"}
    clash_expected = {"vless", "hysteria2", "anytls", "ss"}
    for item in source["clients"]:
        link_lines = subscription_link_lines(item["name"])
        schemes = [line.split("://", 1)[0].lower() for line in link_lines]
        missing = raw_expected - set(schemes)
        if missing:
            fail(f"raw subscription is missing protocols: {sorted(missing)}")
        if len(link_lines) != 12:
            fail(f"raw subscription should contain 12 desktop links, found {len(link_lines)}")
        for marker in ("yuntu-aaitr", "aaitr-exit", "yuntu-exit"):
            count = sum(link_route_marker(line) == marker for line in link_lines)
            if count != 4:
                fail(f"raw subscription should contain 4 {marker} links, found {count}")
        display_names = {link_display_name(line) for line in link_lines}
        if display_names != DISPLAY_NAMES:
            fail(f"raw subscription display names are unexpected: {sorted(display_names)}")
        forbidden = {"socks", "http", "https"}
        leaked = forbidden.intersection(schemes)
        if leaked:
            fail(f"desktop subscription leaked forward-proxy protocols: {sorted(leaked)}")

        json_sub = json.loads(fetch_subscription(item["name"], "json"))
        outbounds = [
            outbound
            for outbound in json_sub.get("outbounds", [])
            if isinstance(outbound, dict) and outbound.get("type") in json_expected
        ]
        outbound_types = {outbound.get("type") for outbound in outbounds}
        missing = json_expected - outbound_types
        if missing:
            fail(f"JSON subscription is missing protocols: {sorted(missing)}")
        if len(outbounds) != 12:
            fail(f"JSON subscription should contain 12 desktop outbounds, found {len(outbounds)}")
        for marker in ("yuntu-aaitr", "aaitr-exit", "yuntu-exit"):
            count = sum(marker in str(outbound.get("tag", "")) for outbound in outbounds)
            if count != 4:
                fail(f"JSON subscription should contain 4 {marker} outbounds, found {count}")

        clash = fetch_subscription(item["name"], "clash")
        for protocol in clash_expected:
            if f"type: {protocol}" not in clash:
                fail(f"Clash subscription is missing protocol: {protocol}")
        if clash.count("type: ss\n      udp: true") != 3:
            fail("Clash subscription should expose UDP on all three Shadowsocks nodes")
        for marker in ("yuntu-aaitr", "aaitr-exit", "yuntu-exit"):
            if clash.count(marker) < 4:
                fail(f"Clash subscription is missing {marker} nodes")
        for protocol in ("socks5", "socks", "http"):
            if f"type: {protocol}" in clash:
                fail(f"Clash subscription leaked forward-proxy type: {protocol}")
        verify_clash_policy(item["name"], clash)
    print(f"verified subscriptions: {len(source['clients'])}")
    print("raw/json/clash protocol coverage: complete")


def verify_protocols(source: dict) -> None:
    sui = SUI()
    sui.login()
    aliases = {
        "vless": "vless",
        "hysteria2": "hysteria2",
        "hy2": "hysteria2",
        "anytls": "anytls",
        "ss": "shadowsocks",
    }
    checks = []
    for client in source["clients"]:
        link_lines = subscription_link_lines(client["name"])
        found = set()
        for link in link_lines:
            scheme = link.split("://", 1)[0].lower()
            protocol = aliases.get(scheme)
            if protocol is None:
                continue
            marker = link_route_marker(link)
            checks.append((protocol, marker, link))
            found.add((protocol, marker))
        for marker in ("yuntu-aaitr", "aaitr-exit", "yuntu-exit"):
            missing = {
                protocol
                for protocol in ("vless", "hysteria2", "anytls", "shadowsocks")
                if (protocol, marker) not in found
            }
            if missing:
                fail(f"subscription is missing {marker} links: {sorted(missing)}")

    verified = 0
    for index, (protocol, marker, link) in enumerate(checks):
        tag = f"verify-{protocol}-{index}-{secrets.token_hex(4)}"
        outbound = sui.link_convert(link)
        if outbound.get("type") != protocol:
            fail(f"s-ui converted {protocol} into an unexpected outbound type")
        outbound["tag"] = tag
        try:
            sui.save("outbounds", outbound)
            result = sui.check_outbound(tag)
            delay = result.get("Delay", result.get("delay", "unknown"))
            verified += 1
            print(f"verified {marker} {protocol} outbound for link {index + 1}: {delay} ms")
        finally:
            try:
                sui.delete_outbound(tag)
            except Exception as exc:  # noqa: BLE001
                fail(f"unable to remove temporary outbound: {type(exc).__name__}")
    expected = len(source["clients"]) * 12
    if verified != expected:
        fail(f"verified {verified} protocol outbounds, expected {expected}")
    print("VLESS Reality, Hysteria2, AnyTLS, and Shadowsocks real outbound checks: complete")


def verify_forward_proxies(source: dict) -> None:
    credential = f"{source['proxy']['name']}:{source['proxy']['password']}"
    checks = {
        "socks5": [
            "curl", "-4fsS", "--max-time", "20",
            "--socks5-hostname", "127.0.0.1:31080",
            "--proxy-user", credential, "https://api.ipify.org",
        ],
        "http": [
            "curl", "-4fsS", "--max-time", "20",
            "--proxy", "http://127.0.0.1:31081",
            "--proxy-user", credential, "https://api.ipify.org",
        ],
        "https": [
            "curl", "-4fsS", "--max-time", "20",
            "--proxy", f"https://{TLS_SNI}:443",
            "--proxy-user", credential, "https://api.ipify.org",
        ],
    }
    for name, command in checks.items():
        result = subprocess.run(command, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            fail(f"{name} proxy test failed with curl exit {result.returncode}")
        if result.stdout.strip() != AAITR_IPV4:
            fail(f"{name} proxy egress did not match the AaITR IPv4 address")
    print("verified forward proxies: SOCKS5, HTTP, HTTPS")
    print("forward proxy egress: AaITR IPv4")
