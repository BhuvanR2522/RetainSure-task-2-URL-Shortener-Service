import re
import random
import string
from urllib.parse import urlparse
from typing import Optional

def is_valid_url(url: str) -> bool:
    """
    Validate if the provided string is a valid URL
    
    Args:
        url: The URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        # Check that we have both scheme and netloc
        if not result.scheme or not result.netloc:
            return False
        
        # Check that scheme is http or https
        if result.scheme not in ['http', 'https']:
            return False
        
        # Check that netloc has at least one character
        if len(result.netloc) == 0:
            return False
        
        # Check that netloc contains a dot (basic domain validation)
        if '.' not in result.netloc:
            return False
        
        # Check that netloc doesn't start or end with a dot
        if result.netloc.startswith('.') or result.netloc.endswith('.'):
            return False
        
        # Check that there are no consecutive dots
        if '..' in result.netloc:
            return False
        
        return True
    except:
        return False

def generate_short_code(length: int = 6) -> str:
    """
    Generate a random alphanumeric short code
    
    Args:
        length: Length of the short code (default: 6)
        
    Returns:
        str: Random alphanumeric string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_unique_short_code(existing_codes: set, length: int = 6) -> str:
    """
    Generate a unique short code that doesn't exist in the provided set
    
    Args:
        existing_codes: Set of existing short codes to avoid
        length: Length of the short code (default: 6)
        
    Returns:
        str: Unique short code
    """
    max_attempts = 1000  # Prevent infinite loops
    attempts = 0
    
    while attempts < max_attempts:
        code = generate_short_code(length)
        if code not in existing_codes:
            return code
        attempts += 1
    
    # If we can't find a unique code after max attempts, 
    # increase length and try again
    return generate_short_code(length + 1)

def normalize_url(url: str) -> str:
    """
    Normalize URL by ensuring it has a scheme
    
    Args:
        url: The URL to normalize
        
    Returns:
        str: Normalized URL with scheme
    """
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url