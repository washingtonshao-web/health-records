"""新建一份档案：python scripts/new_record.py HR-002 <评论 Issue 链接>

根据 templates/ 生成 records/<ID>-facts.md 和 records/<ID>-comments.md。
Issue 需事先建好，标题为 “<ID> 评论”。生成后请在 INDEX.md 加一行。
"""
import datetime
import pathlib
import re
import sys

RAW = "https://raw.githubusercontent.com/washingtonshao-web/health-records/main"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) != 3 or not re.fullmatch(r"HR-\d{3}", sys.argv[1]):
        sys.exit("用法：python scripts/new_record.py HR-002 <评论 Issue 链接>")
    rid, issue_url = sys.argv[1], sys.argv[2]
    values = {
        "{{ID}}": rid,
        "{{DATE}}": datetime.date.today().isoformat(),
        "{{RAW}}": RAW,
        "{{ISSUE_URL}}": issue_url,
    }
    for kind in ("facts", "comments"):
        out = ROOT / "records" / f"{rid}-{kind}.md"
        if out.exists():
            sys.exit(f"{out} 已存在，编号不能复用")
        text = (ROOT / "templates" / f"{kind}.md").read_text(encoding="utf-8")
        for k, v in values.items():
            text = text.replace(k, v)
        out.parent.mkdir(exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
        print("已生成", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
