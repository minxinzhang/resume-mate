from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from resume_mate.core.models import MasterProfile

class TemplateRenderer:
    def __init__(self, theme: str = "standard"):
        self.theme = theme
        # Resolve themes directory relative to this file (resume_mate/renderer/template.py)
        # Structure: resume_mate/renderer/../themes/{theme}
        self.theme_path = Path(__file__).parent.parent / "themes" / theme
        self.env = Environment(
            loader=FileSystemLoader(self.theme_path),
            autoescape=True
        )

    def render(self, profile: MasterProfile) -> str:
        template = self.env.get_template("template.html.j2")
        # Convert Pydantic model to dict for Jinja2
        # mode='json' ensures things like HttpUrl are converted to strings
        profile_dict = profile.model_dump(mode='json', by_alias=True)
        return template.render(**profile_dict)
