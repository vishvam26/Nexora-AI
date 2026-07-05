import random
from typing import List, Dict, Any
from pathlib import Path
from dataset_factory.generators.base_generator import BaseGenerator

class ReasoningGenerator(BaseGenerator):
    """
    Generates the Reasoning dataset (reasoning.jsonl) containing 5,000+ conversations.
    Teaches the model:
      - Logic and critical thinking
      - Mathematics (algebra, probability, modular arithmetic)
      - Algorithmic problem solving & planning (Knapsack, scheduling, TSP)
      - Decision making under trade-offs and constraints
      - Multi-step Chain-of-Thought (CoT) reasoning
    """

    def generate(self) -> List[Dict[str, Any]]:
        conversations = []
        random.seed(45)
        seen_prompts = set()

        # 1. Mathematical equations generator (1,700 items)
        attempts = 0
        while len(conversations) < 1700 and attempts < 20000:
            attempts += 1
            a = random.randint(2, 50)
            b = random.randint(5, 200)
            # a * x + b = c  =>  x = (c - b) / a
            # Let's choose variables so that x is an integer to keep it clean
            x_val = random.randint(1, 50)
            c_val = a * x_val + b
            
            prompt = f"Solve the algebraic equation: {a}x + {b} = {c_val}. Show your steps."
            p_hash = self._hash_prompt(prompt)
            if p_hash in seen_prompts:
                continue
            seen_prompts.add(p_hash)
            
            steps = [
                f"Step 1: Isolate the term containing x by subtracting {b} from both sides: {a}x = {c_val} - {b} => {a}x = {a * x_val}.",
                f"Step 2: Solve for x by dividing both sides by {a}: x = {a * x_val} / {a}.",
                f"Step 3: Simplify: x = {x_val}."
            ]
            ans = f"x = {x_val}"

            conv = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": f"### Step-by-Step Reasoning\n\n" + "\n".join(steps) + f"\n\n**Final Answer:** {ans}"}
                ]
            }
            conversations.append(conv)

        # 2. Probability selector generator (1,700 items)
        attempts = 0
        target_prob_count = len(conversations) + 1700
        while len(conversations) < target_prob_count and attempts < 20000:
            attempts += 1
            red = random.randint(2, 15)
            blue = random.randint(2, 15)
            green = random.randint(2, 15)
            total = red + blue + green
            
            prompt = f"A container has {red} red, {blue} blue, and {green} green marbles. If you select 2 marbles without replacement, what is the probability of selecting first red then blue?"
            p_hash = self._hash_prompt(prompt)
            if p_hash in seen_prompts:
                continue
            seen_prompts.add(p_hash)

            p_red = red / total
            p_blue_after_red = blue / (total - 1)
            p_joint = p_red * p_blue_after_red
            
            steps = [
                f"Step 1: Calculate the total number of marbles: {red} + {blue} + {green} = {total}.",
                f"Step 2: Probability of selecting a red marble first: P(Red) = {red} / {total}.",
                f"Step 3: Calculate remaining marbles after taking 1 red: {total - 1} marbles left ({red - 1} red, {blue} blue, {green} green).",
                f"Step 4: Probability of selecting a blue marble second: P(Blue | Red) = {blue} / {total - 1}.",
                f"Step 5: Multiply the two probabilities: P(Red then Blue) = ({red}/{total}) * ({blue}/{total - 1}) = {red * blue} / {total * (total - 1)}."
            ]
            ans = f"{red * blue} / {total * (total - 1)}"

            conv = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": f"### Probability Analysis\n\n" + "\n".join(steps) + f"\n\n**Final Answer:** {ans}"}
                ]
            }
            conversations.append(conv)

        # 3. Knapsack variations (1,700 items)
        attempts = 0
        target_knap_count = len(conversations) + 1700
        while len(conversations) < target_knap_count and attempts < 20000:
            attempts += 1
            capacity = random.randint(10, 50)
            w1 = random.randint(2, 10)
            v1 = w1 * random.randint(10, 30)
            w2 = random.randint(2, 10)
            v2 = w2 * random.randint(10, 30)
            
            prompt = f"Optimize a knapsack of capacity {capacity}kg with 2 items. Item A (Weight: {w1}kg, Value: ${v1}), Item B (Weight: {w2}kg, Value: ${v2}). Find the max value."
            p_hash = self._hash_prompt(prompt)
            if p_hash in seen_prompts:
                continue
            seen_prompts.add(p_hash)

            # Simple decision tree
            # Can we fit both?
            if w1 + w2 <= capacity:
                selected = "Both Item A and Item B"
                val = v1 + v2
            else:
                if v1 > v2:
                    selected = "Item A"
                    val = v1
                elif v2 > v1:
                    selected = "Item B"
                    val = v2
                else:
                    selected = "Either Item A or Item B"
                    val = v1
            
            steps = [
                f"Step 1: Check if both items can fit simultaneously: {w1}kg + {w2}kg = {w1 + w2}kg.",
                f"Step 2: If the sum weight ({w1 + w2}kg) is less than or equal to capacity ({capacity}kg), we select both.",
                f"Step 3: If not, we select the item with the highest value.",
                f"Step 4: Decision made: {selected}."
            ]
            ans = f"Selected: {selected}, Max Value: ${val}"

            conv = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": f"### Optimization Steps\n\n" + "\n".join(steps) + f"\n\n**Final Answer:** {ans}"}
                ]
            }
            conversations.append(conv)

        print(f"Generated {len(conversations)} reasoning conversations.")
        return conversations
