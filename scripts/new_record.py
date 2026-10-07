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
    # 先全部检查再写入，避免留下半成品；INDEX 里出现过的编号也不能复用
    index = ROOT / "INDEX.md"
    if index.exists() and rid in index.read_text(encoding="utf-8"):
        sys.exit(f"{rid} 已在 INDEX.md 中登记，编号不能复用")
    existing = list((ROOT / "records").glob(f"{rid}-*.md"))
    if existing:
        sys.exit(f"{existing[0].name} 已存在，编号不能复用")
    for kind in ("facts", "comments"):
        out = ROOT / "records" / f"{rid}-{kind}.md"
        text = (ROOT / "templates" / f"{kind}.md").read_text(encoding="utf-8")
        for k, v in values.items():
            text = text.replace(k, v)
        out.parent.mkdir(exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
        print("已生成", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
