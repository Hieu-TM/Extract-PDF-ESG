import re

def clean_number_string(text: str) -> str:
    """Removes non-numeric characters except dots and commas."""
    if text is None:
        return None
    # Replace spaces used as thousands separators
    text = str(text).replace(" ", "")
    # Remove currency symbols and other text
    text = re.sub(r'[^\d.,\-]', '', text)
    return text

def parse_float(text: str) -> float:
    """Parses a messy string into a float, handling different locale separators."""
    if not text:
        return None
    
    text = str(text).strip()
    # Find last occurrence of dot or comma
    last_dot = text.rfind('.')
    last_comma = text.rfind(',')

    if last_dot > last_comma:
        # e.g. 1,234,567.89 or 1234.56
        if last_comma != -1: # has comma
            text = text.replace(',', '')
    elif last_comma > last_dot:
        # e.g. 1.234.567,89 or 1234,56
        if last_dot != -1: # has dot
            text = text.replace('.', '')
        text = text.replace(',', '.')
    else:
        # Neither comma nor dot
        pass
        
    try:
        return float(text)
    except ValueError:
        return None

def normalize_multiplier(value: float, context: str) -> float:
    """Normalizes numbers based on standard text multipliers (millions, billions, etc)."""
    if value is None:
        return None
        
    context_lower = context.lower()
    
    if re.search(r'\b(billion|bn|b)\b', context_lower):
        return value * 1_000_000_000
    elif re.search(r'\b(million|m)\b', context_lower):
        return value * 1_000_000
    elif re.search(r'\b(thousand|k)\b', context_lower):
        return value * 1_000
    
    return value
