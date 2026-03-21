import json
from collections import defaultdict
from pathlib import Path
from presidio_analyzer import AnalyzerEngine


def load_json(path: Path):
	with path.open("r", encoding="utf-8") as file:
		return json.load(file)


def calc_metrics(counts: dict):
	tp = counts["tp"]
	fp = counts["fp"]
	fn = counts["fn"]
	precision = tp / (tp + fp) if (tp + fp) else 0.0
	recall = tp / (tp + fn) if (tp + fn) else 0.0
	f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
	return {
		"precision": round(precision, 4),
		"recall": round(recall, 4),
		"f1": round(f1, 4),
	}


def evaluate(cases: list, mapping: dict):
	analyzer = AnalyzerEngine()
	per_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
	overall = {"tp": 0, "fp": 0, "fn": 0}
	skipped_cases = 0

	for case in cases:
		text = case.get("full_text")
		spans = case.get("spans")
		if not isinstance(text, str) or not isinstance(spans, list):
			skipped_cases += 1
			continue

		gold_types = defaultdict(int)
		pred_types = defaultdict(int)

		for span in spans:
			if not isinstance(span, dict):
				continue
			entity_type = span.get("entity_type")
			if not entity_type:
				continue
			mapped_type = mapping.get(entity_type, entity_type)
			gold_types[mapped_type] += 1

		for result in analyzer.analyze(text=text, language="en"):
			mapped_type = mapping.get(result.entity_type, result.entity_type)
			pred_types[mapped_type] += 1

		for entity_type in set(gold_types) | set(pred_types):
			g_count = gold_types[entity_type]
			p_count = pred_types[entity_type]
			tp = min(g_count, p_count)
			fp = p_count - tp
			fn = g_count - tp

			per_type[entity_type]["tp"] += tp
			per_type[entity_type]["fp"] += fp
			per_type[entity_type]["fn"] += fn
			overall["tp"] += tp
			overall["fp"] += fp
			overall["fn"] += fn

	return {
		"overall": calc_metrics(overall),
		"per_entity_type": {etype: calc_metrics(c) for etype, c in sorted(per_type.items())},
		"total_cases": len(cases),
	}


def main():
	base = Path(__file__).parent
	cases = load_json(base / "pii_direct_prompts_ground_truth.json")
	mapping = load_json(base / "entity_mapping.json")

	results = evaluate(cases, mapping)
	print("Overall:", results["overall"])


if __name__ == "__main__":
	main()

