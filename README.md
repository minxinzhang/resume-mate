# Resume Mate 📝

AI-powered resume tailor that transforms your master career profile into a job-specific resume.

## Features

- **Master Profile:** Keep your entire career history in one YAML file.
- **AI Tailoring:** Uses LLMs (via LiteLLM) to analyze job descriptions and rewrite your resume to match.
- **High Fidelity PDF:** Renders resumes using HTML/CSS and Playwright for pixel-perfect results.
- **Privacy First:** Works with local models (via Ollama) or any major provider (OpenAI, Anthropic, etc.).

## Installation

This project uses `uv` for fast dependency management.

```bash
# Clone the repository
git clone https://github.com/yourusername/resume-mate.git
cd resume-mate

# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## Usage

### 1. Initialize a Project
Scaffold a new project with a default `master-profile.yaml`.
```bash
uv run resume-mate init
```

### 2. Validate your Profile
Check if your YAML file matches the required schema.
```bash
uv run resume-mate validate master-profile.yaml
```

### 3. Build a Standard Resume (Manual)
Generate a PDF from your profile without AI tailoring.
```bash
uv run resume-mate build --input master-profile.yaml --output output/my_resume.pdf
```

### 4. Tailor with AI
Analyze a job description and generate a tailored resume.
```bash
# Set your API key if using a cloud provider
export OPENAI_API_KEY="your-key"

# Tailor the resume
uv run resume-mate tailor jd.txt --input master-profile.yaml --output output/tailored.pdf --model gpt-4o
```

## Configuration

### Supported Models
`resume-mate` uses [LiteLLM](https://docs.litellm.ai/docs/providers), which supports:
- OpenAI (`gpt-4o`, `gpt-3.5-turbo`)
- Anthropic (`claude-3-5-sonnet-20240620`)
- Ollama (`ollama/llama3`)
- And 100+ others...

### Themes
Themes are located in `resume_mate/themes/`. The default theme is `standard`.
You can customize the HTML/CSS in `resume_mate/themes/standard/template.html.j2` and `styles.css`.

## License
MIT
