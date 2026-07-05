import json
import hashlib
from pathlib import Path
import random
from typing import List, Dict, Any, Set, Tuple

class BaseGenerator:
    """
    Base class for all dataset generators in Nexora AI Dataset Factory.
    Provides utility methods for template rendering, multi-turn synthesis,
    duplicate prevention, and JSONL exporting.
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seen_prompts: Set[str] = set()

    def generate(self) -> List[Dict[str, Any]]:
        """
        Abstract method to be implemented by sub-generators.
        Returns a list of conversations. Each conversation is a dictionary:
        {
            "messages": [
                {"role": "user"/"assistant"/"system", "content": "..."}
            ]
        }
        """
        raise NotImplementedError("Subclasses must implement generate()")

    def _hash_prompt(self, prompt: str) -> str:
        """Helper to generate md5 hash of a prompt for duplicate detection."""
        return hashlib.md5(prompt.strip().lower().encode("utf-8")).hexdigest()

    def write_jsonl(self, filename: str, conversations: List[Dict[str, Any]]) -> Path:
        """
        Writes the generated conversations to a JSONL file in the output directory.
        Ensures strict JSONL formatting (one JSON object per line, no markdown wrappers).
        """
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            for conv in conversations:
                # Ensure each line is exactly one line of JSON
                line = json.dumps(conv, ensure_ascii=False)
                f.write(line + "\n")
        return filepath

    def render_template(self, template: str, slots: Dict[str, Any]) -> str:
        """
        Renders a template by formatting placeholders with slot values.
        Supports slot values that are callable, lists, or strings.
        If a slot value is a list, a random element is chosen.
        """
        rendered = template
        # Find all placeholders of form {placeholder}
        # To avoid regex dependencies, we can do a simple loop or use .format with random selection
        # But we need to handle format arguments dynamically. Let's pre-process the slots.
        render_slots = {}
        for k, v in slots.items():
            if isinstance(v, list):
                if not v:
                    render_slots[k] = ""
                else:
                    render_slots[k] = random.choice(v)
            elif callable(v):
                render_slots[k] = v()
            else:
                render_slots[k] = str(v)
        
        # Safe formatting
        try:
            return rendered.format(**render_slots)
        except KeyError as e:
            # Fallback if slot is missing, leave placeholder intact or replace with empty
            return rendered
        except Exception:
            return rendered

    def generate_multi_turn(
        self,
        scenario_templates: List[Tuple[str, str, str, str]], # (turn1_user, turn1_assistant, turn2_user, turn2_assistant)
        slots: Dict[str, List[Any]],
        target_count: int,
        system_prompt: str = None
    ) -> List[Dict[str, Any]]:
        """
        Generates unique multi-turn conversations by rendering templates using slot variations.
        Ensures no duplicate prompts are generated.
        """
        conversations = []
        attempts = 0
        max_attempts = target_count * 10
        
        while len(conversations) < target_count and attempts < max_attempts:
            attempts += 1
            # Pick a random scenario template
            t1_u, t1_a, t2_u, t2_a = random.choice(scenario_templates)
            
            # Resolve the choices beforehand for this execution
            resolved_slots = {}
            for k, v in slots.items():
                if isinstance(v, list):
                    resolved_slots[k] = random.choice(v) if v else ""
                elif callable(v):
                    resolved_slots[k] = v()
                else:
                    resolved_slots[k] = v
            
            try:
                user1 = t1_u.format(**resolved_slots)
            except Exception:
                # In case formatting fails (e.g. key error)
                continue
                
            prompt_hash = self._hash_prompt(user1)
            if prompt_hash in self.seen_prompts:
                continue
            
            self.seen_prompts.add(prompt_hash)
            
            try:
                assistant1 = t1_a.format(**resolved_slots)
                user2 = t2_u.format(**resolved_slots)
                assistant2 = t2_a.format(**resolved_slots)
            except Exception:
                # In case formatting fails
                continue
            
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": user1})
            messages.append({"role": "assistant", "content": assistant1})
            messages.append({"role": "user", "content": user2})
            messages.append({"role": "assistant", "content": assistant2})
            
            conversations.append({"messages": messages})
            
        return conversations
