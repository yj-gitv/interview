# 面试助手 (Interview Assistant)

本地运行的 Web 面试辅助工具，覆盖从简历筛选到面试总结的全流程。

## 快速开始（Docker）

最简单的方式，只需要安装 [Docker](https://www.docker.com/products/docker-desktop/)。

```bash
git clone https://github.com/yj-gitv/interview.git
cd interview
cp .env.example .env
# 编辑 .env，填入你的 LLM API Key
docker compose up --build
```

打开浏览器访问 **http://localhost:3000**

> 修改 `.env` 中的 `APP_PORT` 可以换端口。

## 手动部署（开发模式）

### 环境要求

- **Python** 3.11+
- **Node.js** 18+

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

创建 `.env` 配置文件（放在项目根目录）：

```bash
cp .env.example .env
# 编辑 .env，至少填写 INTERVIEW_OPENAI_API_KEY
```

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
2. **上传简历** — 支持 PDF / Word，自动脱敏
3. **匹配评分** — AI 多维度评分（岗位经验、行业背景、核心能力、成长潜力）
4. **生成问题** — 自动生成结构化面试问题清单
5. **开始面试** — 三栏实时辅助界面（转录 / 问题跟踪 / 追问建议）
6. **生成总结** — 结构化面试报告 + PDF 导出
7. **推送结果** — 一键推送到钉钉/飞书群
8. **对比候选人** — 同岗位多人横向对比

## 配置说明

所有配置通过环境变量或 `.env` 文件设置，前缀为 `INTERVIEW_`。

| 变量 | 说明 | 必填 |
|------|------|------|
| `INTERVIEW_OPENAI_API_KEY` | LLM API 密钥 | 是 |
| `INTERVIEW_OPENAI_BASE_URL` | LLM API 地址 | 否（默认 OpenAI） |
| `INTERVIEW_WHISPER_MODEL` | Whisper 模型 (tiny/base/small/medium) | 否 |
| `INTERVIEW_AUDIO_DEVICE_NAME` | 音频输入设备名称 | 否 |
| `INTERVIEW_DIARIZATION_ENABLED` | 说话人分离开关 | 否（默认 true） |
| `INTERVIEW_DINGTALK_WEBHOOK_URL` | 钉钉机器人 Webhook | 否 |
| `INTERVIEW_FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook | 否 |
| `INTERVIEW_AUTO_CLEANUP_DAYS` | 数据保留天数 | 否（默认 90） |
| `INTERVIEW_DB_ENCRYPTION_KEY` | 数据库加密密钥 | 否 |

推送 Webhook 也可以在系统设置页面直接配置，无需重启。

## 音频录音配置（可选）

面试助手支持两种输入模式：
- **手动输入** — 无需音频设备，直接在界面输入文字
- **实时录音** — 需要音频输入设备（自动识别说话人）

### 使用 BlackHole 捕获会议音频（macOS）

```bash
brew install blackhole-2ch
```

在「音频 MIDI 设置」中创建多输出设备（扬声器 + BlackHole），设为系统默认输出。然后配置：

```
INTERVIEW_AUDIO_DEVICE_NAME=BlackHole 2ch
```

查看可用音频设备：

```bash
python -c "import sounddevice as sd; [print(f'[{i}] {d[\"name\"]}') for i,d in enumerate(sd.query_devices()) if d['max_input_channels']>0]"
```

## 运行测试

```bash
cd backend && source .venv/bin/activate && pytest tests/ -v
```

## 技术栈

| 层面 | 技术 |
|------|------|
| 后端 | Python + FastAPI + SQLAlchemy + SQLite |
| 前端 | React + TypeScript + Vite + Tailwind CSS 4 |
| 语音转录 | faster-whisper（本地） |
| 说话人分离 | 能量检测（内置）/ pyannote-audio（可选） |
| LLM | OpenAI 兼容 API |
| 实时通信 | WebSocket |
| PDF 导出 | fpdf2 |
| 推送 | 钉钉 / 飞书 Webhook |
| 部署 | Docker Compose |
