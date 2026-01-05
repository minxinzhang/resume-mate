import typer
from pathlib import Path
import shutil
import yaml
import webbrowser
from rich.prompt import Confirm
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from resume_mate.utils.console import console, print_yaml_diff
from resume_mate.utils.file_io import extract_text_from_file, write_yaml
from resume_mate.core.models import MasterProfile
from resume_mate.renderer.template import TemplateRenderer
from resume_mate.renderer.pdf import PdfGenerator
from resume_mate.ai.agent import ResumeAgent

app = typer.Typer(
    name="resume-mate",
    help="AI-powered resume tailor",
    add_completion=False,
)

DEFAULT_PROFILE_YAML = """basics:
  name: "John Doe"
  email: "john@example.com"
  phone: "+1 (555) 123-4567"
  summary: "Experienced software engineer..."
  location:
    city: "San Francisco"
    countryCode: "US"

work:
  - name: "Tech Corp"
    position: "Senior Engineer"
    startDate: "2020-01"
    summary: "Led team of 5..."
    highlights:
      - "Improved performance by 50%"
    techStack: ["Python", "AWS"]

education:
  - institution: "University of Tech"
    area: "Computer Science"
    studyType: "Bachelor"
    startDate: "2015-09"
    endDate: "2019-06"
"""

@app.command()
def init(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Directory to initialize"),
):
    """
    Initialize a new resume-mate project.
    """
    console.print(f"[bold]Initializing resume-mate project in {path.resolve()}[/bold]")
    
    path.mkdir(parents=True, exist_ok=True)
    
    profile_path = path / "master-profile.yaml"
    if profile_path.exists():
        console.print(f"[warning]File {profile_path} already exists.[/warning]")
        if not Confirm.ask("Do you want to overwrite it?"):
            console.print("Skipped creating master-profile.yaml")
        else:
            profile_path.write_text(DEFAULT_PROFILE_YAML)
            console.print(f"[success]Created {profile_path}[/success]")
    else:
        profile_path.write_text(DEFAULT_PROFILE_YAML)
        console.print(f"[success]Created {profile_path}[/success]")

def _render_pdf(profile: MasterProfile, theme: str, output: Path):
    """Helper to render profile to PDF."""
    console.print(f"[info]Rendering resume using theme '{theme}'...[/info]")
    
    try:
        renderer = TemplateRenderer(theme=theme)
        html_content = renderer.render(profile)
    except Exception as e:
        console.print(f"[error]Failed to render template: {e}[/error]")
        raise typer.Exit(code=1)

    console.print(f"[info]Generating PDF at {output}...[/info]")
    
    try:
        pdf_gen = PdfGenerator(output_dir=str(output.parent))
        css_path = renderer.theme_path / "styles.css"
        if not css_path.exists():
             console.print(f"[warning]CSS file not found at {css_path}. PDF might look unstyled.[/warning]")

        pdf_gen.generate(html_content, filename=output.name, css_path=css_path)
    except Exception as e:
        console.print(f"[error]Failed to generate PDF: {e}[/error]")
        raise typer.Exit(code=1)

@app.command()
def build(
    profile_file: Path = typer.Option(Path("master-profile.yaml"), "--input", "-i", help="Path to the master profile YAML"),
    theme: str = typer.Option("standard", "--theme", "-t", help="Theme to use"),
    output: Path = typer.Option(Path("output/resume.pdf"), "--output", "-o", help="Output filename"),
):
    """
    Build the resume PDF from the master profile.
    """
    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found.[/error]")
        raise typer.Exit(code=1)

    console.print(f"[info]Loading profile from {profile_file}...[/info]")
    
    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f)
        profile = MasterProfile(**data)
    except Exception as e:
        console.print(f"[error]Failed to validate profile: {e}[/error]")
        raise typer.Exit(code=1)

    _render_pdf(profile, theme, output)
    console.print(f"[success]Resume built successfully: {output}[/success]")

