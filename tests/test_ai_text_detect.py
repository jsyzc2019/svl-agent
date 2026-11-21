# -*- coding: utf-8 -*-
"""固化网文AI检测验证的关键发现。"""
import unittest, json, hashlib
from svagent.ai_text_detect import (
    extract_features, build_matrix, FEATURE_NAMES, load_samples, run
)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
import numpy as np


class TestFeatureExtraction(unittest.TestCase):
    def test_feature_keys(self):
        f = extract_features("他缓缓走进房间。屋子里很安静。“谁在那？”他问。")
        for k in FEATURE_NAMES:
            self.assertIn(k, f)
            self.assertIsInstance(f[k], float)

    def test_empty_safe(self):
        f = extract_features("")
        self.assertEqual(len(f), 8)


class TestSampleIntegrity(unittest.TestCase):
    def test_sample_hash_lock(self):
        actual = hashlib.sha256(open("webnovel_samples.json", "rb").read()).hexdigest()
        lock = open("samples.sha256").read().split()[0]
        self.assertEqual(actual, lock, "样本被篡改")

    def test_label_counts(self):
        s = load_samples()
        from collections import Counter
        c = Counter(x["label"] for x in s)
        self.assertEqual(c["human"], 24)
        self.assertEqual(c["ai"], 12)
        self.assertEqual(c["deai"], 12)


class TestKeyFindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = json.load(open("ai_detect_full_result.json"))
        cls.s = load_samples()
        cls.H = [x for x in cls.s if x["label"] == "human"]
        cls.A = [x for x in cls.s if x["label"] == "ai"]

    def test_original_auc_high_but_gate_triggered(self):
        # 揭盲的高AUC是真实计算结果
        self.assertGreaterEqual(self.R["auc_original"], 0.85)
        # 但G1门禁必须触发(单特征主导)——这是本次核心发现
        self.assertTrue(self.R["gate"]["G1_single_feature_dominant"])

    def test_single_feature_dominance(self):
        # 仅句长就能达到接近全特征的AUC
        sa = self.R["diagnosis"]["single_feature_auc"]
        self.assertGreaterEqual(sa["仅句长"], 0.85)
        # 去掉句长/标点后内容特征近随机
        self.assertLess(sa["纯内容特征(去句长标点)"], 0.65)

    def test_length_confound_absent_but_style_artifact_present(self):
        # 长度本身不是混淆(G2未触发)
        self.assertLess(abs(self.R["gate_length_label_corr"]), 0.5)
        # 但句长均值差异巨大(文风artifact)
        fm = self.R["feature_means"]["sent_len_mean"]
        self.assertGreater(fm["human"] - fm["ai"], 15)

    def test_deai_shallow_vs_deep(self):
        # 表面去味改动小
        self.assertLess(self.R["diagnosis"]["deai_change_rate"], 0.1)
        # 深度去味(改句长)检出率明显下降
        self.assertLessEqual(self.R["diagnosis"]["deep_deai_ablation"]["检出率"], 0.8)

    def test_deai_heldout(self):
        self.assertTrue(self.R["gate"]["G3_deai_heldout"])

    def test_conclusion_honest(self):
        con = self.R["independent_conclusion"]
        self.assertIn("不可靠", con["answer"])
        self.assertIn("自利偏差", con["method_reflection"])


if __name__ == "__main__":
    unittest.main()
