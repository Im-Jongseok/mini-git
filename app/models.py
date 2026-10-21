from dataclasses import dataclass


@dataclass(frozen=True)
class Commit:
    """커밋 메타데이터"""

    hash: str
    message: str
    author: str
    timestamp: str
    parents: tuple[str, ...] = ()
