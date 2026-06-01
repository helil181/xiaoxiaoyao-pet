import json
import os
import random
import re
from collections import Counter
from datetime import datetime

import jieba

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HTML = os.path.join(
    "D:/电脑管家迁移文件/xwechat_files/Backup/data/聊天记录",
    "耀子大人(wxid_ho8pac35ipa322)/耀子大人.html"
)
OUTPUT_MESSAGES = os.path.join(BASE_DIR, "messages.json")
OUTPUT_STYLE = os.path.join(BASE_DIR, "style_profile.json")

STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "什么",
    "怎么", "吗", "啊", "哦", "嗯", "吧", "呢", "哈", "呀", "哪", "还",
    "被", "把", "让", "给", "对", "从", "与", "或", "但", "而", "且",
    "因为", "所以", "如果", "虽然", "然后", "可以", "这个", "那个", "这样",
    "那样", "只是", "就是", "还是", "已经", "可能", "应该", "觉得", "知道",
    "真的", "有点", "一下", "一些", "一点", "大概", "比较", "真的",
    "啊", "吧", "吗", "呢", "的", "了", "哈", "呀", "哦", "嗯",
}


def extract_messages_from_html(html_path):
    from extract_messages import extract_from_html
    return extract_from_html(html_path)


def analyze_style(messages):
    texts = [m["content"] for m in messages]
    print(f"分析 {len(texts)} 条消息...")

    lengths = [len(t) for t in texts]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    max_length = max(lengths) if lengths else 0
    min_length = min(lengths) if lengths else 0

    short_msg = sum(1 for l in lengths if l <= 10)
    medium_msg = sum(1 for l in lengths if 10 < l <= 30)
    long_msg = sum(1 for l in lengths if l > 30)

    all_words = []
    for t in texts:
        words = jieba.lcut(t)
        all_words.extend([w.strip() for w in words if len(w.strip()) >= 2 and w.strip() not in STOP_WORDS])

    word_freq = Counter(all_words)
    top_words = word_freq.most_common(30)
    common_phrases = [w for w, c in top_words if c >= max(3, len(texts) * 0.001)]

    emoji_pattern = re.compile(r'[\U0001F300-\U0001F9FF]|[\u2600-\u27BF]|[\uFE00-\uFEFF]')
    emoji_count = sum(1 for t in texts if emoji_pattern.search(t))
    emoji_freq = emoji_count / len(texts) if texts else 0

    excl_count = sum(t.count("！") + t.count("!") for t in texts)
    question_count = sum(t.count("？") + t.count("?") for t in texts)
    question_tendency = "喜欢反问" if question_count / len(texts) > 0.3 else ("偶尔提问" if question_count / len(texts) > 0.1 else "很少提问")

    ha_count = sum(1 for t in texts if "哈哈" in t or "哈哈哈" in t or "哈哈哈哈" in t)
    ha_freq = ha_count / len(texts) if texts else 0
    laugh_style = "经常笑（高频'哈哈哈'）" if ha_freq > 0.2 else ("偶尔笑" if ha_freq > 0.05 else "不太用'哈哈哈'")

    if avg_length <= 12:
        length_style = f"偏好短句，平均{avg_length:.0f}字/句，说话干脆利落"
    elif avg_length <= 25:
        length_style = f"中等句子，平均{avg_length:.0f}字/句，对话感自然"
    else:
        length_style = f"偏好长句，平均{avg_length:.0f}字/句，喜欢表达详细"

    excl_style = "经常用感叹号，语气热情" if excl_count / len(texts) > 0.3 else "感叹号使用适中"

    style_description = (
        f"你的说话风格：{length_style}。{laugh_style}。{question_tendency}。{excl_style}。"
    )

    if top_words:
        top_desc = "常用词：" + ", ".join(w for w, _ in top_words[:8])
        style_description += f"你在聊天中经常使用这些词：{top_desc}。"
    if "亲亲" in [w for w, _ in top_words[:5]]:
        style_description += "你喜欢用'亲亲'这样的亲昵表达。"
    if ha_freq > 0.15:
        style_description += "你很爱发'哈哈哈哈'，笑点低。"
    if "宝宝" in [w for w, _ in top_words[:10]] or "小宝" in [w for w, _ in top_words[:10]]:
        style_description += "你习惯叫对方'宝宝'或'小宝'。"

    if emoji_freq > 0.1:
        style_description += f"偶尔会用一些表情符号。"
    else:
        style_description += "很少用表情符号。"

    style_profile = {
        "style_description": style_description,
        "common_phrases": common_phrases[:12],
        "top_words": [(w, c) for w, c in top_words[:20]],
        "avg_length": round(avg_length, 1),
        "min_length": min_length,
        "max_length": max_length,
        "emoji_frequency": round(emoji_freq, 3),
        "total_messages": len(texts),
        "generated_at": datetime.now().isoformat(),
    }

    return style_profile


def build_knowledge_base(html_path=DEFAULT_HTML):
    print("=== 解析微信聊天记录 ===")
    messages = extract_messages_from_html(html_path)
    print()

    print("=== 分析说话风格 ===")
    style = analyze_style(messages)
    print()

    with open(OUTPUT_MESSAGES, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False)
    print(f"消息库已保存: {OUTPUT_MESSAGES} ({len(messages)} 条)")

    with open(OUTPUT_STYLE, "w", encoding="utf-8") as f:
        json.dump(style, f, ensure_ascii=False, indent=2)
    print(f"风格描述已保存: {OUTPUT_STYLE}")

    print()
    print("=== 风格分析报告 ===")
    print(f"总消息数: {style['total_messages']}")
    print(f"平均长度: {style['avg_length']} 字/句")
    print(f"最短/最长: {style['min_length']} / {style['max_length']} 字")
    print(f"常用词Top20: {', '.join(w for w, _ in style['top_words'][:10])}")
    print(f"口头禅: {', '.join(style['common_phrases'][:5])}")
    print()
    print(f"风格描述: {style['style_description']}")
    print()
    print("=== 完成！现在可以运行桌宠了 ===")
    return style


if __name__ == "__main__":
    import sys
    html_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HTML
    if not os.path.exists(html_path):
        print(f"找不到HTML文件: {html_path}")
        print("用法: python build_knowledge_base.py <HTML文件路径>")
        sys.exit(1)
    build_knowledge_base(html_path)