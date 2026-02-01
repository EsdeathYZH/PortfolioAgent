# 🤖 PortfolioAgent

An intelligent AI-powered portfolio analysis agent for A-share stocks. PortfolioAgent automates your daily stock analysis workflow, providing comprehensive market reviews and actionable trading insights to help you make informed investment decisions.

> **Your AI trading assistant that works 24/7** - Automatically analyzes your watchlist, monitors market conditions, and delivers insights directly to your preferred channels.

## ✨ Features

- 🤖 **AI-Powered Analysis**: Uses Google Gemini or OpenAI-compatible APIs for intelligent stock analysis
- 📊 **Multi-Data Source Support**: Integrates with AkShare, Tushare, Baostock, YFinance, and efinance
- 🔔 **Multi-Channel Notifications**: Supports WeChat, Feishu, Telegram, Email, Pushover, ServerChan, and custom webhooks
- 👥 **Multi-User Support**: Configure multiple users with individual stock watchlists and notification preferences
- 🌐 **WebUI Interface**: Web-based management interface for configuration and manual analysis triggers
- 📈 **Market Review**: Daily market overview and sentiment analysis
- 🔍 **News Integration**: Real-time news search using Tavily, Bocha, or SerpAPI
- 🐳 **Docker Support**: Easy deployment with Docker Compose
- ⚡ **GitHub Actions**: Free automated execution on GitHub Actions (no server required)
- 📱 **Feishu Cloud Docs**: Automatic generation of daily analysis reports in Feishu cloud documents

## 🏗️ Architecture

The project follows a clean architecture pattern:

```
PortfolioAgent/
├── common/              # Shared utilities and configuration
├── core/                # Core business logic
│   ├── domain/         # Domain models (Analysis, Signal, User, etc.)
│   └── services/       # Business services
│       ├── analysis/   # Stock analysis pipeline
│       ├── advice/     # Trading advice engine
│       ├── backtest/  # Backtesting engine
│       ├── notification/ # Notification service
│       ├── search/     # News search service
│       └── user/       # User configuration management
├── infrastructure/     # External integrations
│   ├── ai/            # AI model integrations (Gemini, OpenAI)
│   ├── data/          # Data persistence (SQLite)
│   ├── external/      # External services (Feishu API)
│   └── fetchers/      # Data source fetchers
└── presentation/      # User interfaces
    ├── cli/           # Command-line interface
    ├── scheduler/     # Task scheduling
    └── web/           # Web UI
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ (3.12 recommended)
- API Keys:
  - **Required**: Gemini API Key ([Get it here](https://aistudio.google.com/)) or OpenAI-compatible API
  - **Recommended**: Tavily API Key for news search ([Get it here](https://tavily.com/))
  - **Optional**: Tushare Token for premium data

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PortfolioAgent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   # Required: AI Model (at least one)
   GEMINI_API_KEY=your_gemini_api_key

   # Required: Stock Watchlist
   STOCK_LIST=600519,300750,002594

   # Required: At least one notification channel
   WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
   # OR
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
   # OR
   TELEGRAM_BOT_TOKEN=xxx
   TELEGRAM_CHAT_ID=xxx
   # OR
   EMAIL_SENDER=your_email@example.com
   EMAIL_PASSWORD=your_email_auth_code

   # Recommended: News Search
   TAVILY_API_KEYS=your_tavily_api_key
   ```

5. **Run the analysis**
   ```bash
   python main.py
   ```

## 📖 Usage

### Command Line Options

```bash
# Full analysis (stocks + market review)
python main.py

# Market review only
python main.py --market-review

# Stocks only (no market review)
python main.py --no-market-review

# Analyze specific stocks
python main.py --stocks 600519,300750

# Dry run (fetch data only, no AI analysis)
python main.py --dry-run

# No notifications
python main.py --no-notify

# Schedule mode (runs daily at configured time)
python main.py --schedule

# Debug mode (verbose logging)
python main.py --debug

# Custom worker count
python main.py --workers 5

# WebUI mode (with analysis)
python main.py --webui

# WebUI only (manual trigger)
python main.py --webui-only
```

### WebUI Interface

Start the WebUI:
```bash
python main.py --webui-only
```

Then access `http://localhost:8000` in your browser.

**Features:**
- 📝 View and edit stock watchlist
- 🚀 Trigger analysis for specific stocks
- 📊 View analysis task status
- 🔗 RESTful API endpoints

**API Endpoints:**
- `GET /` - Configuration management page
- `GET /health` - Health check
- `GET /analysis?code=600519` - Trigger analysis for a stock
- `GET /tasks` - List all analysis tasks
- `GET /task?id=xxx` - Get task status

## 🔧 Configuration

### Environment Variables

#### AI Model Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API Key | ✅* |
| `GEMINI_MODEL` | Gemini model name (default: `gemini-3-flash-preview`) | No |
| `OPENAI_API_KEY` | OpenAI-compatible API Key | Optional |
| `OPENAI_BASE_URL` | OpenAI-compatible API base URL | Optional |
| `OPENAI_MODEL` | OpenAI model name (default: `gpt-4o-mini`) | Optional |

> *At least one AI model (Gemini or OpenAI) is required.

#### Notification Channels

