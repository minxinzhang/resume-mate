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

### 2. Bootstrap from Existing Resume
Import your old PDF, Docx, or Text resume into the Master Profile format using AI.
```bash
uv run resume-mate bootstrap old_resume.pdf --model gpt-4o
```

### 3. Add Content via Natural Language
Add a new work experience or project just by describing it.
```bash
uv run resume-mate add work "I worked at Google as a Senior Engineer from 2020 to 2024. I led the Search Infra team and improved latency by 20% using Rust."
```

### 4. Validate & Analyze
Check if your YAML profile is valid and get AI-driven improvements.
```bash
# Validate schema
uv run resume-mate validate master-profile.yaml

# Get AI suggestions
uv run resume-mate suggest --model gpt-4o
```

### 5. Preview (HTML)
Render the HTML in your browser to iterate on the design.
```bash
uv run resume-mate preview --theme dracula
```

### 6. Build (Manual)
Generate a PDF from your profile without AI tailoring.
```bash
uv run resume-mate build --theme standard --output output/my_resume.pdf
```

### 7. Tailor for a Job (The Core Feature)
Analyze a job description and generate a tailored resume PDF.
```bash
# Set your API key
export OPENAI_API_KEY="your-key"

# Tailor the resume
uv run resume-mate tailor job_description.txt --input master-profile.yaml --output output/tailored.pdf --model gpt-4o
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
