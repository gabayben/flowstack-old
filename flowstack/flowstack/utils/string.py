def extract_words(text: str) -> list[str]:
    text = text.replace(r'\s', ' ')
    text = text.replace(r' +', ' ')
    text.strip()
    return text.split(' ')

def count_words(text: str) -> int:
    return len(extract_words(text))

def count_tokens(text: str) -> int:
    return round(count_words(text) * 1.3)