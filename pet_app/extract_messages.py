import json
import re
import os
from datetime import datetime

JSON_LINE_PATTERN = re.compile(r'^\{"type":\s*\d+,')


def extract_from_html(html_path, output_path=None):
    messages = []
    total_lines = 0
    json_lines = 0
    your_text_lines = 0

    with open(html_path, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            stripped = line.strip()
            if not JSON_LINE_PATTERN.match(stripped):
                continue
            json_lines += 1
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                try:
                    obj = json.loads(stripped.rstrip(","))
                except json.JSONDecodeError:
                    continue
            if obj.get("type") != 1:
                continue
            if obj.get("is_send") != 1:
                continue
            text = obj.get("text", "")
            if not text or not text.strip():
                continue
            ts = obj.get("timestamp", 0)
            dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            messages.append({"content": text, "time": dt})
            your_text_lines += 1

    print(f"总行数: {total_lines}")
    print(f"JSON消息行: {json_lines}")
    print(f"你发送的文字消息: {your_text_lines}")

    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        print(f"已保存到: {output_path}")

    return messages


if __name__ == "__main__":
    import sys
    html_file = sys.argv[1] if len(sys.argv) > 1 else None
    out_file = sys.argv[2] if len(sys.argv) > 2 else "pet_app/messages.json"
    if not html_file:
        html_file = os.path.join(
            "D:/电脑管家迁移文件/xwechat_files/Backup/data/聊天记录",
            "耀子大人(wxid_ho8pac35ipa322)/耀子大人.html"
        )
    if not os.path.exists(html_file):
        print(f"找不到HTML文件: {html_file}")
        print("用法: python extract_messages.py <HTML文件路径> [输出JSON路径]")
        sys.exit(1)
    extract_from_html(html_file, out_file)