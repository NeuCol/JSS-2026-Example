#!/usr/bin/env bash
# Render analysis/tex/fig_eval.tex to a PNG so the generated TikZ can be
# eyeballed without building the paper around it.
#
# The .tex that generate_graphs.py writes is a bare tikzpicture: it assumes the
# paper's preamble supplies pgfplots, the groupplots library, the evalXxx
# colours, and a real \textwidth. This wraps it in the smallest document that
# supplies all four, so what you see is close to what the paper will show —
# font sizes especially, since every size in the figure is relative to the
# document's 10pt base and 0.27\textwidth panels shrink with a narrow one.
#
#   tools/preview_tikz.sh                 # -> $TMPDIR/fig_eval_preview.png
#   DPI=450 tools/preview_tikz.sh         # higher resolution for detail checks
#   OUT=/tmp/x.png tools/preview_tikz.sh  # choose the output file
#   tools/preview_tikz.sh path/to/texdir  # a different tex directory
#
# Needs pdflatex with pgfplots, and pdftoppm (poppler-utils).
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tex_dir="$(cd "${1:-$here/../analysis/tex}" && pwd)"
dpi="${DPI:-200}"
out="${OUT:-${TMPDIR:-/tmp}/fig_eval_preview.png}"
# TeX Live 2022 ships pgfplots 1.18, but older installs cap out lower and error
# out rather than degrade; override if the paper pins something else.
compat="${PGFPLOTS_COMPAT:-1.16}"
# JSS single-column text width. The panels are sized in \textwidth fractions,
# so previewing at standalone's default width would misrepresent every font.
textwidth="${TEXTWIDTH:-469pt}"

for f in fig_eval.tex eval_colors.tex; do
    [ -f "$tex_dir/$f" ] || { echo "missing $tex_dir/$f — run analysis/generate_graphs.py first" >&2; exit 1; }
done

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cp "$tex_dir/fig_eval.tex" "$tex_dir/eval_colors.tex" "$work/"

cat > "$work/main.tex" <<TEX
\\documentclass[border=4pt]{standalone}
\\usepackage{pgfplots}
\\pgfplotsset{compat=$compat}
\\usepgfplotslibrary{groupplots}
\\setlength{\\textwidth}{$textwidth}
\\input{eval_colors.tex}
\\begin{document}
\\input{fig_eval.tex}
\\end{document}
TEX

if ! (cd "$work" && pdflatex -interaction=nonstopmode -halt-on-error main.tex >build.log 2>&1); then
    echo "pdflatex failed:" >&2
    sed -n '/^!/,+6p' "$work/build.log" >&2
    exit 1
fi

mkdir -p "$(dirname "$out")"
pdftoppm -r "$dpi" -png -singlefile "$work/main.pdf" "${out%.png}"
echo "$out"
