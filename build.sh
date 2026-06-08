#!/usr/bin/env bash
# Regenerate the self-contained sally-knowledge-graph.html by inlining the
# vendored force-graph UMD build and the base64-embedded fonts into the source
# template. No network needed. Run after editing sally-knowledge-graph.src.html
# or refreshing anything under vendor/.
set -euo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
src   = open("sally-knowledge-graph.src.html").read()
fonts = open("vendor/fonts.css").read()
fg    = open("vendor/force-graph.min.js").read().replace("</script>", "<\\/script>")
assert "/*__FONTS_CSS__*/" in src and "/*__FORCE_GRAPH_JS__*/" in src
out = src.replace("/*__FONTS_CSS__*/", fonts).replace("/*__FORCE_GRAPH_JS__*/", fg)
open("sally-knowledge-graph.html", "w").write(out)
print("built sally-knowledge-graph.html (%d bytes)" % len(out))
PY
