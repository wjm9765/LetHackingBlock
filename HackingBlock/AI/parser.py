import re
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Union
from AI.count_token import count_tokens

# Load environment variables from .env file
load_dotenv()

def rule_based_parser(raw_output: str, parser_info: dict, used_options: str = "", command_block: dict = None) -> Union[str, List[str]]:
    """
    옵션별 parser_info를 확인하여 적절한 저장 규칙 적용
    
    Args:
        raw_output: 명령어 실행 결과
        parser_info: 기본 파서 정보
        used_options: 사용된 옵션 (예: "-l", "aux")
        command_block: 전체 명령어 블록 (옵션별 parser_info 확인용)
    """
    print("Parsing with: rule_based_parser")
    
    # 1. 옵션별 parser_info 확인 (옵션이 있을 때만)
    if command_block and used_options and used_options.strip():
        option_parser_info = command_block.get("option_parser_info", {})
        
        # 정확한 옵션 매칭 확인
        if used_options in option_parser_info:
            print(f"DEBUG: Using option-specific parser_info for '{used_options}'")
            parser_info = option_parser_info[used_options]
        else:
            # 부분 매칭 확인 (예: "-la"에서 "-l" 찾기)
            matched = False
            for option_key in option_parser_info.keys():
                if option_key in used_options:
                    print(f"DEBUG: Using partial match parser_info for '{option_key}' in '{used_options}'")
                    parser_info = option_parser_info[option_key]
                    matched = True
                    break
            
            # 매칭되지 않으면 기본 parser_info 사용
            if not matched:
                print(f"DEBUG: No matching option found for '{used_options}', using default parser_info")
    else:
        # 옵션이 없으면 기본 parser_info 사용
        print("DEBUG: No options provided, using default parser_info")
    
    # 2. 전처리: 공백 및 ANSI 코드 제거
    cleaned = raw_output.strip()
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned = ansi_escape.sub('', cleaned)
    
    # 3. 최대 아이템 수 제한
    max_items = int(parser_info.get("max_items", 100))

    # 4. 저장 규칙 적용
    storage_rule = parser_info.get("storage_rule", "split_words")
    target_field = parser_info.get("target_field", "unknown")
    print(f"DEBUG: Applying storage_rule: {storage_rule} -> {target_field}")
    
    if storage_rule == "single":
        # whoami, pwd 등 단일 값
        return cleaned
        
    elif storage_rule == "split_lines":
        # find, grep, ls -l 등 줄 단위
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        # 특정 헤더나 불필요한 라인 제거
        if lines and "total" in lines[0]:
            lines = lines[1:]  # "total 24" 같은 첫 줄 제거
        return lines[:max_items]
        
    elif storage_rule == "split_words":
        # 기본 ls, 단어 단위 분할
        words = [word for word in re.split(r'\s+', cleaned) if word and word != 'total']
        return words[:max_items]
        
    elif storage_rule == "extract_paths":
        # 경로 추출
        paths = re.findall(r'(?:^|\s)([~/]?[^\s]+(?:/[^\s]*)*)', cleaned)
        return paths[:max_items]
        
    elif storage_rule == "extract_ips":
        # IP 주소 추출
        ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', cleaned)
        return list(dict.fromkeys(ips))[:max_items]
        
    elif storage_rule == "extract_process_lines":
        # ps 명령어 전용: 헤더 제외
        lines = cleaned.split('\n')
        process_lines = []
        for line in lines:
            line = line.strip()
            # 헤더 라인 스킵 (USER, PID, %CPU 등으로 시작)
            if line and not re.match(r'^(USER|PID|COMMAND|\s*PID)', line):
                process_lines.append(line)
        return process_lines[:max_items]
        
    elif storage_rule == "extract_network_lines":
        # netstat 명령어 전용: 헤더 및 설명 라인 제외
        lines = cleaned.split('\n')
        network_lines = []
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('Active') and 
                not line.startswith('Proto') and
                not line.startswith('Address') and
                ('tcp' in line.lower() or 'udp' in line.lower())):
                network_lines.append(line)
        return network_lines[:max_items]
        
    elif storage_rule == "extract_files":
        # 압축 해제 결과에서 파일명 추출
        lines = cleaned.split('\n')
        files = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('Archive:'):
                if ':' in line and ('inflating:' in line or 'extracting:' in line or 'creating:' in line):
                    filename = line.split(':', 1)[1].strip()
                    if filename:
                        files.append(filename)
                elif line and not line.startswith('Archive'):
                    files.append(line)
        return files[:max_items]
        
    else:
        # 기본값: 단어 분할
        words = [word for word in re.split(r'\s+', cleaned) if word]
        return words[:max_items]

def regex_based_parser(raw_output: str, parser_info: dict) -> list:
    """
    Parses raw output using regex patterns specified in parser_info.
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
    """
    print("Parsing with: llm_based_parser")
    prompt = parser_info.get("llm_prompt")
    if not prompt:
        raise ValueError("prompt_template not found in parser_info for llm_based_parser")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("OPENAI_API_KEY not found or not set in .env file")

    client = OpenAI(api_key=api_key)
    

    token_count = count_tokens(prompt, model="gpt-4o-mini")
    if(token_count > 8000):
        return f"Error: The prompt exceeds the token limit for gpt-4o model. Current token count: {token_count}. Please reduce the input size."
    


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

def parse_output(raw_output: str, parser_info: dict, used_options: str = "", command_block: dict = None, command_name: str = "") -> Union[str, List[str]]:
    """
    Selects the appropriate parser based on the parser_info and parses the raw output.
    """
    parser_type = parser_info.get("type")
    
    if parser_type == "rule_based":
        return rule_based_parser(raw_output, parser_info, used_options, command_block)
    elif parser_type == "regex_based":
        return regex_based_parser(raw_output, parser_info)
    elif parser_type == "llm_based":
        return llm_based_parser(raw_output, parser_info)
   
    else:
        raise ValueError(f"Unknown parser type: {parser_type}")
