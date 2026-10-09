"""最小 AI Agent —— 同一套代码，可跑在 x86，也可跑在 Jetson。

本质不变：调用 API 问模型 -> 执行工具 -> 回喂结果。
模型可换：
  - 云端：DeepSeek（默认，OpenAI 兼容）
  - 本地：Jetson 上用 llama.cpp 起的 OpenAI 兼容服务（LLM_BASE_URL=http://localhost:8080/v1）
"""
import json
import os
import subprocess

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-local"),  # 本地服务不校验，占位即可
)
MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "cat",
            "description": "读取一个文件的全部内容（例如 /etc/hostname、/proc/meminfo、/sys/class/thermal/thermal_zone0/temp）",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件路径"}},
                "required": ["path"],
            },
        },
    }
]


def run_tool(name: str, args: dict) -> str:
    if name == "cat":
        out = subprocess.run(["cat", args["path"]], capture_output=True, text=True)
        return out.stdout or out.stderr
    return f"unknown tool: {name}"


def agent(user_input: str) -> str:
    messages = [{"role": "user", "content": user_input}]
    while True:
        reply = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = reply.choices[0].message
        messages.append(msg)
        if not msg.tool_calls:
            return msg.content
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = run_tool(call.function.name, args)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "读一下 /etc/hostname 里的内容"
    print(agent(q))
