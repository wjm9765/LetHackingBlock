import tiktoken

def count_tokens(text, model="gpt-4o"):
    """입력 텍스트의 토큰 수를 계산합니다"""
    encoder = tiktoken.encoding_for_model(model)
    tokens = encoder.encode(text)
    return len(tokens)