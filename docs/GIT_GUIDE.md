# Git, explained from zero

For four people who have never used Git. Nothing here assumes you know anything.
First-time install and clone steps are in `SETUP.md`.

---

## 1. What Git even is

**Git** is a program on your computer that takes snapshots of your project. Every time
you tell it to, it records exactly what every file looked like at that moment. You can go
back to any snapshot, forever. It never forgets and it never overwrites.

**GitHub** is a website that holds a copy of those snapshots so all four of you can share
them. Git is the tool; GitHub is the meeting point. They're different things, which is why
some steps are typed in a terminal and others are clicked in a browser.

Why bother instead of emailing files: four people editing the same project will overwrite
each other within a week. Git makes that structurally impossible, and gives you a written
record of who changed what and why — which is also most of your project documentation, free.

Two words you'll see constantly: a **commit** is one snapshot with a message saying what
changed. A **repository** (**repo**) is the whole project plus its full history of commits.

---

## 2. Where your work lives

This is the thing that confuses everyone at the start. Your work exists in **four separate
places**, and each command moves it from one to the next. Saving a file in Notepad does not
put it on GitHub — three more steps have to happen.

```
  Your folder          Staging            Your history          GitHub
  the files you  ──▶   changes you've ──▶ snapshots saved,  ──▶ the shared copy
  actually edit        marked to save     still only local      everyone sees
                 git add .          git commit          git push

       ▲                                                            │
       └──────────────────  git pull  ◀────────────────────────────┘
              brings everyone else's work down to you
```

So when Tooba says "I pushed it" and you can't see her changes, the answer is almost always
that you haven't run `git pull`. Your folder is a copy, not a live view.

**Why staging exists:** it looks like a pointless extra step, and at first you can treat it
as one — `git add .` just means "everything I changed". Later it matters: you might have
edited five files but want only three in this commit. Staging is where you choose.

---

## 3. Branches, and why we never work on `main`

A **branch** is a private copy of the project where you can make a mess without affecting
anyone. When the work is finished and someone has checked it, it gets merged back in.

```
              sana/script-normaliser
              ●────────●────────●
             ╱                    ╲   ← pull request, 1 approval required
  ──────────●──────────────────────●──────────●──────▶  main
                                                        always works
```

That gate is not optional — GitHub is configured so nothing reaches `main` without a pull
request and one teammate's approval, **including from Sana**. That's what keeps `main`
always working, so anyone can start new work from it with confidence.

Name branches `yourname/what-it-does`: `tooba/rtl-chat-ui`, `mahnoor/corpus-merge`,
`sabiha/danger-gate`. One branch per piece of work. When it's merged, delete it and make a
new one next time. Branches are cheap and disposable — don't keep one alive for a month and
pile everything into it.

---

## 4. The loop — every single time

Six commands, in this order, every time you change anything. Type them in **Git Bash**,
from inside the project folder.

**Step 1 — go back to `main` and get everyone's latest work**
```bash
git checkout main
git pull
```
Always start here. Branching off a stale `main` means building on something three days old,
and you'll pay for it in conflicts later. Thirty seconds that saves an hour.

**Step 2 — make a branch**
```bash
git checkout -b yourname/what-it-does
```
`-b` means "create it". You're now on the new branch — Git Bash shows the branch name in
brackets at the end of your prompt, so you can always check where you are.

**Step 3 — do the actual work**

Edit files, write code, run things. Nothing here can affect anyone else. Break things freely.

**Step 4 — see what you changed, then mark it**
```bash
git status
git add .
```
Always run `git status` before `git add`, and actually read it. This is where you catch a
`.env` or a 200MB model that shouldn't go up. The `.` means "everything I changed".

**Step 5 — take the snapshot**
```bash
git commit -m "api: add danger-sign gate"
```
Format: `folder: what changed`. Present tense, one line, specific. `updated stuff` is
useless in four months when you're writing the report and trying to find when something changed.

**Step 6 — send it to GitHub**
```bash
git push -u origin yourname/what-it-does
```
Only the first push on a branch needs the long version; after that plain `git push` works.
Git prints a link for opening the pull request — that's your next step.

> Steps 3–5 repeat as often as you like before you push. Small frequent commits beat one
> enormous one — if something breaks you can see exactly which change did it. Commit when
> you finish a thought, not only when you finish the task.

---

## 5. Opening a pull request

A **pull request** (PR) is you asking for your branch to be merged into `main`. It's also
where the conversation happens, and where a lot of your project documentation ends up
without you writing it separately.

1. **Open the link Git printed.** Ends in `/pull/new/your-branch`. If you closed it, the
   repo page shows a yellow banner offering to open a PR from your recent branch.
2. **Check "Files changed" first.** Before anyone else looks, look yourself. Green is added,
   red is removed. You'll catch half your own mistakes here — a stray debug print, a file
   you didn't mean to touch, a line you replaced when you meant to add.
3. **Write the description properly.** What changed, why, and the evidence — a test output,
   a recall number, a screenshot. Two minutes here saves your reviewer ten.
4. **Request a reviewer.** Right-hand side → **Reviewers** → pick one teammate. Then tell
   them in the group chat; GitHub notifications get missed.
5. **Wait — don't merge your own work unreviewed.** The merge button will be greyed out
   saying "Review required". That's branch protection working. Go start something else on a
   new branch; you don't sit idle waiting.

**If you need to change something after opening the PR:** just commit and push to the same
branch again. The PR updates itself. Never close a PR and open a new one to fix a mistake —
that throws away the review conversation.

---

## 6. Reviewing someone else's work

Half of you will be reviewing at any time, and this is the part teams do badly. A PR
approved without being read is worse than no review, because it creates a written record
that someone checked when nobody did.