@app.command()
def preview(
    profile_file: Path = typer.Option(Path("master-profile.yaml"), "--input", "-i", help="Path to the master profile YAML"),
    theme: str = typer.Option("standard", "--theme", "-t", help="Theme to use"),
    output: Path = typer.Option(Path("output/preview.html"), "--output", "-o", help="Output HTML filename"),
):
    """
    Render the resume to HTML and open it in the default browser.
    """
    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found.[/error]")
        raise typer.Exit(code=1)

    console.print(f"[info]Loading profile from {profile_file}...[/info]")
    
    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f)
        profile = MasterProfile(**data)
    except Exception as e:
        console.print(f"[error]Failed to validate profile: {e}[/error]")
        raise typer.Exit(code=1)

    console.print(f"[info]Rendering resume using theme '{theme}'...[/info]")
    try:
        renderer = TemplateRenderer(theme=theme)
        html_content = renderer.render(profile)
    except Exception as e:
        console.print(f"[error]Failed to render template: {e}[/error]")
        raise typer.Exit(code=1)
    
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_content)
    console.print(f"[success]HTML generated at {output}[/success]")

    # Copy CSS for correct styling
    css_source = renderer.theme_path / "styles.css"
    if css_source.exists():
        css_dest = output.parent / "styles.css"
        shutil.copy(css_source, css_dest)
        console.print(f"[info]Copied styles.css to {css_dest}[/info]")
    else:
        console.print(f"[warning]CSS file not found at {css_source}. Preview might look unstyled.[/warning]")

    console.print(f"[info]Opening {output} in browser...[/info]")
    webbrowser.open(f"file://{output.resolve()}")


@app.command()
def bootstrap(
    input_file: Path = typer.Argument(..., help="Path to the old resume file (PDF, Docx, or TXT)"),
    output_file: Path = typer.Option(Path("master-profile.yaml"), "--output", "-o", help="Path to save the generated master profile YAML"),
    model: str = typer.Option("gpt-5.2", "--model", "-m", help="LLM model to use"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="API Key for the LLM provider"),
    api_base: str = typer.Option(None, "--api-base", "-b", help="API Base URL"),
    vision: bool = typer.Option(True, "--vision/--no-vision", help="Use vision for PDFs (better layout understanding)"),
):
    """
    Bootstrap a master-profile.yaml from an existing resume file using AI.
    """
    if not input_file.exists():
        console.print(f"[error]Input file {input_file} not found.[/error]")
        raise typer.Exit(code=1)

    if output_file.exists():
        if not Confirm.ask(f"File {output_file} already exists. Overwrite?"):
            console.print("Operation cancelled.")
            raise typer.Abort()

    console.print(f"[info]Extracting text from {input_file}...[/info]")
    try:
        raw_text = extract_text_from_file(input_file)
    except Exception as e:
        console.print(f"[error]Failed to extract text: {e}[/error]")
        raise typer.Exit(code=1)

    images = None
    if input_file.suffix.lower() == ".pdf" and vision:
        try:
            from resume_mate.utils.vision import pdf_to_base64_images
            with console.status("[bold green]Converting PDF to images for Vision analysis...[/bold green]"):
                images = pdf_to_base64_images(input_file)
            console.print(f"[info]Generated {len(images)} images from PDF.[/info]")
        except ImportError:
            console.print("[warning]PyMuPDF not installed. Skipping vision.[/warning]")
        except Exception as e:
            console.print(f"[warning]Failed to convert PDF to images: {e}. Falling back to text-only.[/warning]")

    agent = ResumeAgent(model_name=model, api_key=api_key, api_base=api_base)
    
    try:
        with console.status("[bold green]Analyzing and converting resume to Master Profile...[/bold green]"):
            profile = agent.bootstrap_profile(raw_text, images=images)
        
        console.print(f"[info]Saving generated profile to {output_file}...[/info]")
        dumped_data = profile.model_dump(mode="json", exclude_none=True, by_alias=True)
        # console.print(f"DEBUG: Dumped data keys: {dumped_data.keys()}")
        write_yaml(dumped_data, output_file)
        console.print(f"[success]Master Profile bootstrapped successfully: {output_file}[/success]")
        
    except Exception as e:
        console.print(f"[error]AI processing failed: {e}[/error]")
        raise typer.Exit(code=1)

