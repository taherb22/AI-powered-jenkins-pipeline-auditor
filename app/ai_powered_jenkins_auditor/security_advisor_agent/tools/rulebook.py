import json
from pathlib import Path
from typing import List, Dict, Any
from pathlib import Path
class Rulebook:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Rulebook, cls).__new__(cls)
        return cls._instance

    def __init__(self, knowledge_base_path: str | None = None):
        if hasattr(self, "_initialized"):
            return

        if knowledge_base_path is None:
            
            knowledge_base_path = Path(__file__).parent.parent / "knowledge_base" / "rules.json"

        knowledge_base_path = knowledge_base_path.resolve()

        print(f"--- Rulebook: Loading security knowledge base from '{knowledge_base_path}' ---")
        try:
            with open(knowledge_base_path, "r", encoding="utf-8") as f:
                rules_data = json.load(f)

            self._rulebook_dict = {rule["rule_id"]: rule for rule in rules_data}
            print(f"--- Rulebook: Loaded {len(self._rulebook_dict)} rules. ---")
            self._initialized = True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"!!! FATAL ERROR: Could not load or parse the knowledge base file at '{knowledge_base_path}'. Error: {e} !!!")
            self._rulebook_dict = {}

    def get_rule_by_id(self, rule_id: str) -> Dict[str, Any] | None:
        return self._rulebook_dict.get(rule_id)

    def get_all_rules(self) -> List[Dict[str, Any]]:
        return list(self._rulebook_dict.values())

rulebook_instance = Rulebook()

