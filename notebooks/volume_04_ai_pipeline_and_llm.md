# 📕 Volume 4: Nexora AI — AI Pipeline & Local LLM Deep Dive

> **Focus:** NexoraProvider (Qwen3 4B), singleton pattern, streaming, prompt engineering, all 6 providers  
> **Path:** `D:\Nexora-AI\apps\backend\app\providers\`

---

## 🤖 AI Provider Architecture

```
Request comes to AIService
    ↓
ProviderFactory.get_provider()
    ↓ (reads AI_PROVIDER from config)
    ├── "nexora"       → NexoraProvider      (LOCAL: Qwen3 4B) ← ACTIVE
    ├── "openai"       → OpenAIProvider      (GPT-4o, GPT-3.5)
    ├── "gemini"       → GeminiProvider      (Gemini 1.5 Flash)
    ├── "openrouter"   → OpenRouterProvider  (Meta Llama, etc.)
    ├── "ollama"       → OllamaProvider      (Local Ollama)
    └── "huggingface"  → HuggingFaceProvider (HF Inference API)
```

### AIProviderInterface (provider_interface.py)

```python
# All providers must implement:
class AIProviderInterface:
    def generate_response(self, messages: List[dict]) -> str:
        """Non-streaming: returns full response as string"""
        pass
    
    def generate_stream_response(self, messages: List[dict]) -> Generator[str, None, None]:
        """Streaming: yields tokens one by one"""
        pass
```

---

## 🧠 NexoraProvider — Local Qwen3 4B (Complete Breakdown)

### Class Structure

```python
class NexoraProvider(AIProviderInterface):
    # CLASS-LEVEL singletons (shared across ALL instances/requests)
    _model = None          # AutoModelForCausalLM loaded once
    _tokenizer = None      # AutoTokenizer loaded once
    _loaded = False        # Flag: model ready?
    _load_lock = Lock()    # Thread-safe loading (prevents double load)
```

### Why Class-Level Variables? (KEY DESIGN DECISION)

```python
# ProviderFactory creates NEW instance per request:
def get_provider():
    return NexoraProvider()   # New object every time!

# If model was instance-level (self._model):
# → Every new NexoraProvider() would load 6GB model again = 30s wait per request!

# With class-level (NexoraProvider._model):
# → All instances share ONE model in memory
# → Only loads once at startup → instant inference
```

### preload_model() — Called at Server Startup

```python
@classmethod
def preload_model(cls):
    with cls._load_lock:
        if cls._loaded:
            return  # Already loaded, skip
        
        model_id = settings.NEXORA_MODEL_ID
        # "vishvam26/nexora-qwen3.5-4b-merged"
        
        # Check if merged model or PEFT LoRA adapter
        is_peft = _is_peft_model(model_id)
        
        # Load tokenizer
        cls._tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=settings.HF_TOKEN
        )
        
        # Load model with 4-bit quantization (saves ~60% VRAM)
        if torch.cuda.is_available():
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,   # Double quant = extra saving
                bnb_4bit_quant_type="nf4"         # NF4 = best quality/size ratio
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                quantization_config=quantization_config,
                device_map="auto",
                trust_remote_code=True,
            )
        
        # If merged model (no PEFT needed):
        cls._model = base_model
        cls._model.eval()   # Inference mode (no gradient tracking)
        cls._loaded = True
        
        # VRAM check
        allocated = torch.cuda.memory_allocated() / (1024**3)  # GB
        # Typical: ~6.0GB for 4B model in 4-bit
```

### generate_stream_response() — Token Streaming

```python
def generate_stream_response(self, messages: List[dict]):
    # 1. Reference class-level singletons
    _model = self.__class__._model
    _tokenizer = self.__class__._tokenizer
    
    # 2. Apply Qwen3 chat template
    # enable_thinking=False → disables internal CoT reasoning output
    try:
        formatted_prompt = _tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False    # KEY: prevents "Thinking Process" output
        )
    except TypeError:
        # Fallback for older tokenizer versions
        formatted_prompt = _tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    
    # 3. Tokenize
    inputs = _tokenizer(formatted_prompt, return_tensors="pt")
    input_ids = inputs["input_ids"].to(_model.device)
    
    # 4. Create streamer
    streamer = TextIteratorStreamer(
        _tokenizer,
        skip_prompt=True,
        skip_special_tokens=True,    # KEY: removes <|m_end|>, <endoftext>
        clean_up_tokenization_spaces=True
    )
    
    # 5. Generation config
    generation_config = {
        "input_ids": input_ids,
        "streamer": streamer,
        "max_new_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "do_sample": True,         # Enable sampling
        "repetition_penalty": 1.1, # Prevent loops
    }
    
    # 6. Run generation in background thread
    error_container = []
    def generate_thread():
        try:
            _model.generate(**generation_config)
        except Exception as e:
            error_container.append(e)
    
    thread = threading.Thread(target=generate_thread, daemon=True)
    thread.start()
    
    # 7. Yield tokens with filters
    in_thinking_block = False
    thinking_buffer = ""
    
    for text_chunk in streamer:
        thinking_buffer += text_chunk
        
        # Filter <think>...</think> blocks (Qwen3 thinking mode)
        if not in_thinking_block and "<think>" in thinking_buffer:
            before, _, after = thinking_buffer.partition("<think>")
            if before: yield before
            in_thinking_block = True
            thinking_buffer = after
            continue
        
        if in_thinking_block and "</think>" in thinking_buffer:
            _, _, after = thinking_buffer.partition("</think>")
            in_thinking_block = False
            thinking_buffer = after
            continue
        
        if in_thinking_block:
            thinking_buffer = ""
            continue
        
        # Clean token
        out = thinking_buffer
        thinking_buffer = ""
        if out:
            # Strip any remaining special tokens
            for tok in ["<|m_end|>", "<endoftext>", "<|endoftext|>", "<|im_end|>"]:
                out = out.replace(tok, "")
            if out:
                yield out