@app.command()
def update(
    new_resume_file: Path = typer.Argument(..., help="Path to the new resume file (PDF, Docx, or TXT) to merge"),
    profile_file: Path = typer.Option(Path("master-profile.yaml"), "--profile", "-p", help="Path to the existing master profile YAML"),
    model: str = typer.Option("gpt-5.2", "--model", "-m", help="LLM model to use"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="API Key for the LLM provider"),
    api_base: str = typer.Option(None, "--api-base", "-b", help="API Base URL"),
    vision: bool = typer.Option(True, "--vision/--no-vision", help="Use vision for PDFs (better layout understanding)"),
):
    """
    Update an existing master profile by merging content from a new resume file.
    """
    if not new_resume_file.exists():
        console.print(f"[error]New resume file {new_resume_file} not found.[/error]")
        raise typer.Exit(code=1)

    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found. Use 'bootstrap' to create a new profile.[/error]")
        raise typer.Exit(code=1)

    # 1. Load Current Profile
    console.print(f"[info]Loading current profile from {profile_file}...[/info]")
    try:
        with open(profile_file, "r") as f:
            current_data = yaml.safe_load(f)
        current_profile = MasterProfile(**current_data)
    except Exception as e:
        console.print(f"[error]Failed to validate existing profile: {e}[/error]")
        raise typer.Exit(code=1)

    # 2. Extract Text from New File
    console.print(f"[info]Extracting text from {new_resume_file}...[/info]")
    try:
        raw_text = extract_text_from_file(new_resume_file)
    except Exception as e:
        console.print(f"[error]Failed to extract text: {e}[/error]")
        raise typer.Exit(code=1)

    images = None
    if new_resume_file.suffix.lower() == ".pdf" and vision:
        try:
            from resume_mate.utils.vision import pdf_to_base64_images
            with console.status("[bold green]Converting PDF to images for Vision analysis...[/bold green]"):
                images = pdf_to_base64_images(new_resume_file)
            console.print(f"[info]Generated {len(images)} images from PDF.[/info]")
        except ImportError:
            console.print("[warning]PyMuPDF not installed. Skipping vision.[/warning]")
        except Exception as e:
            console.print(f"[warning]Failed to convert PDF to images: {e}. Falling back to text-only.[/warning]")

    # 3. Initialize Agent & Merge
    agent = ResumeAgent(model_name=model, api_key=api_key, api_base=api_base)
    
    try:
        with console.status("[bold green]Merging new data into Master Profile...[/bold green]"):
            merged_profile = agent.merge_profile(current_profile, raw_text, images=images)
        
        # 4. Show Diff
        old_yaml = yaml.dump(current_profile.model_dump(mode="json", exclude_none=True, by_alias=True), sort_keys=False)
        new_yaml = yaml.dump(merged_profile.model_dump(mode="json", exclude_none=True, by_alias=True), sort_keys=False)
        
        console.print("\n[bold cyan]=== Proposed Changes ===[/bold cyan]\n")
        print_yaml_diff(old_yaml, new_yaml)
        
        # 5. Confirm & Save
        if Confirm.ask("\nDo you want to apply these changes?"):
            write_yaml(merged_profile.model_dump(mode="json", exclude_none=True, by_alias=True), profile_file)
            console.print(f"[success]Profile updated successfully: {profile_file}[/success]")
        else:
            console.print("[warning]Update cancelled. No changes made.[/warning]")
        
    except Exception as e:
        console.print(f"[error]AI processing failed: {e}[/error]")
        raise typer.Exit(code=1)

