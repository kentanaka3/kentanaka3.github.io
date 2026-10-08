#!/usr/bin/env sh

set -eu

doc_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$doc_dir/.." && pwd)
source_file="$doc_dir/cv.tex"
build_pdf="$doc_dir/cv.pdf"
public_pdf="$repo_dir/cv.pdf"
compile=0
clean=0
dry_run=0

usage() {
    printf 'Usage: %s [--compile] [--clean] [--dry-run]\n' "$0"
    printf '\n'
    printf '  --compile   Compile doc/cv.tex twice and copy doc/cv.pdf to cv.pdf.\n'
    printf '  --clean     Remove LaTeX build artifacts under doc/.\n'
    printf '  --dry-run   Preview --clean removals without deleting files.\n'
}

for option in "$@"; do
    case "$option" in
        --compile)
            compile=1
            ;;
        --clean)
            clean=1
            ;;
        --dry-run)
            dry_run=1
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            printf 'Unknown option: %s\n\n' "$option" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ "$compile" -eq 0 ] && [ "$clean" -eq 0 ]; then
    usage >&2
    exit 2
fi

if [ "$dry_run" -eq 1 ] && [ "$clean" -eq 0 ]; then
    printf '%s\n' '--dry-run requires --clean.' >&2
    exit 2
fi

compile_cv() {
    if ! command -v pdflatex >/dev/null 2>&1; then
        printf '%s\n' 'pdflatex was not found on PATH.' >&2
        exit 127
    fi

    if [ ! -f "$source_file" ]; then
        printf 'LaTeX source not found: %s\n' "$source_file" >&2
        exit 1
    fi

    printf 'Compiling %s\n' "$source_file"
    pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory "$doc_dir" "$source_file"
    pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory "$doc_dir" "$source_file"

    if [ ! -f "$build_pdf" ]; then
        printf 'Expected compiled PDF was not created: %s\n' "$build_pdf" >&2
        exit 1
    fi

    cp "$build_pdf" "$public_pdf"
    printf 'Published %s\n' "$public_pdf"
}

clean_cv() {
    find "$doc_dir" -maxdepth 1 -type f \( \
        -name '*.aux' \
        -o -name '*.bbl' \
        -o -name '*.bcf' \
        -o -name '*.blg' \
        -o -name '*.dvi' \
        -o -name '*.fdb_latexmk' \
        -o -name '*.fls' \
        -o -name '*.idx' \
        -o -name '*.ilg' \
        -o -name '*.ind' \
        -o -name '*.lof' \
        -o -name '*.log' \
        -o -name '*.lot' \
        -o -name '*.nav' \
        -o -name '*.out' \
        -o -name '*.run.xml' \
        -o -name '*.snm' \
        -o -name '*.synctex.gz' \
        -o -name '*.toc' \
        -o -name '*.vrb' \
        -o -name '*.xdv' \
        -o -name 'cv.pdf' \
    \) -print | while IFS= read -r file; do
        if [ "$dry_run" -eq 1 ]; then
            printf 'Would remove %s\n' "$file"
        else
            rm -f -- "$file"
            printf 'Removed %s\n' "$file"
        fi
    done

    if [ "$dry_run" -eq 1 ]; then
        printf 'Dry run complete for %s\n' "$doc_dir"
    else
        printf 'LaTeX cleanup complete for %s\n' "$doc_dir"
    fi
}

if [ "$compile" -eq 1 ]; then
    compile_cv
fi

if [ "$clean" -eq 1 ]; then
    clean_cv
fi
