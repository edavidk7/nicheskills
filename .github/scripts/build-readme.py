"""Inline each skill's README.md into the main README between the skills markers."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
START, END = "<!-- skills:start -->", "<!-- skills:end -->"


def skill_name(skill_md: pathlib.Path) -> str:
    match = re.search(r"^---\n.*?^name:\s*[\"']?([^\"'\n]+)", skill_md.read_text(), re.S | re.M)
    if not match:
        sys.exit(f"error: no `name:` in the frontmatter of {skill_md.relative_to(ROOT)}")
    return match.group(1).strip()


def section(skill_md: pathlib.Path) -> str:
    folder = skill_md.parent
    readme = folder / "README.md"
    if not readme.is_file():
        sys.exit(f"error: missing {readme.relative_to(ROOT)} (every skill needs a 1-2 sentence README)")
    lines = readme.read_text().strip().splitlines()
    if lines and lines[0].startswith("# "):  # drop a title heading; the skill name is used instead
        lines = lines[1:]
    body = "\n".join(lines).strip()
    return f"### [{skill_name(skill_md)}]({folder.relative_to(ROOT).as_posix()})\n{body}"


skills = sorted((ROOT / "skills").rglob("SKILL.md"), key=skill_name)
block = "\n\n".join(section(s) for s in skills)

readme_path = ROOT / "README.md"
text = readme_path.read_text()
if START not in text or END not in text:
    sys.exit(f"error: README.md must contain {START} and {END}")
head, rest = text.split(START, 1)
_, tail = rest.split(END, 1)
new = f"{head}{START}\n{block}\n{END}{tail}"

if new != text:
    readme_path.write_text(new)
    print(f"README.md updated ({len(skills)} skills)")
else:
    print(f"README.md already up to date ({len(skills)} skills)")
