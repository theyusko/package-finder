import re
from typing import Tuple, List

def find_thread_flags(description: str, readme: str = None) -> Tuple[bool, List[str]]:
    """
    Analyze package description and readme for threading support.
    Returns (has_threading, thread_flags).
    """
    thread_keywords = {
        '-t', '--threads', '-threads', '--thread', '-thread',
        '--nthreads', '-nthreads', '--num-threads', '-n',
        '--cores', '-cores', '--num-cores'
    }
    
    # Common patterns for thread-related flags
    thread_patterns = [
        r'-t\s*\d+',
        r'--threads\s*\d+',
        r'--thread\s*\d+',
        r'-n\s*\d+',
        r'--num-threads\s*\d+',
        r'--cores\s*\d+'
    ]
    
    text_to_search = (description or '').lower() + ' ' + (readme or '').lower()
    
    # Look for thread-related keywords
    found_flags = set()
    
    # Check for exact matches of thread flags
    for keyword in thread_keywords:
        if keyword in text_to_search:
            found_flags.add(keyword)
    
    # Check for pattern matches
    for pattern in thread_patterns:
        if re.search(pattern, text_to_search):
            matches = re.findall(pattern, text_to_search)
            found_flags.update(matches)
    
    # Also look for general threading indicators
    has_threading = any(word in text_to_search for word in 
                       ['parallel', 'multithread', 'multi-thread', 'multi thread', 
                        'concurrent', 'cpu cores', 'processor cores'])
    
    return has_threading or len(found_flags) > 0, list(found_flags)