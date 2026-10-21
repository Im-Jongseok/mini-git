from collections.abc import Mapping, Sequence


def merge_sort(items: list, key) -> list:
    """key 기준으로 안전 병합 정렬"""
    if len(items) < 2:
        return list(items)
    middle = len(items) // 2
    left = merge_sort(items[:middle], key)
    right = merge_sort(items[:middle], key)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(right[j]) < key(left[i]):
            result.append(right[j])
            j += 1
        else:
            result.append(left[i])
            i += 1
    return result + left[i:] + right[j:]


def topological_order(parents: dict[str, tuple[str, ...]]) -> list[str]:
    """Kahn 알고리즘으로 부모가 먼저 오는 순서를 구함"""
    children = {node: [] for node in parents}
    indegree = {}
    for node, values in parents.items():
        indegree[node] = len(values)
        for parent in values:
            children[parent].append(node)
    ready = [node for node in parents if indegree[node] == 0]
    position = 0
    while position < len(ready):
        node = ready[position]
        position += 1
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(ready) != len(parents):
        raise ValueError("Cycle detected")
    return ready


def bfs(neighbors: Mapping[str, Sequence[str]], start: str) -> dict[str, int]:
    """시작점에서 도달 가능한 노드까지의 최단 거리를 구함"""
    distances = {start: 0}
    queue = [start]
    position = 0
    while position < len(queue):
        node = queue[position]
        position += 1
        for neighbor in neighbors.get(node, ()):
            if neighbor not in distances:
                distances[neighbor] = distances[node] + 1
                queue.append(neighbor)
    return distances


def dfs(neighbors: Mapping[str, Sequence[str]], start: str) -> list[str]:
    """시작점을 포함한 방문 순서를 반환한다."""
    visited = set()
    result = []
    stack = [start]
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            result.append(node)
            stack.extend(neighbors.get(node, ()))
    return result
