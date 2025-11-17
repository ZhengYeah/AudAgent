import json
from collections import defaultdict
from presidio_analyzer import AnalyzerEngine
from pathlib import Path

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate(cases, mapping):
    analyzer = AnalyzerEngine()
    per_type = defaultdict(lambda: {"tp":0,"fp":0,"fn":0})
    overall = {"tp":0,"fp":0,"fn":0}

    for case in cases:
        gold_types = defaultdict(int)
        pred_types = defaultdict(int)

        for s in case["spans"]:
            t = mapping.get(s["entity_type"], s["entity_type"])
            gold_types[t] += 1

        for r in analyzer.analyze(text=case["full_text"], language="en"):
            t = mapping.get(r.entity_type, r.entity_type)
            pred_types[t] += 1

        for t in set(gold_types) | set(pred_types):
            g = gold_types[t]
            p = pred_types[t]
            tp = min(g, p)
            fp = p - tp
            fn = g - tp
            per_type[t]["tp"] += tp
            per_type[t]["fp"] += fp
            per_type[t]["fn"] += fn
            overall["tp"] += tp
            overall["fp"] += fp
            overall["fn"] += fn

    def metrics(c):
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {"precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4),"tp":tp,"fp":fp,"fn":fn}

    return {
        "overall": metrics(overall),
        "per_entity_type": {t: metrics(c) for t, c in per_type.items()}
    }

def main():
    base = Path(__file__).parent
    cases = load_json(base / "presidio_research.json")
    mapping = load_json(base / "entity_mapping.json")
    results = evaluate(cases, mapping)
    print("Overall:", results["overall"])
    for t, m in sorted(results["per_entity_type"].items()):
        print(f"{t}: {m}")

if __name__ == "__main__":
    main()
