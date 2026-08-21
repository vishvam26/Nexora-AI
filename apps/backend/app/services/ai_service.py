from typing import List, Generator
from app.providers.provider_factory import ProviderFactory


from app.config import settings

class AIService:
    """
    Service layer abstracting interactions with various LLM providers using Provider Architecture.
    """

    @staticmethod
    def _generate_smart_mock(messages: List[dict]) -> str:
        prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                prompt = m.get("content", "")
                break
        p = prompt.lower()

        if "peft" in p or "qlora" in p or "lora" in p or "fine-tun" in p or "tuning" in p:
            return """### 🚀 PEFT & QLoRA Fine-Tuning Overview

**PEFT (Parameter-Efficient Fine-Tuning)** enables updating Large Language Models (LLMs) without training all parameters (which would require hundreds of GBs of VRAM). 

**QLoRA (Quantized Low-Rank Adaptation)** pushes efficiency further by combining **4-bit NormalFloat (NF4) quantization** with low-rank adapter matrices ($W = W_0 + \\frac{\\alpha}{r} (A \\times B)$).

---

### 🔑 Key Components of QLoRA:
1. **4-Bit NF4 Quantization**: Quantizes base model weights to 4-bit representation, saving ~75% VRAM.
2. **Double Quantization (DQ)**: Quantizes quantization constants to save an additional 0.37 bits/param.
3. **Paged Optimizers**: Prevents memory spikes by using NVIDIA CUDA Unified Memory for page-to-page transfers between GPU and CPU.

---

### 💻 Python Code Example (Unsloth + HuggingFace PEFT):

```python
from unsloth import FastLanguageModel
import torch

# 1. Load 4-bit Base Model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)

# 2. Add QLoRA Adapter Configuration
model = FastLanguageModel.get_peft_model(
    model,
    r=16, # LoRA Rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# 3. Train Model with SFTTrainer
from trl import SFTTrainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    max_seq_length=2048,
)
trainer.train()
```

---
*Grounded with Nexora AI RAG Engine.*"""
        elif "fastapi" in p or "rest" in p or "api" in p or "code" in p:
            return """### ⚡ Production-Ready FastAPI REST API Example

Here is a clean FastAPI backend boilerplate with Pydantic v2 validation, CORS, and async endpoints:

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List

app = FastAPI(title="Nexora API", version="1.0.0")

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str

@app.post("/api/v1/register", status_code=201)
async def register_user(payload: UserRegister):
    return {"message": f"User {payload.full_name} registered successfully!"}
```"""
        else:
            return f"### 🤖 Nexora AI Studio\n\nI have processed your query regarding: **'{prompt[:150]}'**\n\nThe RAG pipeline retrieved vector embeddings and verified knowledge chunks. Everything is running with optimal latency."

    @staticmethod
    def generate_response(messages: List[dict], provider_override: str = None) -> str:
        """
        Instantiates the configured provider and generates a completion response.
        """
        prov_name = (provider_override or settings.AI_PROVIDER).lower().strip()
        if prov_name == "mock":
            last_prompt = messages[-1].get("content", "") if messages else ""
            if "JSON" in last_prompt:
                return '{"score": 0.85, "faithfulness": 0.90, "answer_relevance": 0.85, "confidence_score": 0.88, "root_cause": "None", "domain_tag": "Finance"}'
            return AIService._generate_smart_mock(messages)

        provider = ProviderFactory.get_provider(provider_override)
        return provider.generate_response(messages)

    @staticmethod
    def generate_stream_response(messages: List[dict], provider_override: str = None) -> Generator[str, None, None]:
        """
        Instantiates the configured provider and yields token completions dynamically.
        Uses `yield from` to properly chain the generator so SSE tokens flow to the HTTP response.
        """
        prov_name = (provider_override or settings.AI_PROVIDER).lower().strip()
        if prov_name == "mock":
            full_text = AIService._generate_smart_mock(messages)
            # Split into natural paragraph chunks for smooth streaming UI
            chunks = full_text.split(" ")
            for i, word in enumerate(chunks):
                yield word + (" " if i < len(chunks) - 1 else "")
            return

        provider = ProviderFactory.get_provider(provider_override)
        yield from provider.generate_stream_response(messages)




