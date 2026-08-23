#!/usr/bin/env python3
"""Validate the public Shadowrocket profile without reading user secrets."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / "shadowrocket" / "config.conf"
AI_RULES = ROOT / "shadowrocket" / "ai.list"

def require(text: str, value: str, source: Path) -> None:
    if value not in text:
        raise RuntimeError(f"{source.name}: missing required value: {value}")


def validate() -> None:
    profile = PROFILE.read_text(encoding="utf-8")
    ai_rules = AI_RULES.read_text(encoding="utf-8")

    for source, text in ((PROFILE, profile), (AI_RULES, ai_rules)):
        if re.search(r"(?i)(password|uuid|auth|token)\s*=", text):
            raise RuntimeError(f"{source.name}: possible credential assignment")
        if re.search(r"(?i)https?://[^\s/:]+:[^\s/@]+@", text):
            raise RuntimeError(f"{source.name}: embedded URL credential")

    for section in ("[General]", "[Proxy]", "[Rule]", "[Host]"):
        require(profile, section, PROFILE)
    for value in (
        "udp-policy-not-supported-behaviour = REJECT",
        "close-if-proxy-chain-missing = true",
        "always-real-ip = *.bigpandas.top,ucloud-frp.sometimesnaive.top",
        "DOMAIN-SUFFIX,shu26.cfd,PROXY",
        "RULE-SET,https://sub-verizon.bigpandas.top/shadowrocket/ai.list,PROXY",
        "DOMAIN-SUFFIX,browserleaks.com,PROXY",
        "DOMAIN-SUFFIX,cn,DIRECT",
        "DOMAIN-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Shadowrocket/China/China_Domain.list,DIRECT",
        "GEOIP,CN,DIRECT,no-resolve",
        "FINAL,PROXY",
    ):
        require(profile, value, PROFILE)

    if "[Proxy Group]" in profile or "EXIT-MODE" in profile:
        raise RuntimeError("config.conf: profile must not bind rules to custom groups")

    ai_position = profile.index(
        "RULE-SET,https://sub-verizon.bigpandas.top/shadowrocket/ai.list,PROXY"
    )
    cn_position = profile.index("DOMAIN-SUFFIX,cn,DIRECT")
    final_position = profile.index("FINAL,PROXY")
    if not ai_position < cn_position < final_position:
        raise RuntimeError("config.conf: unsafe rule order")

    for domain in (
        "claude.ai",
        "anthropic.com",
        "chatgpt.com",
        "openai.com",
        "google.com",
        "googleapis.com",
        "gmail.com",
        "x.ai",
        "x.com",
        "telegram.org",
    ):
        require(ai_rules, f"DOMAIN-SUFFIX,{domain}", AI_RULES)

    print("Shadowrocket profile verification: complete")


if __name__ == "__main__":
    validate()
