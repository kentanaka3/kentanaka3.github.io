#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 1 ]]; then
    printf 'Usage: %s [--check]\n' "$0" >&2
    exit 1
fi
case "${1:-}" in
    ""|--check) ;;
    *) printf 'Usage: %s [--check]\n' "$0" >&2; exit 1 ;;
esac

root_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root_dir"
command -v python3 >/dev/null || { printf 'Python 3 is required for validation.\n' >&2; exit 1; }

printf '%s\n' '==> Validating semantic HTML, structured data, and public resources...'
python3 "$root_dir/util/validate_site.py"

if [[ "${1:-}" == --check ]]; then
    exit 0
fi

printf '%s\n' '==> Staging the public site in _site/...'
if [[ -L _site || ( -e _site && ! -d _site ) ]]; then
    printf 'Refusing to replace a symlink or non-directory at _site.\n' >&2
    exit 1
fi
rm -rf -- _site
mkdir -p _site/data _site/web/css _site/web/js _site/web/img
cp index.html cv.pdf llms.txt _site/
cp web/css/index.css _site/web/css/
cp web/js/index.js _site/web/js/
cp data/cv.json _site/data/
cp web/img/fish.png web/img/logo-hanko.png _site/web/img/
printf '%s\n' '[PASS] Public artifact prepared; no commit or push was performed.'