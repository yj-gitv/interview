# 面试助手 (Interview Assistant)

本地运行的 Web 面试辅助工具，覆盖从简历筛选到面试总结的全流程。

## 环境要求

- **Python** 3.11+
- **Node.js** 18+
- **macOS**（音频捕获依赖 macOS 音频系统）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yj-gitv/interview.git
cd interview
```

### 2. 后端设置

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

创建 `.env` 配置文件：

```bash
cat > .env << 'EOF'
INTERVIEW_OPENAI_API_KEY=你的API_KEY
INTERVIEW_OPENAI_BASE_URL=https://api.openai.com/v1
INTERVIEW_OPENAI_MODEL_FAST=gpt-4o-mini
INTERVIEW_OPENAI_MODEL_STRONG=gpt-4o
INTERVIEW_AUDIO_DEVICE_NAME=MacBook Pro麦克风
EOF
```

> `INTERVIEW_AUDIO_DEVICE_NAME` 需要改成你设备上实际的音频输入设备名。  
> 运行以下命令查看可用设备：
> ```bash
> python -c "import sounddevice as sd; [print(f'[{i}] {d[\"name\"]}') for i,d in enumerate(sd.query_devices()) if d['max_input_channels']>0]"
> ```

启动后端：

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. 前端设置

```bash
cd frontend
npm install
npm run dev
```

### 4. 打开浏览器

访问 http://localhost:5173

## 使用流程

1. **创建岗位** — 填写岗位名称和 JD
2. **上传简历** — 支持 PDF / Word
3. **匹配评分** — AI 多维度评分（岗位经验、行业背景、核心能力、成长潜力）
4. **生成问题** — 自动生成结构化面试问题清单
5. **开始面试** — 三栏实时辅助界面（转录 / 问题跟踪 / 追问建议）
6. **生成总结** — 结构化面试报告 + PDF 导出

## 音频录音配置（可选）

面试助手支持两种输入模式：
- **手动输入** — 无需音频设备，直接在界面输入文字
- **实时录音** — 需要音频输入设备

### 使用 BlackHole 捕获腾讯会议音频

```bash
brew install blackhole-2ch
```

在「音频 MIDI 设置」中创建多输出设备（扬声器 + BlackHole），设为系统默认输出。然后在 `.env` 中设置：

```
INTERVIEW_AUDIO_DEVICE_NAME=BlackHole 2ch
```

## 运行测试

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

## 技术栈

| 层面 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SQLAlchemy + SQLite |
| 前端 | React + TypeScript + Vite + Tailwind CSS 4 |
| 语音转录 | faster-whisper（本地） |
| LLM | OpenAI 兼容 API |
| 实时通信 | WebSocket |
| PDF 导出 | fpdf2 |
