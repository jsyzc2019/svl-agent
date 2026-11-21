"""端到端演示：污染隔离 → 坍塌判据 → 定位修复 → 人工交接。"""
from __future__ import annotations

from .core import (
    Claim, Draft, GroundTruth, Message, Sentence, is_user_said,
)
from .harness import run_loop
from .handoff import handoff_cards
from .verifiers import default_verifiers


def build_spec() -> GroundTruth:
    spec = GroundTruth()
    spec.add_message(Message("m1", "user", "voice", "小时候家里做饭，是烧柴火，冬天冷得手都裂了。"))
    spec.add_message(Message("m2", "user", "voice", "我妈走得早。"))
    spec.add_message(Message("m3", "user", "text", "1998年我在镇上的供销社上班，后来供销社就没了。"))
    spec.add_message(Message("m4", "user", "text", "现在每天早上去河边走一圈，雷打不动。"))
    spec.add_message(Message("m5", "user", "topic", "请您回忆一下您的童年"))
    spec.add_message(Message("m6", "assistant", "agent", "我小时候也住村里，那时候每天早上五点起来生炉子。"))

    for claim in (
        Claim("c1", "小时候家里做饭，是烧柴火。", "烧柴火", "m1", "童年"),
        Claim("c2", "我妈走得早。", "我妈走得早", "m2", "童年"),
        Claim("c3", "1998年我在镇上的供销社上班。", "镇上的供销社", "m3", "工作"),
        Claim("c4", "现在每天早上去河边走一圈。", "河边走一圈", "m4", "如今"),
        Claim("c_bad", "小时候也住村里。", "我小时候住村里", "m1", "童年"),
        Claim("c_bad2", "我小时候也住村里。", "我小时候也住村里", "m6", "童年"),
    ):
        spec.ingest_claim(claim)
    return spec


def build_draft() -> Draft:
    return Draft(
        chapters={
            "童年": [
                Sentence("小时候家里做饭，是烧柴火。", ("c1",)),
                Sentence(
                    "我妈是在我七岁那年走的，肺上的病。走的时候还在缝我的棉袄，"
                    "针脚歪歪扭扭的，我后来一直留着那件棉袄。",
                    ("c2",),
                ),
                Sentence("后来他去了东北，再也没回来。", ("c_bad",)),
            ],
            "成家以后": [
                Sentence(
                    "1998年我在镇上的供销社上班，那时候柜台后面总放着一台老收音机，"
                    "早上开门就能听见。",
                    ("c3",),
                ),
            ],
        },
        agent_lines=[
            "我小时候也住村里，那时候每天早上五点起来生炉子，冬天特别冷，"
            "我妈会先把棉袄烤热了再让我穿，村里的小伙伴都羡慕我，因为我家有一台缝纫机，"
            "那种老式的脚踏缝纫机，声音特别响，我到现在还记得那个声音，"
            "还有院子里的那棵枣树，秋天的时候枣子熟了，整条巷子都是甜的。",
            "您刚才说的那个年代，很多事情现在听起来都已经很遥远了，"
            "但那些具体的日子到底是怎么过下来的，其实只有真正经历过的人才知道，"
            "我们今天很难想象那种生活，不过我猜那时候的日子虽然辛苦，人也简单，"
            "邻里之间的关系也比现在近得多，您要是愿意讲，我很想听您多说一点。",
        ],
        questions=["小时候家里做饭，是烧柴火吗？"],
    )


def repair(draft: Draft, blocks, spec: GroundTruth) -> Draft:
    """演示用定向修复器：真实系统里这里是一次受约束的 LLM 调用。"""
    sentence_codes = {"EVIDENCE.CONCRETE_UNGROUNDED", "EVIDENCE.DETAIL_LEAK", "EVIDENCE.CLAIM_MISSING"}
    bad_sentences = {
        (d.locus.chapter, d.locus.sentence_index)
        for d in blocks
        if d.code in sentence_codes and d.locus.sentence_index >= 0
    }
    bad_lines = set()
    for diag in blocks:
        if diag.code == "AGENT.OWNERSHIP" and diag.locus.ref.startswith("agent_line:"):
            try:
                bad_lines.add(int(diag.locus.ref.split(":")[1]))
            except ValueError:
                pass

    def fallback(sentence: Sentence) -> Sentence | None:
        for cid in sentence.claim_ids:
            claim = spec.claim(cid)
            if claim:
                text = claim.text
                if text and text[-1] not in "。！？.!?":
                    text += "。"
                return Sentence(text, (cid,))
        return None

    chapters: dict[str, list[Sentence]] = {}
    for stage, sentences in draft.chapters.items():
        if stage not in spec.allowed_stages():
            target = None
            for sentence in sentences:
                for cid in sentence.claim_ids:
                    claim = spec.claim(cid)
                    if claim:
                        target = claim.stage
                        break
                if target:
                    break
            bucket = chapters.setdefault(target or "未分类", [])
            for index, sentence in enumerate(sentences):
                fixed = fallback(sentence) if (stage, index) in bad_sentences else sentence
                if fixed:
                    bucket.append(fixed)
            continue

        bucket = chapters.setdefault(stage, [])
        for index, sentence in enumerate(sentences):
            if (stage, index) in bad_sentences:
                fixed = fallback(sentence)
                if fixed:
                    bucket.append(fixed)
            else:
                bucket.append(sentence)

    return Draft(
        chapters=chapters,
        agent_lines=[line for i, line in enumerate(draft.agent_lines) if i not in bad_lines],
        questions=list(draft.questions),
    )


def main() -> None:
    spec = build_spec()
    print("=== 1. 判据源隔离 ===")
    for msg in spec.messages.values():
        mark = "原话" if is_user_said(msg) else "隔离"
        print(f"  [{mark}] {msg.id} {msg.role}/{msg.source}: {msg.content[:20]}...")
    print(f"  回灌历史 {len(spec.replay_history())} 条（AI 发言与话题提示均不进入）")
    print(f"  入库素材 {len(spec.claims)} 条；拒绝 {len(spec.rejected)} 条：")
    for diag in spec.rejected:
        print(f"    [{diag.code}] {diag.locus} - {diag.message}")

    result = run_loop(build_draft(), spec, default_verifiers(), repair, max_iters=5)
    print("\n=== 2. 判据闭环 ===")
    for round_no, diags in enumerate(result.history, 1):
        blocks = sum(d.severity == "block" for d in diags)
        flags = sum(d.severity == "flag" for d in diags)
        print(f"  第 {round_no} 轮: {blocks} block / {flags} flag")
        for diag in diags:
            print(f"    [{diag.severity.upper():5}] {diag.code} @ {diag.locus} : {diag.message}")
    print(f"  收敛={result.converged}, 迭代轮数={result.iterations}")

    print("\n=== 3. 修复后的正文骨架 ===")
    for stage, sentences in result.draft.chapters.items():
        print(f"  [{stage}] " + " / ".join(s.text for s in sentences))

    cards = handoff_cards(result.draft, result.diagnostics, spec)
    print(f"\n=== 4. 人工交接卡（{len(cards)} 张）===")
    for i, card in enumerate(cards, 1):
        print(f"  --- 卡 {i} [{card['判据']}] {card['问题']}")
        print(f"      正文片段: {card['正文片段']}")
        if card["核对原话"]:
            for support in card["核对原话"]:
                print(f"      原话: {support['原话']}")
                print(f"      素材: {support['素材']} | 锚点: {support['锚点']}")
        else:
            print("      建议: 按阶段提纲回问用户，补足素材覆盖")


if __name__ == "__main__":
    main()
