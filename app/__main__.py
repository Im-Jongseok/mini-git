from app.cli import execute


def main() -> None:
    """명령을 반복해서 읽고 실행"""
    repo = None
    while True:
        try:
            line = input("mini-git> ")
        except EOFError:
            break
        if line.strip().lower() in {"exit", "quit"}:
            break
        repo, output = execute(repo, line)
        if output:
            print(output)


if __name__ == "__main__":
    main()
