"""Publish only the built review site without changing the main worktree or history."""

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(*arguments, input=None, environment=None):
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, input=input, text=True, env=environment).strip()


def main():
    source = ROOT / "docs"
    if not (source / "rounds.json").is_file():
        raise RuntimeError("Build the round-review gallery first")
    with tempfile.TemporaryDirectory(prefix="platform-pages-index-") as temporary:
        environment = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "index"))
        git("read-tree", "--empty", environment=environment)
        for path in sorted(source.rglob("*")):
            if path.is_file():
                blob = git("hash-object", "-w", str(path))
                git("update-index", "--add", "--cacheinfo", "100644", blob,
                    path.relative_to(source).as_posix(), environment=environment)
        tree = git("write-tree", environment=environment)
        parent = subprocess.run(["git", "rev-parse", "--verify", "refs/heads/gh-pages"],
                                cwd=ROOT, capture_output=True, text=True)
        arguments = ["commit-tree", tree]
        if parent.returncode == 0:
            old = parent.stdout.strip()
            if git("rev-parse", old + "^{tree}") == tree:
                print("Review gallery already matches gh-pages")
                return
            arguments += ["-p", old]
        message = ("Publish actual Unreal round-review evidence\n\n"
                   "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\n")
        commit = git(*arguments, input=message)
        git("update-ref", "refs/heads/gh-pages", commit,
            parent.stdout.strip() if parent.returncode == 0 else "0" * 40)
        subprocess.run(["git", "push", "origin", "refs/heads/gh-pages"], cwd=ROOT, check=True)
        print("Published static gallery commit", commit)


if __name__ == "__main__":
    main()