| Variable | Description | Required |
|----------|-------------|----------|
| `WECHAT_WEBHOOK_URL` | WeChat Work webhook URL | Optional* |
| `FEISHU_WEBHOOK_URL` | Feishu webhook URL | Optional* |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Optional* |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | Optional* |
| `EMAIL_SENDER` | Email sender address | Optional* |
| `EMAIL_PASSWORD` | Email auth code (not password) | Optional* |
| `EMAIL_RECEIVERS` | Email recipients (comma-separated) | Optional |
| `PUSHOVER_USER_KEY` | Pushover user key | Optional* |
| `PUSHOVER_API_TOKEN` | Pushover API token | Optional* |
| `SERVERCHAN_SEND_KEY` | ServerChan API key | Optional* |
| `CUSTOM_WEBHOOK_URLS` | Custom webhook URLs (comma-separated) | Optional* |
| `CUSTOM_WEBHOOK_BEARER_TOKEN` | Bearer token for custom webhooks | Optional |
| `SINGLE_STOCK_NOTIFY` | Send notification per stock (default: `false`) | Optional |

> *At least one notification channel is required.

#### Feishu Cloud Documents (Optional)

| Variable | Description | Required |
|----------|-------------|----------|
| `FEISHU_APP_ID` | Feishu app ID | Optional |
| `FEISHU_APP_SECRET` | Feishu app secret | Optional |
| `FEISHU_FOLDER_TOKEN` | Feishu cloud folder token | Optional |

#### Search Services

| Variable | Description | Required |
|----------|-------------|----------|
| `TAVILY_API_KEYS` | Tavily API keys (comma-separated) | Recommended |
| `BOCHA_API_KEYS` | Bocha API keys (comma-separated) | Optional |
| `SERPAPI_API_KEYS` | SerpAPI keys (comma-separated) | Optional |

#### Data Sources

| Variable | Description | Required |
|----------|-------------|----------|
| `TUSHARE_TOKEN` | Tushare Pro token | Optional |

#### System Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `STOCK_LIST` | Stock codes (comma-separated) | - |
| `MAX_WORKERS` | Concurrent threads | `3` |
| `MARKET_REVIEW_ENABLED` | Enable market review | `true` |
| `SCHEDULE_ENABLED` | Enable scheduled tasks | `false` |
| `SCHEDULE_TIME` | Daily execution time (HH:MM) | `18:00` |
| `WEBUI_ENABLED` | Enable WebUI | `false` |
| `WEBUI_HOST` | WebUI host | `127.0.0.1` |
| `WEBUI_PORT` | WebUI port | `8000` |
| `LOG_DIR` | Log directory | `./logs` |

### Multi-User Configuration

The system supports multiple users with individual configurations:

```env
# List of users (comma-separated)
USERS=user1,user2

# User 1 configuration
USER_user1_STOCKS=600519,300750
USER_user1_WECHAT_WEBHOOK_URL=https://...
USER_user1_FEISHU_WEBHOOK_URL=https://...

# User 2 configuration
USER_user2_STOCKS=000001,002594
USER_user2_TELEGRAM_BOT_TOKEN=xxx
USER_user2_TELEGRAM_CHAT_ID=xxx
```

## 🐳 Docker Deployment

### Quick Start

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Service Modes

| Service | Description | Port |
|---------|-------------|------|
| `analyzer` | Scheduled task mode | - |
| `webui` | WebUI mode (manual trigger) | 8000 |

### Run Both Modes

```bash
docker-compose up -d analyzer webui
```

## ☁️ GitHub Actions Deployment

Deploy PortfolioAgent for free on GitHub Actions (no server required):

1. **Fork the repository**

2. **Configure Secrets**

   Go to `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

   Add required secrets:
   - `GEMINI_API_KEY`
   - `STOCK_LIST`
   - At least one notification channel
   - `TAVILY_API_KEYS` (recommended)

3. **Enable Actions**

   Go to `Actions` tab → Enable workflows

4. **Manual Test**

   Go to `Actions` → `Run workflow` → Select mode → Run

5. **Schedule**

   Default: Weekdays at 18:00 (Beijing time)

   Edit `.github/workflows/daily_analysis.yml` to customize:
   ```yaml
   schedule:
     - cron: '0 10 * * 1-5'  # UTC time (+8 = Beijing time)
   ```

## 📊 Analysis Features

### Stock Analysis

- **Technical Analysis**: MA trends, volume analysis, pattern recognition
- **Fundamental Analysis**: Sector position, company highlights
- **Sentiment Analysis**: News summary, market sentiment, hot topics
- **Trading Advice**: Buy/sell/hold recommendations with confidence levels
- **Risk Warnings**: Key risk points and alerts

### Market Review

- Daily market overview
- Sector rotation analysis
- Market sentiment summary
- Key events and news

### Decision Dashboard

Each analysis includes a structured decision dashboard:
- **Core Conclusion**: One-sentence summary
- **Position Advice**: Recommendations for different positions
- **Sniper Points**: Key price levels
- **Action Checklist**: Pre-trade checklist
- **Risk Alerts**: Important warnings

## 🔍 Data Sources

The system uses multiple data sources with automatic fallback:

1. **efinance** (Priority 0) - East Money data
2. **AkShare** (Priority 1) - Free A-share data
3. **Tushare Pro** (Priority 2) - Premium data (requires token)
4. **Baostock** (Priority 3) - Free backup source
5. **YFinance** (Priority 4) - International markets

## 📝 Supported Stock Formats

- **A-shares**: 6-digit codes (e.g., `600519`, `000001`, `300750`)
- **Hong Kong stocks**: `hk` prefix + 5 digits (e.g., `hk00700`, `hk09988`)

## 🧪 Testing

```bash
# Run all tests
python -m pytest test/

# Run specific test file
python -m pytest test/test_functionality.py

# Run with coverage
python -m pytest test/ --cov=core --cov=infrastructure
```

## 📚 Documentation

- [Full Configuration Guide](docs/full-guide.md) - Complete configuration reference
- [Deployment Guide](docs/DEPLOY.md) - Detailed deployment instructions

---

**PortfolioAgent** - Your intelligent portfolio analysis assistant
