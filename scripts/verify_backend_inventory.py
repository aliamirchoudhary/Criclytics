"""Read-only release guard: unexpected remote files require operator review."""
import argparse
from pathlib import Path


def unexpected_files(remote, staged):
    staged = Path(staged)
    allowed = {p.relative_to(staged).as_posix() for p in staged.rglob('*') if p.is_file()}
    allowed.add('.gitattributes')  # Hosting-managed metadata.
    return set(remote) - allowed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--staged', type=Path, default=Path('build/backend'))
    args = parser.parse_args()
    if not args.staged.is_dir():
        parser.error('Stage the backend before checking inventory')
    try:
        from huggingface_hub import HfApi
        remote = HfApi().list_repo_files(args.repo, repo_type='space')
    except Exception as error:
        raise SystemExit('Remote inventory unavailable: ' + type(error).__name__) from None
    count = len(unexpected_files(remote, args.staged))
    if count:
        raise SystemExit(f'Release blocked: {count} unexpected remote files need operator review; nothing deleted')
    print('Remote inventory matches the staged allowlist')


if __name__ == '__main__':
    main()
