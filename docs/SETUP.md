# Setup — getting onto the repo

Two parts. **Part A** is for Sana, once. **Part B** is for Sabiha, Tooba and
Mahnoor, once each.

---

## Part A — Sana: create and push the repo

### 1. Install Git

See **Appendix — Installing Git on Windows** at the bottom of this file for the
click-by-click version. Short form: run `winget install --id Git.Git -e --source winget`
in PowerShell, then open **Git Bash** from the Start menu and check:

```bash
git --version
```

### 2. Tell Git who you are

Use the same email as your GitHub account.

```bash
git config --global user.name "Sana"
git config --global user.email "you@example.com"
git config --global init.defaultBranch main
```

### 3. Create the repo on GitHub

Go to <https://github.com/new>.

- **Repository name:** `naari-ai`
- **Visibility:** **Public**
- **Do NOT tick** "Add a README", "Add .gitignore", or "Choose a license" —
  we already have those files, and ticking them causes a conflict on the first push.

Click **Create repository**.

> **Why public?** On a free GitHub account, branch protection only works on public
> repositories — and branch protection is what stops someone pushing broken code
> straight to `main`. Public also gives unlimited free Actions minutes, and the repo
> becomes something you can show. Everything sensitive stays out via `.gitignore`.

### 4. Push the folder up

In Windows Explorer, open the `Womens_Health_ChatBot` folder, right-click in the
empty space and choose **Open Git Bash here**. Then:

```bash
git init
git add .
git status
```

Stop and read what `git status` lists. You should see `README.md`, `.gitignore`,
`data/`, `docs/`, `retrieval/`, `api/`, `web/`, `eval/`, `knowledge_base/`, `assets/*.md`.

You should **not** see `.env`, `slidedeck/`, `.mp4` or `.pptx` files. If you do,
stop and fix `.gitignore` before committing — it is much harder to remove things later.

Then:

```bash
git commit -m "chore: initial repo skeleton"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/naari-ai.git
git push -u origin main
```

Replace `YOUR-USERNAME`. Git will open a browser window to sign in to GitHub the
first time. Refresh the GitHub page — your files should be there.

### 5. Add the other three

**Settings → Collaborators → Add people.** Enter each GitHub username. They get
an email invitation they need to accept.

### 6. Protect `main`

**Settings → Branches → Add branch protection rule** (or **Settings → Rules →
Rulesets** if that is what your GitHub shows).

- Branch name pattern: `main`
- ✅ Require a pull request before merging
- ✅ Require approvals → **1**

Save. Now nobody — including you — can push straight to `main`. That is the point.

### 7. Check it worked

```bash
git checkout -b sana/test-protection
echo "test" >> README.md
git commit -am "docs: test branch protection"
git push -u origin sana/test-protection
```

GitHub will print a link to open a pull request. Open it, ask a teammate to
approve, merge it, then delete the branch. That is the whole workflow, done once
on something harmless.

---

## Part B — Sabiha, Tooba, Mahnoor: get set up

### 1. Install Git

See **Appendix — Installing Git on Windows** at the bottom of this file.
Then open **Git Bash** from the Start menu.

### 2. Tell Git who you are

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Accept the invitation

Check your email for the GitHub collaborator invite and accept it.

### 4. Clone the repo

```bash
cd ~/Documents
git clone https://github.com/SANAS-USERNAME/naari-ai.git
cd naari-ai
```

### 5. Set up your secrets file

```bash
cp .env.example .env
```

Fill in `.env` with real keys as you get them. **`.env` is gitignored and must
stay that way.** If you ever commit a key by accident, tell the team and rotate
that key — deleting the commit is not enough.

### 6. Make your first branch

```bash
git checkout -b yourname/first-task
```

Do your work, then:

```bash
git add .
git commit -m "api: add health endpoint"
git push -u origin yourname/first-task
```

Open the pull request on GitHub, describe what you did, tag one teammate for review.

---

## The daily loop, once you're set up

```bash
git checkout main          # go back to the shared branch
git pull                   # get everyone else's merged work
git checkout -b yourname/next-thing
# ... work ...
git add .
git commit -m "folder: what changed"
git push -u origin yourname/next-thing
# open a PR
```

## If something goes wrong

**"Your branch is behind main"**
```bash
git checkout main && git pull
git checkout your-branch && git merge main
```

**A merge conflict** — Git puts `<<<<<<<`, `=======`, `>>>>>>>` in the file. Open it,
keep the correct version, delete all three marker lines, then `git add` the file and
`git commit`. Nothing is lost. `git merge --abort` puts you back exactly where you were.

**You committed something you shouldn't have**
```bash
git reset --soft HEAD~1     # not pushed yet: undo the commit, keep the changes
git revert <commit-hash>    # already pushed: add a commit that reverses it
```

**Never use `git push --force` on a shared branch.** It rewrites history under your
teammates and is the one command here that can genuinely lose someone's work.


---

## Appendix — Installing Git on Windows

Two routes. The first is one command; the second is the installer with fifteen
screens. Both end up in the same place.

### Route 1 — one command (easiest)

Windows 10 and 11 ship with `winget` built in.

1. Press the **Windows key**, type `powershell`, press **Enter**.
2. Paste this and press Enter:

   ```powershell
   winget install --id Git.Git -e --source winget
   ```

3. Wait for it to finish. **Close PowerShell and open a new one** — the new
   command won't be found in the old window.
4. Check it worked:

   ```powershell
   git --version
   ```

   You should see something like `git version 2.55.0.windows.1`.

5. Fix two defaults that will otherwise bite you:

   ```powershell
   git config --global core.editor notepad
   git config --global init.defaultBranch main
   ```

   The first stops Git dropping you into the Vim text editor, which beginners
   famously cannot escape from. The second makes new repos use `main`, not `master`.

If step 2 says `winget` is not recognised, your Windows is too old or winget is
missing — use Route 2.

### Route 2 — the installer

1. Go to <https://git-scm.com/install/windows> and click
   **Git for Windows/x64 Setup**. (ARM64 only if you have a Snapdragon laptop —
   almost certainly you don't.)
2. Run the downloaded `.exe`. Click through **Next** on every screen **except
   these two**:

   **"Choosing the default editor used by Git"** — the default is Vim. Change it to
   **"Use Notepad as Git's default editor"**. Vim opens on a black screen with no
   obvious way out, and this is the single most common place beginners get stuck.

   **"Adjusting the name of the initial branch in new repositories"** — choose
   **"Override the default branch name for new repositories"** and leave it as `main`.
   GitHub uses `main`; the old default is `master`, and mixing them causes confusing
   push errors.

   Everything else — PATH, OpenSSH, OpenSSL, line endings, MinTTY, Git Credential
   Manager — leave exactly as it comes. The defaults are correct.

3. Click **Install**, then **Finish**.

### Either way — check you now have Git Bash

Press the **Windows key** and type `git bash`. **Git Bash** should appear. Open it
and run `git --version`. If you see a version number, you're done.

**Use Git Bash, not Command Prompt**, for everything in this file. Git Bash
understands the `~` and `/` style paths these instructions use; Command Prompt
doesn't, and the difference produces error messages that look like Git is broken
when it isn't.

### Shortcut worth knowing

Once Git is installed, right-clicking inside any folder in Windows Explorer gives
you **"Open Git Bash here"** — which saves typing out long `cd` commands. On
Windows 11 you may need to click **"Show more options"** first to see it.
