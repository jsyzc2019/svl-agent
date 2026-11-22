"""§107 独立确认集取料：arXiv:2611.22027 GauntletScore（从未用过的全新论文）。
一手抓 abs + full HTML，逐文件 SHA256，写 fetch_log.json，全文去标签成 paper_flat.txt。
"""
import requests, hashlib, re, json, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
ARXIV = "2611.22027"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; svagent-evidence-fetch/1.0)"}

def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                return r
            last = f"status={r.status_code} bytes={len(r.content)}"
        except Exception as e:
            last = repr(e)
        time.sleep(2 + i * 2)
    raise RuntimeError(f"fetch failed {url}: {last}")

def sha_bytes(b): return hashlib.sha256(b).hexdigest()

log = []
# abs
r = fetch(f"https://arxiv.org/abs/{ARXIV}")
open(f"{BASE}/S01_arxiv_abs.html", "wb").write(r.content)
log.append({"file": "S01_arxiv_abs.html", "url": f"https://arxiv.org/abs/{ARXIV}",
            "status": r.status_code, "bytes": len(r.content), "sha256": sha_bytes(r.content), "ok": True})

# full HTML（ar5iv 或 arxiv html）
full_url = f"https://arxiv.org/html/{ARXIV}"
try:
    rf = fetch(full_url, tries=3)
    full_src = "arxiv_html"
except Exception:
    rf = fetch(f"https://ar5iv.labs.arxiv.org/html/{ARXIV}", tries=3)
    full_src = "ar5iv"
open(f"{BASE}/S02_arxiv_full.html", "wb").write(rf.content)
log.append({"file": "S02_arxiv_full.html", "url": full_url if full_src == "arxiv_html" else f"https://ar5iv.labs.arxiv.org/html/{ARXIV}",
            "status": rf.status_code, "bytes": len(rf.content), "sha256": sha_bytes(rf.content), "ok": True, "source": full_src})

# 全文去标签 -> paper_flat.txt
from bs4 import BeautifulSoup
soup = BeautifulSoup(rf.content, "html.parser")
for tag in soup(["script", "style", "nav", "footer"]):
    tag.decompose()
text = soup.get_text(separator="\n")
text = re.sub(r"\n{3,}", "\n\n", text)
text = re.sub(r"[ \t]+", " ", text).strip()
open(f"{BASE}/paper_flat.txt", "w", encoding="utf-8").write(text)
log.append({"file": "paper_flat.txt", "derived_from": "S02_arxiv_full.html",
            "bytes": len(text.encode("utf-8")), "sha256": sha_bytes(text.encode("utf-8")), "ok": True})

json.dump(log, open(f"{BASE}/fetch_log.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
open(f"{BASE}/source.sha256", "w").write(sha_bytes(rf.content) + "\n")
print("source(full) sha256 =", sha_bytes(rf.content))
print("paper_flat bytes =", len(text.encode("utf-8")))
for e in log:
    print(" ", e["file"], e.get("status", "derived"), e["bytes"], e["sha256"][:16])
