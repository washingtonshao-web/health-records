"""由 GitHub Action 调用：把 Issue 里的一条评论追加到对应档案的评论层。

输入（环境变量）：ISSUE_TITLE, COMMENT_BODY, COMMENT_AUTHOR, COMMENT_URL, COMMENT_DATE
输出（GITHUB_OUTPUT）：status = appended / proposal / skipped，cid，file
"""
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKER = "<!-- NEW-COMMENTS-BELOW -->"
EMPTY = "（暂无评论）"


def output(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kv.items())
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(lines)
    print(lines, end="")


def strip_fences(body):
    lines = body.strip().splitlines()
    if lines and lines[0].lstrip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def main():
    m = re.match(r"\s*(HR-\d{3})", os.environ["ISSUE_TITLE"])
    if not m:
        return output(status="skipped", reason="标题不是档案编号")
    rid = m.group(1)
    path = ROOT / "records" / f"{rid}-comments.md"
    if not path.exists():
        return output(status="skipped", reason=f"找不到 {path.name}")

    body = strip_fences(os.environ["COMMENT_BODY"].replace("\r\n", "\n"))
    if not body:
        return output(status="skipped", reason="内容为空")
    if re.match(r"#+\s*事实更新提议", body):
        return output(status="proposal")

    text = path.read_text(encoding="utf-8")
    nums = [int(n) for n in re.findall(r"^### C-(\d{4})", text, re.M)]
    cid = f"C-{(max(nums) if nums else 0) + 1:04d}"
    author = os.environ["COMMENT_AUTHOR"]
    date = os.environ.get("COMMENT_DATE", "")[:10]

    lines = body.splitlines()
    if lines[0].startswith("#"):
        header = re.sub(r"^#+\s*", "", lines[0])
        if re.match(r"C-[\d?？]+", header):
            header = re.sub(r"^C-[\d?？]+", cid, header)
        else:
            header = f"{cid} · {header}"
        lines = lines[1:]
    else:
        header = f"{cid} · {date} · （未注明模型） · 提问人：@{author}"
    entry = (
        f"### {header}\n"
        + "\n".join(lines).strip()
        + f"\n\n_提交：@{author} · [原始评论]({os.environ['COMMENT_URL']})_\n"
    )
    # 评论内容按 Markdown 原样保留；行尾加两个空格以保持逐行显示
    entry = "\n".join(
        (ln + "  ") if ln and not ln.startswith(("#", "|", "-", "*", ">", "_")) else ln
        for ln in entry.splitlines()
    ) + "\n"

    text = text.replace(f"\n{EMPTY}\n", "\n", 1)
    text = text.replace(MARKER, f"{MARKER}\n\n{entry}", 1)
    path.write_text(text, encoding="utf-8", newline="\n")
    output(status="appended", cid=cid, file=f"records/{path.name}")


if __name__ == "__main__":
    main()
