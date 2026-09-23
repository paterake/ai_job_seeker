"""
Build a 7-section merged HTML + combined JSON shortlist from per-section _shortlist_A…G.json outputs.
Performs cross-section dedup (first-section wins), re-numbers rank, writes timestamped + latest-alias,
and prints a summary used by the human-readable report Step 6.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from html import escape as _h
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "implementation" / "job_seeker" / "src"))

from ai_job_seeker.cli import (  # noqa: E402
    _render_merged_table,
    _DUAL_STYLES_EXTRA,
    _stamp_for_output,
    _write_with_timestamp,
    _atomic_json_dump,
)
from ai_job_seeker.ingest.schema import JobListing, ListingSource, _parse_date  # noqa: E402
from ai_job_seeker.match.schema import ScoredListing  # noqa: E402
from ai_job_seeker.match.deterministic import hard_blocked  # noqa: E402


def _rehydrate_listing(d: dict) -> JobListing:
    d = dict(d or {})
    src_raw = d.get("source") or "unknown"
    if isinstance(src_raw, str):
        try:
            src = ListingSource(src_raw)
        except ValueError:
            src = ListingSource.UNKNOWN
    else:
        src = ListingSource.UNKNOWN
    d["source"] = src
    d["posted_at"] = _parse_date(d.get("posted_at"))
    d.setdefault("source_id", "")
    d.setdefault("title", "")
    d.setdefault("company", "")
    d.setdefault("location", "")
    d.setdefault("description", "")
    d.setdefault("url", "")
    return JobListing(**{k: d[k] for k in [
        "source", "source_id", "title", "company", "location", "description", "url",
        "posted_at", "salary_min", "salary_max", "remote", "contract_type",
    ] if k in d})


def _rehydrate_scored(d: dict) -> ScoredListing:
    return ScoredListing(
        listing=_rehydrate_listing(d.get("listing") or {}),
        phase1_score=float(d.get("phase1_score") or 0.0),
        phase1_evidence=list(d.get("phase1_evidence") or []),
        phase2_score=(float(d["phase2_score"]) if d.get("phase2_score") is not None else None),
        phase2_rationale=(list(d["phase2_rationale"]) if d.get("phase2_rationale") is not None else None),
        fabricated_claim_flags=list(d.get("fabricated_claim_flags") or []),
        final_score=float(d.get("final_score") or 0.0),
        ranked_position=d.get("ranked_position"),
    )

SECTIONS: list[dict] = [
    {
        "key": "A",
        "title": "Marketing & Communications",
        "tagline": "Graduate entry-level marketing, comms, content, PR, brand & social roles.",
        "badge_class": "badge-marketing",
        "json": "_pipeline/_shortlist_A.json",
    },
    {
        "key": "B",
        "title": "Historian, Research & Academic",
        "tagline": "Research, insight, policy, bid-writing, editorial, heritage & museum — broad creative History-BA fit.",
        "badge_class": "badge-history",
        "json": "_pipeline/_shortlist_B.json",
    },
    {
        "key": "C",
        "title": "Accounts, Finance & Audit",
        "tagline": "Highest CV-proof match (85/100 success-likelihood) — numeracy + audit + accounts office experience.",
        "badge_class": "badge-marketing",
        "json": "_pipeline/_shortlist_C.json",
    },
    {
        "key": "D",
        "title": "Office, Admin & Secretarial",
        "tagline": "#2 success-likelihood — reception, front-of-house, office manager, admin experience all present.",
        "badge_class": "badge-history",
        "json": "_pipeline/_shortlist_D.json",
    },
    {
        "key": "E",
        "title": "Events & Customer Service",
        "tagline": "#3 success-likelihood — hospitality + waiting-staff + client-facing engagement CV proofs.",
        "badge_class": "badge-marketing",
        "json": "_pipeline/_shortlist_E.json",
    },
    {
        "key": "F",
        "title": "HR, People & Recruitment",
        "tagline": "#4 success-likelihood — stakeholder engagement + office/admin track translates cleanly into HR grad roles.",
        "badge_class": "badge-history",
        "json": "_pipeline/_shortlist_F.json",
    },
    {
        "key": "G",
        "title": "Teaching, Tutoring & Education Support",
        "tagline": "#5 success-likelihood — 3+ years academic support + Kumon marking + TA proofs on CV.",
        "badge_class": "badge-marketing",
        "json": "_pipeline/_shortlist_G.json",
    },
]

OUT_DIR = Path(__file__).resolve().parent / "implementation" / "job_seeker" / "config" / "output"


def _dedup_key(d: dict) -> tuple[str, str]:
    lst = d.get("listing") or {}
    return (
        (lst.get("title") or "").strip().lower(),
        (lst.get("company") or "").strip().lower(),
    )


def load_section(sec: dict) -> list[dict]:
    p = OUT_DIR / sec["json"]
    if not p.exists():
        return []
    raw = json.loads(p.read_text(encoding="utf-8"))
    # dual-cohort write for B: {"history":[...]} wrapper; single-cohort writes: [list]
    if isinstance(raw, dict):
        for k in ("history", "marketing", "scored"):
            if k in raw and isinstance(raw[k], list):
                return raw[k]
        return []
    if isinstance(raw, list):
        return raw
    return []


def esc(x) -> str:
    return "" if x is None else _h(str(x))


def salary_range(d: dict) -> str:
    lst = d.get("listing") or {}
    mn = lst.get("salary_min")
    mx = lst.get("salary_max")
    if mn and mx:
        return f"£{mn:,}–£{mx:,}"
    if mn:
        return f"£{mn:,}+"
    if mx:
        return f"≤£{mx:,}"
    return ""


def salary_min_int(d: dict) -> int:
    lst = d.get("listing") or {}
    return int(lst.get("salary_min") or 0)


def build_7_section_html(
    scored_sections: list[dict],
    out_path: Path,
    *,
    candidate_name: str,
    search_terms: str,
    location: str,
    per_section_removed: dict[str, int],
    applied_total: int,
) -> Path:
    ts = datetime.now()

    meta_bits: list[str] = [f"Generated: {esc(ts.strftime('%A %d %B %Y, %H:%M'))}"]
    if search_terms:
        meta_bits.append(f"Search:&nbsp;<code>{esc(search_terms)}</code>")
    if location:
        meta_bits.append(f"Location:&nbsp;<code>{esc(location)}</code>")
    meta_html = " · ".join(meta_bits)

    # Badge colors for 7 cohorts — reuse marketing/history + extras cycled
    badge_colors = [
        ("badge-marketing", "#fdf2f8", "#9d174d"),
        ("badge-history",   "#ecfeff", "#155e75"),
        ("badge-accounts",  "#dcfce7", "#166534"),
        ("badge-admin",     "#fef3c7", "#92400e"),
        ("badge-events",    "#ffedd5", "#9a3412"),
        ("badge-hr",        "#fae8ff", "#86198f"),
        ("badge-teach",     "#e0e7ff", "#3730a3"),
    ]

    styles = f"""
