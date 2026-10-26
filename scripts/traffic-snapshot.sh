#!/bin/bash
# Für launchd nach ~/.local/bin/chemdraw-traffic-snapshot.sh kopieren (Documents ist dort gesperrt).
# Rohdaten bleiben unter ~/.local/share/chemdraw-mcp/traffic, nie im öffentlichen Repo.
set -euo pipefail
export PATH=/usr/bin:/bin:/usr/sbin:/sbin
export GH_PROMPT_DISABLED=1
export GH_REPO=jurimaxam-dotcom/chemdraw-mcp
GH=${CHEMDRAW_TRAFFIC_GH:-/Users/tom/.local/bin/gh}
ROOT=${CHEMDRAW_TRAFFIC_ROOT:-/Users/tom/.local/share/chemdraw-mcp}
OUT="$ROOT/traffic"
DATUM=$(/bin/date +%F)
printf '%s traffic-snapshot start pid=%s\n' "$(/bin/date -Iseconds)" "$$"
/bin/mkdir -p "$OUT"
cd "$ROOT"
TMP=$(/usr/bin/mktemp -d "$OUT/.snapshot.XXXXXX")
trap '/bin/rm -rf "$TMP"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
REPO=$GH_REPO
"$GH" api "repos/$REPO/traffic/views" > "$TMP/views.json"
"$GH" api "repos/$REPO/traffic/clones" > "$TMP/clones.json"
"$GH" api "repos/$REPO/traffic/popular/referrers" > "$TMP/referrers.json"
"$GH" api "repos/$REPO/traffic/popular/paths" > "$TMP/paths.json"
# Messzeit gehört zum Traffic, nicht zum Ende der nachfolgenden Profilabrufe.
CAPTURED=$(/bin/date -u +%Y-%m-%dT%H:%M:%SZ)
# Traffic zuerst atomar sichern: auch Abbruch/Fehler im Zusatzteil verliert ihn nicht.
/usr/bin/jq -en --arg datum "$DATUM" --arg captured_at "$CAPTURED" \
  --slurpfile views "$TMP/views.json" --slurpfile clones "$TMP/clones.json" \
  --slurpfile referrers "$TMP/referrers.json" --slurpfile paths "$TMP/paths.json" \
  '{datum: $datum, captured_at: $captured_at, views: $views[0], clones: $clones[0],
    referrers: $referrers[0], paths: $paths[0], stargazers: null,
    stargazers_error: "Stargazer collection incomplete"}
   | if (.views.count | type) == "number" and (.views.views | type) == "array"
     and (.clones.count | type) == "number" and (.clones.clones | type) == "array"
     and (.referrers | type) == "array" and (.paths | type) == "array"
     then . else error("Invalid traffic response") end' > "$TMP/base.json"
/bin/cp "$TMP/base.json" "$TMP/publish.json"
/bin/mv "$TMP/publish.json" "$OUT/$DATUM.json"
printf 'null\n' > "$TMP/stargazers.json"
STAR_ERROR=''
if "$GH" api "repos/$REPO/stargazers?per_page=100" --paginate \
    -H 'Accept: application/vnd.github.star+json' > "$TMP/pages.json" \
    && /usr/bin/jq -es 'if all(.[]; type == "array") then add // [] else error("Invalid star page") end' \
       "$TMP/pages.json" > "$TMP/stars.json"; then
  : > "$TMP/profiles.jsonl"
  while IFS= read -r STAR; do
    LOGIN=$(/usr/bin/jq -r '.user.login' <<< "$STAR")
    PROFILE_ERROR=''
    if ! "$GH" api "users/$LOGIN" > "$TMP/profile.json" \
        || ! /usr/bin/jq -e 'type == "object" and (.created_at | type == "string")' \
             "$TMP/profile.json" > /dev/null; then
      printf '{}\n' > "$TMP/profile.json"
      PROFILE_ERROR='Profile fetch failed'
      printf 'traffic-snapshot warning: profile unavailable login=%s\n' "$LOGIN" >&2
    fi
    /usr/bin/jq -n --argjson star "$STAR" --slurpfile profile "$TMP/profile.json" \
      --arg error "$PROFILE_ERROR" \
      '$profile[0] as $p | {login: $star.user.login, starred_at: $star.starred_at,
       created_at: $p.created_at, followers: $p.followers, public_repos: $p.public_repos,
       location: $p.location, company: $p.company, bio: $p.bio,
       profile_error: (if $error == "" then null else $error end)}' >> "$TMP/profiles.jsonl"
  done < <(/usr/bin/jq -c '.[]' "$TMP/stars.json")
  /usr/bin/jq -s '.' "$TMP/profiles.jsonl" > "$TMP/stargazers.json"
else
  STAR_ERROR='Stargazer fetch failed; traffic retained'
  printf 'traffic-snapshot warning: %s\n' "$STAR_ERROR" >&2
fi
/usr/bin/jq -en --arg error "$STAR_ERROR" --slurpfile base "$TMP/base.json" \
  --slurpfile stargazers "$TMP/stargazers.json" \
  '$base[0] + {stargazers: $stargazers[0],
    stargazers_error: (if $error == "" then null else $error end)}' > "$TMP/snapshot.json"
/bin/mv "$TMP/snapshot.json" "$OUT/$DATUM.json"
printf '%s traffic-snapshot ok repo=%s file=%s\n' \
  "$(/bin/date -Iseconds)" "$REPO" "$OUT/$DATUM.json"
