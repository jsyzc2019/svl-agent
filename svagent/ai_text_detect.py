# -*- coding: utf-8 -*-
"""网文 AI 文本客观判别引擎 —— 严格执行 ai_detect_preregistration.json 锁存判据。
8 个预定义浅层风格特征 + 逻辑回归 + 5折CV(H vs A) + D 全程留出。
"""
import json, re, math
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score

# 预注册词表（判据锁存的一部分）
FORMAL_WORDS = ["仿佛", "犹如", "然而", "须臾", "明灭不定", "骤然", "蓦地",
                "深邃", "不容置疑", "喃喃自语", "此起彼伏", "棱角分明",
                "转瞬", "旋即", "须臾之间", "目光如炬", "嘴角勾起"]
PUNCT = set("，。！？；：、")
SENT_SPLIT = re.compile(r'[。！？!?]+')


def extract_features(text: str) -> dict:
    """提取 8 个预注册特征。"""
    n = len(text)
    # 句子切分
    sents = [s for s in SENT_SPLIT.split(text) if len(s.strip()) > 0]
    sent_lens = [len(s) for s in sents]
    sent_len_mean = float(np.mean(sent_lens)) if sent_lens else 0.0
    sent_len_cv = float(np.std(sent_lens) / np.mean(sent_lens)) if sent_lens and np.mean(sent_lens) > 0 else 0.0
    # TTR 词汇多样性（字级）
    ttr = len(set(text)) / n if n > 0 else 0.0
    # 标点密度
    punct_rate = sum(1 for c in text if c in PUNCT) / n if n > 0 else 0.0
    # 对话占比（中文引号包裹）
    dialogue = re.findall(r'[“"]([^”"]{2,})[”"]', text)
    dialogue_ratio = sum(len(d) for d in dialogue) / n if n > 0 else 0.0
    # 书面/AI高频词命中率（每千字）
    hits = sum(text.count(w) for w in FORMAL_WORDS)
    formal_word_hits = hits / (n / 1000.0) if n > 0 else 0.0
    # 段落数（按换行）
    paragraph_count = text.count("\n") + 1
    # 感叹+问号密度
    exclaim_question_rate = sum(1 for c in text if c in "！？!?") / n if n > 0 else 0.0
    return {
        "sent_len_cv": sent_len_cv,
        "sent_len_mean": sent_len_mean,
        "ttr": ttr,
        "punct_rate": punct_rate,
        "dialogue_ratio": dialogue_ratio,
        "formal_word_hits": formal_word_hits,
        "paragraph_count": float(paragraph_count),
        "exclaim_question_rate": exclaim_question_rate,
    }


FEATURE_NAMES = ["sent_len_cv", "sent_len_mean", "ttr", "punct_rate",
                 "dialogue_ratio", "formal_word_hits", "paragraph_count",
                 "exclaim_question_rate"]


def load_samples(path="webnovel_samples.json"):
    d = json.load(open(path))
    return d["samples"]


def build_matrix(samples):
    X = np.array([[extract_features(s["text"])[f] for f in FEATURE_NAMES] for s in samples])
    y = np.array([1 if s["label"] == "ai" else 0 for s in samples])  # ai=1, human=0
    return X, y


def run():
    samples = load_samples()
    H = [s for s in samples if s["label"] == "human"]
    A = [s for s in samples if s["label"] == "ai"]
    D = [s for s in samples if s["label"] == "deai"]

    # 校验样本锁
    lock = open("samples.sha256").read().split()[0]
    import hashlib
    actual = hashlib.sha256(open("webnovel_samples.json", "rb").read()).hexdigest()
    assert actual == lock, "样本被篡改!"

    train = H + A
    Xtr, ytr = build_matrix(train)
    scaler = StandardScaler().fit(Xtr)
    Xs = scaler.transform(Xtr)

    # --- 5折交叉验证 AUC (H vs A) ---
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = LogisticRegression(random_state=42, max_iter=1000)
    proba_cv = cross_val_predict(model, Xs, ytr, cv=cv, method="predict_proba")[:, 1]
    auc_original = roc_auc_score(ytr, proba_cv)

    # --- 在全部 H+A 上重训, 对 D 预测(全程留出) ---
    model_full = LogisticRegression(random_state=42, max_iter=1000).fit(Xs, ytr)
    Xd = scaler.transform(np.array([[extract_features(s["text"])[f] for f in FEATURE_NAMES] for s in D]))
    proba_d = model_full.predict_proba(Xd)[:, 1]
    pred_d_ai = (proba_d >= 0.5).astype(int)
    deai_detect_rate = float(pred_d_ai.mean())
    deai_pass_rate = float(1 - deai_detect_rate)

    # --- 反虚荣门禁 G2: 长度与标签相关性 ---
    lengths = np.array([len(s["text"]) for s in train])
    corr_len_label = float(np.corrcoef(lengths, ytr)[0, 1])

    # --- 单特征 AUC (诊断) ---
    single_auc = {}
    for i, f in enumerate(FEATURE_NAMES):
        try:
            single_auc[f] = round(float(roc_auc_score(ytr, Xtr[:, i])), 3)
        except Exception:
            single_auc[f] = None

    result = {
        "sample_counts": {"human": len(H), "ai": len(A), "deai": len(D)},
        "auc_original": round(float(auc_original), 4),
        "deai_detect_rate": round(deai_detect_rate, 4),
        "deai_pass_rate": round(deai_pass_rate, 4),
        "deai_proba_mean": round(float(proba_d.mean()), 4),
        "gate_length_label_corr": round(corr_len_label, 4),
        "single_feature_auc": single_auc,
        "feature_means": {
            f: {"human": round(float(Xtr[ytr == 0, i].mean()), 4),
                "ai": round(float(Xtr[ytr == 1, i].mean()), 4)}
            for i, f in enumerate(FEATURE_NAMES)
        },
        "decision": {},
    }
    # 判据判定（按预注册 R1-R6）
    a = result["auc_original"]
    result["decision"]["R_original"] = ("R1_detectable" if a >= 0.8 else
                                        "R2_weak" if a >= 0.6 else "R3_fail")
    d = result["deai_detect_rate"]
    result["decision"]["R_deai"] = ("R5_holds" if d >= 0.8 else
                                    "R6_gray" if d >= 0.6 else "R4_breaks")
    # 门禁判定
    result["gate"] = {
        "G1_single_feature_dominant": max(abs(v - 0.5) for v in single_auc.values() if v) >= 0.35,
        "G2_length_confound": abs(corr_len_label) > 0.5,
        "G3_deai_heldout": True,
        "G4_boundaries_written": True,
    }
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=2))
