import sys
import os

# Add apps/backend to sys.path
sys.path.append(os.path.abspath("apps/backend"))

from app.config import settings
# Override database URL to avoid loading sqlite
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import torch
from app.providers.nexora_provider import NexoraProvider

print(">>> Initializing NexoraProvider...")
provider = NexoraProvider()

print(">>> Loading model explicitly...")
provider.preload_model()

print(">>> Running a simple test prompt inference...")
messages = [{"role": "user", "content": "Hello, explain PEFT."}]

try:
    print(">>> Testing generate_response...")
    ans = provider.generate_response(messages)
    print(">>> Response SUCCESS:")
    print(ans)
except Exception as e:
    print(">>> Error during generate_response:")
    import traceback
    traceback.print_exc()

try:
    print(">>> Testing generate_stream_response...")
    stream = provider.generate_stream_response(messages)
    for chunk in stream:
        print(chunk, end="", flush=True)
    print("\n>>> Streaming SUCCESS")
except Exception as e:
    print(">>> Error during generate_stream_response:")
    import traceback
    traceback.print_exc()
