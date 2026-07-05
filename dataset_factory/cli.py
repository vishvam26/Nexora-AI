import argparse
import sys
from pathlib import Path
from dataset_factory.generators.identity_gen import IdentityGenerator
from dataset_factory.generators.personality_gen import PersonalityGenerator
from dataset_factory.generators.coding_gen import CodingGenerator
from dataset_factory.generators.reasoning_gen import ReasoningGenerator
from dataset_factory.generators.business_gen import BusinessGenerator
from dataset_factory.generators.conversation_gen import ConversationGenerator
from dataset_factory.generators.system_prompts_gen import SystemPromptsGenerator
from dataset_factory.validator import DatasetValidator

EXPECTED_FILES = [
    "identity.jsonl",
    "personality.jsonl",
    "coding.jsonl",
    "reasoning.jsonl",
    "business.jsonl",
    "api.jsonl",
    "software_engineering.jsonl",
    "database.jsonl",
    "python.jsonl",
    "javascript.jsonl",
    "react.jsonl",
    "nextjs.jsonl",
    "flutter.jsonl",
    "fastapi.jsonl",
    "nodejs.jsonl",
    "docker.jsonl",
    "git.jsonl",
    "system_design.jsonl",
    "debugging.jsonl",
    "conversation.jsonl",
    "system_prompts.jsonl"
]

def main():
    parser = argparse.ArgumentParser(description="Nexora AI Dataset Factory CLI")
    parser.add_argument("--generate", action="store_true", help="Generate all datasets")
    parser.add_argument("--validate", action="store_true", help="Validate existing datasets")
    parser.add_argument("--output-dir", type=str, default="datasets", help="Output directory for datasets")
    
    # If no flags passed, run both generate and validate
    args = parser.parse_args()
    run_all = not (args.generate or args.validate)
    
    workspace_root = Path(__file__).resolve().parent.parent
    datasets_dir = workspace_root / args.output_dir
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    if args.generate or run_all:
        print("="*60)
        print("         STARTING DATASET GENERATION WORKFLOW")
        print("="*60)
        
        # 1. Identity Generator
        print("\n--> Generating Identity Dataset...")
        id_gen = IdentityGenerator(datasets_dir)
        id_convs = id_gen.generate()
        id_gen.write_jsonl("identity.jsonl", id_convs)
        
        # 2. Personality Generator
        print("\n--> Generating Personality Dataset...")
        p_gen = PersonalityGenerator(datasets_dir)
        p_convs = p_gen.generate()
        p_gen.write_jsonl("personality.jsonl", p_convs)
        
        # 3. Coding Generator (handles master coding and all 14 splits)
        print("\n--> Generating Coding & Technical Split Datasets...")
        c_gen = CodingGenerator(datasets_dir)
        c_convs = c_gen.generate()
        c_gen.write_jsonl("coding.jsonl", c_convs)
        
        # 4. Reasoning Generator
        print("\n--> Generating Reasoning Dataset...")
        r_gen = ReasoningGenerator(datasets_dir)
        r_convs = r_gen.generate()
        r_gen.write_jsonl("reasoning.jsonl", r_convs)
        
        # 5. Business Generator
        print("\n--> Generating Business Dataset...")
        b_gen = BusinessGenerator(datasets_dir)
        b_convs = b_gen.generate()
        b_gen.write_jsonl("business.jsonl", b_convs)
        
        # 6. Conversation Generator
        print("\n--> Generating Conversation Dataset...")
        conv_gen = ConversationGenerator(datasets_dir)
        conv_convs = conv_gen.generate()
        conv_gen.write_jsonl("conversation.jsonl", conv_convs)
        
        # 7. System Prompts Generator
        print("\n--> Generating System Prompts Dataset...")
        sp_gen = SystemPromptsGenerator(datasets_dir)
        sp_convs = sp_gen.generate()
        sp_gen.write_jsonl("system_prompts.jsonl", sp_convs)
        
        print("\nGeneration Complete! All files written to", datasets_dir.resolve())
        print("="*60)

    if args.validate or run_all:
        print("\n" + "="*60)
        print("         STARTING DATASET VALIDATION WORKFLOW")
        print("="*60)
        
        validator = DatasetValidator(datasets_dir)
        results = validator.validate_all(EXPECTED_FILES)
        
        all_valid = results["all_valid"]
        report = results["report"]
        
        print(f"\nValidation Summary:")
        print(f"Directory: {datasets_dir.resolve()}")
        print("-" * 60)
        
        total_conversations = 0
        
        for name in EXPECTED_FILES:
            filepath = datasets_dir / name
            status_str = "VALID" if report[name]["valid"] else "INVALID"
            line_count = 0
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
            
            total_conversations += line_count
            print(f" - {name:<30} | Status: {status_str:<7} | Records: {line_count:,}")
            
            if not report[name]["valid"]:
                print(f"   Errors:")
                for err in report[name]["errors"]:
                    print(f"     * {err}")
                    
        print("-" * 60)
        print(f"Total Unique Conversations across all datasets: {total_conversations:,}")
        print("-" * 60)
        
        if all_valid:
            print("\nSUCCESS: All files successfully validated with 0 errors!")
            sys.exit(0)
        else:
            print("\nWARNING: Some files failed validation. Check error outputs above.")
            sys.exit(1)

if __name__ == "__main__":
    main()
