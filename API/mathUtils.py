"""
Any needed math function here
"""

from typing import Optional

def parseNum(x: any) -> Optional[float]:
    try:
        return float(x) if x not in (None, "", "NaN") else None
    except ValueError:
        return None