<style>
  :root {{
    --bg: #fafbfc;
    --fg: #1f2937;
    --muted: #6b7280;
    --border: #e5e7eb;
    --accent: #1d4ed8;
    --accent-2: #0f766e;
    --zebra: #f3f4f6;
    --pill: #eef2ff;
    --pill-green: #dcfce7;
    --pill-grey: #f3f4f6;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0 auto; max-width: 1180px; padding: 32px 24px 80px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg); color: var(--fg); font-size: 15px; line-height: 1.45;
  }}
  h1 {{ margin: 0 0 6px; font-size: 28px; }}
  .meta {{ color: var(--muted); margin-bottom: 8px; }}
  code {{ background: #eef0f3; padding: 1px 6px; border-radius: 4px; font-size: 13px; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .apply {{ word-break: break-all; font-size: 13px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin: 10px 0 20px; box-shadow: 0 1px 2px rgba(0,0,0,.03); }}
  th, td {{ padding: 11px 12px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }}
  th {{ background: #111827; color: #f9fafb; font-weight: 600; font-size: 13px; letter-spacing: .01em; }}
  tbody tr:nth-child(even) td {{ background: var(--zebra); }}
  td.pos, td.score, td.src, td.dt, td.sal {{ white-space: nowrap; }}
  td.score, td.sal {{ font-variant-numeric: tabular-nums; }}
  td.pos {{ text-align: right; font-weight: 600; }}
  td.role a {{ font-weight: 600; }}
  .pill {{ display: inline-block; background: var(--pill); color: #3730a3; padding: 2px 8px; border-radius: 999px; font-size: 12px; margin: 2px 4px 2px 0; }}
  .pill-green {{ background: var(--pill-green); color: #166534; }}
  .pill-grey  {{ background: var(--pill-grey);  color: #374151; }}
  .score-pill {{ float: right; display: inline-block; background: var(--accent); color: #fff; padding: 2px 10px; border-radius: 999px; font-size: 13px; font-weight: 600; }}
  .score-line {{ margin: 4px 0 8px; }}
  .rationale {{ margin: 8px 0; padding: 8px 12px; background: #ecfeff; color: #0c4a6e; border: 1px solid #a5f3fc; border-radius: 6px; }}
  .card {{
    background: #fff; border: 1px solid var(--border); border-radius: 10px;
    margin-bottom: 12px; padding: 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,.03);
  }}
  .card summary {{ cursor: pointer; font-size: 16px; list-style: none; padding: 4px 0; }}
  .card summary::-webkit-details-marker {{ display: none; }}
  .card summary:hover {{ color: var(--accent); }}
  .card > * + * {{ margin-top: 8px; }}
  .ev ul {{ margin: 6px 0 0 0; padding-left: 20px; }}
  .flags {{ color: #991b1b; background: #fef2f2; padding: 8px 12px; border-radius: 6px; border: 1px solid #fecaca; }}
  h2 {{ font-size: 20px; }}
  .footer {{ margin-top: 40px; color: var(--muted); font-size: 12px; text-align: center; }}
  .cohort-h2 {{ display: flex; align-items: baseline; gap: 12px; margin-top: 40px; }}
  .cohort-badge {{
    display: inline-block; font-size: 13px; font-weight: 600;
    padding: 3px 10px; border-radius: 999px; letter-spacing: .02em;
  }}
  .badge-marketing {{ background: #fdf2f8; color: #9d174d; }}
  .badge-history   {{ background: #ecfeff; color: #155e75; }}
  .badge-accounts  {{ background: #dcfce7; color: #166534; }}
  .badge-admin     {{ background: #fef3c7; color: #92400e; }}
  .badge-events    {{ background: #ffedd5; color: #9a3412; }}
  .badge-hr        {{ background: #fae8ff; color: #86198f; }}
  .badge-teach     {{ background: #e0e7ff; color: #3730a3; }}
  .cohort-intro {{ color: var(--muted); margin: 4px 0 18px; }}
  .toc {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; margin: 16px 0 28px; }}
  .toc h3 {{ margin: 0 0 8px; font-size: 14px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
  .toc ul {{ margin: 0; padding-left: 20px; }}
  .toc li {{ margin: 3px 0; }}
  .stats-pills {{ margin: 6px 0 0; }}
  table.merged-table {{ margin: 8px 0 32px; }}
  table.merged-table tbody tr.role-row td,
  table.merged-table tbody tr.detail-row td {{ border-bottom: none; }}
  table.merged-table tbody tr.detail-row {{ border-bottom: 1px solid var(--border); }}
  table.merged-table tbody tr.detail-row.alt-band td.evidence-row,
  table.merged-table tbody tr.role-row.alt-band td {{ background: var(--zebra); }}
</style>
"""

    toc_lines: list[str] = [
        '<div class="toc">',
        "<h3>Contents — 7 independently-ranked sections</h3>",
        "<ul>",
    ]
    for i, sec in enumerate(scored_sections):
        count = len(sec["scored"])
        removed = per_section_removed.get(sec["key"], 0)
        toc_lines.append(
            f'<li><a href="#sec-{sec["key"]}"><b>Section {sec["key"]}.</b> {esc(sec["title"])}</a> '
            f'— top {count} (applied-roles filtered: {removed} removed from {applied_total} tracked applications)</li>'
        )
    toc_lines.append("</ul>")
    toc_lines.append(
        '<p style="margin:10px 0 0;color:var(--muted);font-size:13px">'
        "Sections are independently ranked, ordered by success-likelihood fit to your CV. "
        "Cross-section dedup applied — no role appears twice across A–G (first matching section wins). "
        "Role details, score evidence and Apply buttons are merged inline per role (2-row-band table format, no separate accordion cards)."
        "</p></div>"
    )
    toc_html = "\n".join(toc_lines)

    sections_html: list[str] = []
    for i, sec in enumerate(scored_sections):
        key = sec["key"]
        scored = sec["scored"]
        stats_html = ""
        if scored:
            sals = [salary_min_int(x) for x in scored if salary_min_int(x) > 0]
            sal_low = min(sals) if sals else 0
            sal_high = max(sals) if sals else 0
            avg = round(sum(x.get("final_score", 0) for x in scored) / len(scored), 1)
            badges = [
                f'<span class="pill pill-green">Count:&nbsp;{len(scored)}</span>',
                f'<span class="pill">CV match avg:&nbsp;{avg:.1f}</span>',
            ]
            if sal_low and sal_high:
                badges.append(f'<span class="pill pill-grey">Salary band:&nbsp;£{sal_low:,}–£{sal_high:,}</span>')
            elif sal_low:
                badges.append(f'<span class="pill pill-grey">Salary min:&nbsp;£{sal_low:,}+</span>')
            stats_html = '<div class="stats-pills">' + " ".join(badges) + "</div>"

        try:
            rendered = _render_merged_table(sec["scored_objs"])
        except Exception as _e:
            print(f"[WARN] render section {key} failed: {_e}", file=sys.stderr)
            rendered = "<p><i>Rendering skipped for this section.</i></p>"

        sections_html.append(
            f"""
<a id="sec-{esc(key)}"></a>
<div class="cohort-h2">
  <h2 style="margin:0">Section {esc(key)} — {esc(sec["title"])}</h2>
  <span class="cohort-badge badge-{['marketing','history','accounts','admin','events','hr','teach'][i]}">
    SECTION {esc(key)} · TOP {len(scored)}
  </span>
</div>
<p class="cohort-intro">{esc(sec["tagline"])}</p>
{stats_html}
{rendered}
"""
        )

    body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Shortlist — {esc(candidate_name)} · 7 Sections</title>
{styles}
</head>
<body>
<h1>{esc(candidate_name)}&nbsp;· Job Shortlist (7 Sections)</h1>
<p class="meta">{meta_html}</p>
<p>
  <b>{sum(len(s["scored"]) for s in scored_sections)}</b> shortlisted roles across
  <b>{len(scored_sections)}</b> independently-ranked sections, sorted by success-likelihood fit to your CV.
  <code>agent</code> mode — phase-1 deterministic scoring only (no LLM / Ollama, 8GB M3 safe).
</p>

{toc_html}

{"".join(sections_html)}

<p class="footer">Generated by ai_job_seeker (Stage 3 Match · 7-section expanded pipeline · agent mode) · {esc(datetime.now().isoformat(timespec='seconds'))}</p>
</body>
</html>
"""

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    return out_path


def main() -> int:
    ts_run, _ = _stamp_for_output()
    candidate_name = "Kiera Patel"

    loaded_sections: list[dict] = []
    total_hard_blocked = 0
    hard_blocked_reasons: dict[str, int] = {}
    for sec_def in SECTIONS:
        raw_list = load_section(sec_def)
        filtered = []
        for d in raw_list:
            lst_obj = _rehydrate_listing(d.get("listing") or {})
            reason = hard_blocked(lst_obj)
            if reason is None:
                filtered.append(d)
            else:
                total_hard_blocked += 1
                hard_blocked_reasons[reason] = hard_blocked_reasons.get(reason, 0) + 1
        loaded_sections.append({
            "key": sec_def["key"],
            "title": sec_def["title"],
            "tagline": sec_def["tagline"],
            "badge_class": sec_def["badge_class"],
            "raw": filtered,
        })
    if total_hard_blocked:
        print(f"[build hard-block] Defence-in-depth: {total_hard_blocked} role(s) "
              f"dropped post-match (should already be filtered upstream).")
        for r, n in sorted(hard_blocked_reasons.items(), key=lambda kv: -kv[1]):
            print(f"  · {n}× {r}")

    applied_total_path = OUT_DIR / "_pipeline" / "applied_jobs.json"
    applied_total = 0
    if applied_total_path.exists():
        try:
            applied_total = len(json.loads(applied_total_path.read_text(encoding="utf-8")))
        except Exception:
            applied_total = 0

    # Cross-section dedup (first wins) + re-number ranked_position
    seen_keys: set[tuple[str, str]] = set()
    per_section_removed: dict[str, int] = {}
    final_sections: list[dict] = []

    for sec in loaded_sections:
        kept: list[dict] = []
        removed = 0
        for d in sec["raw"]:
            k = _dedup_key(d)
            if k in seen_keys:
                removed += 1
                continue
            seen_keys.add(k)
            kept.append(d)
        per_section_removed[sec["key"]] = removed
        # Renumber rank
        for i, d in enumerate(kept, start=1):
            d["ranked_position"] = i
        # Rehydrate to ScoredListing objects for table rendering
        hydrate = [_rehydrate_scored(d) for d in kept]
        for i, obj in enumerate(hydrate, start=1):
            obj.ranked_position = i
        final_sections.append({
            "key": sec["key"],
            "title": sec["title"],
            "tagline": sec["tagline"],
            "badge_class": sec["badge_class"],
            "scored": kept,              # plain dicts for JSON
            "scored_objs": hydrate,      # rehydrated objects for render
        })

    # Per-section counts + stats for report
    report_rows: list[dict] = []
    for sec in final_sections:
        scored = sec["scored"]
        if scored:
            sals = [salary_min_int(x) for x in scored if salary_min_int(x) > 0]
            low = min(sals) if sals else 0
            high = max(sals) if sals else 0
            avg = round(sum(x.get("final_score", 0) for x in scored) / len(scored), 1)
            top3 = [
                {
                    "role": (x.get("listing") or {}).get("title"),
                    "company": (x.get("listing") or {}).get("company"),
                    "salary": salary_range(x),
                    "score": round(x.get("final_score", 0), 1),
                }
                for x in scored[:3]
            ]
        else:
            low = high = 0
            avg = 0
            top3 = []
        report_rows.append({
            "key": sec["key"],
            "title": sec["title"],
            "count": len(scored),
            "cv_match_avg": avg,
            "salary_min": low,
            "salary_max": high,
            "cross_dedup_removed": per_section_removed.get(sec["key"], 0),
            "top3": top3,
        })

    # 1) Combined JSON — {a,b,c,d,e,f,g: [...], generated_at}
    combined_payload = {s["key"].lower(): s["scored"] for s in final_sections}
    combined_payload["generated_at"] = ts_run.isoformat(timespec="seconds")
    combined_payload["sections_meta"] = report_rows
    combined_payload["applied_roles_tracked"] = applied_total

    combined_json_path = OUT_DIR / "_pipeline" / "latest_shortlist.json"
    s_json, latest_json = _write_with_timestamp(
        str(combined_json_path),
        lambda p, pl=combined_payload: _atomic_json_dump(pl, p),
        ts=ts_run,
    )
    print(f"Wrote combined JSON : {s_json}")
    print(f"  (latest alias     : {latest_json})")

    # Also per-section latest JSON in _pipeline for traceability
    for sec in final_sections:
        sec_json = OUT_DIR / "_pipeline" / f"latest_shortlist_{sec['key'].lower()}.json"
        try:
            s, l = _write_with_timestamp(
                str(sec_json),
                lambda p, arr=sec["scored"]: _atomic_json_dump(arr, p),
                ts=ts_run,
            )
            print(f"  wrote sec-{sec['key']} JSON: {l}")
        except Exception as _e:
            print(f"  warn sec-{sec['key']} JSON: {_e}", file=sys.stderr)

    # 2) Markdown shortlist (combined, engineering traceability only; _pipeline/)
    md_lines: list[str] = []
    md_lines.append(f"# Job Shortlist — {candidate_name} (7 Sections)")
    md_lines.append("")
    md_lines.append(f"Generated: {ts_run.isoformat(timespec='seconds')}  ")
    md_lines.append("Location: `London`  ")
    md_lines.append(
        "Search: `marketing exec grad + marketing assist grad + research assist grad + policy grad + "
        "bid writer grad + accounts grad + grad admin + events grad + HR grad + grad TA`"
    )
    md_lines.append("")
    md_lines.append(
        f"Total shortlisted: **{sum(len(s['scored']) for s in final_sections)} roles** across 7 sections. "
        f"Applied-roles tracked: {applied_total}."
    )
    md_lines.append("")
    md_lines.append("| Section | Focus | Count | CV match avg | Salary band | Cross-dedup removed |")
    md_lines.append("|---|---|---:|---:|---|---:|")
    for r in report_rows:
        band = (
            f"£{r['salary_min']:,}–£{r['salary_max']:,}"
            if r["salary_min"] and r["salary_max"]
            else "not listed"
        )
        md_lines.append(
            f"| {r['key']} | {r['title']} | {r['count']} | {r['cv_match_avg']:.1f} | {band} | {r['cross_dedup_removed']} |"
        )
    md_lines.append("")
    for sec in final_sections:
        r = next(x for x in report_rows if x["key"] == sec["key"])
        md_lines.append(f"## Section {sec['key']} — {sec['title']}")
        md_lines.append("")
        md_lines.append(f"> {sec['tagline']}")
        md_lines.append("")
        md_lines.append(
            f"Count: **{len(sec['scored'])}** · Avg CV match: **{r['cv_match_avg']:.1f}** · "
            f"Cross-dedup removed: {r['cross_dedup_removed']}"
        )
        md_lines.append("")
        md_lines.append("| # | Score | Source | Role | Company | Salary |")
        md_lines.append("|---|---:|---|---|---|---|")
        for d in sec["scored"]:
            lst = d.get("listing") or {}
            url = lst.get("url") or ""
            title = lst.get("title") or ""
            t80 = (title[:80] + "…") if len(title) > 80 else title
            role_md = f"[{t80}]({url})" if url else t80
            sal = salary_range(d)
            src = lst.get("source") or "?"
            if isinstance(src, dict):
                src = src.get("value") or "?"
            md_lines.append(
                f"| {d.get('ranked_position', '?')} "
                f"| {d.get('final_score', 0):.1f} "
                f"| {src} "
                f"| {role_md} "
                f"| {lst.get('company') or ''} "
                f"| {sal} |"
            )
        md_lines.append("")

    md_path = OUT_DIR / "_pipeline" / "latest_shortlist.md"
    try:
        s_md, latest_md = _write_with_timestamp(
            str(md_path),
            lambda p, lines=md_lines: (lambda pp=Path(p): (pp.parent.mkdir(parents=True, exist_ok=True), pp.write_text("\n".join(lines), encoding="utf-8"), pp)[-1])(),
            ts=ts_run,
        )
        print(f"Wrote Markdown      : {s_md}")
        print(f"  (latest alias     : {latest_md})")
    except Exception as _e:
        print(f"  warn markdown: {_e}", file=sys.stderr)

    # 3) Build Kiera-facing 7-section HTML at top-level (Kiera-facing only)
    html_path = OUT_DIR / "latest_shortlist.html"

    def _html_writer(p, fs=final_sections, cn=candidate_name,
                     st="9 pooled grad searches (marketing x2, research/policy/bid-writer, accounts, admin, events, HR, teaching)",
                     loc="London", rm=per_section_removed, at=applied_total):
        return build_7_section_html(
            fs,
            Path(p),
            candidate_name=cn,
            search_terms=st,
            location=loc,
            per_section_removed=rm,
            applied_total=at,
        )

    try:
        s_html, latest_html = _write_with_timestamp(str(html_path), _html_writer, ts=ts_run)
        print(f"Wrote shortlist HTML: {s_html}")
        print(f"  (latest alias     : {latest_html})")
    except Exception as _e:
        print(f"ERROR html write: {_e}", file=sys.stderr)
        raise

    # 4) Print compact per-section report on stdout for Step 6 to pick up
    print()
    print("=== 7-SECTION PIPELINE SUMMARY ===")
    print(f"Total roles shortlisted across sections: {sum(len(s['scored']) for s in final_sections)}")
    print(f"Applied roles tracked (filtered per section): {applied_total}")
    for r in report_rows:
        band = (
            f"£{r['salary_min']:,}–£{r['salary_max']:,}"
            if r["salary_min"] and r["salary_max"]
            else "not listed"
        )
        print(
            f"  [{r['key']}] {r['title']:<40} count={r['count']:>3}  "
            f"avgCV={r['cv_match_avg']:>4.1f}  band={band:<20}  "
            f"cross-dedup-removed={r['cross_dedup_removed']:>2}"
        )
        for t in r["top3"]:
            print(
                f"      · #{t.get('score',0):.1f}  {t['role'][:60]}  —  {t['company'] or '?'}  ({t['salary'] or 'no sal'})"
            )
    print("=== END SUMMARY ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
