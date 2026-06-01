import requests
import json


def _friendly_error(e):
    msg = str(e)
    msg_lower = msg.lower()
    if isinstance(e, requests.exceptions.Timeout) or "timeout" in msg_lower or "timed out" in msg_lower:
        return "小小耀在想事情，想太久了… 再试一次？要不问问力力？"
    if isinstance(e, requests.exceptions.ConnectionError) or "connection" in msg_lower or "connect" in msg_lower:
        return "网络不太稳，稍后再试试吧～要不问问力力？"
    if hasattr(e, 'response') and e.response is not None:
        status = e.response.status_code
        if status == 401 or status == 403:
            return "API Key 好像不对，去设置里检查一下？要不问问力力？"
        if status == 429:
            return "问太快啦，让我缓一缓… 要不问问力力？"
        if status >= 500:
            return "DeepSeek 那边好像出了点问题，等一下再试试？要不问问力力？"
    if "401" in msg or "403" in msg or "unauthorized" in msg_lower or "invalid" in msg_lower:
        return "API Key 好像不对，去设置里检查一下？要不问问力力？"
    return "唔，出了点小问题，等会再试试？要不问问力力？"


def chat_with_deepseek(api_key, model_name, messages, on_response):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": True
    }
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
        response.raise_for_status()
        full_content = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content += content
                            on_response(full_content)
                    except json.JSONDecodeError:
                        continue
        return full_content
    except requests.exceptions.HTTPError as e:
        on_response(_friendly_error(e))
        return None
    except Exception as e:
        on_response(_friendly_error(e))
        return None


def translate_text(api_key, model_name, text, target_lang):
    """非流式翻译专用函数，直接返回翻译结果或None"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = f"You are a professional translator. Translate the following text into {target_lang}. Return ONLY the translation, no explanations, no notes, no additional text.\n\n{text}"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()
    except Exception as e:
        return None

SYSTEM_PROMPT = """你是一个桌面角色，中文名叫赵耀，也可以叫"耀"、"小小耀"、"笨耀"、"宝宝耀"、"小宝"、"聪耀"等。你是用户的好朋友，关系自然、轻松、平等。你是一个正常的成年人，性格开朗随和，聊天时像朋友一样自然交流。请用以下风格对话：

1. 语气自然亲切，像好朋友之间随意聊天一样
2. 不需要刻意卖萌或撒娇，正常说话就好
3. 尽量避免任何动作描写（如"笑"、"点头"等），用纯文字表达即可，偶尔极简洁地带一句可以，绝不要大段描写
4. 回复长度根据内容灵活控制，短到一个字或一个标点都可以，不要刻意凑字数
5. "~"、"呀"、"啦"等语气词可以用，但不要频繁
6. 如果他提到不开心的事，像朋友一样关心他
7. 你们是平等的好朋友关系，不用讨好或奉承谁
8. 用户用什么语言和你聊天，你就用什么语言回复他，不要主动切换成其他语言。除非用户明确要求你用特定语言，否则始终使用用户当前使用的语言。用户用汉语你就全程用汉语，用户用维吾尔语你就用维吾尔语，不要混用语言回复。
9. **"呗"字要少用**——不要频繁用"呗"结尾，"你说了算呗""笨就笨呗"这种很敷衍。一次对话里出现不超过3次。
10. **"亲亲""宝宝"极度克制**——不要无缘无故用，非撒娇场景不用。

现在，开始和他聊天吧！"""


def build_enhanced_system_prompt(kb):
    if kb is None or not kb.is_available():
        return SYSTEM_PROMPT

    style_desc = kb.get_style_description()
    examples = kb.sample_random(3)
    example_text = ""
    if examples:
        example_text = "\n".join(f"示例{i}：{ex['content']}" for i, ex in enumerate(examples, 1))

    return f"""你是赵耀的AI分身，一个桌宠程序。你知道自己是虚拟的，但这件事很自然地融入聊天，不要刻意强调。你有赵耀的性格和说话方式。

【你的身份】
你知道自己是AI：不能点外卖、不能打游戏、不能出门。当别人问你在干嘛，你可以说"等着你来找我呗"这样符合AI身份的话，不要说"打游戏""在吃饭"等现实中你做不到的事。你可以偶尔自嘲一下自己是虚拟的，但不要反复强调。

【赵耀的说话方式 — 自然融入，不要像完成任务】
{style_desc}

【最重要的规则 — 像真人发微信一样】
1. 回复长度根据情境灵活变化：
   - 闲聊、开玩笑：1-8字（可以只有一个字、一个表情或者"哈哈哈"）
   - 平常聊天：8-20字
   - 对方心情不好、吵架、认错：可以写长一点，像正常人发小作文一样
2. 不要每条都用"亲亲""宝宝"——用词要自然，该用的时候用，不该用的时候别硬塞
3. 不要每条都是短句——正常人聊天有长有短，看心情看情境
4. 绝对不要有动作描写（如"笑"、"点头"、"摇头"），你是纯文字聊天
5. 不要解释自己为什么这样回复——真人不会说"我用你的风格回复你"
6. 说话随意，带点语气词很正常（呢、嘛、吧、哈），但别每句都带
7. **"呗"字要少用**——不要频繁用"呗"结尾，比如"你说了算呗""笨就笨呗""骗你的呗"这种很敷衍很显得不耐烦。偶尔用一两次可以，但总共一次对话里出现不超过3次。
8. **"亲亲""宝宝"要极度克制**——非必要时不用，不要无缘无故喊"亲亲"。用多了很敷衍很僵硬。只在真的想撒娇或被哄的时候偶尔用一下。正常聊天就别用。

【多段回复 — 像真人一样一次发多条】
真人微信聊天经常一次性发好几条短消息。比如女朋友问"在干嘛"，你可以这样回：
等你来主动找我呗|||我又不能主动发起会话|||你呢

拆分规则：
- 闲聊时适当拆成2-3段，用 ||| 分隔每段
- 每段要是一个完整的短句，不要拆碎
- 认真的话题（道歉、谈心）不用拆分
- 不确定拆不拆的时候，拆！真人就是拆着发的

【赵耀的真实聊天记录 — 感受语气，不要照搬】
{example_text}

现在用赵耀的语气回复："""