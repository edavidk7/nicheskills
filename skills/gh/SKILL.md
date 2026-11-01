---
name: gh
description: "GitHub CLI (gh) operations: repos, PRs, issues, releases, Actions workflows, gists, search, and raw API calls. Use when the user asks to create/manage repos, open/review/merge pull requests, file/close issues, create releases, check CI status, search GitHub, or interact with the GitHub API."
---

# GitHub CLI Skill

Perform GitHub operations via the `gh` CLI. Always verify `gh` is installed and authenticated before proceeding.

## Pre-flight Check

```bash
gh auth status
```

If not authenticated, instruct the user to run `gh auth login`.

## Running gh from an agent

**Pass everything as flags.** Without a terminal, `gh` refuses to prompt and fails, for example `must provide --title and --body (or --fill …) when not running interactively`. If your shell does have a terminal, it would wait at a prompt or open a pager instead. Prefix commands with `GH_PROMPT_DISABLED=1 GH_PAGER=cat` so both cases behave the same.

**Write multi-line markdown bodies through stdin**, to avoid quoting problems with backticks, `$` and quotes:
```bash
gh pr create --title "Fix login redirect" --body-file - <<'EOF'
## Summary
- Handles `?next=` correctly
EOF
```
The same `--body-file -` works for `gh issue create`, `gh pr comment`, `gh issue comment`, `gh pr edit` and `gh release create --notes-file -`. Never use `--editor`/`-e`, and never run `gh gist edit` without a local file, since both open a text editor.

**Avoid commands that don't return.** `gh run watch` and `gh pr checks --watch` keep running until CI finishes, which can outlast your command timeout. Run them in the background if your harness supports that. Otherwise, poll `gh pr checks <n>` or `gh run view <id> --json status,conclusion`. Add `--exit-status` (run watch) or `--fail-fast` (pr checks) so a failure stops the command right away.

**Check with the user before anything others can see or that's hard to undo:**
- Creating PRs, issues, comments, reviews, releases, public repos or public gists.
- Merging, closing, deleting, renaming, archiving, transferring, or changing visibility.
- Setting secrets, or triggering workflows.

Read-only commands (`list`, `view`, `diff`, `checks`, `search`, `api` GETs) don't need a check. Only pass `--yes` after the user has said yes to that specific action.

**Watch @-mentions in text you post.** GitHub notifies whoever a bare `@name` refers to. Write `@name` only for someone you mean to notify, and put other uses in backticks.

## Core Operations

### Repositories

```bash
gh repo create <name> [--public|--private] [--clone] [--description "..."]
gh repo clone <owner/repo>
gh repo fork <owner/repo> [--clone]
gh repo view [<owner/repo>] [--web]
gh repo list [<owner>] [--limit N] [--json name,url,description]
gh repo edit [<owner/repo>] [--description "..."]
gh repo edit [<owner/repo>] --visibility public|private|internal --accept-visibility-change-consequences   # both flags required
gh repo delete <owner/repo> --yes
gh repo rename <new-name>
gh repo archive <owner/repo>
gh repo set-default <owner/repo>
```

### Pull Requests

```bash
gh pr create --title "..." --body "..." [--base main] [--head feature] [--draft] [--reviewer user] [--label bug]
gh pr list [--state open|closed|merged|all] [--author user] [--label label] [--json number,title,state]
gh pr view <number> [--web] [--json title,body,reviews,state]
gh pr checkout <number|branch>
gh pr merge <number> [--merge|--squash|--rebase] [--delete-branch] [--auto]
gh pr close <number>
gh pr reopen <number>
gh pr review <number> --approve [--body "..."]
gh pr review <number> --request-changes --body "..."
gh pr diff <number>
gh pr checks <number> [--watch --fail-fast]   # --watch blocks; see "Running gh from an agent"
gh pr ready <number>                    # Mark draft PR as ready
gh pr comment <number> --body "..."
gh pr edit <number> [--title "..."] [--add-label label] [--add-reviewer user]
```

### Issues

```bash
gh issue create --title "..." --body "..." [--label bug] [--assignee user] [--milestone "v1"]
gh issue list [--state open|closed|all] [--label label] [--assignee user] [--json number,title,state]
gh issue view <number> [--web] [--json title,body,comments]
gh issue close <number> [--reason completed|"not planned"|duplicate]
gh issue reopen <number>
gh issue comment <number> --body "..."
gh issue edit <number> [--title "..."] [--add-label label] [--add-assignee user]
gh issue pin <number>
gh issue unpin <number>
gh issue transfer <number> <dest-repo>
gh issue develop <number> --checkout      # Create branch for issue
```

