# -*- coding: utf-8 -*-
"""康波交接期历史类比文章的核查结果数据（真实核查，非合成）。"""
import json

ARTICLE_NOTE = ("用户提供的文章《康波交接期的产业和市场推演：对照1975-1982发生的一切，"
                "2023-2029正在发生的是又一个循环》，核心方法为历史类比推演："
                "把1975-1982逐段对应到2023-2026，并据此预测2027-2029。")

RESULT = {
 "object": "用户提供的文章《康波交接期的产业和市场推演》",
 "date": "2026-11-21",
 "scope": "依第29-31节纪律: 不据文风判作者身份; 核事实真伪 + 推论有效性 + 推理方法可靠性",
 "primary_sources": [
  "摩根士丹利官网/SEC/Anthropic官方S-1 (当下事件)",
  "康德拉季耶夫长波 Wikiwand/百度百科/东方财富宏观研报 (框架学术地位)",
  "Yardeni《Predicting the Markets》/雪球《长熊的尽头》 (1982历史细节)",
  "MCP官方博客/Anthropic公告 (MCP数据)",
 ],
 "fact_checks": [
  {"claim": "1982年8月12日标普500跌至102.42, 8月13日墨西哥违约, 随后18年大牛市", "verdict": "属实(细节微差)",
   "evidence": "行情数据确认8月12日标普收盘102.42; 墨西哥财长8月12日宣布无力偿债、美联储8月13日降息(文章把违约日写成8月13日, 差一天); 道指从777涨到2000年1月11723, +1408.9%, '18年牛市'属实", "confidence": "high"},
  {"claim": "1981年基金利率20%/10年期国债15.84%/失业率10.8%; IBM PC 1981-8-12发布", "verdict": "属实",
   "evidence": "多来源一致: 联邦基金利率1981年6月冲到20%左右, 失业率10.8%为大萧条以来最高, IBM PC于1981年8月12日发布并确立Wintel标准", "confidence": "high"},
  {"claim": "Altair 8800 1975年1月登《大众电子》封面 / VisiCalc / Oracle首套数据库 / Apple-Genentech 1976成立", "verdict": "属实(科技史常识)",
   "evidence": "均为计算机史标准事实, 与科技史博物馆编年一致; 文章此处是准确的史实叙述", "confidence": "high"},
  {"claim": "2026四大云厂资本开支7250亿美元、同比+77%", "verdict": "属实",
   "evidence": "证券时报/工商时报/中国工信新闻网多源确认: 亚马逊微软谷歌Meta 2026合计资本开支约7250亿美元, 较2025年4100亿增长77%", "confidence": "high"},
  {"claim": "Claude Code年化收入25亿美元", "verdict": "属实",
   "evidence": "长桥证券报道: Claude Code发布6个月创造10亿美元年化收入, 到2026年2月突破25亿美元", "confidence": "high"},
  {"claim": "David Cahn测算AI年收入需6000亿美元才合理", "verdict": "属实(且门槛已上调)",
   "evidence": "红杉David Cahn 2024年《AI's $600B Question》确提出6000亿门槛; 但2026年7月已上调到3万亿美元。文章用的是2024年旧数字, 真实缺口比文中更大", "confidence": "high"},
  {"claim": "MCP协议月下载9700万次、2025年12月捐赠Linux基金会", "verdict": "属实",
   "evidence": "MCP官方博客确认: 2025-12-09捐赠给Linux基金会旗下Agentic AI Foundation, 月SDK下载超9700万次, 1万个活跃服务器", "confidence": "high"},
  {"claim": "OpenAI 2026年6月秘密提交上市申请; Anthropic 11月定价上市(代码ANT)", "verdict": "属实",
   "evidence": "SEC/TechCrunch确认: OpenAI 2026-6-8提交机密S-1; Anthropic 2026-11-10设定价格区间70-78美元, 代码ANT, 预计11月19日交易", "confidence": "high"},
  {"claim": "ChatGPT十二亿周活 / OpenAI年化收入500亿美元", "verdict": "数字存疑(口径差异)",
   "evidence": "ipobonanza披露ChatGPT约9亿周活(2026), 与文中12亿有出入; OpenAI年化收入公开口径250亿-500亿不等, 500亿属乐观上限。数字方向对但偏高", "confidence": "medium"},
  {"claim": "(框架地基)我们正处于康波交接的特殊时期, 有极强规律性", "verdict": "框架有争议",
   "evidence": "Wikiwand: 新古典经济学家多半不承认长波理论, 即使认可者对流起/年代/划分也无定论, 批评者认为是'强加于大量统计资料上的概念'; 东方财富宏观研报: 对1970年后划分争论极大, '康波级别上的定位偏差足以葬送投资生命'; 学界对第五轮尾声/第六轮起点无共识", "confidence": "high"},
  {"claim": "(推理方法)1975-1982与2023-2029逐年对应, 据此预测2027出清/2028转折/2029洗盘", "verdict": "方法不可靠",
   "evidence": "n=1历史类比: 用单一历史片段做模板; 13个'对应点'是从无尽历史细节里事后挑选能配对的(confirmation bias); 预测大量使用'大概率/可能/候选/可以推演'等模糊限定词, 具体数字+模糊措辞=不可证伪; 从一轮成功转折归纳'四条规律'忽略大量未走通的历史线(幸存者偏差)", "confidence": "high"},
  {"claim": "(操作建议)出清是建仓窗口/买点在恐慌里/提前列被错杀清单, 且无风险免责", "verdict": "隐性投资建议无免责",
   "evidence": "文章给出具体择时操作建议(建仓窗口/买点/被错杀清单/盯金融条件), 但全文无任何'不构成投资建议'提示, 与大摩研报明确免责形成对照", "confidence": "high"},
 ],
 "core_finding": "事实层几乎全部属实(历史+当下数据均可核验), 这是它与'伪名言鸡汤文'的本质区别。但事实核查这一层'通过'后, 误导藏在下一层: 地基(康波)本身学界无共识却被当成既定规律; 用n=1历史片段逐年硬套当下并预测未来; 13个对应点是事后挑选; 预测用模糊限定词不可证伪。当事实全真时, 危险不在素材, 而在把素材组织成结论的推理方法。",
 "honest_boundaries": [
  "不据文风断言作者是AI还是人——第29节已证浅层文风判别抓的是文风artifact",
  "历史类比并非全无价值: 作为启发式思考(what to look at)可以提供观察清单; 问题在于把它当作确定性预测工具(as what will happen)",
  "康波框架争议是学界主流批评的记录(Wikiwand/百度百科/东方财富研报), 不等于否定长波理论; 我的判断是'地基不稳、不宜作为确定性预测依据', 不是'康波一定是错的'",
  "对未来的具体预测(2027-2029)无法现在证伪, 我的批评针对推理方法的可靠性(不可证伪性、n=1、事后选择), 不是断言预测一定不准",
 ],
 "three_layer_conclusion": {
  "can_say": "历史事实和当下数据大多可核验且属实; 文中对产业趋势(算力投入、IPO、MCP标准、资本开支强度)的描述与公开信息一致——作者确实做了功课, 不是编造。",
  "cannot_say": "不能因为事实都对就接受'2027出清/2028转折/2029洗盘'的预测并据此操作。康波地基无共识; 方法是n=1历史类比; 逐年对应是事后挑选; 预测用模糊限定词不可证伪; 还给了无免责的具体择时建议。",
  "method_reflection": "第30节'事实真实性≠作者身份', 第31节'事实真实性≠推论有效性'(主体错位), 这一节再进一层: '事实真实性≠推理方法可靠性'。当前两层核查都通过后, 还剩第三道关——把真素材组织成结论的那套推理本身是否站得住。历史类比是最古老也最危险的一种: 它用真实的过去, 给不确定的未来穿上确定性的外衣。",
 }
}

if __name__ == "__main__":
    from collections import Counter
    open("/workspace/kondratieff_input.txt", "w", encoding="utf-8").write(ARTICLE_NOTE)
    json.dump(RESULT, open("/workspace/kondratieff_factcheck.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("saved kondratieff_factcheck.json")
    print(Counter(x["verdict"] for x in RESULT["fact_checks"]))
