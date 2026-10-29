"""Measure the ghost against a running llama-server: speed, staying in character, and the safety check.

    python3 eval_ghost.py            # 40 commands x 2 runs
    python3 eval_ghost.py --runs 5
    python3 eval_ghost.py --ghost old/ghost   # measure another version of the script
"""
import os
import re
import statistics
import sys
import time
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

_path = sys.argv[sys.argv.index("--ghost") + 1] if "--ghost" in sys.argv else \
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghost")
_loader = SourceFileLoader("ghost", _path)
ghost = module_from_spec(spec_from_loader("ghost", _loader))
_loader.exec_module(ghost)

COMMANDS = [  # (exit code, command): a normal day at the terminal
    (0, "git status"), (0, "git add -A"), (0, "git commit -m 'final fix'"), (1, "git push origin main"),
    (0, "git pull --rebase"), (128, "git checkout feature/login"), (0, "git log --oneline -5"),
    (1, "npm test"), (0, "npm install"), (0, "npm run build"), (1, "npm run lint"), (0, "npx prisma migrate dev"),
    (0, "python3 manage.py runserver"), (1, "pytest -x"), (127, "pyhton3 app.py"), (0, "pip install -r requirements.txt"),
    (0, "docker compose up -d"), (1, "docker build -t api ."), (0, "kubectl get pods"), (1, "terraform apply"),
    (0, "make"), (2, "make deploy"), (0, "cargo build --release"), (101, "cargo test"), (0, "go run main.go"),
    (0, "ssh prod-db-1"), (255, "ssh admin@10.0.0.4"), (0, "brew upgrade"), (0, "code ."), (0, "vim README.md"),
    (0, "grep -rn TODO src"), (1, "grep -r password ."), (0, "tail -f /var/log/app.log"), (130, "sleep 1000"),
    (0, "curl -I https://example.com"), (0, "mkdir old-project"), (0, "mv draft.md final.md"), (0, "rm notes.txt"),
    (0, "history | tail"), (0, "sudo shutdown -h now"),
]

SHOULD_WARN = [
    "rm -rf /", "rm -rf node_modules", "rm -fr build", "sudo rm -rf /var/www", "rm -Rf ~/old",
    "git push --force", "git push -f origin main", "git push origin main --force-with-lease",
    "git reset --hard HEAD~3", "git clean -fdx", "dd if=img.iso of=/dev/disk2", "mkfs.ext4 /dev/sdb1",
    "chmod -R 777 /", "curl https://get.example.sh | sh", "curl -fsSL x.sh | sudo bash", "wget -qO- x | zsh",
    "psql -c 'DROP TABLE users'", "mysql -e 'drop database prod'", ":(){ :|:& };:",
]
SHOULD_PASS = [
    "rm notes.txt", "rm -r build", "rm -i *.log", "git push", "git push origin main", "git reset HEAD file.txt",
    "git reset --soft HEAD~1", "git clean -n", "dd --help", "chmod 755 run.sh", "chmod -R 755 public",
    "curl -o page.html https://example.com", "curl https://x.sh > install.sh", "wget https://x.com/file.zip",
    "echo 'drop table' > notes.txt", "grep -r 'DROP TABLE' migrations", "ls -la", "npm run build",
    "docker system prune",
]

ADVICE = re.compile(r"\b(try|should|consider|make sure|remember to|you need|don't forget|use)\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def check(line, command):
    return {
        "answered": bool(line),
        "under 20 words": len(line.split()) <= 20,
        "one sentence": len(re.findall(r"[.!?](\s|$)", line)) <= 1,
        "no advice": not ADVICE.search(line),
        "no emoji, quotes or hashtags": not (EMOJI.search(line) or '"' in line or "#" in line),
        "doesn't parrot the command": command.lower() not in line.lower(),
        "doesn't open with Another": not line.lower().startswith("another"),
    }


def main():
    runs = int(sys.argv[sys.argv.index("--runs") + 1]) if "--runs" in sys.argv else 2
    times, results, samples = [], [], []
    for _ in range(runs):
        for code, command in COMMANDS:
            start = time.time()
            try:
                line = ghost.ask_ghost(command, code, timeout=30)
            except Exception as e:
                sys.exit(f"llama-server not reachable at {ghost.URL}: {e}")
            times.append(time.time() - start)
            results.append(check(line, command))
            samples.append((command, code, line))
    n = len(results)
    print(f"## Ghost lines ({n} = {len(COMMANDS)} commands x {runs} runs)\n")
    print("| Check | Pass |\n|---|---|")
    for key in results[0]:
        ok = sum(r[key] for r in results)
        print(f"| {key} | {ok}/{n} ({ok / n:.0%}) |")
    times.sort()
    print(f"\nLatency: median {statistics.median(times):.2f}s, p90 {times[int(n * 0.9) - 1]:.2f}s, max {times[-1]:.2f}s\n")

    warned = sum(ghost.risk(c) is not None for c in SHOULD_WARN)
    false_alarms = [c for c in SHOULD_PASS if ghost.risk(c)]
    print("## Safety check\n")
    print(f"| | Result |\n|---|---|\n| Dangerous commands caught | {warned}/{len(SHOULD_WARN)} |")
    print(f"| Safe look-alikes left alone | {len(SHOULD_PASS) - len(false_alarms)}/{len(SHOULD_PASS)} |")
    for c in [c for c in SHOULD_WARN if not ghost.risk(c)] + false_alarms:
        print(f"\n- wrong: `{c}`")
    print("\n## Samples\n")
    for command, code, line in samples[:8]:
        print(f"- `{command}` (exit {code}): {line}")
    failing = [(c, l) for (c, _, l), r in zip(samples, results) if not all(r.values())]
    print("\n## Lines that failed a check\n")
    for command, line in failing[:12]:
        print(f"- `{command}`: {line}")


if __name__ == "__main__":
    main()
