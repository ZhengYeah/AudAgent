"""
Input: Natural language description of a target policy (in the `pri_policy` folder)
Output: `PolicyTarget` class instances after applying ontology graphs
"""
import json
import re
from typing import Any, Dict, Iterable, List, Optional, Set

from audagent.auditor.models import PolicyTarget


# --- Ontology helpers ---

def _collect_leaves(node: Dict[str, Any]) -> Set[str]:
    """Collect leaf names under a node (recursively)."""
    children = node.get("children", [])
    if not children:
        name = node.get("name")
        return {name} if name else set()
    leaves: Set[str] = set()
    for c in children:
        leaves.update(_collect_leaves(c))
    return leaves

def _iter_nodes(tree: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Depth-first traversal over all nodes (excluding implicit root)."""
    stack: List[Dict[str, Any]] = list(tree.get("children", []))
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.get("children", []))

def build_ontology_map(ontology_json: dict[str, Any]) -> Dict[str, Set[str]]:
    """
    Map each ontology node name (lowercased) -> set of leaf data type names.
    """
    mapping: Dict[str, Set[str]] = {}
    for node in _iter_nodes(ontology_json):
        name = node.get("name")
        if not name:
            continue
        leaves = _collect_leaves(node)
        mapping[name.lower()] = leaves or {name}
    # Ensure every leaf name also maps to itself
    for leaves in list(mapping.values()):
        for leaf in leaves:
            key = leaf.lower()
            mapping.setdefault(key, {leaf})
    return mapping


# --- Text normalization and matching ---

_STOPWORDS = {
    "and", "or", "the", "of", "a", "an", "to", "for",
    "data", "information", "personal", "similar", "technologies"
}

def _stem(tok: str) -> str:
    """Light stemming for plural/inflection normalization."""
    if tok.endswith("ies") and len(tok) > 3:
        return tok[:-3] + "y"
    if tok.endswith("es") and len(tok) > 3:
        return tok[:-2]
    if tok.endswith("s") and len(tok) > 3:
        return tok[:-1]
    return tok

def _tokens(s: str, drop_stop: bool = False) -> List[str]:
    s = s.lower()
    s = s.replace("_", " ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    toks = [_stem(t) for t in s.split() if t]
    if drop_stop:
        toks = [t for t in toks if t not in _STOPWORDS]
    return toks

def _token_overlap_match(phrase: str, text: str) -> bool:
    """
    Decide if 'phrase' matches 'text' by token overlap (after normalization).
    Require >= 0.5 coverage of the phrase tokens (excluding stopwords).
    """
    p = set(_tokens(phrase, drop_stop=True))
    if not p:
        return False
    t = set(_tokens(text, drop_stop=True))
    inter = p & t
    return (len(inter) / max(1, len(p))) >= 0.5

# Lightweight synonyms that commonly appear in policies
_SYNONYM_REDIRECTS: Dict[str, Set[str]] = {
    # token in policy text -> ontology node name to consider
    "identity": {"identifiers"},
    "payment": {"financial information"},
    "cookie": {"cookie identifier"},
    "cookies": {"cookie identifier"},
    "connection": {"device information"},
    "device": {"device information"},
    "contact": {"contact information"},
    "usage": {"behavioral and usage data"},
}

# --- Field normalization ---

def _normalize_collection(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.lower()
    if "indirect" in s:
        return "indirect"
    if "direct" in s:
        return "direct"
    return None

def _normalize_processing(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.lower()
    if "irrelevant" in s:
        return "irrelevant"
    if "relevant" in s:
        return "relevant"
    return None

def _normalize_disclosure(d: Optional[str]) -> Optional[str]:
    if d is None:
        return None
    if isinstance(d, list):
        if any("service providers" in str(x).lower() for x in d):
            return "service providers"
        else:
            return ", ".join(str(x) for x in d)
    return str(d)

def _normalize_retention(s: Any) -> Optional[float]:
    if isinstance(s, (int, float)):
        return float(s)
    elif "as long as" in str(s).lower():
        return 10**5  # Assume very long retention
    return 10**5 # If not specified or ambiguous, assume infinite retention

ONTOLOGY_PATH = "./ontology/data_type_graph.json" # Path to ontology file

"""
Main class to format target policy
"""
class PolicyTargetFormatter:
    def __init__(self, simplified_json: List[Dict[str, Any]] , ontology=ONTOLOGY_PATH) -> None:
        self.simplified_json = simplified_json
        with open(ontology, "r") as f:
            ontology_json = json.load(f)
        self.ontology_map = build_ontology_map(ontology_json)

    def format_target_policy(self) -> List[PolicyTarget]:
        """
        Convert entries in 'simplified_privacy_model.json' to a list of PolicyTarget
        using 'data_type_graph.json' to expand coarse data types into fine-grained ones.
        """
        results: List[PolicyTarget] = []

        for entry in self.simplified_json:
            raw_type: str = entry.get("types_of_data_collected", "") or ""
            raw_type_l = raw_type.lower()
            # Collect matched leaf types
            matched: Set[str] = set()
            # 1) Direct phrase/substring match against any ontology node name
            for node_name, leaves in self.ontology_map.items():
                node_phrase = node_name
                if node_phrase in raw_type_l or node_phrase.replace("_", " ") in raw_type_l:
                    matched.update(leaves)
                    continue
                if _token_overlap_match(node_phrase, raw_type_l):
                    matched.update(leaves)

            # 2) Synonym redirects (by tokens in policy text)
            policy_tokens = set(_tokens(raw_type_l, drop_stop=True))
            for tok in list(policy_tokens):
                for redirect in _SYNONYM_REDIRECTS.get(tok, set()):
                    leaves = self.ontology_map.get(redirect)
                    if leaves:
                        matched.update(leaves)
            # Fallback: keep the original coarse-grained type if nothing matched
            if not matched:
                pass

            collection = _normalize_collection(entry.get("methods_of_collection"))
            processing = _normalize_processing(entry.get("data_usage"))
            disclosure = _normalize_disclosure(entry.get("data_disclosure"))
            retention = _normalize_retention(entry.get("retention_period"))
            prohibited_col = entry.get("prohibited_col", False)
            prohibited_dis = entry.get("prohibited_dis", False)

            for dt in sorted(matched):
                results.append(PolicyTarget(
                    data_type=dt,
                    prohibited_col=prohibited_col,
                    collection=collection,
                    processing=processing,
                    disclosure=disclosure,
                    prohibited_dis=prohibited_dis,
                    retention=retention))
        return results


# if __name__ == "__main__":
#     pri_policy_path = "../pri_policy/anthropic/simplified_privacy_model.json"
#
#     with open(pri_policy_path, "r") as f:
#         simplified_json = json.load(f)
#
#     formatter = PolicyTargetFormatter(simplified_json)
#     policy_targets = formatter.format_target_policy()
#
#     # user defined policy targets
#     user_policy_path = "../pri_policy/user_defined/prohibited_policy.json"
#     with open(user_policy_path, "r") as f:
#         user_policy_json = json.load(f)
#     new_formatter = PolicyTargetFormatter(user_policy_json)
#     user_policy_targets = new_formatter.format_target_policy()
#     policy_targets.extend(user_policy_targets)
#
#     for pt in policy_targets:
#         print(pt.model_dump_json())