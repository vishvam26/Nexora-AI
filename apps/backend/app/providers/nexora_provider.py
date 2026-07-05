import logging
import time
import threading
from typing import List, Generator
from fastapi import HTTPException, status
from app.config import settings
from app.providers.provider_interface import AIProviderInterface

logger = logging.getLogger("app.providers.nexora_provider")
logger.setLevel(logging.INFO)
import os
try:
    file_handler = logging.FileHandler("C:/Users/vishv/.gemini/antigravity-ide/brain/ba311efa-90f6-4f38-a17e-4d8a2be32c35/backend.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
except Exception:
    pass


class NexoraProvider(AIProviderInterface):
    """
    Provider implementation for loading and running the local fine-tuned Nexora model
    (vishvam26/nexora-qwen3.5-4b-lora-v1) with GPU acceleration and CPU fallback.
    Caches model and tokenizer globally to prevent reloading on every request.
    """

    _model = None
    _tokenizer = None
    _load_lock = threading.Lock()
    _loaded = False

    def __init__(self):
        # Trigger preloading if not already loaded, but do not block instantiation
        if not self._loaded:
            try:
                self.preload_model()
            except Exception as e:
                logger.error(f"Lazy model preloading failed: {e}")

    @classmethod
    def preload_model(cls) -> None:
        """
        Thread-safe method to load the model and tokenizer from Hugging Face / PEFT
        and merge weights for fast inference.
        """
        if cls._loaded:
            return

        with cls._load_lock:
            if cls._loaded:
                return

            logger.info("Initializing Nexora local model preloading...")
            start_time = time.monotonic()

            try:
                import torch
                import transformers
                from transformers import AutoModelForCausalLM, AutoTokenizer
                from peft import PeftModel, PeftConfig
            except ImportError as e:
                logger.error(f"Missing deep learning dependencies for NexoraProvider: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Deep learning packages (torch, transformers, peft, accelerate) are not installed. "
                           "Please run 'pip install torch transformers peft accelerate' to use the local Nexora provider."
                )

            try:
                # Clean up any stale HF lock files to prevent hanging/getting stuck
                try:
                    from huggingface_hub.constants import HF_HUB_CACHE
                    import os
                    if os.path.exists(HF_HUB_CACHE):
                        logger.info(f"Checking for stale lock files in HF cache: {HF_HUB_CACHE}")
                        for root, dirs, files in os.walk(HF_HUB_CACHE):
                            for file in files:
                                if file.endswith(".lock"):
                                    lock_file_path = os.path.join(root, file)
                                    try:
                                        os.remove(lock_file_path)
                                        logger.warning(f"Removed stale lock file: {lock_file_path}")
                                    except Exception:
                                        # Skip if currently locked by another active process
                                        pass
                except Exception as cache_clean_err:
                    logger.warning(f"Failed to clean stale HF cache locks: {cache_clean_err}")

                model_id = settings.NEXORA_MODEL_ID
                logger.info(f"Loading PeftConfig from adapter path: '{model_id}'")
                
                # Resolve base model
                is_peft = False
                try:
                    peft_config = PeftConfig.from_pretrained(model_id, token=settings.HF_TOKEN or None)
                    base_model_id = peft_config.base_model_name_or_path
                    is_peft = True
                    logger.info(f"Resolved base model from adapter config: '{base_model_id}'")
                except Exception as config_err:
                    base_model_id = settings.NEXORA_BASE_MODEL_ID
                    logger.warning(
                        f"Could not load PeftConfig or resolve base model. Falling back to NEXORA_BASE_MODEL_ID='{base_model_id}'. Details: {config_err}"
                    )

                # Export HF_TOKEN to environment to ensure all huggingface_hub operations are authenticated
                if getattr(settings, "HF_TOKEN", None):
                    import os
                    os.environ["HF_TOKEN"] = settings.HF_TOKEN

                # Determine device
                device = settings.NEXORA_DEVICE.lower().strip()
                if device == "auto":
                    device_map = "auto"
                elif device == "cuda":
                    device_map = "cuda" if torch.cuda.is_available() else "cpu"
                    if device_map == "cpu":
                        logger.warning("CUDA device was requested but is unavailable. Falling back to CPU.")
                else:
                    device_map = "cpu"

                # Select optimal dtype based on device capabilities
                if torch.cuda.is_available():
                    torch_dtype = torch.float16  # float16 is best for 4-bit quantized layers on T4 GPU
                    device_map = "auto"          # must be auto for bitsandbytes quantization
                    logger.info(f"CUDA is available. Enabled 4-bit config with dtype={torch_dtype} and device_map={device_map}")
                else:
                    # CPU mode fallback
                    torch_dtype = torch.bfloat16
                    device_map = None
                    logger.info(f"Using CPU mode with dtype={torch_dtype}")


                # Load Tokenizer
                logger.info(f"Downloading/Loading tokenizer for model: '{model_id}'")
                cls._tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    token=settings.HF_TOKEN or None
                )

                # Load Base Model
                logger.info(f"Downloading/Loading base causal LM model: '{base_model_id}'")
                try:
                    # Determine quantization parameters to prevent OOM
                    kwargs = {
                        "torch_dtype": torch_dtype,
                        "device_map": device_map,
                        "low_cpu_mem_usage": True,
                        "trust_remote_code": True,
                        "token": settings.HF_TOKEN or None
                    }
                    if torch.cuda.is_available() and device_map != "cpu":
                        kwargs["load_in_4bit"] = True
                        logger.info("Using 4-bit quantization to prevent memory OOM")
                    
                    base_model = AutoModelForCausalLM.from_pretrained(
                        base_model_id,
                        **kwargs
                    )

                except Exception as first_err:
                    logger.warning(
                        f"Failed initial load of base model: {first_err}. Retrying with float32 and AutoModel..."
                    )
                    # Safe fallback: load with float32 and AutoModel class
                    from transformers import AutoModel
                    base_model = AutoModel.from_pretrained(
                        base_model_id,
                        torch_dtype=torch.float32,
                        device_map=None,
                        low_cpu_mem_usage=True,
                        trust_remote_code=True,
                        token=settings.HF_TOKEN or None
                    )

                if is_peft:
                    # Load PEFT LoRA adapter
                    logger.info(f"Wrapping base model with LoRA adapter from: '{model_id}'")
                    peft_model = PeftModel.from_pretrained(
                        base_model,
                        model_id,
                        token=settings.HF_TOKEN or None
                    )

                    # On CPU, avoid merge_and_unload to prevent RAM spikes and speed up loading
                    if device_map is None or device_map == "cpu":
                        logger.info("Running on CPU. Keeping PEFT model without merging to save RAM...")
                        cls._model = peft_model
                    else:
                        logger.info("Merging LoRA weights into base model and unloading adapter...")
                        cls._model = peft_model.merge_and_unload()
                else:
                    logger.info("Model is loaded directly as base model (no PEFT wrapping required).")
                    cls._model = base_model
                cls._model.eval()

                cls._loaded = True
                load_duration = time.monotonic() - start_time
                logger.info(f"Nexora model successfully loaded and cached in {load_duration:.2f}s")

                # Log memory diagnostics if CUDA is used
                if torch.cuda.is_available() and device_map != "cpu":
                    allocated = torch.cuda.memory_allocated() / (1024**3)
                    reserved = torch.cuda.memory_reserved() / (1024**3)
                    logger.info(f"CUDA Memory Usage after load: Allocated={allocated:.2f}GB | Reserved={reserved:.2f}GB")

            except Exception as e:
                cls._model = None
                cls._tokenizer = None
                cls._loaded = False
                logger.error(f"Failed to preload local Nexora model: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load local Nexora model. Details: {str(e)}"
                )

    def _ensure_loaded(self) -> None:
        """Helper to ensure the model is loaded before handling request."""
        if not self._loaded or self._model is None or self._tokenizer is None:
            self.preload_model()

    def generate_response(self, messages: List[dict]) -> str:
        self._ensure_loaded()
        
        import torch
        logger.info(f"Nexora generation request started (turns={len(messages)})")
        start_time = time.monotonic()

        try:
            # 1. Format using Qwen Chat Template
            formatted_prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # 2. Tokenize inputs and move to model device
            inputs = self._tokenizer(formatted_prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self._model.device)
            attention_mask = inputs.get("attention_mask", None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(self._model.device)

            input_length = input_ids.shape[1]

            # 3. Generate completion
            generation_config = {
                "max_new_tokens": settings.NEXORA_MAX_NEW_TOKENS,
                "temperature": settings.NEXORA_TEMPERATURE,
                "top_p": settings.NEXORA_TOP_P,
                "do_sample": settings.NEXORA_TEMPERATURE > 0.0,
                "pad_token_id": self._tokenizer.pad_token_id or self._tokenizer.eos_token_id
            }

            with torch.no_grad():
                output_ids = self._model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    **generation_config
                )

            # Extract generated tokens
            generated_ids = output_ids[0][input_length:]
            response_text = self._tokenizer.decode(generated_ids, skip_special_tokens=True)

            latency = time.monotonic() - start_time
            tokens_generated = len(generated_ids)
            tokens_per_sec = tokens_generated / latency if latency > 0 else 0.0

            logger.info(
                f"Nexora generation completed: tokens={tokens_generated} | "
                f"latency={latency:.2f}s | throughput={tokens_per_sec:.1f} tok/sec"
            )
            return response_text

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
                logger.error("CUDA Out-of-Memory (OOM) encountered during Nexora model execution.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Local AI model ran out of GPU memory. Please reduce context size or restart server."
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Inference runtime error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Nexora generation execution failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Local model inference failed: {str(e)}"
            )

    def generate_stream_response(self, messages: List[dict]) -> Generator[str, None, None]:
        import torch
        from transformers import TextIteratorStreamer
        from threading import Thread

        # 0. Handle model loading asynchronously to prevent read timeouts on HTTP requests
        if not self._loaded or self._model is None or self._tokenizer is None:
            yield "🔄 Nexora AI: Initializing and loading local model into RAM (approx. 9GB). This can take 1-2 minutes on first run...\n"
            
            # Start preloading in a background thread
            loading_thread = Thread(target=self.preload_model)
            loading_thread.start()
            
            # Wait for it to load, yielding dot heartbeats to keep connection alive
            while loading_thread.is_alive() and not self._loaded:
                time.sleep(2)
                yield "."
                
            if not self._loaded:
                yield "\n❌ Failed to load local model. Please check backend logs."
                return
            
            yield "\n✅ Model loaded successfully! Starting generation...\n\n"

        logger.info(f"Nexora streaming generation started (turns={len(messages)})")
        start_time = time.monotonic()

        try:
            # 1. Format using Qwen Chat Template
            formatted_prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # 2. Tokenize inputs and move to model device
            inputs = self._tokenizer(formatted_prompt, return_tensors="pt")
            input_ids = inputs["input_ids"].to(self._model.device)
            attention_mask = inputs.get("attention_mask", None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(self._model.device)

            # 3. Create streamer
            streamer = TextIteratorStreamer(
                self._tokenizer,
                skip_prompt=True,
                clean_up_tokenization_spaces=True
            )

            generation_config = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "streamer": streamer,
                "max_new_tokens": settings.NEXORA_MAX_NEW_TOKENS,
                "temperature": settings.NEXORA_TEMPERATURE,
                "top_p": settings.NEXORA_TOP_P,
                "do_sample": settings.NEXORA_TEMPERATURE > 0.0,
                "pad_token_id": self._tokenizer.pad_token_id or self._tokenizer.eos_token_id
            }

            # Container to propagate errors from background thread
            error_container = []

            def generate_target():
                try:
                    with torch.no_grad():
                        self._model.generate(**generation_config)
                except Exception as thread_exc:
                    error_container.append(thread_exc)

            # 4. Start background thread
            generation_thread = Thread(target=generate_target)
            generation_thread.start()

            token_count = 0
            ttft = None

            # 5. Yield generated tokens as they arrive
            for text_chunk in streamer:
                # Catch thread error if raised
                if error_container:
                    raise error_container[0]

                if text_chunk:
                    if ttft is None:
                        ttft = time.monotonic() - start_time
                    token_count += 1
                    yield text_chunk

            generation_thread.join()

            # Final check for errors that occurred late in thread
            if error_container:
                raise error_container[0]

            latency = time.monotonic() - start_time
            tokens_per_sec = token_count / latency if latency > 0 else 0.0
            logger.info(
                f"Nexora streaming completed: tokens={token_count} | ttft={ttft:.2f}s | "
                f"total_latency={latency:.2f}s | throughput={tokens_per_sec:.1f} tok/sec"
            )

        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                torch.cuda.empty_cache()
                logger.error("CUDA Out-of-Memory (OOM) encountered during Nexora streaming.")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Local AI model ran out of GPU memory during stream."
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Streaming inference error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Nexora streaming execution failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Local model streaming failed: {str(e)}"
            )
