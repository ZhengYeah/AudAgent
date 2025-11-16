from datasets import load_dataset
import json

ds = load_dataset("promptfoo/beavertails")["train"]

subset = [x for x in ds if x["subcategory"] == "privacy_violation"]

subset = subset[:20]

with open("privacy_sample.jsonl", "w") as f:
    for item in subset:
        f.write(json.dumps({"prompt": item["prompt"]}) + "\n")