@app.command()
def tailor(
    job_description_file: Path = typer.Argument(..., help="Path to the job description file (text)"),
    profile_file: Path = typer.Option(Path("master-profile.yaml"), "--input", "-i", help="Path to the master profile YAML"),
    theme: str = typer.Option("standard", "--theme", "-t", help="Theme to use"),
    output: Path = typer.Option(Path("output/tailored_resume.pdf"), "--output", "-o", help="Output filename"),
    model: str = typer.Option("gpt-5.2", "--model", "-m", help="LLM model to use (e.g., gpt-5.2, claude-3-5-sonnet)"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="API Key for the LLM provider"),
    api_base: str = typer.Option(None, "--api-base", "-b", help="API Base URL (for proxies or Ollama)"),
):
    """
    Tailor the resume to a specific job description using AI.
    """
    # 1. Validate inputs
    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found.[/error]")
        raise typer.Exit(code=1)
    if not job_description_file.exists():
        console.print(f"[error]Job description file {job_description_file} not found.[/error]")
        raise typer.Exit(code=1)

    # 2. Load Profile
    console.print(f"[info]Loading profile from {profile_file}...[/info]")
    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f)
        profile = MasterProfile(**data)
    except Exception as e:
        console.print(f"[error]Failed to validate profile: {e}[/error]")
        raise typer.Exit(code=1)

    # 3. Read JD
    jd_text = job_description_file.read_text()
    
    # 4. Initialize Agent
    agent = ResumeAgent(model_name=model, api_key=api_key, api_base=api_base)
    
    # Check for API Key (LiteLLM relies on env vars usually, but we can warn if obviously missing for OpenAI)
    # This is a loose check; other providers might use different keys.
    if "gpt" in model and not api_key and not os.getenv("OPENAI_API_KEY"):
         console.print("[warning]Warning: OPENAI_API_KEY not found in environment variables. tailored generation might fail.[/warning]")

    # 5. Analyze and Tailor
    try:
        with console.status("[bold green]Analyzing Job Description...[/bold green]"):
            analysis = agent.analyze_job_description(jd_text)
        
        console.print("[info]Job Analysis Complete. Key terms extracted.[/info]")
        console.print(f"   [dim]Keywords: {', '.join(analysis.get('keywords', [])[:5])}...[/dim]")

        with console.status("[bold green]Tailoring Resume Content... (This may take a minute)[/bold green]"):
            tailored_profile = agent.tailor_profile(profile, analysis)
        
    except Exception as e:
        console.print(f"[error]AI processing failed: {e}[/error]")
        raise typer.Exit(code=1)

    # 6. Save Tailored YAML (for inspection)
    yaml_output = output.with_suffix(".yaml")
    console.print(f"[info]Saving tailored profile data to {yaml_output}...[/info]")
    write_yaml(tailored_profile.model_dump(mode="json", exclude_none=True, by_alias=True), yaml_output)

    # 7. Render PDF
    _render_pdf(tailored_profile, theme, output)
    console.print(f"[success]Tailored resume built successfully: {output}[/success]")


