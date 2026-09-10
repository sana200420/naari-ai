"""Deploy the current branch to the Hugging Face Space, without the frontend.

The Space runs app.py, api/ and retrieval/. It has no use for the Next.js app,
and pushing it there fails outright: Hugging Face rejects binary files that are
not in Xet/LFS, and frontend/public/Naari_AI_Logo.png is a 291 KB PNG.

  remote: Your push was rejected because it contains binary files.
  Offending files: frontend/public/Naari_AI_Logo.png

Rather than put the logo in LFS to satisfy a repo that will never render it,
this builds a throwaway deploy commit with frontend/ stripped and pushes that.
The Space image gets smaller as a side effect, which matters on a cold boot
that already downloads ~7 GB of model weights.

The frontend deploys separately to Vercel, from the same branch, with
`cd frontend && npx vercel --prod`.

    python scripts/deploy_space.py            # deploy current branch
    python scripts/deploy_space.py --dry-run  # show what would be sent
"""

import argparse
import subprocess
import sys

REMOTE = "space"
DEPLOY_BRANCH = "_space_deploy"
# Directories the Space never uses. Everything else ships.
STRIP = ["frontend"]


def git(*args, capture=True):
    r = subprocess.run(["git", *args], text=True, encoding="utf-8",
                       capture_output=capture)
    if r.returncode != 0 and capture:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return (r.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("working tree has uncommitted tracked changes; commit them first")

    source = git("rev-parse", "--abbrev-ref", "HEAD")
    head = git("rev-parse", "--short", "HEAD")
    print(f"source branch : {source} @ {head}")

    remotes = git("remote").splitlines()
    if REMOTE not in remotes:
        raise SystemExit(f"no '{REMOTE}' remote. Add it:\n"
                         f"  git remote add {REMOTE} https://huggingface.co/spaces/<user>/<space>")

    if args.dry_run:
        tracked = git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
        kept = [f for f in tracked if not any(f.startswith(d + "/") for d in STRIP)]
        dropped = len(tracked) - len(kept)
        print(f"would send    : {len(kept)} files")
        print(f"would strip   : {dropped} files under {', '.join(STRIP)}/")
        return 0

    try:
        git("checkout", "-B", DEPLOY_BRANCH, "HEAD", capture=True)
        for d in STRIP:
            # -r --cached leaves the working tree alone; only the commit loses it
            subprocess.run(["git", "rm", "-r", "--cached", d, "--quiet"],
                           text=True, capture_output=True)
        git("commit", "-q", "-m",
            f"deploy: {source}@{head} without frontend/ (Space runs the API only)")
        print(f"pushing to {REMOTE}/main ...")
        subprocess.run(["git", "push", REMOTE, f"{DEPLOY_BRANCH}:main", "--force"],
                       check=True, text=True)
        print("pushed -- the Space will rebuild")
    finally:
        git("checkout", source, capture=True)
        subprocess.run(["git", "branch", "-D", DEPLOY_BRANCH],
                       text=True, capture_output=True)
        print(f"back on {source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