### Releases

```bash
gh release create <tag> [files...] --title "..." --notes "..." [--draft] [--prerelease] [--target branch]
gh release create <tag> --generate-notes   # Auto-generate notes from commits
gh release list [--limit N]
gh release view <tag>
gh release download <tag> [--pattern "*.zip"]
gh release delete <tag> --yes
gh release edit <tag> [--title "..."] [--notes "..."] [--draft=false]
gh release upload <tag> <files...>
```

### Gists

```bash
gh gist create <file> [--public] [--desc "..."]
gh gist create --filename "name.ext" - <<< "content"   # From stdin
gh gist list [--public|--secret] [--limit N]
gh gist view <id|url> [--raw]
gh gist edit <id|url> --filename <name> <local-file>   # replace a file's content (without a local file it opens an editor)
gh gist clone <id|url>
gh gist delete <id|url>
gh gist rename <id|url> <old-name> <new-name>
```

### GitHub Actions

```bash
gh run list [--workflow name.yml] [--status success|failure|in_progress] [--limit N] [--json databaseId,status,conclusion]
gh run view <run-id> [--log] [--log-failed]
gh run watch <run-id> --exit-status       # Blocks until the run ends; see "Running gh from an agent"
gh run rerun <run-id> [--failed]          # Re-run failed jobs only
gh run cancel <run-id>
gh run download <run-id> [--name "artifact-name"]
gh workflow list
gh workflow view <name|id>
gh workflow run <name|file> [--ref branch] [-f key=value]   # Trigger workflow_dispatch
gh workflow enable <name|id>
gh workflow disable <name|id>
gh cache list [--limit N]
gh cache delete <id|key>
```

### Search

```bash
gh search repos <query> [--language lang] [--limit N] [--json fullName,description,url]
gh search issues <query> [--repo owner/repo] [--state open] [--limit N]
gh search prs <query> [--repo owner/repo] [--state open]
gh search commits <query> [--repo owner/repo]
gh search code <query> [--repo owner/repo] [--language lang]
```

### Labels

```bash
gh label create <name> --color "0052cc" [--description "..."]
gh label list [--json name,color,description]
gh label edit <name> --name <new-name> [--color "..."]
gh label delete <name> --yes
gh label clone <source-repo>              # Copy labels from another repo
```

### Secrets & Variables (Actions)

```bash
gh secret set <name> [--repo owner/repo] < secret-file.txt   # read from a file, never --body: that puts the secret in the command and transcript
gh secret list
gh secret delete <name>
gh variable set <name> --body "value"
gh variable list
gh variable delete <name>
```

### Raw API Calls

For anything not covered by a subcommand:

```bash
gh api <endpoint> [--method GET|POST|PUT|PATCH|DELETE] [-f key=value] [--jq '.field']
```

Examples:

```bash
# Get repo info
gh api repos/{owner}/{repo}

# List collaborators
gh api repos/{owner}/{repo}/collaborators --jq '.[].login'

# Add a topic
gh api repos/{owner}/{repo}/topics --method PUT -f names[]="topic1" -f names[]="topic2"

# GraphQL query
gh api graphql -f query='{ viewer { login repositories(first: 5) { nodes { name } } } }'

# Paginate results
gh api repos/{owner}/{repo}/issues --paginate --jq '.[].title'
```

### Other Useful Commands

```bash
gh status                                 # Dashboard: assigned issues, PRs, mentions
gh browse [--projects|--wiki|--settings]  # Open repo in browser
gh extension list                         # List installed extensions
gh extension install <repo>               # Install an extension
```

## Guidelines

- **JSON output**: Append `--json field1,field2` to most list/view commands for structured output. Combine with `--jq` for filtering.
- **Web flag**: Most view commands accept `--web` to open in browser instead of terminal.
- **Repo context**: Commands run from inside a git repo auto-detect `owner/repo`. Otherwise pass `-R owner/repo`.
- **Confirmation**: follow the list in "Running gh from an agent". It covers everything other people can see, not just destructive commands.
- **Rate limits**: For bulk operations, be mindful of GitHub API rate limits (5000 req/hr authenticated).
- **Pagination**: Use `--limit N` or `--paginate` (API) for large result sets.
