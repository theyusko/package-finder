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
        '--cores', '-cores', '--num-cores',
        '-p', '--processes', '-processes', 
        '--parallel', '-parallel',
        '--jobs', '-j', 
        '--workers', '-w',
        '--cpus', '-cpus',
        '--threads-per-process', '--tpp'
    }
    
    thread_patterns = [
        r'-t\s*\d+',
        r'--threads\s*\d+',
        r'--thread\s*\d+',
        r'-n\s*\d+',
        r'--num-threads\s*\d+',
        r'--cores\s*\d+'
        r'-p\s*\d+',
        r'--processes\s*\d+',
        r'--parallel\s*\d*',
        r'-j\s*\d+',
        r'--jobs\s*\d+',
        r'--workers\s*\d+',
        r'--cpus\s*\d+',
        r'--threads-per-process\s*\d+'
    ]
    
    text_to_search = (description or '').lower() + ' ' + (readme or '').lower()
    
    found_flags = set()
    
    for keyword in thread_keywords:
        if keyword in text_to_search:
            found_flags.add(keyword)
    
    for pattern in thread_patterns:
        if re.search(pattern, text_to_search):
            matches = re.findall(pattern, text_to_search)
            found_flags.update(matches)
    
    threading_indicators = [
        'parallel', 'multithread', 'multi-thread', 'multi thread', 
        'concurrent', 'cpu cores', 'processor cores',
        'parallel processing', 'thread pool', 'threadpool',
        'multithreading', 'parallelization', 'concurrent processing',
        'distributed computing', 'parallel computation'
    ]
    
    has_threading = any(word in text_to_search for word in threading_indicators)
    
    return has_threading or len(found_flags) > 0, list(found_flags)