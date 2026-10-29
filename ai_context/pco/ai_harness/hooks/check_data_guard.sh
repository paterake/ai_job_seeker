#!/usr/bin/env bash
# check_data_guard.sh — gate for one file read or search; agent-neutral. The agent's adapter passes the file path as
# an argument (it may be empty). Refuses a file that holds personal data or is an Office document, so neither reaches
# the model. Types, patterns, allowlist and size cap come from governance/data_guard.yaml.
# Usage: check_data_guard.sh --path <file path>
# Pass: exit 0, no output. Deny: exit 2, one GOVERNANCE STOP line on stderr. The line names the reason code, the path,
# the pattern (or type) and the line number, never matched text: the adapter forwards stderr to the model.
# Evaluation order:
#   1. Deny by Office type on the name, even if the file does not exist: case-insensitive on the extension of the
#      given name and of the name it resolves to through symlinks. If ruby or the config is unavailable, this step
#      does not decide and evaluation continues.
#   2. An empty path, a directory or a missing file: exit 0.
#   3. Otherwise `file`, ruby and the config (a type list and a pattern list, both non-empty) are required, or exit 2.
#   4. A file over the size cap, or a binary one (a PDF, say), passes unscanned. Both are known gaps.
#   5. Scan with the patterns, ignoring a path on the allowlist and a match equal to an allowlisted string.
set -uo pipefail

stop() {
    printf 'GOVERNANCE STOP: check_data_guard.sh %s\n' "$1" >&2
    exit 2
}
refuse() {
    printf 'GOVERNANCE STOP: denial_reason: data_guard_refused; path: %s; %s\n' "$path" "$1" >&2
    exit 2
}

path=""
given=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --path)
            [[ $# -ge 2 ]] || stop "--path needs a value"
            path="$2"
            given=1
            shift 2
            ;;
        *) stop "unknown argument: $1" ;;
    esac
done
[[ $given -eq 1 ]] || stop "was given no --path (wire the agent adapter)"

# The repo root is four levels above this script: <repo>/ai_context/pco/ai_harness/hooks/.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
CONFIG="$REPO_ROOT/ai_context/pco/governance/data_guard.yaml"

# One tagged line per setting: T type, S size cap, P name<TAB>regex, A path glob, X exact string.
config=""
if command -v ruby >/dev/null 2>&1; then
    config="$(ruby -ryaml -e "
d = YAML.load_file(ARGV[0])
d['office_types'].each { |t| puts \"T#{t.to_s.downcase}\" }
puts \"S#{Integer(d['max_scan_bytes'])}\"
d['patterns'].each { |n, r| puts \"P#{n}\t#{r}\" }
(d.dig('allowlist', 'paths') || []).each { |g| puts \"A#{g}\" }
(d.dig('allowlist', 'strings') || []).each { |s| puts \"X#{s}\" }
" "$CONFIG" 2>/dev/null)"
fi
have_config=0
if printf '%s\n' "$config" | grep -q '^T' && printf '%s\n' "$config" | grep -q '^P'; then have_config=1; fi

[[ -n "$path" ]] || exit 0

# Office type, on the given name and on the name after following symlinks.
if [[ $have_config -eq 1 ]]; then
    resolved="$path"
    n=0
    while [[ -L "$resolved" && $n -lt 40 ]]; do
        t="$(readlink "$resolved")"
        [[ "$t" == /* ]] && resolved="$t" || resolved="$(dirname "$resolved")/$t"
        n=$((n + 1))
    done
    for name in "$path" "$resolved"; do
        ext="$(printf '%s' "${name##*.}" | tr '[:upper:]' '[:lower:]')"
        [[ "$name" == *.* ]] && printf '%s\n' "$config" | grep -qx "T$ext" && refuse "type: $ext"
    done
fi

[[ -f "$path" ]] || exit 0

[[ $have_config -eq 1 ]] || stop "cannot enforce: no usable ruby or $CONFIG (type and pattern lists must be non-empty)"
command -v file >/dev/null 2>&1 || stop "cannot enforce: file not found on PATH"

cap="$(printf '%s\n' "$config" | sed -n 's/^S//p')"
[[ "$(wc -c < "$path")" -le "$cap" ]] || exit 0
[[ "$(file -b --mime-encoding -- "$path")" != binary ]] || exit 0

while IFS= read -r glob; do
    # shellcheck disable=SC2053
    [[ "$path" == $glob ]] && exit 0
done < <(printf '%s\n' "$config" | sed -n 's/^A//p')

allowed="$(printf '%s\n' "$config" | sed -n 's/^X//p')"
while IFS=$'\t' read -r name regex; do
    while IFS=: read -r line match; do
        # The phone, national_id and card_number patterns match one boundary character on each side; compare without it.
        skip=0
        if [[ -n "$allowed" ]]; then
            lead="${match#?}"; trail="${match%?}"
            for cand in "$match" "$lead" "$trail" "${lead%?}"; do
                printf '%s\n' "$allowed" | grep -qxF -- "$cand" && skip=1 && break
            done
        fi
        [[ $skip -eq 1 ]] && continue
        refuse "pattern: $name; line: $line"
    done < <(LC_ALL=C grep -noE -- "$regex" "$path" 2>/dev/null)
done < <(printf '%s\n' "$config" | sed -n 's/^P//p')
exit 0
