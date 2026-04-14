# 面试助手 (Interview Assistant)

本地运行的 Web 面试辅助工具，覆盖从简历筛选到面试总结的全流程。

---

## 给非技术用户的一键部署指南

> 整个过程大约 10-15 分钟，只需要跟着下面的步骤操作，不需要写任何代码。

### 第一步：安装 Docker Desktop

Docker 是一个"容器"工具，可以把整个应用打包运行，你不需要理解它的原理，只需要安装并启动。

1. 打开 https://www.docker.com/products/docker-desktop/ ，点击 **Download for Windows**（Mac 用户选 Mac 版本）
2. 下载完成后双击安装程序，一路点 **Next / 下一步**，直到安装完成
3. 安装完成后 **重启电脑**
4. 重启后桌面会出现 **Docker Desktop** 图标，**双击启动它**
5. 等待左下角状态变为绿色 **"Engine running"**，表示 Docker 已就绪

> **Windows 用户注意**：如果提示需要启用 WSL 2，按照弹窗提示操作即可，通常只需重启一次。

### 第二步：下载项目文件

**方式 A（推荐，最简单）**：
1. 打开 https://github.com/yj-gitv/interview/archive/refs/heads/main.zip
2. 浏览器会自动下载一个 zip 文件
3. 右键点击下载的 zip 文件 → **全部解压缩** → 选择一个你能找到的位置（例如桌面）
4. 解压后你会得到一个 `interview-main` 文件夹

**方式 B（如果你已安装 Git）**：
```bash
git clone https://github.com/yj-gitv/interview.git
cd interview
```

### 第三步：配置 API Key

1. 进入解压后的 `interview-main` 文件夹（或 `interview` 文件夹）
2. 找到文件 `.env.example`，**复制一份**，将副本重命名为 `.env`
   - Windows：右键 `.env.example` → 复制 → 粘贴 → 将 `.env.example - 副本` 改名为 `.env`
   - 如果看不到 `.env.example`，在文件管理器顶部点 **查看** → 勾选 **隐藏的项目**
3. 用**记事本**打开 `.env` 文件
4. 修改以下两行（第 2 行和第 3 行）：
   ```
   INTERVIEW_OPENAI_API_KEY=把这里替换成你的API密钥
   INTERVIEW_OPENAI_BASE_URL=把这里替换成你的API地址
   ```
   例如，如果你使用 OpenAI 官方 API：
   ```
   INTERVIEW_OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   INTERVIEW_OPENAI_BASE_URL=https://api.openai.com/v1
   ```
5. 保存并关闭

> **重要**：`.env` 文件包含你的 API 密钥，请勿分享给他人。

### 第四步：启动应用

1. **打开终端 / 命令提示符**
   - Windows：在 `interview-main` 文件夹内，按住 Shift 键，右键空白处 → **在此处打开 PowerShell 窗口**
   - Mac：打开"终端"应用，输入 `cd ` 然后把文件夹拖进终端窗口，按回车
2. 输入以下命令并按回车：
   ```bash
   docker compose up --build
   ```
3. 首次启动会下载依赖，**需要等待约 10-20 分钟**（取决于网速），请耐心等待
4. 当你看到类似以下内容时，说明启动成功：
   ```
   frontend-1  | ... start worker process ...
   backend-1   | INFO:     Application startup complete.
   ```

### 第五步：开始使用

1. 打开浏览器（推荐 Chrome），访问 **http://localhost:3000**
2. 你会看到面试助手的界面，可以开始使用了！

### 日常使用

| 操作 | 方法 |
|------|------|
| **启动** | 确保 Docker Desktop 已运行，然后在项目文件夹打开终端，输入 `docker compose up -d` |
| **停止** | 在终端输入 `docker compose down` |
| **查看日志** | 在终端输入 `docker compose logs -f` |
| **更新版本** | 重新下载 zip 解压（保留旧的 `.env` 文件），然后 `docker compose up --build -d` |

### 常见问题

**Q：启动时提示 "Docker Desktop is not running"**
A：双击桌面上的 Docker Desktop 图标，等待状态变绿后重试。

**Q：浏览器打开 localhost:3000 显示空白或报错**
A：回到终端检查是否有红色错误信息。最常见的原因是 `.env` 文件中的 API Key 填写有误。

**Q：实时转录 / 语音识别不工作**
A：点击"启动音频"后，浏览器会弹出麦克风授权，请点击**允许**。确保使用 Chrome 浏览器。

**Q：想换端口（3000 被占用）**
A：在 `.env` 文件中取消注释并修改 `APP_PORT=8080`（改成你想要的端口号）。

---

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
