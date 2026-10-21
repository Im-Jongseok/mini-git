import argparse
import shlex
from typing import NoReturn

from app.models import Commit
from app.repository import Repository


def format_commits(commits: list[Commit]) -> str:
    """커밋의 식별자, 작성자, 시각과 메시지를 출력 문자열 만듦"""
    return (
        "\n".join(
            f"commit {commit.hash} ({commit.author}, {commit.timestamp})\n"
            f"    {commit.message}"
            for commit in commits
        )
        or "No commits found."
    )


class CommandParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise ValueError("Invalid args")


def _create_parsers() -> dict[str, CommandParser]:
    arguments = {
        "init": ("author",),
        "branch": ("name",),
        "switch": ("name",),
        "commit": ("message",),
        "log": (),
        "path": ("start", "goal"),
        "ancestors": ("commit_hash",),
        "search": (),
    }
    parsers = {}
    for command, names in arguments.items():
        parser = CommandParser(
            prog=command, add_help=False, allow_abbrev=False
        )
        parser.set_defaults(command=command)
        for name in names:
            parser.add_argument(name)
        parsers[command] = parser
    parsers["log"].add_argument("--sort-by", choices=("date", "author"))
    search = parsers["search"].add_mutually_exclusive_group(required=True)
    search.add_argument("keyword", nargs="?")
    search.add_argument("--author")
    return parsers


_PARSERS = _create_parsers()


def _parse_command(line: str) -> tuple[str, list[str]]:
    parts = line.strip().split(maxsplit=1)
    command = parts[0].lower()
    argument_text = parts[1] if len(parts) == 2 else ""
    try:
        args = shlex.split(argument_text)
    except ValueError:
        raise ValueError("Invalid args") from None
    if command not in {"log", "search"}:
        args.insert(0, "--")
    elif command == "search" and (
        argument_text.startswith(("'", '"'))
        or (args and not args[0].startswith("--"))
    ):
        args.insert(0, "--")
    return command, args


def _initialize(
    repo: Repository | None, author: str
) -> tuple[Repository, str]:
    if repo is not None:
        raise ValueError("Already initialized")
    return Repository(author), (
        "Initialized repository.\nCurrent branch: main\n"
        f"Current user: {author}"
    )


def _search_commits(repo: Repository, args: argparse.Namespace) -> str:
    if args.author is not None:
        found = repo.search_author(args.author)
    else:
        found = repo.search_keyword(args.keyword)
    return format_commits(found)


def _run_command(repo: Repository, args: argparse.Namespace) -> str:
    match args.command:
        case "branch":
            repo.branch(args.name)
            return f"Created branch: {args.name}"
        case "switch":
            repo.switch(args.name)
            return f"Switched to branch: {args.name}"
        case "commit":
            commit = repo.commit(args.message)
            return f"[{repo.head} {commit.hash}] {commit.message}"
        case "log":
            return format_commits(repo.log(args.sort_by))
        case "path":
            path = repo.path(args.start, args.goal)
            return "Path: " + " -> ".join(path) if path else "No path"
        case "ancestors":
            return format_commits(repo.ancestors(args.commit_hash))
        case "search":
            return _search_commits(repo, args)
        case _:
            raise ValueError(f"Unknown command: {args.command}")


def execute(
    repo: Repository | None, line: str
) -> tuple[Repository | None, str]:
    """명령 한 줄을 처리하고 갱신된 저장소와 출력 문자열을 반환"""
    if not line.strip():
        return repo, ""
    try:
        command, args = _parse_command(line)
        parser = _PARSERS.get(command)
        if parser is None:
            raise ValueError(f"Unknown command: {command}")
        if command == "init":
            return _initialize(repo, parser.parse_args(args).author)
        if repo is None:
            raise ValueError("Not initialized")
        args = parser.parse_args(args)
        return repo, _run_command(repo, args)
    except ValueError as error:
        return repo, str(error)
