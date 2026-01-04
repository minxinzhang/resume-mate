from playwright.sync_api import sync_playwright
from pathlib import Path

class PdfGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate(self, html_content: str, filename: str = "resume.pdf", css_path: Path | None = None):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Set content
            page.set_content(html_content)
            
            # Add CSS if provided
            if css_path and css_path.exists():
                page.add_style_tag(path=css_path)

            # Generate PDF
            output_path = self.output_dir / filename
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "1cm", "right": "1cm", "bottom": "1cm", "left": "1cm"}
            )
            
            browser.close()
            return output_path
