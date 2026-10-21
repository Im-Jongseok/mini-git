import json
from datetime import datetime
from hashlib import sha256

from app import algorithms
from app.indexing import InvertedIndex
from app.models import Commit


class Repository:
    """커밋, 브랜치, HEAD, 역색인 저장·조회·관리"""

    def __init__(self, author: str):
        self.author = author
        self.head = "main"
        self.branches: dict[str, str | None] = {"main": None}
        self.commits: dict[str, Commit] = {}
        self.parent_map: dict[str, tuple[str, ...]] = {}
        self.index = InvertedIndex()

    def branch(self, name: str) -> None:
        """현재 커밋을 가리키는 브랜치 생성"""
        if name in self.branches:
            raise ValueError(f"Branch already exists: {name}")
        self.branches[name] = self.branches[self.head]

    def switch(self, name: str) -> None:
        """HEAD 변경"""
        if name not in self.branches:
            raise ValueError(f"Unknown branch: {name}")
        self.head = name

    def commit(self, message: str) -> Commit:
        """커밋과 색인을 추가하고 현재 브랜치를 갱신"""
        parent = self.branches[self.head]
        parents = () if parent is None else (parent,)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = json.dumps([message, self.author, timestamp, parents])
        commit_hash = sha256(payload.encode("utf-8")).hexdigest()
        commit = Commit(
            hash=commit_hash,
            message=message,
            author=self.author,
            timestamp=timestamp,
            parents=parents,
        )
        existing = self.commits.get(commit_hash)
        if existing is not None:
            if existing != commit:
                raise ValueError("Hash collision")
        else:
            self.commits[commit_hash] = commit
            self.parent_map[commit_hash] = commit.parents
            self.index.add(commit_hash, message, self.author)
        self.branches[self.head] = commit_hash
        return self.commits[commit_hash]

    def _resolve_commit(self, commit_hash: str) -> str:
        if commit_hash in self.commits:
            return commit_hash
        matches = [
            name
            for name in self.commits
            if commit_hash and name.startswith(commit_hash)
        ]
        if not matches:
            raise ValueError(f"Unknown commit: {commit_hash}")
        if len(matches) > 1:
            raise ValueError(f"Ambiguous commit: {commit_hash}")
        return matches[0]

    def log(self, sort_by: str | None = None) -> list[Commit]:
        """기본은 위상 순서, 옵션이 있으면 날짜 또는 작성자 순서로 조회한다."""
        if sort_by is None:
            return [
                self.commits[name]
                for name in algorithms.topological_order(self.parent_map)
            ]
        if sort_by not in ("date", "author"):
            raise ValueError("Invalid args")
        field = "timestamp" if sort_by == "date" else "author"
        return algorithms.merge_sort(
            list(self.commits.values()),
            key=lambda commit: getattr(commit, field),
        )

    def path(self, start: str, goal: str) -> list[str] | None:
        """존재하는 두 커밋 사이의 최단 경로를 조회한다."""
        start = self._resolve_commit(start)
        goal = self._resolve_commit(goal)
        neighbors = {node: [] for node in self.parent_map}
        for node, values in self.parent_map.items():
            for parent in values:
                neighbors[node].append(parent)
                neighbors[parent].append(node)

        distances = algorithms.bfs(neighbors, goal)
        if start not in distances:
            return None

        path = [start]
        while path[-1] != goal:
            node = path[-1]
            candidates = [
                neighbor
                for neighbor in neighbors[node]
                if distances.get(neighbor) == distances[node] - 1
            ]
            chosen = min(candidates, key=lambda value: value + "->")
            path.append(chosen)
        return path

    def ancestors(self, commit_hash: str) -> list[Commit]:
        """지정한 커밋의 모든 조상을 조회한다."""
        commit_hash = self._resolve_commit(commit_hash)
        return [
            self.commits[name]
            for name in algorithms.dfs(self.parent_map, commit_hash)[1:]
        ]

    def search_keyword(self, keyword: str) -> list[Commit]:
        """키워드 역색인으로 커밋을 조회한다."""
        return [
            self.commits[name] for name in self.index.find_keyword(keyword)
        ]

    def search_author(self, author: str) -> list[Commit]:
        """작성자 역색인으로 커밋을 조회한다."""
        return [self.commits[name] for name in self.index.find_author(author)]
