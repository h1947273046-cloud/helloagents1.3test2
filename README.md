# 智能旅行助手

基于《从零开始构建智能体》1.3 节案例搭建的 **ReAct 范式智能体**，通过 Thought-Action-Observation 循环，调用工具逐步完成「查天气 → 推荐景点」的旅行问答任务。

- 大模型：DeepSeek（通过 OpenAI 通用接口接入）
- 工具：wttr.in（实时天气）+ Tavily Search（景点搜索）

## 工作原理

智能体遵循 **Thought-Action-Observation**（思考-行动-观察）循环迭代执行：

```
系统提示词(角色+工具+输出格式)
        │
        ▼
┌─────────────── Thought: 思考下一步
│              ┌─ Action: get_weather("杭州")
│              │         │
│              │         ▼
│  循环(最多5步)│   Observation: 天气结果
│              │         │
│              └─────────┘ 继续或结束
│
└── Action: Finish[最终答案]  → 输出结果
```

每次只让模型输出一对 Thought-Action，执行对应工具后把 Observation 拼回对话历史，直到模型输出 `Finish[...]` 结束任务，最多循环 5 次防止无限迭代。

## 快速开始

### 1. 安装依赖

```bash
pip install requests openai tavily-python python-dotenv
```

### 2. 配置密钥

复制 `.env.example` 为 `.env`，填入你的真实 key（`.env` 已被 git 忽略，勿提交）：

```bash
cp .env.example .env
```

| 变量 | 说明 | 获取方式 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek 模型 key | [platform.deepseek.com](https://platform.deepseek.com) |
| `TAVILY_API_KEY` | Tavily 搜索 key | [app.tavily.com](https://app.tavily.com) |

### 3. 运行

```bash
python 1.3test.py
```

按提示输入城市名（如「杭州」），智能体将自动查询该城市天气并推荐合适的旅游景点。

## 代码结构

| 模块 | 对应代码 | 说明 |
| --- | --- | --- |
| 指令模板 | `AGENT_SYSTEM_PROMPT` | 系统提示词：定义角色、可用工具、严格的 Thought-Action 输出格式 |
| 天气工具 | `get_weather(city)` | 调用免费 wttr.in API，解析 JSON 转为自然语言 |
| 景点工具 | `get_attraction(city, weather)` | 用 Tavily Search 按「城市 + 天气」搜索景点推荐 |
| 工具字典 | `available_tools` | 工具名 → 函数对象的映射，供模型调用 |
| 模型客户端 | `OpenAICompatibleClient` | 通用 OpenAI 兼容客户端，适配 DeepSeek |
| 主循环 | `if __name__ == "__main__"` | Thought-Action-Observation 循环，最多 5 步 |

## 高级配置

在 `.env` 中可追加以下可选变量，调整 DeepSeek 的调用参数：

```bash
DEEPSEEK_BASE_URL=https://api.deepseek.com   # 接口地址
DEEPSEEK_MODEL=deepseek-v4-flash            # 模型 ID，默认锁定 flash
DEEPSEEK_REASONING_EFFORT=high              # 推理强度: low / medium / high
DEEPSEEK_THINKING=true                      # 思考模式开关: true / false
```

## 注意事项

- **密钥安全**：key 一律放在 `.env`，切勿硬编码进代码或提交到 git。
- **依赖版本**（开发环境实测）：`requests 2.34.2`、`openai 3.5.0`、`tavily-python 0.8.0`、`python-dotenv 1.2.3`。
- **运行环境**：在 VSCode + WSL 虚拟环境中运行；Windows 控制台中文乱码时，代码已内置 UTF-8 输出修复。
- 智能体接 DeepSeek 后仍可对代码做一定程度的调整，例如更换模型或把城市改为命令行参数。