Open the PR → **Files changed** → read the diff. Click any line to comment on that exact
line. When done, **Review changes** (top right) and pick:

| Choice | Use it when |
|---|---|
| **Comment** | You have questions or notes but aren't making a call yet |
| **Approve** | You read it, understood it, happy for it to go into `main` |
| **Request changes** | Something is wrong and must be fixed first. Say clearly what |

**What to actually look for**
- Does it do what the description says?
- Any secrets, keys, or `.env` content in the diff? This is the one thing that must never slip through.
- Anything touching another person's folder without them being asked?
- Safety code (danger gate, output filters) — are there tests, and do they cover the nasty cases?
- Could you maintain this if the author vanished for two weeks?

You are not expected to understand every line of someone else's specialism. *"I don't
understand what this function does, can you add a comment?"* is a legitimate and useful
review comment. Asking is the job.

---

## 7. Who approves what

| What changed | Who approves | Why |
|---|---|---|
| Anything in your own folder | Any one teammate | Fresh eyes catch mistakes; one approval is the enforced minimum |
| A contract in `docs/contracts/` | **Both** owners of the two sides | A contract change breaks someone else's code silently |
| Corpus or eval sets in `data/` | Mahnoor | She owns data integrity and the numbers everything is measured against |
| Safety code — danger gate, filters | Sabiha **plus** one other | Highest-consequence code in the project. Two people read it, always |
| Architecture, thresholds, retrieval | Sana | She holds the design and knows what a change ripples into |
| Anything urgent at 2am before a deadline | Still one teammate | Deadline pressure is exactly when the rule earns its keep. Wake someone up |

### After approval

1. **The author merges, not the reviewer.** Click **Squash and merge** → **Confirm**.
   Squash turns your eleven messy commits into one clean commit on `main`, keeping the
   history readable.
2. **Delete the branch.** GitHub offers a button right after merging. Click it.
3. **Everyone else pulls:**
   ```bash
   git checkout main
   git pull
   ```
   Do this every morning and after anyone announces a merge. Most conflicts come from
   people working on stale copies.

---

## 8. When it goes wrong

None of these are emergencies. Git almost never loses work — it's specifically built not to.

**"I forgot to make a branch and started editing on main"**
Nothing is lost. Make the branch now; your uncommitted changes come with you:
```bash
git checkout -b yourname/what-it-does
```
Then carry on from step 4 of the loop.

**"My branch is behind main"**
Someone merged while you were working. Bring their changes into your branch:
```bash
git checkout main
git pull
git checkout your-branch
git merge main
```

**"I have a merge conflict"**
Two people changed the same lines and Git won't guess. Open the file:
```
<<<<<<< HEAD
your version of the line
=======
their version of the line
>>>>>>> main
```
Decide what the line should actually say — sometimes yours, sometimes theirs, sometimes a
combination. Delete all three marker lines. Then `git add .` and `git commit`. Nothing is
lost. If you'd rather back out, `git merge --abort` puts you exactly back where you were.

**"I committed but haven't pushed, and want to undo it"**
```bash
git reset --soft HEAD~1
```
Commit gone, your file changes still there. Fix and commit again.

**"I already pushed something wrong"**
Don't delete history. Add a commit that undoes it:
```bash
git log --oneline          # find the commit's short hash
git revert <the-hash>
```

**"I committed an API key"**
Removing the file is **not enough** — it stays in the history and the repo is public.
**Revoke that key right now** in whatever service issued it and generate a new one. Then
remove the file and tell the team so nobody keeps using the dead key. Revoke first; cleanup
can wait five minutes.

**"Git Bash pastes garbage like `^[[200~`"**
Run this once, then close and reopen Git Bash:
```bash
echo 'set enable-bracketed-paste off' >> ~/.inputrc
```
Paste with **right-click** or **Shift+Insert** — Ctrl+V isn't paste in this terminal. Paste
one line at a time.

**"I have no idea what state I'm in"**
```bash
git status
```
It tells you which branch you're on, what's changed, what's staged, and usually suggests the
command you want. Read it properly rather than skimming. Still stuck? Paste the whole output
into the group chat — somebody has hit it before.

> ⚠️ **The one genuinely dangerous command.** Never run `git push --force` on a branch
> someone else might be using. It rewrites shared history and can destroy a teammate's work.
> Everything else in Git is recoverable. This one isn't always.

---

## 9. Cheat sheet

| Command | What it does |
|---|---|
| `git status` | Where am I, what have I changed. Run it constantly |
| `git checkout main` | Switch to the main branch |
| `git pull` | Download everyone else's merged work |
| `git checkout -b name/thing` | Create a new branch and switch to it |
| `git checkout name/thing` | Switch to a branch that already exists |
| `git branch` | List your branches; a star marks where you are |
| `git add .` | Mark all your changes to be saved |
| `git commit -m "msg"` | Take the snapshot, with a message |
| `git commit -am "msg"` | Add and commit in one go (tracked files only) |
| `git push` | Upload your commits to GitHub |
| `git log --oneline` | List recent commits, newest first |
| `git diff` | Show what you've changed but not yet staged |
| `git merge main` | Pull main's changes into your branch |
| `git merge --abort` | Back out of a merge that's going badly |

### The five rules

1. Never commit directly to `main`. Branch, PR, one approval.
2. Start every piece of work from an up-to-date `main`.
3. Stay inside your own folder. Need something changed elsewhere? Ask its owner.
4. Never commit `.env` or any key. If you do, revoke the key immediately.
5. Read `git status` before you `git add`. Every time.

**You will not break anything.** This feels precarious for about a week and then becomes
automatic. `main` is protected, every commit is recoverable, and all four of you are
learning it at the same time. The only real mistake available to you is committing a
secret — and rule 4 covers that.
