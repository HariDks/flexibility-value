#!/bin/sh
# Render memo.html to a five-page PDF via headless Chrome.
# The artifact host supplies the <html>/<head> wrapper, so a standalone copy
# has to be assembled first or the doctype lands after content and Chrome
# falls into quirks mode.
set -e
DIR=$(cd "$(dirname "$0")" && pwd)
python3 - "$DIR" <<'PY'
import pathlib, sys
d = pathlib.Path(sys.argv[1])
t = (d / "memo.html").read_text()
i = t.index('<div class="page">')
(d / ".memo-print.html").write_text(
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    + t[:i] + '</head>\n<body>\n' + t[i:] + '\n</body>\n</html>\n')
PY
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=15000 \
  --print-to-pdf="$DIR/memo.pdf" "file://$DIR/.memo-print.html" 2>/dev/null
rm -f "$DIR/.memo-print.html"
echo "memo.pdf written"