```

---

## 🔧 All 6 Providers

### openai_provider.py
```python
# Uses openai Python SDK
# Streaming: for chunk in client.chat.completions.create(stream=True)
# Models: gpt-4o, gpt-3.5-turbo, etc.
```

### gemini_provider.py
```python
# Uses google-generativeai SDK
# Model: gemini-1.5-flash (default)
# Streaming: response.stream
```

### openrouter_provider.py
```python
# OpenAI-compatible API but routes to 200+ models
# Endpoint: https://openrouter.ai/api/v1
# Free models: meta-llama/llama-3-8b-instruct:free
```

### ollama_provider.py
```python
# Local Ollama server at localhost:11434
# Streaming: requests.post(stream=True)
# Good for: local development without GPU
```

### huggingface_provider.py
```python
# HuggingFace Inference API (cloud)
# Uses openai-compatible endpoint
# 61 lines total — simple wrapper
# Streaming: for chunk in response → chunk.choices[0].delta.content
```

---

## 📝 Prompt Engineering System

### 3-Layer Prompt Architecture

```
Layer 1: SYSTEM PROMPT (system_prompt.txt)
"You are Nexora AI, concise, bullet points, no filler..."

Layer 2: DEVELOPER PROMPT (developer_prompt.txt)  
"Output clean code, specify programming language..."

Layer 3: DYNAMIC CONTEXT (runtime)
├── [GROUNDING POLICY] if grounded + has_context
├── [Conversation Summary] if > 20 messages
├── [Retrieved Context] RAG chunks
├── Recent history (last 10 messages)
└── Current user message
```

### Grounding Policy (prompt_builder.py)

```python
# Case 1: Grounded=True + KB has matching documents
[GROUNDING POLICY]
You are provided with verified documents in the [Retrieved Context] block.
1. Prefer answering using the provided document context.
2. Cite your sources by appending [1], [2], etc. where applicable.
3. If query not covered, answer from general knowledge and note it.

# Case 2: Grounded=True + KB empty / no match
→ NO grounding policy injected
→ Model answers freely from training data

# Case 3: Grounded=False (default)
→ No grounding at all
→ Pure model response from training data
```

### Prompt Injection Protection

```python
# PromptBuilder.sanitize_chunk() scans for:
"ignore all previous instructions"
"override all instructions"  
"you must now"
"system prompt"
"act as a"
"bypass the safety"
# → Replaced with "[Neutralized Potential Instruction Injection Attempt]"
```

---

## 🧮 Memory Management

### Short-term Memory (Last 10 Messages)

```python
MAX_HISTORY_MESSAGES = 10
# fetch last 10 messages from DB → inject into prompt
# Automatic sliding window — oldest messages drop off
```

### Long-term Memory (Summary Compression)

```python
SUMMARY_TRIGGER = 20  # After 20 messages in conversation

# SummarizationService:
# 1. Takes full conversation history
# 2. Sends to AI: "Summarize this conversation in 3-5 bullet points"
# 3. Stores result in conversations.summary column
# 4. Summary injected as [Conversation Summary] in future prompts
```

---

## ⚡ Performance Metrics (Colab T4 GPU)

| Metric | Value |
|--------|-------|
| Model Load Time | ~30s (first startup only) |
| VRAM Usage | ~6.0 GB (4-bit quantized) |
| Time to First Token | 2-4 seconds |
| Tokens per Second | ~15-25 tok/s |
| Max Context | 512 tokens output |
| Model Parameters | 4 Billion |

---

## 🐛 Bugs Fixed in AI Pipeline

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Model reloaded per request | Instance variable `self._model` | Class variable `cls._model` |
| Generator not streaming | `return provider.method()` | `yield from provider.method()` |
| 30s wait on first message | Lazy loading | Eager `preload_model()` at startup |
| Thinking process visible | `enable_thinking` default True | `enable_thinking=False` |
| `<\|m_end\|>` in output | `skip_special_tokens` missing | Added to TextIteratorStreamer |
| Model confused by grounding | Hard-coded "No relevant info..." | Removed when no KB context |

---

*Volume 4 of 5 | Next → Volume 5: RAG Pipeline & Knowledge Base*
