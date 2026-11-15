# Sourced. split_rule FILE N prints part N of FILE, where parts are runs of whole "## " sections, each at most
# PCO_RULE_PART_MAX characters (default 9000, under the 10,000-character hook output cap with room for a note).
# split_rule_count FILE prints the number of parts. A single section longer than the maximum is its own part.
split_rule() {
  awk -v want="$2" -v max="${PCO_RULE_PART_MAX:-9000}" '
    function flush() { if (sec != "") { if (len > 0 && len + length(sec) > max) { part++; len = 0 }
                         if (part == want) printf "%s", sec; len += length(sec); sec = "" } }
    BEGIN { part = 1; len = 0; sec = "" }
    /^## / { flush() }
    { sec = sec $0 "\n" }
    END { flush() }' "$1"
}
split_rule_count() {
  awk -v max="${PCO_RULE_PART_MAX:-9000}" '
    function flush() { if (sec != "") { if (len > 0 && len + length(sec) > max) { part++; len = 0 }
                         len += length(sec); sec = "" } }
    BEGIN { part = 1; len = 0; sec = "" }
    /^## / { flush() }
    { sec = sec $0 "\n" }
    END { flush(); print part }' "$1"
}
