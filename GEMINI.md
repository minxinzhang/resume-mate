# Resume Mate Context

## Project Overview
**Resume Mate** is a Python-based CLI tool designed to act as an "AI Resume Strategist". It decouples resume content from presentation by maintaining a comprehensive "Master Profile" (YAML) and using AI to tailor this content for specific job descriptions before rendering it into a high-fidelity PDF.

## Tech Stack
-   **Language:** Python 3.14+
-   **Package Manager:** `uv` (Astral)
-   **CLI Framework:** `typer`
-   **Data Validation:** `pydantic`
-   **Templating:** `jinja2`
-   **AI/LLM:** `litellm` (Unified interface for OpenAI, Anthropic, Ollama, etc.)
-   **PDF Engine:** `playwright` (Headless Chromium)

## Key Files & Directories
-   `resume_mate/`
    -   `main.py`: **Entry Point.** Contains the Typer app and all CLI command definitions.
    -   `core/models.py`: **Data Schema.** Pydantic models defining the structure of `master-profile.yaml` (Basics, Work, Education, etc.).
    -   `ai/agent.py`: **Intelligence.** Wraps `litellm` interactions for bootstrapping, tailoring, and suggestions.
    -   `renderer/`:
        -   `template.py`: Jinja2 environment setup.
        -   `pdf.py`: Playwright script to render HTML to PDF.
    -   `themes/`: Directory for resume themes (Jinja2 templates + CSS).
-   `master-profile.yaml`: The user's single source of truth for their career history.
-   `AI_RESUME_TAILOR_PLAN.md`: Development roadmap and architecture documentation.
-   `pyproject.toml`: Project configuration and dependencies.

## CLI Command Reference
Run commands using `uv run resume-mate [command]`.

| Command | Description | Key Options |
| :--- | :--- | :--- |
| `init` | Scaffold a new project with a default `master-profile.yaml`. | `--path` |
| `validate` | Check if a YAML profile matches the Pydantic schema. | |
| `build` | Render a PDF from the profile *without* AI tailoring. | `--theme`, `--output` |
| `preview` | Render HTML and open it in the default browser. | `--theme` |
| `tailor` | **Core Feature.** Tailor resume to a specific JD using AI. | `jd_file`, `--model`, `--output` |
| `bootstrap` | Create a profile from an existing PDF/Docx resume using AI. | `--input`, `--model` |
| `add` | Add an entry (work, project, skill) using natural language. | `entity_type`, `description` |
| `suggest` | Get AI-driven feedback and gap analysis on the profile. | `--model` |

## Development Guidelines
-   **Dependency Management:** Always use `uv sync` to install dependencies.
-   **Running Locally:** Use `uv run resume-mate ...` to execute the CLI.
-   **Theme Development:**
    -   Themes are located in `resume_mate/themes/<theme_name>/`.
    -   Each theme requires `template.html.j2` and `styles.css`.
    -   Use the `preview` command to iterate on designs quickly.
-   **AI Integration:**
    -   `ResumeAgent` in `ai/agent.py` handles all LLM calls.
    -   Ensure `OPENAI_API_KEY` (or relevant provider key) is set in the environment when testing AI features.

## Architecture Notes
1.  **Separation of Concerns:** Data (`MasterProfile`) is strictly separated from presentation (`renderer`).
2.  **Agentic Workflow:** The `tailor` command uses a multi-step process: Analyze JD -> Select Content -> Rewrite Content -> Render.
3.  **PDF Generation:** We use Playwright for "pixel-perfect" CSS printing, which provides better results than simpler HTML-to-PDF libraries.
