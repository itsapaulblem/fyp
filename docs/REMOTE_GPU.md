# Remote GPU and Ollama

The simplest secure setup is to run this repository on the GPU host and use
`OLLAMA_BASE_URL=http://127.0.0.1:11434`. Alternatively, forward the port over
SSH and keep the same local URL. Ollama binds to localhost by default and its
local endpoint requires no authentication, so do not expose port 11434 directly
to the public internet.

Install the NVIDIA driver appropriate for the host, install Ollama using its
official instructions, then pull the exact models:

```bash
ollama pull qwen3.5:27b
ollama pull qwen3.5:35b
ollama list
```

Monitor `nvidia-smi` during a smoke run and inspect Ollama process information to
confirm GPU placement. Model file size is not the full VRAM requirement because
context/KV cache and runtime overhead also consume memory. Start with one model
loaded, a modest context, and one request at a time.

Official references:

- https://docs.ollama.com/api/introduction
- https://docs.ollama.com/api/chat
- https://docs.ollama.com/capabilities/vision
- https://docs.ollama.com/faq
- https://ollama.com/library/qwen3.5/tags

