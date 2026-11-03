#!/usr/bin/env python3
"""仓库自检：结构、frontmatter、断链、本机信息、编码。

无第三方依赖，只用标准库。CI 与本地都能跑：
    python3 .github/check.py
"""

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

errors = []
warns = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warns.append(msg)


# ---------- 1. 必需文件 ----------
for f in ["SKILL.md", "README.md", "LICENSE", ".gitignore"]:
    if not os.path.exists(f):
        err("缺少必需文件：%s" % f)

# ---------- 2. frontmatter ----------
if os.path.exists("SKILL.md"):
    s = open("SKILL.md", encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m:
        err("SKILL.md 缺少 YAML frontmatter")
    else:
        fm = m.group(1)
        nm_m = re.search(r"^name:\s*(.+)$", fm, re.M)
        de_m = re.search(r"^description:\s*(.+)$", fm, re.M)
        nm = nm_m.group(1).strip() if nm_m else ""
        de = de_m.group(1).strip() if de_m else ""
        if not nm:
            err("frontmatter 缺少 name")
        elif not re.match(r"^[a-z0-9-]+$", nm):
            err("name 必须是小写字母/数字/连字符：%s" % nm)
        elif nm != os.path.basename(ROOT):
            err("name 与目录名不一致：name=%s 目录=%s" % (nm, os.path.basename(ROOT)))
        if not de:
            err("frontmatter 缺少 description")
        elif len(de) > 1024:
            err("description 超过 1024 字符：%d" % len(de))

# ---------- 3. 内部链接 ----------
for f in glob.glob("**/*.md", recursive=True):
    t = open(f, encoding="utf-8").read()
    refs = set(re.findall(r"(?:references|assets)/[A-Za-z0-9_.-]+\.md", t))
    refs |= set(re.findall(r"\]\(([^)#\s]+\.md)\)", t))
    for ref in refs:
        if not (os.path.exists(ref)
                or os.path.exists(os.path.join(os.path.dirname(f), ref))
                or os.path.exists(os.path.basename(ref))):
            err("%s 中存在断链：%s" % (f, ref))

# ---------- 4. 本机路径 / 隐私 ----------
BAD = [
    (r"[A-Za-z]:[/\\](?:Users|workbuddy)", "本机绝对路径"),
    (r"/(?:home|Users)/[A-Za-z0-9._-]+", "家目录路径"),
    (r"_sandbox\w*|_test-docs", "本地测试目录"),
    (r"\b[\w.+-]+@(?!users\.noreply\.github\.com)[\w-]+\.[a-z]{2,}\b", "邮箱地址"),
]
for f in glob.glob("**/*", recursive=True):
    if not os.path.isfile(f) or f.endswith((".png", ".jpg", ".zip")):
        continue
    if f.replace(os.sep, "/") == ".github/check.py":   # 自检脚本本身含匹配串，跳过
        continue
    try:
        t = open(f, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    for pat, label in BAD:
        if re.search(pat, t):
            err("%s 含%s" % (f, label))

# ---------- 5. 编码 ----------
for f in glob.glob("**/*.md", recursive=True) + ["LICENSE"]:
    b = open(f, "rb").read()
    if b[:3] == b"\xef\xbb\xbf":
        err("%s 带 BOM" % f)
    if b"\r\n" in b:
        warn("%s 含 CRLF（.gitattributes 会在提交时转 LF）" % f)

# ---------- 6. 体量提示 ----------
if os.path.exists("SKILL.md"):
    n = len(open("SKILL.md", encoding="utf-8").read())
    if n > 20000:
        warn("SKILL.md 体量偏大（%d 字符），考虑把细节移入 references/" % n)

# ---------- 输出 ----------
for w in warns:
    print("WARN  %s" % w)
for e in errors:
    print("ERROR %s" % e)
print("---")
print("检查完成：%d 个错误，%d 个警告" % (len(errors), len(warns)))
sys.exit(1 if errors else 0)
