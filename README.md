# Transmission Line Simulator Chatbot

The assistant now answers calculations and core transmission-line questions offline.
It does not send questions to Wikipedia, DuckDuckGo, or another cloud service.

## Optional offline language model

For broader natural-language questions, install [Ollama](https://ollama.com/) and
download a small local model once:

```bash
ollama pull qwen2.5:3b
ollama serve
```

Then start the simulator normally. The chat uses `qwen2.5:3b` at
`http://127.0.0.1:11434` and remains local. Change the model with
`POWER_ASSISTANT_MODEL`; set `POWER_ASSISTANT_LOCAL_LLM=0` to disable it.

Verified simulator questions still use the analytical calculation engine before
the language model, so the model cannot replace active numerical results.
