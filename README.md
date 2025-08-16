# Novel Diver - Interactive Fanfiction MVP

An interactive fanfiction application where users become protagonists in dynamic stories. Make decisions that influence the narrative while AI controls other characters and generates unexpected twists.

## Features

- **World Selection**: Choose from multiple genres (cultivation, martial arts, fantasy, sci-fi, modern urban)
- **Character Creation**: Define your protagonist with name, background, traits, and goals
- **Dynamic Storytelling**: AI generates narrative and pauses at decision points
- **User Choices**: Make decisions that influence story direction
- **Session Management**: Save and export your unique story
- **Clean Interface**: Built with Streamlit for easy interaction

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

3. Enter your API key in the sidebar:
   - Choose your preferred AI provider (Gemini recommended)
   - Get your free API key from the provided link
   - Enter it in the sidebar to start generating stories

**No environment variables needed!** The app will guide you through the API setup process.

## Project Structure

```
novel-diver-mvp/
├─ app.py                # Main Streamlit application
├─ config.py             # API configuration and key management
├─ prompts/              # World and character prompt templates
├─ modules/
│   ├─ story_engine.py   # Core story generation logic
│   ├─ character.py      # Character data models
│   └─ decision.py       # Decision tracking and history
├─ saved_sessions/       # Saved story files
└─ requirements.txt      # Python dependencies
```

## API Configuration

**Easy Setup Through the App:**
No need to set environment variables! The app provides an intuitive interface to configure your AI provider:

- **Google Gemini** (Recommended): Free with generous limits - Get your key at [ai.google.dev](https://ai.google.dev/)
- **Hugging Face** (Free Alternative): Completely free - Get your token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- **OpenAI** (Advanced): Paid service with excellent quality - Get your key at [platform.openai.com](https://platform.openai.com/)

**Optional: Environment Variables**
If you prefer, you can still set environment variables:
- `GEMINI_API_KEY`: Your Google Gemini API key
- `HUGGINGFACE_TOKEN`: Your Hugging Face token
- `OPENAI_API_KEY`: Your OpenAI API key

## Development

This is the Minimal Viable Product (MVP) version. Future enhancements may include:
- Local model integration (e.g., Ollama)
- Visual decision tree mapping
- Multiplayer co-op sessions
- Mobile app version

## License

MIT License - Feel free to fork and modify!
