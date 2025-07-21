import re
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def rule_based_parser(raw_output: str, parser_info: dict) -> list:
    """
    Parses raw output based on simple whitespace splitting.
    It assumes the output is a list of items separated by newlines or spaces.
    """
    print("Parsing with: rule_based_parser")
    # Splits by any whitespace and filters out empty strings
    return [item for item in re.split(r'\s+', raw_output) if item]

def regex_based_parser(raw_output: str, parser_info: dict) -> list:
    """
    Parses raw output using regex patterns specified in parser_info.
    The patterns are expected to be in a "patterns" array, each with a "regex" field.
    """
    print("Parsing with: regex_based_parser")
    
    patterns = parser_info.get("patterns")
    if not patterns:
        raise ValueError("Patterns array not found in parser_info for regex_based_parser")
    
    print(f"DEBUG: Found {len(patterns)} patterns")
    
    all_matches = []
    for i, pattern_info in enumerate(patterns):
        regex_pattern = pattern_info.get("regex")
        if not regex_pattern:
            print(f"DEBUG: Pattern {i} has no regex field")
            continue
            
        print(f"DEBUG: Pattern {i}: {repr(regex_pattern)}")
        matches = re.findall(regex_pattern, raw_output, re.MULTILINE)
        print(f"DEBUG: Pattern {i} matches: {matches}")
        all_matches.extend(matches)
    
    print(f"DEBUG: Total matches: {all_matches}")
    return all_matches

def llm_based_parser(raw_output: str, parser_info: dict) -> str:
    """
    Parses raw output using the OpenAI GPT-4o-mini model.
    The prompt template is specified in the parser_info dictionary as "prompt_template".
    """
    print("Parsing with: llm_based_parser")
    prompt = parser_info.get("prompt_template")
    if not prompt:
        raise ValueError("prompt_template not found in parser_info for llm_based_parser")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("OPENAI_API_KEY not found or not set in .env file")

    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that processes text."},
                {"role": "user", "content": f"{prompt}\n\nHere is the text to process:\n\n{raw_output}"}
            ],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred with the OpenAI API: {e}")
        return f"Error during LLM parsing: {e}"

def parse_output(raw_output: str, parser_info: dict) -> list | str:
    """
    Selects the appropriate parser based on the parser_info and parses the raw output.
    """
    parser_type = parser_info.get("type")
    
    if parser_type == "rule_based":
        return rule_based_parser(raw_output, parser_info)
    elif parser_type == "regex_based":
        return regex_based_parser(raw_output, parser_info)
    elif parser_type == "llm_based":
        return llm_based_parser(raw_output, parser_info)
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")
