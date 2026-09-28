"""Create a shared draft once, under the central workflow concurrency lock."""
import argparse
from release_common import REPO, draft, gh, version


def prepare_draft(tag):
    version(tag)
    try:
        draft(tag)
    except RuntimeError as exc:
        if 'HTTP 404' not in str(exc):
            raise
        gh('release', 'create', tag, '--repo', REPO, '--target', 'main', '--draft',
           '--title', f'ProdCast {tag} — draft', '--notes',
           'Component builds are collecting here. Assemble and validate the complete package before publishing.')
    current = draft(tag)
    if 'assembly-lock.json' in {a['name'] for a in current['assets']}:
        raise ValueError('Draft is already frozen; choose a new release version')
    print('Draft ready:', current['html_url'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', required=True)
    prepare_draft(parser.parse_args().version)
