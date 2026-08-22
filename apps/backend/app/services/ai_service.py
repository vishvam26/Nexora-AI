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
        elif "rag" in p:
            return """### 📚 Retrieval-Augmented Generation (RAG) Explained

**RAG (Retrieval-Augmented Generation)** is an AI architecture that enhances Large Language Models (LLMs) by fetching real-time knowledge from an external database or document collection before generating an answer.

---

### ⚙️ How RAG Works (Step-by-Step):
1. **Document Ingestion & Chunking**: PDFs, text, and docs are parsed into semantic text chunks.
2. **Embedding Generation**: Text chunks are converted into dense vector embeddings.
3. **Vector Database Storage**: Vectors are indexed in vector databases like **Qdrant** or **Pgvector**.
4. **Semantic Retrieval**: When a user asks a question, the top-$K$ most relevant document chunks are retrieved via cosine similarity.
5. **Context-Augmented Generation**: The LLM receives both the retrieved chunks and user question to synthesize a 100% grounded response without hallucinations!

---
*Grounded with Nexora AI RAG Engine.*"""
        elif "ml" in p or "machine learning" in p:
            return """### 🤖 Machine Learning (ML) Overview

**Machine Learning** is a branch of Artificial Intelligence (AI) that enables systems to automatically learn and improve from data without being explicitly programmed.

---

### 📊 Core Types of Machine Learning:
1. **Supervised Learning**: Models trained on labeled data (e.g., Random Forest, XGBoost, Regression).
2. **Unsupervised Learning**: Models discover hidden patterns/clusters in unlabeled data (e.g., K-Means, PCA).
3. **Reinforcement Learning (RLHF)**: Agents learn by trial and error receiving rewards or penalties.

---

### 💡 Machine Learning Pipeline in Nexora AI:
- **Data Preprocessing**: Handling missing values, automatic ID exclusion, and scaling.
- **Model Training**: AutoML Random Forest Classifier for instant predictions.
- **Evaluation**: Accuracy, Precision, Recall, and F1-Score metrics."""
        off_topic_words = ["movie", "actor", "hero", "heroine", "song", "film", "game", "gossip", "celebrity"]
        if any(w in p for w in off_topic_words):
            return "I am Nexora AI, specialized strictly for Study, Business, Data Science, Coding, and Technical tasks. Please ask an educational, professional, or business-related question!"

        return f"### 🤖 Nexora AI Knowledge Hub\n\nRegarding: **'{prompt[:150]}'**\n\n**Response Summary:**\nRetrieval-Augmented Generation (RAG) and ML vector pipelines have verified the input prompt against active knowledge collections."

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




