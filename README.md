# agent-on-jetson

> 把上一篇的**最小 AI Agent** 搬到 **Jetson（Orin）** 上跑：先在 x86 跑通，再部署到边缘。

本质不变：**调用 API 问模型 → 执行工具 → 回喂结果**。到边缘，变的只是**运行环境**和**性能约束**。

## 两种跑法

### A. 边缘执行 + 云端大脑（最简单，先用它跑通）
Agent 跑在 Jetson 上，模型仍在云端（DeepSeek）：

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY="sk-..."
python agent.py "看一下 /etc/hostname"
```

### B. 本地模型（离线 / 低延迟 / 隐私）
用 **llama.cpp** 在 Jetson 上跑本地 LLM，再让 Agent 指过去（OpenAI 兼容）：

```bash
# 1) 编译 llama.cpp（aarch64 + CUDA；Orin 的算力是 8.7）
git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87
cmake --build build --config Release -j

# 2) 起本地 OpenAI 兼容服务（示例用小模型，按需换）
./build/bin/llama-server -m models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
    -c 2048 --host 0.0.0.0 --port 8080

# 3) Agent 指向本地（同一套循环，零改动）
export LLM_BASE_URL="http://localhost:8080/v1"
export LLM_MODEL="local"
python agent.py "看一下 /proc/meminfo 还剩多少内存"
```

## 开机自启（systemd）

见 [`agent.service`](./agent.service)：

```bash
sudo cp agent.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now agent
```

## 注意（要点，具体以你的环境为准）

- **架构**：Jetson 是 **aarch64**，部分 pip 包要能在设备上编译；先确保 `python3` + `pip` 可用。
- **CUDA 算力**：Orin = **8.7**（`-DCMAKE_CUDA_ARCHITECTURES=87`），写错编不过或跑不了 GPU。
- **内存**：Jetson 是**统一内存**，`llama-server -c` 的上下文别开太大，否则 OOM。
- **功耗/散热**：`sudo nvpmodel -m 0`（最大性能）/ 用 `tegrastats` 看温度与功耗。
- **日志**：systemd 下用 `journalctl -u agent -f` 排错。

## 相关

- 文章：<https://embedai.com.cn/posts/deploy-agent-on-jetson>
- 姊妹仓库（Agent 主循环）：<https://github.com/zishuowang696/agent-from-scratch>
- MCP：<https://github.com/zishuowang696/mcp-demo>

## 许可

MIT
