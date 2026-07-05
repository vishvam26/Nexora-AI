import json
import requests
import sys

# Parse .env manually
env_vars = {}
try:
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
except Exception as e:
    print(f"Error reading .env: {e}")
    sys.exit(1)

token = env_vars.get("HF_TOKEN")
model = env_vars.get("NEXORA_MODEL_ID")

if not token:
    print("HF_TOKEN not found in .env")
    sys.exit(1)
if not model:
    print("NEXORA_MODEL_ID not found in .env")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "inputs": "<|im_start|>user\nWrite a hello world python code<|im_end|>\n<|im_start|>assistant\n",
    "parameters": {
        "max_new_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9,
        "stop": ["<|im_end|>", "<|im_start|>"]
    },
    "stream": True
}

# The new routing URL for Serverless Inference API is 'https://router.huggingface.co/hf-inference/models/<MODEL_ID>'
url = f"https://router.huggingface.co/hf-inference/models/{model}"
print(f"URL: {url}")
print("Sending POST request to Hugging Face Serverless Inference API...")

try:
    # Use verify=False to bypass any local antivirus SSL issues
    response = requests.post(url, headers=headers, json=payload, stream=True, verify=False)
    
    if response.status_code == 503 or (response.status_code == 400 and "loading" in response.text.lower()) or (response.status_code == 503 and "loading" in response.text.lower()):
        print("\n🔄 Model is loading on Hugging Face Serverless. Please wait...")
        try:
            print(response.json())
        except Exception:
            print(response.text)
        sys.exit(0)
        
    response.raise_for_status()
    print("\n🎉 SUCCESS! Streaming response:\n")
    
    for line in response.iter_lines():
        if line:
            decoded = line.decode("utf-8").strip()
            if decoded.startswith("data:"):
                try:
                    data = json.loads(decoded[5:].strip())
                    token_text = data.get("token", {}).get("text", "")
                    if token_text not in ["<|im_end|>", "<|im_start|>"]:
                        sys.stdout.write(token_text)
                        sys.stdout.flush()
                except Exception as parse_err:
                    pass
    print()
except Exception as e:
    print(f"\n❌ FAILED: {e}")
    if 'response' in locals() and hasattr(response, 'text'):
        print(f"Response body: {response.text}")
