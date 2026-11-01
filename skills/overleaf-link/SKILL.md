---
name: overleaf-link
description: Use when the user wants to read, inspect, summarize, or edit an Overleaf project (LaTeX paper, thesis, report) — listing files, reading main.tex, finding or extracting a \section, rewriting a section, or pushing changes back to Overleaf. Triggers on "Overleaf", overleaf.com/project URLs, olp_ git tokens, or git.overleaf.com.
---

# Overleaf via Git

## Overview
Overleaf exposes every project as a git repo at `https://git.overleaf.com/<PROJECT_ID>`, using username `git` and a personal Git token as the password. Everything works with plain `git` and shell tools. No MCP server is needed. (This is a port of github.com/mjyoo2/OverleafMCP.)

**Core rule:** pull before every read or write. Commit and push only the files you meant to change. Never write the token to disk, into a remote URL, or into output.

## First Use: Connecting to Overleaf
Run these steps in order the first time in a session, before any other Overleaf work. Speak like a helpful colleague setting something up alongside the user. Each message is one or two short sentences covering what you found, what you need (if anything), and the exact next step. Run the checks quietly and report only the result. Never print a token, and never ask the user to paste one into the chat.

### Step 0: Introduce the requirement
Open your first Overleaf message of the session with this note, once, and then continue with Step 1 straight away:
> Quick note before we start: I can connect to Overleaf only through its Git integration, which requires **Overleaf Premium**. Either your own plan or the project owner's plan counts.

If the user says they don't have Premium, say kindly that this skill can't reach their project and stop the setup. Don't run the checks or ask for credentials.

### Step 1: Check environment variables
The project ID and the token are checked separately. This reports only whether each one is present, never its value:
```bash
if [ -n "$OVERLEAF_PROJECT_ID" ]; then echo "id: env"; else echo "id: missing"; fi
if [ -n "$OVERLEAF_GIT_TOKEN" ]; then echo "token: env"
elif [ -s "$OVERLEAF_GIT_TOKEN_FILE" ]; then echo "token: token-file"
elif [ -n "$OVERLEAF_GIT_TOKEN_FILE" ]; then echo "token: token-file-empty-or-missing"
else echo "token: missing"; fi
```
- **Both found:** say *"Found your Overleaf project ID and token in your environment, connecting now."* Then go to Step 4.
- **Only one found:** say so in one line and continue to Step 2 for the other. For example: *"Found your Git token in your environment. I just need to know which project."*
- **`token-file-empty-or-missing`:** say *"`OVERLEAF_GIT_TOKEN_FILE` points to `<path>`, but that file is empty or doesn't exist. Could you check it?"*
- **Neither found:** go to Step 2 without mentioning it.

### Step 2: Check the projects file (for whatever is still missing)
The file can supply the project ID, the token, or both. Anything found in the environment takes priority. The file has the shape `{"projects": {"<key>": {"name": "...", "projectId": "...", "gitToken": "olp_..."}}}`. Read it only through these helpers, which print names and IDs but never tokens. **Don't `cat` or open the file yourself**, because that would put every token into the conversation.
```bash
CFG="${OVERLEAF_PROJECTS_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/overleaf-mcp/projects.json}"
[ -f "$CFG" ] || CFG=./projects.json
ovl_get() {  # ovl_get <project-key> <field>
  if command -v jq >/dev/null; then jq -r --arg p "$1" --arg f "$2" '.projects[$p][$f] // empty' "$CFG"
  else python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["projects"].get(sys.argv[2],{}).get(sys.argv[3]) or "")' "$CFG" "$1" "$2"; fi; }
ovl_list() {  # prints "<key><TAB><name>" per project
  if command -v jq >/dev/null; then jq -r '.projects | to_entries[] | "\(.key)\t\(.value.name // "")"' "$CFG"
  else python3 -c 'import json,sys; [print(k+"\t"+(v.get("name") or "")) for k,v in json.load(open(sys.argv[1]))["projects"].items()]' "$CFG"; fi; }

if [ ! -f "$CFG" ]; then echo "file: none"
elif ! command -v jq >/dev/null && ! command -v python3 >/dev/null; then echo "file: no-parser"
else ovl_list; fi
```
- **One project, or the user already named one:** say *"Using your Overleaf project **Main Paper**."* and go to Step 4 with `P=<key>`.
- **Several projects and it's unclear which one:** ask *"I see a few Overleaf projects: **Main Paper** and **PhD Thesis**. Which one should I open?"*
- **`file: no-parser`:** say *"I found your projects file. To read it without showing your token, I need `jq`. Shall I install it (`brew install jq`)? Or, if you'd rather, set `OVERLEAF_PROJECT_ID` and `OVERLEAF_GIT_TOKEN` instead."*
- **`file: none`:** go to Step 3, unless Step 1 already found both values.

