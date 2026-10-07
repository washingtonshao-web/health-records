"""由 GitHub Action 调用：把 Issue 里的一条评论追加到对应档案的评论层。

输入（环境变量）：ISSUE_TITLE, COMMENT_BODY, COMMENT_AUTHOR, COMMENT_URL
输出（GITHUB_OUTPUT）：status = appended / proposal / duplicate / skipped / error，cid，file，reason

规则：
- 只收录第一行以 C-???? 开头的评论块；一条 Issue 回复只能有一个评论块。
- “事实更新提议”永不写入任何文件，只提醒维护人核对。
- 同一条 Issue 评论只写入一次（按评论链接去重），重跑安全。
- 编号取当前评论层及其归档文件中的最大编号 + 1。
"""
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKER = "<!-- NEW-COMMENTS-BELOW -->"
EMPTY = "（暂无评论）"
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\n]*\n(.*?)^ {0,3}\1[ \t]*$", re.M | re.S)
HEAD = re.compile(r"^[#*\s]*C-[\dX?？x_]+\**", re.I)  # 评论块首行
PROPOSAL = re.compile(r"^[#*\s]*事实更新提议", re.M)
# 写入档案时用角色名代替 GitHub 用户名，避免账号与档案直接关联
ROLE = {"washingtonshao-web": "维护人"}


def output(**kv):
    lines = "".join(f"{k}={str(v).replace(chr(10), ' ')}\n" for k, v in kv.items())
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(lines)
    print(lines, end="")


def main():
    m = re.match(r"\s*(HR-\d{3})(?!\d)", os.environ["ISSUE_TITLE"])
    if not m:
        return output(status="skipped", reason="Issue 标题不是档案编号")
    rid = m.group(1)
    path = ROOT / "records" / f"{rid}-comments.md"
    if not path.exists():
        return output(status="skipped", reason=f"找不到 {path.name}")

    raw = os.environ["COMMENT_BODY"].replace("\r\n", "\n").strip()
    if HEAD.match(raw):  # 没加代码块直接粘贴；截掉后面的提议
        blocks = [PROPOSAL.split(raw, 1)[0].rstrip("`~ \n")]
    else:
        blocks = [b.strip() for _, b in FENCE.findall(raw)] or [raw]
    comments = [b for b in blocks if b and HEAD.match(b.splitlines()[0])]
    has_proposal = bool(PROPOSAL.search(raw))
    if not comments:
        return output(status="proposal" if has_proposal else "skipped",
                      reason="没有找到以 C-???? 开头的评论块")
    if len(comments) > 1:
        return output(status="skipped", reason="一次只能贴一个评论块，请分开发")

    url = os.environ["COMMENT_URL"]
    files = sorted(path.parent.glob(f"{rid}-comments*.md"))
    texts = [p.read_text(encoding="utf-8") for p in files]
    if any(f"<!-- src: {url} -->" in t for t in texts):
        return output(status="duplicate", reason="这条评论已写入过")

    text = path.read_text(encoding="utf-8")
    if text.count(MARKER) != 1:
        return output(status="error", reason="评论层插入标记缺失或重复")
    nums = [int(n) for t in texts for n in re.findall(r"^### C-(\d{4,})", t, re.M)]
    cid = f"C-{(max(nums) if nums else 0) + 1:04d}"

    lines = comments[0].splitlines()
    first = re.sub(r"^[#*\s]+|[*\s]+$", "", lines[0])
    header = re.sub(r"^C-[\dX?？x_]+", cid, first, count=1, flags=re.I)
    body = []
    for ln in lines[1:]:
        ln = re.sub(r"^ {0,3}#{1,3}(\s)", r"####\1", ln)  # 正文标题降级，避免冒充评论标题
        ln = ln.replace(MARKER, "").replace("<!--", "&lt;!--")
        # 行尾两个空格：GitHub 页面上逐行显示
        keep = ln.strip() and not ln.lstrip().startswith(("|", "-", "*", ">", "#", "```", "~~~"))
        body.append(ln + "  " if keep else ln)
    if sum(bool(re.match(r" {0,3}(```|~~~)", ln)) for ln in body) % 2:
        body.append("```")  # 补上未闭合的代码块
    who = ROLE.get(os.environ["COMMENT_AUTHOR"], "协作者")
    entry = (f"### {header}\n" + "\n".join(body).strip()
             + f"\n\n_提交：{who} · [原始评论]({url})_\n<!-- src: {url} -->\n")

    if not nums:
        text = text.replace(f"{MARKER}\n\n{EMPTY}", MARKER, 1)
    text = text.replace(MARKER, f"{MARKER}\n\n{entry}", 1)
    path.write_text(text, encoding="utf-8", newline="\n")
    output(status="appended", cid=cid, file=f"records/{path.name}",
           reason="另含事实更新提议，未写入事实层" if has_proposal else "")


if __name__ == "__main__":
    main()
