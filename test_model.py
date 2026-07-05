import sys
import os

# Add backend directory to path
sys.path.append(r"D:\Nexora-AI\apps\backend")

# Set dummy env vars if needed
os.environ["DATABASE_URL"] = "sqlite:///./nexora_ai.db"
os.environ["AI_PROVIDER"] = "nexora"

try:
    from app.config import settings
    print("Settings loaded successfully:")
    print("NEXORA_MODEL_ID:", settings.NEXORA_MODEL_ID)
    print("NEXORA_BASE_MODEL_ID:", settings.NEXORA_BASE_MODEL_ID)
    print("NEXORA_DEVICE:", settings.NEXORA_DEVICE)
except Exception as e:
    print("Failed to load settings:", e)
    sys.exit(1)

print("\nAttempting to import torch, transformers, peft...")
try:
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel, PeftConfig
    print("Imports successful.")
except Exception as e:
    print("Failed to import packages:", e)
    sys.exit(1)

print("\nStarting model preloading...")
try:
    model_id = settings.NEXORA_MODEL_ID
    print(f"Loading PeftConfig from adapter path: '{model_id}'")
    peft_config = PeftConfig.from_pretrained(model_id)
    base_model_id = peft_config.base_model_name_or_path
    print(f"Resolved base model: '{base_model_id}'")
    
    device = settings.NEXORA_DEVICE.lower().strip()
    if device == "auto":
        device_map = "auto"
    elif device == "cuda":
        device_map = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device_map = "cpu"
        
    if torch.cuda.is_available() and device_map != "cpu":
        torch_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    else:
        torch_dtype = torch.float32
        device_map = "cpu"
        
    print(f"Device map: {device_map}, Dtype: {torch_dtype}")
    
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    print("Tokenizer loaded.")
    
    print("Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch_dtype,
        device_map=device_map,
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )
    print("Base model loaded.")
    
    print("Loading PeftModel...")
    peft_model = PeftModel.from_pretrained(base_model, model_id)
    print("PeftModel loaded.")
    
    print("Merging weights...")
    model = peft_model.merge_and_unload()
    model.eval()
    print("Model loaded successfully!")
    
except Exception as e:
    print("Error encountered:")
    import traceback
    traceback.print_exc()
