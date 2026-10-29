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
#   5. A path on the allowlist, or covered by an active entry in the repo's committed exception registry, passes
#      unscanned. An entry counts only in HEAD (`git show`), never in the working tree, and Office types are never
#      excepted (step 1 returns first). An entry whose rule is the config's exception_rule fails the gate closed
#      when a field is missing, a date is not a quoted ISO string, or its status is not active, expired or revoked;
#      for an active, unexpired entry it also fails closed when expires minus granted exceeds exception_max_days,
#      the evidence file is not in HEAD, or the scope is not `path:<glob>` whose first segment is a plain name
#      (letters, digits, dot, dash, underscore: no pattern characters; not . or ..) and no segment is `..`.
#      Entries that are expired or revoked, or past expires, are skipped and the file is scanned.
#   6. Scan with the patterns, ignoring a match equal to an allowlisted string.
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

# One tagged line per setting: T type, S size cap, R exception rule, M exception max days, P name<TAB>regex,
# A path glob, X exact string.
config=""
if command -v ruby >/dev/null 2>&1; then
    config="$(ruby -ryaml -e "
d = YAML.load_file(ARGV[0])
d['office_types'].each { |t| puts \"T#{t.to_s.downcase}\" }
puts \"S#{Integer(d['max_scan_bytes'])}\"
puts \"R#{d.fetch('exception_rule')}\"
puts \"M#{Integer(d['exception_max_days'])}\"
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

# Repo exceptions, read from the committed registry only. No git, no HEAD or no file means no exceptions.
registry="$(git -C "$REPO_ROOT" show HEAD:ai_context/project/governance/exception_registry.yaml 2>/dev/null)" || registry=""
if [[ -n "$registry" ]]; then
    ex="$(printf '%s\n' "$registry" | ruby -ryaml -rdate -e '
bad = ->(m) { puts "!#{m}"; exit 1 }
rule, max = ARGV[0], Integer(ARGV[1])
d = YAML.safe_load(STDIN.read, permitted_classes: [Date])
ex = d.is_a?(Hash) ? d["exceptions"] : nil
bad.("exceptions is not a list") unless ex.is_a?(Array)
iso = /\A\d{4}-\d{2}-\d{2}\z/
ex.each do |e|
  bad.("an entry is not a mapping") unless e.is_a?(Hash)
  next unless e["rule"] == rule
  %w[id rule justification owner granted_by granted expires scope status evidence].each do |k|
    bad.("entry lacks #{k}") if e[k].nil? || e[k].to_s.strip.empty?
  end
  g, x = %w[granted expires].map do |k|
    bad.("#{k} is not a quoted ISO date") unless e[k].is_a?(String) && e[k] =~ iso
    begin Date.iso8601(e[k]) rescue bad.("#{k} does not parse") end
  end
  bad.("status is not active, expired or revoked") unless %w[active expired revoked].include?(e["status"])
  next if e["status"] != "active" || Date.today >= x
  bad.("expires is more than #{max} days after granted") if (x - g) > max
  m = /\Apath:(.+)\z/.match(e["scope"].to_s)
  bad.("scope is not path:<glob>") unless m
  glob = m[1]
  first = glob.split("/", 2)[0].to_s
  bad.("scope glob is not anchored to a literal first segment") unless first =~ /\A[A-Za-z0-9._-]+\z/ && first != "." && first != ".." && !glob.split("/").include?("..")
  ev = e["evidence"].to_s
  bad.("evidence is not a repo-relative path") if ev.start_with?("/") || ev.split("/").include?("..")
  puts "E#{ev}"
  puts "G#{glob}"
end
' "$(printf '%s\n' "$config" | sed -n 's/^R//p')" "$(printf '%s\n' "$config" | sed -n 's/^M//p')" 2>/dev/null)" ||
        stop "cannot read exception registry: $(printf '%s\n' "$ex" | sed -n 's/^!//p')"
    globs="$(printf '%s\n' "$ex" | sed -n 's/^G//p')"
    while IFS= read -r ev; do
        git -C "$REPO_ROOT" cat-file -e "HEAD:$ev" 2>/dev/null || stop "cannot read exception registry: evidence is not in HEAD"
    done < <(printf '%s\n' "$ex" | sed -n 's/^E//p')
    if [[ -n "$globs" ]]; then
        # Canonical path of the file (symlinks followed), compared with the canonical repo root.
        target="$resolved"
        [[ "$target" == /* ]] || target="$PWD/$target"
        canon="$(cd -P "$(dirname "$target")" 2>/dev/null && pwd -P)/$(basename "$target")"
        root="$(cd -P "$REPO_ROOT" && pwd -P)"
        if [[ "$canon" == "$root"/* ]]; then
            rel="${canon#"$root"/}"
            while IFS= read -r glob; do
                # shellcheck disable=SC2053
                [[ "$rel" == $glob ]] && exit 0
            done <<< "$globs"
        fi
    fi
fi

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
