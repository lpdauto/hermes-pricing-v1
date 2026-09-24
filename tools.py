"""Deterministic PRICING_V1 calculator."""

import json
import math

METHOD_VERSION = "PRICING_V1"

BASE_PRICES = {
    ("kia", "sorento"): {"years": range(2011, 2021), "engines": {"3.3l"}, "base": 800},
    ("hyundai", "santa fe"): {
        "years": {
            2011: {"3.5l"}, 2012: {"3.5l"}, 2013: {"3.3l"}, 2014: {"3.3l"},
            2015: {"3.3l"}, 2016: {"3.3l"}, 2017: {"3.3l"}, 2018: {"3.3l"},
        },
        "base": 695,
    },
    ("hyundai", "santa fe xl"): {"years": {2019: {"3.3l"}}, "base": 695},
    ("kia", "sedona"): {
        "years": {
            2011: {"3.5l"}, 2012: {"3.5l"}, 2013: {"3.5l"}, 2014: {"3.5l"},
            2015: {"3.3l"}, 2016: {"3.3l"}, 2017: {"3.3l"}, 2018: {"3.3l"},
            2019: {"3.3l"}, 2020: {"3.3l"},
        },
        "base": 355,
    },
    ("hyundai", "azera"): {"years": range(2011, 2021), "engines": {"3.3l"}, "base": 600},
    ("kia", "cadenza"): {"years": range(2011, 2021), "engines": {"3.3l"}, "base": 200},
    ("hyundai", "sonata"): {"years": range(2015, 2023), "engines": {"2.4l"}, "base": 635},
    ("kia", "optima"): {"years": range(2015, 2023), "engines": {"2.4l"}, "base": 800},
    ("hyundai", "genesis"): {"years": range(2015, 2021), "engines": {"3.8l"}, "base": 350},
}

def _norm(value):
    return str(value or "").strip().lower()

def _engine_norm(value):
    return _norm(value).replace(" ", "")

def _mileage_adjustment(mileage, mileage_status):
    status = _norm(mileage_status)
    if status in {"unknown", "tmu", "not actual", "not_actual"} or mileage is None:
        return -0.10
    m = int(mileage)
    if m < 100000:
        return 0.15
    if m < 150000:
        return 0.10
    if m < 180000:
        return 0.00
    if m <= 200000:
        return -0.05
    return -0.10

def _run_adjustment(run_status):
    return 0.15 if _norm(run_status) in {"run & drive", "run and drive", "run_drive"} else 0.0

def _front_adjustment(front_risk):
    value = _norm(front_risk).replace("-", "_").replace(" ", "_")
    if value in {"normal_moderate", "normal", "moderate"}:
        return 0.0, None
    if value in {"borderline", "borderline_substantial", "substantial"}:
        return -0.15, None
    if value == "severe":
        return None, "SEVERE_FRONT_EXCLUDED"
    return None, "INVALID_FRONT_RISK"

def _lookup_base(make, model, year, engine):
    spec = BASE_PRICES.get((_norm(make), _norm(model)))
    if not spec:
        return None, "VEHICLE_NOT_IN_BUY_LIST"
    y = int(year)
    e = _engine_norm(engine)
    years = spec["years"]
    if isinstance(years, range):
        if y not in years or e not in spec["engines"]:
            return None, "VEHICLE_NOT_IN_BUY_LIST"
    else:
        allowed = years.get(y)
        if not allowed or e not in allowed:
            return None, "VEHICLE_NOT_IN_BUY_LIST"
    return spec["base"], None

def handle_pricing(params: dict, **kwargs) -> str:
    del kwargs
    try:
        make = kwargs.get("make")
        model = kwargs.get("model")
        year = kwargs.get("year")
        engine = kwargs.get("engine")
        mileage = kwargs.get("mileage")
        mileage_status = kwargs.get("mileage_status", "ACTUAL")
        run_status = kwargs.get("run_status", "")
        front_risk = kwargs.get("front_risk", "NORMAL_MODERATE")

        base, err = _lookup_base(make, model, year, engine)
        if err:
            return json.dumps({"pricing_status": "NOT_PRICED", "pricing_method": METHOD_VERSION, "reason": err})

        front_adj, front_err = _front_adjustment(front_risk)
        if front_err:
            return json.dumps({
                "vehicle": f"{year} {make} {model}",
                "base_price": base,
                "pricing_status": "EXCLUDED" if front_err == "SEVERE_FRONT_EXCLUDED" else "NOT_PRICED",
                "pricing_method": METHOD_VERSION,
                "reason": front_err,
            })

        mileage_adj = _mileage_adjustment(mileage, mileage_status)
        run_adj = _run_adjustment(run_status)
        total_adj = mileage_adj + run_adj + front_adj
        raw = base * (1 + total_adj)
        final_max = math.floor(raw / 25) * 25

        return json.dumps({
            "vehicle": f"{year} {make} {model}",
            "base_price": base,
            "mileage": mileage,
            "mileage_adjustment": mileage_adj,
            "run_status": run_status,
            "run_drive_adjustment": run_adj,
            "front_classification": front_risk,
            "front_adjustment": front_adj,
            "total_adjustment": total_adj,
            "raw_calculated_maximum": round(raw, 2),
            "final_max_hammer": int(final_max),
            "pricing_status": "PRICED",
            "pricing_method": METHOD_VERSION,
        })
    except Exception as exc:
        return json.dumps({"pricing_status": "ERROR", "pricing_method": METHOD_VERSION, "reason": str(exc)})


def register_tools(ctx) -> None:
    """Register PRICING_V1 during Hermes tool discovery."""
    from .schemas import PRICING_V1

    ctx.register_tool(
        name="pricing_v1",
        toolset="pricing_v1",
        schema=PRICING_V1,
        handler=handle_pricing,
        description="Deterministic auction max-hammer calculator using approved PRICING_V1 rules.",
    )
