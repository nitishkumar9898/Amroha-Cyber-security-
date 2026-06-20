# compliance_engine/report_generator.py
"""Report generation utilities for compliance.
Uses Jinja2 templates to produce HTML and optionally PDF via weasyprint.
"""
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Assuming templates are stored in a 'templates' directory under compliance_engine
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

def render_report(context: dict, template_name: str = "compliance_report.html") -> str:
    """Render a compliance report to HTML string.
    Args:
        context: Dictionary with data to populate the template.
        template_name: Filename of the Jinja2 template.
    Returns:
        Rendered HTML as a string.
    """
    template = env.get_template(template_name)
    return template.render(**context)

# Optional PDF conversion (requires weasyprint installed)
def render_pdf(html_content: str, output_path: str):
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)
    except ImportError:
        raise RuntimeError("weasyprint is required for PDF generation. Install it via pip.")
