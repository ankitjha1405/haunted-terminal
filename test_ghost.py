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
        user = ghost.build_messages("make", 2)[1]["content"]
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

    def test_speak_is_silent_without_server(self):
        ghost.URL = "http://127.0.0.1:9/nothing"
        ghost.CHANCE = 1.0
        self.assertEqual(ghost.main(["ghost", "speak", "0", "ls"]), 0)


if __name__ == "__main__":
    unittest.main()