@app.command()
def add(
    entity_type: str = typer.Argument(..., help="Type of entry to add (work, project, education, skill)"),
    description: str = typer.Argument(..., help="Natural language description of the experience or project"),
    profile_file: Path = typer.Option(Path("master-profile.yaml"), "--input", "-i", help="Path to the master profile YAML"),
    model: str = typer.Option("gpt-5.2", "--model", "-m", help="LLM model to use"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="API Key"),
    api_base: str = typer.Option(None, "--api-base", "-b", help="API Base URL"),
):
    """
    Add a new entry (work, project, education, or skill) to your Master Profile using natural language.
    """
    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found.[/error]")
        raise typer.Exit(code=1)

    # Load Profile
    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f)
        profile = MasterProfile(**data)
    except Exception as e:
        console.print(f"[error]Failed to load profile: {e}[/error]")
        raise typer.Exit(code=1)

    agent = ResumeAgent(model_name=model, api_key=api_key, api_base=api_base)
    
    try:
        with console.status(f"[bold green]Parsing {entity_type} details...[/bold green]"):
            entity_data = agent.extract_entity(description, entity_type)
        
        console.print(f"[info]Extracted {entity_type} data:[/info]")
        console.print(entity_data)
        
        if not Confirm.ask("Do you want to add this to your profile?"):
            console.print("Cancelled.")
            return

        # Append to profile
        if entity_type == "work":
            from resume_mate.core.models import WorkExperience
            profile.work.append(WorkExperience(**entity_data))
        elif entity_type == "project":
            from resume_mate.core.models import Project
            profile.projects.append(Project(**entity_data))
        elif entity_type == "education":
            from resume_mate.core.models import Education
            profile.education.append(Education(**entity_data))
        elif entity_type == "skill":
            from resume_mate.core.models import Skill
            profile.skills.append(Skill(**entity_data))
        else:
            console.print(f"[error]Unsupported entity type: {entity_type}[/error]")
            raise typer.Exit(code=1)

        # Save back to YAML
        write_yaml(profile.model_dump(mode="json", exclude_none=True, by_alias=True), profile_file)
        console.print(f"[success]Successfully added {entity_type} to {profile_file}[/success]")

    except Exception as e:
        console.print(f"[error]Failed to add entry: {e}[/error]")
        raise typer.Exit(code=1)

@app.command()
def suggest(
    profile_file: Path = typer.Option(Path("master-profile.yaml"), "--input", "-i", help="Path to the master profile YAML"),
    model: str = typer.Option("gpt-5.2", "--model", "-m", help="LLM model to use"),
    api_key: str = typer.Option(None, "--api-key", "-k"),
    api_base: str = typer.Option(None, "--api-base", "-b"),
):
    """
    Get AI-powered suggestions and identify gaps in your Master Profile.
    """
    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found.[/error]")
        raise typer.Exit(code=1)

    # Load Profile
    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f)
        profile = MasterProfile(**data)
    except Exception as e:
        console.print(f"[error]Failed to load profile: {e}[/error]")
        raise typer.Exit(code=1)

    agent = ResumeAgent(model_name=model, api_key=api_key, api_base=api_base)
    
    try:
        with console.status("[bold green]Analyzing profile and generating suggestions...[/bold green]"):
            feedback = agent.suggest_improvements(profile)
        
        console.print("\n[bold cyan]=== Resume Mate Analysis ===[/bold cyan]\n")
        
        console.print("[bold yellow]Gaps Identified:[/bold yellow]")
        for gap in feedback.get("gaps", []):
            console.print(f" • {gap}")
            
        console.print("\n[bold green]Actionable Suggestions:[/bold green]")
        for suggestion in feedback.get("suggestions", []):
            console.print(f" • {suggestion}")

        console.print("\n[bold magenta]Recommended Skills to Add:[/bold magenta]")
        console.print(f" {', '.join(feedback.get('recommended_skills', []))}")

        console.print("\n[bold white]Overall Critique:[/bold white]")
        console.print(f" {feedback.get('overall_critique', 'N/A')}")
        
    except Exception as e:
        console.print(f"[error]AI processing failed: {e}[/error]")
        raise typer.Exit(code=1)

@app.command()
def validate(
    profile_file: Path = typer.Argument(Path("master-profile.yaml"), help="Path to the master profile YAML"),
):
    """
    Validate the master profile YAML against the schema.
    """
    if not profile_file.exists():
        console.print(f"[error]Profile file {profile_file} not found.[/error]")
        raise typer.Exit(code=1)

    console.print(f"[info]Validating {profile_file}...[/info]")
    
    try:
        with open(profile_file, "r") as f:
            data = yaml.safe_load(f)
        MasterProfile(**data)
        console.print(f"[success]{profile_file} is valid![/success]")
    except Exception as e:
        console.print(f"[error]Validation failed for {profile_file}:[/error]")
        console.print(f"[dim]{e}[/dim]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
