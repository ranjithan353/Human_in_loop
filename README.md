# Human-in-the-Loop Social Media Manager

An AI-powered social media manager that generates LinkedIn/X posts from news articles, with human approval workflow using LangGraph, LangChain, and Tweepy.

## 🎯 Features

- **AI Post Generation**: Automatically generates engaging social media posts from news articles
- **Human-in-the-Loop**: Workflow pauses for human review before publishing
- **State Persistence**: Uses LangGraph's MemorySaver to persist workflow state across restarts
- **Post Editing**: Regenerate posts based on human feedback
- **Twitter Integration**: Publish approved posts directly to Twitter/X using Tweepy
- **Checkpoint System**: Resume workflows after application restart

## 📋 Prerequisites

- Python 3.8 or higher
- Ollama installed and running (for local LLM)
- Twitter/X API credentials (for publishing - optional)

## 🚀 Installation

1. **Clone or download this project**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and set up Ollama:**
   - Download and install Ollama from https://ollama.ai
   - Pull a model (recommended: llama3.2):
     ```bash
     ollama pull llama3.2
     ```
   - Verify Ollama is running:
     ```bash
     ollama list
     ```

4. **Set up environment variables (optional):**
   - Copy `env.example` to `.env`
   - Configure Ollama settings if needed:
     ```env
     OLLAMA_MODEL=llama3.2
     OLLAMA_BASE_URL=http://localhost:11434
     ```
   - Add Twitter API keys only if you want to publish posts:
     ```env
     TWITTER_API_KEY=your_twitter_api_key_here
     TWITTER_API_SECRET=your_twitter_api_secret_here
     TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
     TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
     TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
     ```

## 🔑 Getting API Keys

### Ollama Setup
1. Install Ollama from https://ollama.ai
2. Pull a model: `ollama pull llama3.2` (or any other model like `mistral`, `llama3`, etc.)
3. Start Ollama service (usually runs automatically)
4. The default URL is `http://localhost:11434` (can be changed in `.env`)

### Twitter/X API Credentials
1. Go to https://developer.twitter.com/en/portal/dashboard
2. Create a new project and app
3. Generate API keys and tokens
4. Copy all credentials to your `.env` file

## 📖 Usage

### Step 1: Generate a Post from an Article

**Option A: Provide article as a file**
```bash
python main.py article.txt
```

**Option B: Enter article interactively**
```bash
python main.py
# Then paste your article and press Ctrl+D (Mac/Linux) or Ctrl+Z (Windows)
```

The workflow will:
1. Generate a social media post from the article
2. **Pause and wait for human approval** (this is the interrupt point)
3. Save the state to a checkpoint

### Step 2: Review and Approve/Edit

Run the approval script:
```bash
python approve_post.py
```

You'll see the generated post and can:
- **Approve**: Type `approve`, `yes`, `ok`, or `publish` to publish to Twitter
- **Edit**: Provide editing instructions (e.g., "Make it more casual", "Add emojis")
- **Quit**: Type `quit` to exit without publishing

If you provide editing instructions, the workflow will:
1. Regenerate the post based on your feedback
2. Pause again for your review
3. Run `approve_post.py` again to review the new version

### Example Workflow

```bash
# Terminal 1: Generate post
$ python main.py news_article.txt
🤖 Generating post from article...
✓ Post generated (1 attempt):
------------------------------------------------------------
Exciting news in AI! New research shows...
#AI #TechNews
------------------------------------------------------------

⏸️  Workflow paused - Waiting for human approval...
💡 Use the approval script to review and approve/edit the post.
   Run: python approve_post.py

# Terminal 2: Review and approve
$ python approve_post.py
📋 GENERATED POST
------------------------------------------------------------
Exciting news in AI! New research shows...
#AI #TechNews
------------------------------------------------------------

Your feedback: approve
▶️  Resuming workflow with your feedback...
📤 Publishing post to Twitter...
✅ Post published successfully!
```

## 🏗️ Project Structure

```
human-in-the-loop/
├── main.py                 # Main script to start workflow
├── approve_post.py         # Human approval interface
├── workflow.py             # LangGraph workflow definition
├── post_generator.py       # Post generation using LangChain
├── twitter_client.py       # Twitter API integration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🔧 How It Works

### LangGraph Workflow

The workflow consists of these nodes:

1. **generate_post**: Uses LangChain to generate a post from the article
2. **wait_for_approval**: **Interrupts** here - waits for human input
3. **process_feedback**: Processes human feedback (approve/edit)
4. **publish_post**: Publishes to Twitter if approved

### State Persistence

- Uses `MemorySaver` checkpointer to save workflow state
- Each workflow run has a unique `thread_id`
- State persists even if you close the application
- Resume workflows using the same `thread_id`

### Interrupt Mechanism

- LangGraph's `interrupt_before` pauses execution at the `wait_for_approval` node
- The workflow state is saved to a checkpoint
- `approve_post.py` resumes the workflow with human feedback

## 🎓 Key Learnings

This project demonstrates:

1. **Breakpoints**: How to stop an autonomous agent for safety/quality checks
2. **Persistence**: Using checkpoints to save state of long-running conversations
3. **Human-in-the-Loop**: Integrating human feedback into AI workflows
4. **State Management**: Managing workflow state across multiple interactions

## 🐛 Troubleshooting

### "No workflow state found"
- Make sure you've run `main.py` first to generate a post
- Check that you're using the correct `thread_id`

### "Missing Twitter API credentials"
- Verify your `.env` file has all required Twitter credentials
- Make sure the `.env` file is in the project root

### "Post is too long"
- Twitter has a 280 character limit
- The generator should respect this, but you can adjust `POST_MAX_LENGTH` in `.env`

### Workflow not resuming
- Ensure you're using the same `thread_id` for both `main.py` and `approve_post.py`
- The `thread_id` is saved in `current_thread_id.txt` automatically

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OLLAMA_MODEL` | Ollama model name (e.g., "llama3.2", "mistral") | No (default: llama3.2) |
| `OLLAMA_BASE_URL` | Ollama API base URL | No (default: http://localhost:11434) |
| `TWITTER_API_KEY` | Twitter API key | No (only for publishing) |
| `TWITTER_API_SECRET` | Twitter API secret | No (only for publishing) |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | No (only for publishing) |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter access token secret | No (only for publishing) |
| `TWITTER_BEARER_TOKEN` | Twitter bearer token | Optional |
| `POST_TONE` | Post tone (e.g., "professional", "casual") | No |
| `POST_MAX_LENGTH` | Maximum post length in characters | No (default: 280) |

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secure
- The `.env.example` file is safe to commit (no real keys)

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

Feel free to fork, modify, and use this project for learning LangGraph and human-in-the-loop workflows!

---

**Happy Posting! 🚀**

