# -*- coding: utf-8 -*-
"""构建三类网文样本，落地 webnovel_samples.json（带真实标签）。
- H 真人：《斗破苍穹》(天蚕土豆, 2009起, ChatGPT前) 章节切成~500字片段，随机抽24个
- A AI：ai_samples_raw.py 中现场创作的12段
- D 去味：对 A 用 humanizer 24 模式中的确定性规则改写，仍是 AI 起源

长度匹配：H 片段控制在与 A 相近的字数区间，避免"长度"成为判别器作弊特征。
随机种子固定，样本一次性写定，不在看过判别结果后调整。
"""
import json, re, random
from ai_samples_raw import AI_SAMPLES

SEED = 20261121
rng = random.Random(SEED)

# ---------- H 真人样本 ----------
def load_human_chunks():
    s = open('doupo_train.txt', 'rb').read().decode('utf-8')
    pat = re.compile(r'第[零一二三四五六七八九十百千万\d]+章[^\r\n]{0,30}')
    ms = list(pat.finditer(s))
    chapters = []
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(s)
        body = re.sub(r'\s+', '', s[start:end])
        if len(body) > 600:
            chapters.append((m.group().strip(), body))
    # 跳过前几章(可能含声明/序)，把每章切成 ~500 字的片段
    chunks = []
    for title, body in chapters[3:]:
        j = 0
        while j + 430 <= len(body):
            L = rng.randint(450, 555)  # 长度波动，与AI/去味样本区间一致
            seg = body[j:j + L]
            if len(seg) >= 430:
                chunks.append({"text": seg, "src": "斗破苍穹:" + title})
            j += L + rng.randint(30, 90)  # 片段间留间隔，避免重叠
    return chunks

human_chunks = load_human_chunks()
print("H chunks available:", len(human_chunks))
# 固定种子抽 24 个
h_sample = rng.sample(human_chunks, 24)
for i, x in enumerate(h_sample):
    x["id"] = f"H{i:02d}"; x["label"] = "human"

# ---------- A AI 样本 ----------
a_sample = []
for i, t in enumerate(AI_SAMPLES):
    t = re.sub(r'\s+', '', t)  # 与真人样本同样去空白，公平
    a_sample.append({"id": f"A{i:02d}", "label": "ai", "text": t, "src": "LLM-generated"})

# ---------- D 去味样本：humanizer 确定性规则改写 ----------
# 基于 wiki "Signs of AI writing" 的中文适配：破排比/增口语/删套路/变句长/加语气
HEDGE = [
    "说真的，", "我猜，", "反正吧，", "怎么说呢，", "要我说，",
    "这事儿吧，", "讲真，", "估计是，", "怎么说，", "反正我觉着，",
]
COLLOQ = {
    "仿佛": "好像", "犹如": "就像", "然而": "可", "此外": "还有",
    "随即": "接着", "顿时": "一下", "霎时": "一瞬间", "须臾": "没一会儿",
    "蓦地": "突然", "嘴角微微上扬": "咧嘴笑了一下", "眼神复杂": "说不清什么表情",
    "不容置疑的威严": "不容反驳的劲儿", "喃喃自语": "小声嘀咕",
    "此起彼伏": "一个接一个", "缓缓": "慢慢", "骤然": "猛地",
    "深邃": "深", "明灭不定": "忽明忽暗", "棱角分明": "有棱有角",
    "在劫难逃": "怕是躲不过", " succumb": "",
}
FILLER_SENT = [
    "他愣了一下。", "这事儿透着古怪。", "说不上为什么。", "气氛有点怪。",
    "我心里犯嘀咕。", "可仔细一瞧，也不是那么回事。", "这下有意思了。",
]

def deai(text, idx):
    r = rng  # 使用同一固定种子流，保证可复现
    out = text
    # 1) 书面词→口语词
    for k, v in COLLOQ.items():
        if v: out = out.replace(k, v)
    # 2) 在若干句号后插入口语短句，制造句长波动与"人味"停顿
    parts = out.split("。")
    newparts = []
    for p in parts:
        newparts.append(p)
        if p and r.random() < 0.18:
            newparts.append(r.choice(FILLER_SENT))
    out = "。".join(newparts)
    # 3) 段首偶尔加口语连接词
    lines = out.split("\n")
    lines = [ (r.choice(HEDGE) + l if l and r.random() < 0.12 else l) for l in lines ]
    out = "\n".join(lines)
    return out

d_sample = []
for i, t in enumerate(AI_SAMPLES):
    t2 = deai(re.sub(r'\s+', '', t), i)
    d_sample.append({"id": f"D{i:02d}", "label": "deai", "text": t2, "src": "LLM-generated→humanizer"})

# ---------- 长度统计与落盘 ----------
import statistics as st
for name, samp in [("H", h_sample), ("A", a_sample), ("D", d_sample)]:
    lens = [len(x["text"]) for x in samp]
    print(f"{name}: n={len(samp)} len mean={st.mean(lens):.0f} min={min(lens)} max={max(lens)}")

all_samples = h_sample + a_sample + d_sample
payload = {
    "seed": SEED,
    "source_note": "真人样本=斗破苍穹(2009, ChatGPT前, 高置信人类); AI样本=Agent现场创作; 去味样本=humanizer规则改写AI样本",
    "samples": all_samples,
}
with open('webnovel_samples.json', 'w') as f:
    json.dump(payload, f, ensure_ascii=False, indent=1)
print("saved webnovel_samples.json, total", len(all_samples))
