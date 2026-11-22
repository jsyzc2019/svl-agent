任务：文本对二分类。
输入是一批文本对，每对包含 text_a 与 text_b 两段文字。请观察数据，归纳一个确定性的二分类函数 judge(text_a, text_b)，把每一对文本分成两类。
（本任务不指定两类的业务含义，请仅依据文本本身的结构归纳。）

要求：纯字符串/正则实现，确定性；不使用随机数、时间、样本 id、外部文件或样本文本硬编码。
返回 (decision: bool, signals: list, notes: list)。请在你的目录里写 judge_<条件>_by_agent.py（定义 judge(text_a, text_b)）与 designer_note.json（简述你归纳的判据与理由）。