### Step 3: Guided setup (ask only for what's missing)
Send one friendly message that lists only the missing items:
> Let's connect your Overleaf project. It takes about a minute, and I need:
> 1. **Your project link** *(only if the ID is missing)*. Just paste the URL from your browser (`https://www.overleaf.com/project/…`).
> 2. **A Git token** *(only if the token is missing)*. In Overleaf, go to **Account Settings → Git Integration → Generate token**. Keep it handy for now, and I'll give you a private file to paste it into so it never shows up in our chat.

When they send the link, take the ID from the part after `/project/`. Then create the file, using `TOKEN_LINE` to decide whether it gets a token placeholder:
```bash
CFG="${OVERLEAF_PROJECTS_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/overleaf-mcp/projects.json}"
if [ -n "$OVERLEAF_GIT_TOKEN" ] || [ -s "$OVERLEAF_GIT_TOKEN_FILE" ]; then TOKEN_LINE=""   # token comes from the environment
else TOKEN_LINE=', "gitToken": "PASTE_TOKEN_HERE"'; fi
mkdir -p "$(dirname "$CFG")" && [ ! -e "$CFG" ] && (umask 077; cat > "$CFG" <<EOF
{ "projects": { "default": { "name": "My Paper", "projectId": "<ID>"$TOKEN_LINE } } }
EOF
) && echo "created $CFG"
```
- **Token already in the environment:** say *"Saved your project ID to `<path>` so you won't need to paste it again."* Then go to Step 4.
- **Token placeholder added:** say *"I've created `<path>`, which only you can read. Open it, replace `PASTE_TOKEN_HERE` with your token, save, and let me know."* In Claude Code, offer `! nano "<path>"`, or `! open -e "<path>"` on macOS. When they confirm, go to Step 4.

If the user pastes the token into the chat anyway, don't scold them. Save it into the file for them, then add one gentle line: *"Saved. Since it's now in our chat history, you may want to create a fresh token at some point."*

### Step 4: Connect and confirm
```bash
P="${P:-default}"   # the project key chosen in Step 2
# Resolve each value on its own: environment first, then the projects file.
ID="$OVERLEAF_PROJECT_ID"
if [ -z "$ID" ] && [ -f "$CFG" ]; then ID="$(ovl_get "$P" projectId)"; fi
TOKEN="$OVERLEAF_GIT_TOKEN"
if [ -z "$TOKEN" ] && [ -s "$OVERLEAF_GIT_TOKEN_FILE" ]; then TOKEN="$(tr -d '[:space:]' < "$OVERLEAF_GIT_TOKEN_FILE")"; fi
if [ -z "$TOKEN" ] && [ -f "$CFG" ]; then TOKEN="$(ovl_get "$P" gitToken)"; fi
[ "$TOKEN" = PASTE_TOKEN_HERE ] && TOKEN=""
if [ -z "$ID" ] || [ -z "$TOKEN" ]; then
  [ -z "$ID" ] && echo "MISSING: project ID"; [ -z "$TOKEN" ] && echo "MISSING: token"
else
  AUTH="http.extraHeader=Authorization: Basic $(printf 'git:%s' "$TOKEN" | base64 | tr -d '\n')"
  REPO="${TMPDIR:-/tmp}/overleaf-$ID"
  og() { GIT_TERMINAL_PROMPT=0 git -c "$AUTH" -C "$REPO" "$@"; }   # authenticated git in the repo
  if [ -d "$REPO/.git" ] || GIT_TERMINAL_PROMPT=0 git -c "$AUTH" clone -q "https://git.overleaf.com/$ID" "$REPO"; then
    og config user.name >/dev/null || { og config user.name "Overleaf Agent"; og config user.email agent@overleaf.local; }
    echo "connected: $(og ls-files | wc -l | tr -d ' ') files"
  else echo "CONNECT_FAILED (see git error above)"; fi
fi
```
- **Connected:** confirm briefly and hand control back, for example *"You're connected to **Main Paper**: 14 files, main file `main.tex`. What would you like to do?"*
- **`MISSING: …`:** say kindly which value is still missing, and go back to Step 3 for just that one.
- **`CONNECT_FAILED`:** check the git error printed above it, then use the matching message below.
- **401/403 or `Authentication failed`:** *"Overleaf didn't accept that token. It may have expired, or Git integration may not be included in this Overleaf plan. Could you create a new token and update the file?"*
- **404 / `not found`:** *"I couldn't find that project. Could you double-check the project link?"*

