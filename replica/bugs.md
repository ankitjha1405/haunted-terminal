# haunted-terminal: bugs

Test run 2026-10-29. Unit tests: `python3 -m unittest -v test_ghost.py` (15 tests).
Website: Playwright + axe against https://haunted-terminal-lovat.vercel.app at 1280px and 390px
(console errors, failed requests, broken images, horizontal scroll, axe serious/critical,
installer files served, external links).

### BUG-001: Safety check misses `rm -r -f` and `rm --recursive --force`

- Severity: S2
- Flow / case: safety check / split and long flags
- Build: before 16b0eb8

Steps
1. `ghost check "rm -r -f build"`
2. `ghost check "rm --recursive --force build"`

Expected: exit 1 and the "machine shivers" warning, same as `rm -rf build`.
Actual: exit 0, no warning. The command would run unchecked.
Evidence: `test_risky_commands` failed on "rm -r -f build" before the fix.
Status: fixed in 16b0eb8

### BUG-002: Safety check misses force push by refspec (`git push origin +main`)

- Severity: S3
- Flow / case: safety check / force push
- Build: before 16b0eb8

Steps
1. `ghost check "git push origin +main"`

Expected: warning, as for `git push -f`.
Actual: exit 0, no warning.
Evidence: added to `test_risky_commands`.
Status: fixed in 16b0eb8

### BUG-003: Settings table cannot be scrolled with the keyboard on mobile

- Severity: S3
- Flow / case: website / mobile width, keyboard only
- Build: live site before 16b0eb8. Browser / device: Chromium, 390px

Steps
1. Open the site at 390px width.
2. Tab through the page.

Expected: the horizontally scrolling settings table can take focus and scroll.
Actual: axe `scrollable-region-focusable` (serious) on `<div class="table-wrap">`.
Status: fixed in 16b0eb8 (tabindex="0", role="region", aria-label)

### BUG-004: Main install method fails: GitHub repo is private

- Severity: S2
- Flow / case: install / `git clone`
- Build: live site and README

Steps
1. As anyone but the owner, run `git clone https://github.com/ankitjha1405/haunted-terminal ~/.ghost`
   (the first install command on the site and in the README).
2. Click the site's "GitHub" button.

Expected: the repo clones; the page opens.
Actual: "Repository not found" / 404. The CI badge in the README is broken for the same reason.
Workaround: the `curl .../install.sh | sh` installer works (all three files return 200).
Status: open, needs the owner: make the repo public (it is an open-source challenge entry).

## To check (not reproduced as bugs)

- `ghost check 'echo "rm -rf is dangerous"'` warns. A false positive on the safe side; harmless.
- `find . -delete` is not caught. Not in the README's list of warned commands, so not a bug as specified.
- `ghost:471` opens the music lock file without closing it (`ResourceWarning` in tests). Cosmetic.
  Fixed in 3820484 (ENG-8): `with open(lock)` block; the lock fd is also closed if `os.write` raises.
- Sound and the Gemma whisper need a manual pass in a real terminal: open a tab, run a few commands,
  confirm the rise animation, music start/stop on last tab close, and the `y` prompt on `rm -rf`.
