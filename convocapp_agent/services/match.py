import json

from deep_translator import GoogleTranslator

from clients.llm import call_llm
from utils.date import parse_nlp_datetime
from prompts.prompt_builder import render_prompt
from models.match_models import CreateMatch
from clients.studio import studio


async def create_match(message: str):
    create_prompt = render_prompt("extract_where_when.txt.tmpl", user_input=message)
    arguments = call_llm(create_prompt, "extract_where_when")
    parsed_args: CreateMatch = CreateMatch.model_validate(json.loads(arguments.strip()))
    when = GoogleTranslator(source=parsed_args.language or "auto", target="en").translate(parsed_args.when)
    parsed_args.when = parse_nlp_datetime(when)
    result = await studio.create_match(parsed_args)
    return result