Shell state may not carry over between tool calls. If it doesn't, start each later command with the `CFG`/helper lines from Step 2 and the Step 4 block (it skips cloning once the repo exists).

## Quick Reference
| Task | Command |
|---|---|
| Sync | `og pull --ff-only` |
| List .tex files | `og ls-files '*.tex'` (drop the pattern to list all files) |
| Read a file | `cat "$REPO/main.tex"` |
| List sections (with line numbers) | `grep -nE "$SEC_RE" "$REPO/main.tex"` (see below) |
| Extract one section | `awk -v T="Introduction" -f sec.awk "$REPO/main.tex"` (see below) |
| Status summary | `og log --oneline -5`, the file list, and the section list of the main file (the one containing `\documentclass`) |
| Commit and push | `og add -- main.tex && og commit -m "msg" && og push` |

```bash
SEC_RE='\\(part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{'
```

**sec.awk** prints a section from its heading up to the next heading at the *same or higher* level, or `\end{document}`, so subsections are included:
```awk
BEGIN { lv["part"]=-1; lv["chapter"]=0; lv["section"]=1; lv["subsection"]=2; lv["subsubsection"]=3; lv["paragraph"]=4; lv["subparagraph"]=5 }
match($0, /\\(part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{[^}]*\}/) {
  h = substr($0, RSTART+1, RLENGTH-1); type = h; sub(/[*{].*/, "", type)
  title = h; sub(/^[^{]*\{/, "", title); sub(/\}$/, "", title)
  if (on && lv[type] <= tl) exit
  if (!on && title == T) { on = 1; tl = lv[type] }
}
on && /\\end\{document\}/ { exit }
on { print }
```
Write it to a scratch file outside `$REPO`. Titles must match exactly, and `\section*{X}` matches `X`.

## Editing Workflow
1. `og pull --ff-only`. Then read the file or section you will change.
2. Edit the file in `$REPO` in place, using the normal file-edit tool. To replace a whole section, include its heading line, and keep or deliberately rewrite its subsections.
3. Run `og diff --stat` and confirm that only the intended files changed.
4. Commit with a descriptive message and push. **Pushing changes the user's live Overleaf project, so confirm with the user before the first push.**

## Common Mistakes
| Problem | Fix |
|---|---|
| Push rejected (non-fast-forward) | Someone edited in Overleaf. Run `og pull --rebase`, re-check the diff, then push again. |
| Pull reports CONFLICT | Stop. Show the conflicting hunks, resolve them with the user, or `og rebase --abort` and let them fix it in Overleaf. |
| `Authentication failed` / 403 | Wrong project ID, or the token is expired or revoked. Ask for a new token. Do not retry in a loop. |
| Token in `.git/config` or logs | Don't use `https://git:TOKEN@...` URLs. Use the `-c http.extraHeader` form above, which saves nothing to disk. |
| Paths escaping the repo | Only touch paths inside `$REPO`. Reject `..` and absolute paths from user input. |
| Sections in `\input{}`/`\include{}` files | Grep the main file for `\input{` and `\include{`, and look in those files too. |
| Git token availability | Git integration needs an Overleaf plan that includes it. If clone fails with 403 despite a valid token, mention this. |
