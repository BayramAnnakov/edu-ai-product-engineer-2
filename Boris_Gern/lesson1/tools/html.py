from jinja2 import Environment, FileSystemLoader
import os
from schema import ReportPayload


def build_html(payload: ReportPayload, template_path: str = "templates", output_file: str = "report.html") -> str:
    """Builds an HTML report from a payload using a Jinja2 template."""
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template("report.html.j2")

    html_content = template.render(payload.model_dump())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return f"Report saved to {os.path.abspath(output_file)}"
