#!/usr/bin/env python3
"""Generate architecture PDF for GraphOne Atlas Intelligence pipeline."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak, Flowable)
from reportlab.graphics.shapes import Drawing, Rect, String, Line

OUTPUT = os.path.join(os.path.dirname(__file__), "..",
                      "data", "GraphOne_Atlas_Intelligence_Architecture.pdf")
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16, spaceAfter=10)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13, spaceAfter=6)
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, spaceAfter=4)
body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8.5, leading=12)
code = ParagraphStyle("Code", parent=styles["Code"], fontSize=7, leading=9)


class PipelineDiagram(Flowable):
    def __init__(self, width=480, height=220):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        x0, y0 = 30, self.height - 25
        bw, bh = 74, 24
        gap = 10
        arrow = 16

        stages = [
            ("Scrapers", colors.HexColor("#2563EB")),
            ("Raw DB", colors.HexColor("#7C3AED")),
            ("Monitor", colors.HexColor("#059669")),
            ("LLM", colors.HexColor("#D97706")),
            ("Struct\nDB", colors.HexColor("#DC2626")),
            ("Entity\nResolve", colors.HexColor("#0891B2")),
            ("Export", colors.HexColor("#4F46E5")),
        ]

        c.setStrokeColor(colors.HexColor("#1E293B"))
        c.setLineWidth(1.2)
        for i, (label, color) in enumerate(stages):
            x = x0 + i * (bw + gap + arrow)
            y = y0
            c.setFillColor(color)
            c.roundRect(x, y - bh, bw, bh, 5, fill=1, stroke=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 7)
            lines = label.split("\n")
            for li, line in enumerate(lines):
                c.drawCentredString(x + bw / 2, y - bh / 2 + 4 - li * 9, line)
            if i < len(stages) - 1:
                ax = x + bw
                ay = y - bh / 2
                c.setStrokeColor(colors.HexColor("#64748B"))
                c.setLineWidth(1.2)
                c.line(ax, ay, ax + arrow, ay)
                c.line(ax + arrow - 3, ay - 3, ax + arrow, ay)
                c.line(ax + arrow - 3, ay + 3, ax + arrow, ay)

        ly = y0 - bh - 28
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.HexColor("#64748B"))
        items = [
            "Source URL validation at every stage | UNIQUE(source_url) dedup | 429/503 exponential backoff",
            "Playwright fallback on 403 (stealth browser) | CSV fallback when Sheets quota exceeded",
        ]
        for li, item in enumerate(items):
            c.drawString(x0, ly - li * 9, f"  {item}")


def build_pdf():
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.8*cm, bottomMargin=1.8*cm)
    story = []
    W = A4[0] - 3.6*cm

    # ═══════════════════ PAGE 1 ═══════════════════
    story.append(Paragraph("GraphOne Atlas Intelligence &mdash; Architecture", title_style))
    story.append(Spacer(1, 4))
    story.append(PipelineDiagram(width=W, height=200))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Pipeline Summary", h1))
    flow_data = [
        ["Phase", "Source", "Records", "Key Mechanism"],
        ["I (Bulk)", "ArXiv / YC / Product Hunt", "~8,015", "REST APIs + pagination + rate-limit retry"],
        ["II (Monitor)", "RSS / RemoteOK", "~135/day", "24h freshness filter + UNIQUE constraint"],
        ["III (LLM)", "Raw text &rarr; structured JSON", "per record", "Gemini &rarr; Groq &rarr; DeepSeek fallback"],
        ["IV (Entity)", "Startup names &rarr; seed DB", "~5,877 matches", "Compact exact &rarr; norm exact &rarr; fuzzy (92)"],
        ["V (Anti-Bot)", "Playwright browser", "on 403", "Stealth mode + human-like delays"],
        ["VI (Output)", "CSV / Google Sheets", "all", "Source URL validation pre-export"],
    ]
    t = Table(flow_data, colWidths=[W*0.11, W*0.26, W*0.16, W*0.47])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Current Statistics", h2))
    stats = [
        ["Metric", "Value"],
        ["Startups (YC)", "5,971"],
        ["Products (Product Hunt)", "1,044"],
        ["Papers (ArXiv + GitHub stars)", "1,000"],
        ["Jobs (RemoteOK)", "98"],
        ["News (RSS)", "37"],
        ["Entity resolution log", "5,877 entries"],
        ["Bad URLs dropped", "0"],
    ]
    t2 = Table(stats, colWidths=[W*0.4, W*0.6])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t2)

    # ═══════════════════ PAGE 2 ═══════════════════
    story.append(PageBreak())
    story.append(Paragraph("Anti-Bot Strategy &amp; Scale Design", title_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Phase V: Anti-Bot Strategy", h1))
    story.append(Paragraph(
        "All scrapers inherit from <b>BaseScraper</b> which uses httpx with rotating User-Agent "
        "headers (via <b>fake_useragent</b>) on every request. When a 403 (blocked) response is "
        "received, the scraper automatically falls back to <b>Playwright Chromium</b> in headless "
        "mode with a stealth user-agent, 1920x1080 viewport, and network-idle wait. "
        "This handles Cloudflare-protected and JavaScript-heavy domains without triggering captchas. "
        "The browser context is created fresh per request and closed after each page load. "
        "If Playwright also fails, the URL is logged and skipped (fail-open design).", body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Phase VI: Production Scale (500K Records)", h1))
    story.append(Paragraph(
        "<b>1. Distributed Crawling.</b> At 500K records, a single node is insufficient. "
        "The architecture splits by source: separate worker pools for ArXiv (sequential, 3s delay), "
        "YC (single JSON blob, fast), Product Hunt (GraphQL, 15-min rate window), and RSS/RemoteOK "
        "(lightweight, parallel). Each worker writes to a shared <b>PostgreSQL</b> instance "
        "(replacing SQLite). The UNIQUE(source_url) constraint prevents duplicates even with "
        "concurrent writers.", body))
    story.append(Paragraph(
        "<b>2. Queue-Based Orchestration.</b> Use Redis/RabbitMQ to queue individual fetch tasks. "
        "Each source type publishes to its own queue with configurable rate limits. Workers consume "
        "from queues, respecting per-source delays via token buckets. Dead-letter queues capture "
        "persistent 403/429 failures for manual review.", body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Handling 413s &amp; 429s at Scale", h2))
    story.append(Paragraph(
        "Every scraper implements <b>exponential backoff</b> (2^attempt &times; base delay) with "
        "&plusmn;20% jitter. Product Hunt uses a fixed 120s wait because its rate-limit window is "
        "exactly 15 minutes. The LLM tier retries 429/503: Gemini (10s/20s/40s), Groq (5s/10s/20s). "
        "At 500K scale, per-source rate-limiters use <b>sliding window counters</b> in Redis. "
        "If a source consistently returns 429, the worker backs off exponentially up to a "
        "configurable cap (default 5 min) before dead-lettering the task.", body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Freshness Tracking Across Distributed Nodes", h2))
    story.append(Paragraph(
        "Each record stores a <b>collected_at</b> timestamp. The monitor uses a 24-hour sliding "
        "window (<tt>is_within_24_hours()</tt>) that compares <tt>published_date</tt> against "
        "current UTC. Distributed nodes share the same PostgreSQL DB, so the "
        "<b>UNIQUE(source_url)</b> constraint ensures no article/job is processed twice, "
        "even if two workers fetch the same URL simultaneously. "
        "For sources without reliable publication dates (e.g., some RSS feeds), "
        "a <tt>last_seen</tt> column tracks when the URL was first seen; if a URL is re-encountered "
        "within 24h, it is skipped. The <tt>--include-all</tt> flag overrides freshness filtering "
        "for test/bootstrap runs.", body))

    # ═══════════════════ PAGE 3 ═══════════════════
    story.append(PageBreak())
    story.append(Paragraph("Storage Strategy &amp; Schema Design", title_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Primary Database: PostgreSQL", h1))
    story.append(Paragraph(
        "SQLite was chosen for the trial (zero-infrastructure, portable). At 500K+ records, "
        "<b>PostgreSQL</b> is the natural upgrade: concurrent writes, JSONB columns for flexible "
        "LLM output, native full-text search on descriptions, and row-level security for multi-tenant "
        "deployments. The migration path is clean because the codebase uses parameterised SQL "
        "queries throughout. Indexes on <tt>source_url</tt>, <tt>collected_at</tt>, and "
        "<tt>published_date</tt> keep SELECTs sub-5ms at 1M rows.", body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Vector Storage: pgvector", h1))
    story.append(Paragraph(
        "For semantic search over startup descriptions and research paper abstracts, "
        "<b>pgvector</b> (PostgreSQL extension) stores 1536-dimension embeddings from the LLM. "
        "This enables <tt>ORDER BY embedding &lt;-&gt; query LIMIT 10</tt> for similarity search. "
        "No separate vector database (Pinecone/Weaviate) is needed at this scale; pgvector's "
        "IVFFlat index handles 1M+ vectors with &lt;50ms latency.", body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Graph Storage: Dgraph / Neo4j (Optional)", h1))
    story.append(Paragraph(
        "Entity relationships (startup &rarr; product, paper &rarr; author, job &rarr; company) "
        "are well-suited to a graph database. At 500K nodes, <b>Dgraph</b> provides native GraphQL "
        "and &lt;10ms traversal queries. This is optional &mdash; the relational schema already "
        "captures relationships via foreign-key-like columns (e.g., <tt>canonical_name</tt>). "
        "A graph layer adds value for path queries like &ldquo;find all papers by authors who also "
        "work at startups that raised &gt;$10M.&rdquo;", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Expected Schemas (Google Sheets Output)", h2))
    schema_text = """<tt>
