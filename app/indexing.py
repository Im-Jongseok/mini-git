class InvertedIndex:
    """키워드와 작성자별 커밋 식별자를 저장"""

    def __init__(self):
        self.keyword_index: dict[str, list[str]] = {}
        self.author_index: dict[str, list[str]] = {}

    def add(self, commit_hash: str, message: str, author: str) -> None:
        """메시지의 중복 토큰을 제거해 색인에 추가"""
        for token in set(message.lower().split()):
            self.keyword_index.setdefault(token, []).append(commit_hash)
        self.author_index.setdefault(author, []).append(commit_hash)

    def find_keyword(self, keyword: str) -> list[str]:
        """검색어의 모든 토큰이 있는 커밋을 등록 순서로 반환"""
        tokens = keyword.lower().split()
        if not tokens:
            return []
        candidates = self.keyword_index.get(tokens[0], [])
        remaining = [
            set(self.keyword_index.get(token, [])) for token in tokens[1:]
        ]

        return [
            commit_hash for commit_hash in candidates
            if all(commit_hash in matches for matches in remaining)
        ]

    def find_author(self, author:str) -> list[str]:
        """작성자 이름이 정확히 일치하는 커밋을 반환"""
        return list(self.author_index.get(author, []))