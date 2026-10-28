# haunted-terminal

A ghost lives in your zsh. It watches the commands you run and whispers about them. Before you run something you cannot take back, it asks if you are sure.

The ghost is [Gemma 4](https://huggingface.co/ggml-org/gemma-4-E2B-it-GGUF), running on your own machine through [llama.cpp](https://github.com/ggml-org/llama.cpp). Your shell history never leaves your laptop.

```
$ git commit -m "final fix"
  👻 Final. I said that in 1987. I am still here.
$ rm -rf node_modules
👻 The machine shivers. You are about to run rm -rf. Proceed? [y/N]
```

Built for the [DEV Hacktoberfest Open-Source AI Challenge, Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26).

## Install

1. Start Gemma (the first run downloads the model):

   ```sh
   brew install llama.cpp
   llama-server -hf ggml-org/gemma-4-E2B-it-GGUF --port 8080
   ```

2. Install the ghost:

   ```sh
   git clone https://github.com/ankitjha1405/haunted-terminal ~/.ghost
   echo 'source ~/.ghost/ghost.zsh' >> ~/.zshrc
   ```

   Or use the [installer](https://haunted-terminal-lovat.vercel.app/install.sh). The ghost will warn you about piping it into `sh`. Read it first.

3. Open a new terminal.

## How it works

- `ghost.zsh` adds two zsh hooks. `precmd` sends the last command and its exit code to `ghost speak`. A wrapped `accept-line` widget runs `ghost check` before Enter, and asks you to confirm if the command is risky.
- `ghost` is one Python file with no dependencies. It calls llama-server's OpenAI-compatible endpoint with a ghost persona, and prints the reply in dim italics.
- The risky-command check is plain regex, not the model. It must be instant and must never hallucinate.
- If llama-server is not running, the ghost stays silent. It never blocks your shell.

## Settings

| Variable | Default | What it does |
|---|---|---|
| `GHOST_CHANCE` | `0.35` | Chance the ghost comments on a command. `1` for every command. |
| `GHOST_URL` | `http://127.0.0.1:8080/v1/chat/completions` | Any OpenAI-compatible endpoint. |
| `GHOST_VOICE` | off | `say` for the offline macOS whisper, `elevenlabs` for an ElevenLabs voice. |
| `ELEVENLABS_API_KEY` | | Needed for `GHOST_VOICE=elevenlabs`. |
| `GHOST_VOICE_ID` | George | ElevenLabs voice ID. |

With `GHOST_VOICE=elevenlabs`, only the ghost's line is sent to ElevenLabs. It may quote your command, so use `say` if that matters.

## Tests

```sh
python3 -m unittest -v test_ghost.py
```

## License

MIT