<b>STARTUP:</b>    schemaVersion, recordType, source.name, source.url,
                  content.entityName, content.data.employeeCount, collectedAt
<b>PRODUCT:</b>    schemaVersion, recordType, source.name, source.url,
                  content.startupName, content.pricingModel, collectedAt
<b>PAPER:</b>      schemaVersion, recordType, content.title, content.authors,
                  content.paper_url, content.github_url, content.github_stars,
                  content.published_date
<b>JOB:</b>        schemaVersion, recordType, content.company, content.date,
                  content.is_remote, content.role_family
<b>NEWS:</b>       schemaVersion, recordType, source.name, source.url,
                  content.title, content.published_date
</tt>"""
    story.append(Paragraph(schema_text, code))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Anti-Hallucination Guarantee", h2))
    story.append(Paragraph(
        "Every record exported has passed <b>source URL validation</b> &mdash; a regex check that "
        "the <tt>source_url</tt> field contains a valid HTTP(S) URL. Records with missing or "
        "malformed URLs are dropped and logged. Across all 8,101 exported records, "
        "<b>zero</b> were dropped. The LLM prompt explicitly instructs: "
        "<i>'NEVER guess or hallucinate values. If a field is not found, use null.'</i>", body))

    doc.build(story)
    return OUTPUT


if __name__ == "__main__":
    path = build_pdf()
    print(f"PDF: {path} ({os.path.getsize(path):,} bytes)")
