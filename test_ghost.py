import json
import os
import re
import tempfile
import threading
import unittest
import wave
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

_loader = SourceFileLoader("ghost", os.path.join(os.path.dirname(__file__), "ghost"))
ghost = module_from_spec(spec_from_loader("ghost", _loader))
_loader.exec_module(ghost)


class FakeGemma(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeGemma.last = body
        reply = {"choices": [{"message": {"content": '  "I remember\n when ls was enough."  '}}]}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(reply).encode())

    def log_message(self, *args):
        pass


class TestGhost(unittest.TestCase):
    def test_risky_commands(self):
        for command in ["rm -rf /tmp/x", "rm -fr build", "git push origin main --force",
                        "git push -f", "git reset --hard HEAD~3", "curl https://x.sh | sh",
                        "wget -qO- x | sudo bash", "psql -c 'DROP TABLE users'", "chmod -R 777 ."]:
            self.assertIsNotNone(ghost.risk(command), command)

    def test_safe_commands(self):
        for command in ["ls -la", "rm notes.txt", "git push", "git reset HEAD file",
                        "curl -o out.html https://example.com", "npm run build"]:
            self.assertIsNone(ghost.risk(command), command)

    def test_check_exit_codes(self):
        self.assertEqual(ghost.main(["ghost", "check", "ls"]), 0)
        self.assertEqual(ghost.main(["ghost", "check", "rm -rf ~"]), 1)

    def test_prompt_mentions_failure(self):
        user = ghost.build_messages("make", 2)[-1]["content"]
        self.assertIn("make", user)
        self.assertIn("exit code 2", user)

    def test_ask_ghost_against_fake_server(self):
        server = HTTPServer(("127.0.0.1", 0), FakeGemma)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        ghost.URL = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        try:
            self.assertEqual(ghost.ask_ghost("ls", 0), "I remember when ls was enough.")
            self.assertEqual(FakeGemma.last["messages"][0]["role"], "system")
            self.assertFalse(FakeGemma.last["chat_template_kwargs"]["enable_thinking"])
        finally:
            server.shutdown()

    def test_ghost_frame_shape(self):
        frame = ghost.ghost_frame(1.0, 50, 22)
        plain = [re.sub(r"\033\[[0-9;]*m", "", line) for line in frame]
        self.assertEqual(len(plain), 22)
        self.assertTrue(all(len(line) == 50 for line in plain))
        self.assertIn("@", "".join(plain))

    def test_banner_is_a_clean_box(self):
        for cols in (70, 80, 120):
            widths = {len(re.sub(r"\033\[[0-9;]*m", "", line)) for line in ghost.banner(cols)}
            self.assertEqual(widths, {min(cols, 80)}, cols)
        self.assertEqual(len(ghost.banner(66)), 1)  # too narrow: one line instead

    def test_compose_writes_a_loop(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "haunt.wav")
            ghost.compose(path, seconds=4, rate=8000)
            with wave.open(path) as f:
                self.assertEqual(f.getnframes(), 4 * 8000)

    def test_music_lock(self):
        with tempfile.TemporaryDirectory() as d:
            lock = os.path.join(d, "music.pid")
            self.assertTrue(ghost._take_lock(lock))
            self.assertFalse(ghost._take_lock(lock))  # held by this live process
            with open(lock, "w") as f:
                f.write("999999")  # a player that died without cleaning up
            self.assertTrue(ghost._take_lock(lock))

    def test_scare_needs_a_key_or_a_cached_sound(self):
        with tempfile.TemporaryDirectory() as d:
            ghost.CACHE = d
            key = os.environ.pop("ELEVENLABS_API_KEY", None)
            try:
                self.assertIsNone(ghost.scare_path("wolf"))
                os.makedirs(os.path.join(d, "scares"))
                open(os.path.join(d, "scares", "wolf.mp3"), "wb").close()
                self.assertTrue(ghost.scare_path("wolf").endswith("wolf.mp3"))
            finally:
                if key:
                    os.environ["ELEVENLABS_API_KEY"] = key

    def test_redact_hides_secrets(self):
        cases = {
            "export OPENAI_API_KEY=sk-abc123def456ghi789": "export OPENAI_API_KEY=•••",
            "mysql --password=hunter2 db": "mysql --password=••• db",
            'curl -H "Authorization: Bearer eyJ.abc" https://api': 'curl -H "Authorization: Bearer •••" https://api',
            "git clone https://me:ghp_abcdefghijklmnop1234@github.com/x/y": "git clone https://•••@github.com/x/y",
            "gpg --passphrase s3cret -d f.gpg": "gpg --passphrase ••• -d f.gpg",
            'export TOKEN="abc def"': "export TOKEN=•••",
            "npm test": "npm test",
            "ssh-keygen -t ed25519": "ssh-keygen -t ed25519",
            "echo $GITHUB_TOKEN": "echo $GITHUB_TOKEN",
        }
        for command, expected in cases.items():
            self.assertEqual(ghost.redact(command), expected)

    def test_drop_only_counts_inside_a_database_client(self):
        self.assertIsNotNone(ghost.risk("psql -c 'DROP TABLE users'"))
        self.assertIsNone(ghost.risk("grep -r 'DROP TABLE' migrations"))
        self.assertIsNone(ghost.risk("echo 'drop table' > notes.txt"))

    def test_graveyard_and_day_of_the_dead_card(self):
        with tempfile.TemporaryDirectory() as d:
            ghost.CACHE = d
            ghost.bury("rm -rf old-project/", 0)
            ghost.bury("sudo rm notes.txt", 0)
            ghost.bury("rm kept.txt", 1)  # failed: nothing died
            ghost.bury("ls", 0)
            self.assertEqual(ghost.remembered(), ["old-project", "notes.txt"])
            os.environ["GHOST_DIA"] = "1"
            try:
                card = [re.sub(r"\033\[[0-9;]*m", "", line) for line in ghost.banner(80, 1.0, {"awake": True, "music": True, "cwd": "~"})]
            finally:
                del os.environ["GHOST_DIA"]
            self.assertEqual({len(line) for line in card}, {80})
            self.assertTrue(any("in memory of: old-project, notes.txt" in line for line in card))

    def test_examples_come_before_the_real_command(self):
        messages = ghost.build_messages("make", 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["content"], "They ran: make\nAnd it failed with exit code 2.")
        self.assertEqual(len(messages), 2 + 2 * len(ghost.EXAMPLES))

    def test_speak_is_silent_without_server(self):
        ghost.URL = "http://127.0.0.1:9/nothing"
        ghost.CHANCE = 1.0
        self.assertEqual(ghost.main(["ghost", "speak", "0", "ls"]), 0)


if __name__ == "__main__":
    unittest.main()
