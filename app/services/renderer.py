import re
from typing import Any, Union, Dict, List
import jinja2
from app.models.schema import Resume

def escape_latex(text: str) -> str:
    """Escapes LaTeX special characters in a string."""
    if not isinstance(text, str):
        return str(text)
    
    # Define LaTeX special character replacements
    conv = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    
    # Compile a regex to match characters that need escaping.
    # Note: Sort keys by length descending to match multi-char sequences if any (e.g. \\) first.
    pattern = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=lambda item: -len(item))))
    return pattern.sub(lambda match: conv[match.group()], text)

def escape_latex_recursive(data: Any) -> Any:
    """Recursively traverses a dict/list/model and escapes all string values for LaTeX."""
    if isinstance(data, dict):
        return {key: escape_latex_recursive(val) for key, val in data.items()}
    elif isinstance(data, list):
        return [escape_latex_recursive(item) for item in data]
    elif isinstance(data, str):
        return escape_latex(data)
    elif hasattr(data, "model_dump"): # For Pydantic models
        return escape_latex_recursive(data.model_dump())
    else:
        return data

class LaTeXRenderer:
    def __init__(self, templates_dir: str = "templates"):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            block_start_string='((*',
            block_end_string='*))',
            variable_start_string='(((',
            variable_end_string=')))',
            comment_start_string='((#',
            comment_end_string='#))',
            autoescape=False # LaTeX needs raw string output, autoescape is for HTML
        )
        
        # Register the escape filter in the Jinja2 environment as well
        self.env.filters['escape_latex'] = escape_latex

    def render(self, template_name: str, resume_data: Union[Resume, Dict[str, Any]]) -> str:
        """
        Renders the LaTeX template with the given resume data.
        Automatically escapes LaTeX special characters.
        """
        # Convert to dictionary and escape strings
        escaped_data = escape_latex_recursive(resume_data)
        
        # Load the template and render it
        template = self.env.get_template(template_name)
        return template.render(**escaped_data)
