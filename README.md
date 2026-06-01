# 🐱 小小耀桌宠

一个可爱的 Windows 桌面宠物应用，基于 PySide6 构建。角色「小小耀」会在你的桌面上走动、跑步、跳舞，还会和你聊天！

## ✨ 功能特点

- **生动动画** — 六种动作：待机、走路、跑步、跳舞、打招呼、无语
- **AI 聊天** — 接入 DeepSeek API，小小耀会用独特的性格和你对话
- **系统托盘** — 最小化到托盘，不打扰你的工作
- **拖动交互** — 可以随意拖动小小耀到桌面任意位置
- **互动彩蛋** — 双击小小耀会有反应，连续点击太多会生气跑掉 😂
- **云端同步** — 支持 Supabase 云端消息同步（可选）
- **知识库** — 可以注入聊天记录让小小耀学习说话风格
- **自动启动** — 支持开机自启
- **多语言** — 支持汉语和维吾尔语双语问候

## 🛠 技术栈

- **Python 3.9+**
- **PySide6** — Qt for Python 桌面框架
- **DeepSeek API** — AI 对话引擎
- **Supabase** — 云端数据同步（可选）
- **Pillow** — 图像处理
- **jieba** — 中文分词

## 📦 安装与运行

### 1. 克隆仓库

```bash
git clone https://github.com/你的用户名/小小耀桌宠.git
cd 小小耀桌宠/pet_app
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

复制配置模板并填入你的 DeepSeek API Key：

```bash
copy config.example.json config.json
```

然后编辑 `config.json`，填入你的 API Key：

```json
{
  "api_key": "sk-你的DeepSeek-API-Key",
  "model_name": "deepseek-v4-flash",
  "always_on_top": true,
  "auto_start": false,
  "pet_size": 300
}
```

> 🔑 获取 DeepSeek API Key：访问 [platform.deepseek.com](https://platform.deepseek.com) 注册并获取。

### 4. 运行

```bash
python main.py
```

或者双击运行 `main.pyw`（无控制台窗口）。

## 🎮 使用说明

| 操作 | 效果 |
|------|------|
| 拖拽角色 | 移动小小耀到任意位置 |
| 双击角色 | 触发随机的打招呼/跳舞动作 |
| 连续双击6次 | 小小耀会无语 😑 |
| 继续连续点 | 小小耀会生气跑掉 🏃‍♂️ |
| 右键点击 | 打开菜单（聊天、记录、设置、退出） |
| 系统托盘右键 | 显示/隐藏、打开聊天、设置、退出 |

## 📁 项目结构

```
pet_app/
├── main.py              # 主入口
├── main.pyw             # 无控制台入口
├── pet_window.py        # 桌宠主窗口
├── character.py         # 角色动画精灵
├── chat_window.py       # 聊天窗口
├── chat_history.py      # 聊天记录
├── settings_window.py   # 设置窗口
├── ai_chat.py           # DeepSeek API 调用
├── cloud_db.py          # Supabase 云同步
├── knowledge_base.py    # 知识库（说话风格学习）
├── interactions.py      # 互动表情与对话
├── theme.py             # UI 主题
├── app_paths.py         # 路径工具
├── auto_start.py        # 开机自启
├── sprites/             # 角色精灵动画帧
│   ├── idle_frames/     # 待机
│   ├── walk_frames/     # 走路
│   ├── run_frames/      # 跑步
│   ├── dance_frames/    # 跳舞
│   ├── greet_frames/    # 打招呼
│   └── speechless_frames/ # 无语
├── assets/              # 头像等资源
├── config.example.json  # 配置模板
└── requirements.txt     # 依赖列表
```

## 🚧 构建 EXE

使用 PyInstaller 打包为独立 exe：

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --add-data "sprites;sprites" --add-data "assets;assets" main.py
```

## 📝 许可证

MIT License

## ❤️ 致谢

这个小程序是送给女朋友的礼物，希望她看到桌面上有个可爱的小家伙能开心一点～

也希望能给其他想给喜欢的人做小礼物的人一些灵感 💡

<small>跨越山海相遇，却被山海阻隔。故事留在了这里，愿它曾照亮过彼此。</small>

<small>"مىنى كەچۈرۈڭ"</small>