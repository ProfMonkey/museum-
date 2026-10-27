"""V34 · deterministic, deliberately fictional civilization-rule engine.

This is an interactive toy model. Scores are rule-driven game counters, NOT
historical facts, forecasts or economic/demographic science. No randomness,
external calls or user-data training. Revise the MODEL_VERSION if rules change.
"""
from __future__ import annotations

MODEL_VERSION = 1
STAT_KEYS = ("knowledge", "supplies", "ecology", "cohesion", "culture")
STAT_NAMES = {"knowledge":"知识","supplies":"物资","ecology":"生态","cohesion":"凝聚","culture":"文化"}
INITIAL = {key: 50 for key in STAT_KEYS}
# Optional foreign-object impact. Fixed toy model; not a scientific causal claim.
ANOMALY_EFFECT = {"knowledge": 5, "culture": 4, "cohesion": -3}

POLICIES = {
    "research": {
        "label": "研究未知", "caption": "优先寻找新知识，消耗物资与生态",
        "delta": {"knowledge": 13, "supplies": -6, "ecology": -4, "cohesion": -1, "culture": 1},
    },
    "harvest": {
        "label": "拓荒生产", "caption": "增加补给，同时加剧资源压力",
        "delta": {"knowledge": 1, "supplies": 14, "ecology": -10, "cohesion": 1, "culture": -1},
    },
    "diplomacy": {
        "label": "文明交流", "caption": "增强凝聚与文化，消耗部分物资",
        "delta": {"knowledge": 3, "supplies": -3, "ecology": -1, "cohesion": 10, "culture": 8},
    },
    "restore": {
        "label": "生态修复", "caption": "恢复生态，让渡一部分生产资源",
        "delta": {"knowledge": 2, "supplies": -5, "ecology": 14, "cohesion": 2, "culture": 1},
    },
    "arts": {
        "label": "艺术与传承", "caption": "增强文化认同和凝聚，消耗物资",
        "delta": {"knowledge": 3, "supplies": -5, "ecology": 0, "cohesion": 6, "culture": 13},
    },
    "fortify": {
        "label": "封闭防御", "caption": "提升短期凝聚与物资，削弱知识与文化",
        "delta": {"knowledge": -5, "supplies": 5, "ecology": -3, "cohesion": 7, "culture": -8},
    },
}

# Transparent game modifiers: at most one +3 or -3 to one stat for a given
# world law and policy. This is deliberately *not* a causal model of history.
LAW_EFFECT = {
    "time_reverse": {"research": ("knowledge", 3), "harvest": ("supplies", -3)},
    "size_swap": {"harvest": ("supplies", 3), "restore": ("ecology", -3)},
    "memory_trade": {"arts": ("culture", 3), "research": ("cohesion", -3)},
    "material_exchange": {"harvest": ("ecology", 3), "research": ("supplies", -3)},
    "world_merge": {"diplomacy": ("cohesion", 3), "fortify": ("culture", -3)},
    "cause_reverse": {"research": ("knowledge", -3), "restore": ("ecology", 3)},
}


def clamp(n: int) -> int:
    return min(100, max(0, n))


def apply_turn(before: dict, policy: str, world_law: str, anomaly: bool = False) -> dict:
    """Pure deterministic transition. Both deltas and resulting state are returned.

    Numeric deltas are measured *after* 0..100 capping, so the explanation
    always matches the actual resulting value.
    """
    if policy not in POLICIES:
        raise ValueError("unknown civilization policy")
    old = {k: clamp(int(before[k])) for k in STAT_KEYS}
    base = dict(POLICIES[policy]["delta"])
    if anomaly:
        for stat,shift in ANOMALY_EFFECT.items():
            base[stat] += shift
    modifier = LAW_EFFECT.get(world_law, {}).get(policy)
    bonus = None
    if modifier:
        target, change = modifier
        base[target] += change
        bonus = {"stat":target, "adjustment":change,
                 "reason":"所选虚构世界法则的显式游戏规则加成"}
    after = {k: clamp(old[k] + base[k]) for k in STAT_KEYS}
    delta = {k: after[k] - old[k] for k in STAT_KEYS}
    weak = sorted((k for k in STAT_KEYS if after[k] < 25), key=lambda k:(after[k],k))
    high = sorted((k for k in STAT_KEYS if after[k] >= 80), key=lambda k:(-after[k],k))
    if weak:
        event = "虚构文明遭遇「"+STAT_NAMES[weak[0]]+"紧张」"
        mood = "crisis"
    elif high:
        event = "虚构文明迎来「"+STAT_NAMES[high[0]]+"繁盛」"
        mood = "golden"
    else:
        event = "虚构文明进入新的抉择年代"
        mood = "steady"
    if anomaly:
        event += " · 异世界物件介入"
    return {"before":old,"after":after,"delta":delta,"modifier":bonus,
            "anomaly":anomaly,"anomaly_effect":dict(ANOMALY_EFFECT) if anomaly else None,
            "event":event,"mood":mood,
            "policy":policy,"policy_label":POLICIES[policy]["label"],
            "model_version":MODEL_VERSION}
