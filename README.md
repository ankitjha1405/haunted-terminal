# haunted-terminal

When you open a terminal, an ASCII ghost rises out of the dark and a haunting loop starts to play. Then it stays. It watches the commands you run and whispers about them. Before you run something you cannot take back, it asks if you are sure.

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
- After the ghost fades, a neon jack-o'-lantern welcome card shows whether Gemma is awake, the music, your folder, and credits.
- The intro is a signed distance field (a circle head, a body with a wavy hem) drawn in `@$%` and lit with a violet halo, 24 frames a second.
- The music is ["Horror Music" by kiravale](https://pixabay.com/) from Pixabay (Pixabay Content License), saved as `haunt.mp3`. If that file is missing, the code composes its own loop: a D minor drone with a sour E-flat, filtered wind, and a detuned music box with echoes. Every frequency loops in a whole number of cycles, so the 48-second loop has no seam. One player serves all your terminal tabs and stops when the last one closes.
- If llama-server is not running, the ghost stays silent. It never blocks your shell.

## Settings

| Variable | Default | What it does |
|---|---|---|
| `GHOST_INTRO` | on | `0` skips the ghost animation when a terminal opens. |
| `GHOST_MUSIC` | on | `0` turns off the background music. `ghost hush` stops it right now. |
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

Code: MIT. `haunt.mp3`: "Horror Music" by kiravale, from Pixabay, under the Pixabay Content License.
