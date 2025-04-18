import os
from jinja2 import Environment, FileSystemLoader

PROMPT_DIR = os.path.join(os.path.dirname(__file__))
env = Environment(loader=FileSystemLoader(PROMPT_DIR))


def render_prompt(template_name: str, **kwargs) -> str:
    try:
        template = env.get_template(template_name)
        return template.render(**kwargs)
    except Exception as e:
        raise RuntimeError(f"Error rendering template {template_name}: {e}")
