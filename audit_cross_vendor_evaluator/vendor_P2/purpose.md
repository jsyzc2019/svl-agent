任务：近似重复文本判定。
背景：这是一批来自文档去重场景的文本对。text_a 与 text_b 是两段文字。去重目标是判断两段文字是否是同一句话的近似版本——允许删去个别词、改写措辞或做细微编辑后仍表达基本相同的，视为近似重复；内容实质不同、表达了另一件事的，视为不重复。
请从数据中归纳一个确定性的二分类函数 judge(text_a, text_b)，decision=True 表示近似重复，False 表示实质不同。

要求：纯字符串/正则实现，确定性；不使用随机数、时间、样本 id、外部文件或样本文本硬编码。
返回 (decision: bool, signals: list, notes: list)。请在你的目录里写 judge_<条件>_by_agent.py（定义 judge(text_a, text_b)）与 designer_note.json（简述你归纳的判据与理由）。