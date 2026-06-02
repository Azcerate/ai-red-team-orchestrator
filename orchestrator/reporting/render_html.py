"""HTML (and PDF) rendering."""
from __future__ import annotations
from pathlib import Path
from .builder import ReportModel
from .render_md import render_markdown

_HTML_SHELL = """<!doctype html><html><head><meta charset="utf-8">
<title>AI Red Team Report — {client}</title>
<style>
body{{font-family:system-ui,Arial,sans-serif;max-width:920px;margin:2rem auto;color:#13203a}}
h1{{color:{primary}}} table{{border-collapse:collapse;width:100%}}
td,th{{border:1px solid #ccc;padding:6px 10px;text-align:left}}
blockquote{{background:#f5f7fb;border-left:4px solid {primary};padding:8px 12px}}
</style></head><body>
{body}
<hr><footer style="color:#888;font-size:.85rem">{footer}</footer>
</body></html>"""


def render_html(model: ReportModel, out_dir: str = "reports") -> Path:
    md_path = render_markdown(model, out_dir)
    body = _markdown_to_html(md_path.read_text(encoding="utf-8"))
    branding = (model.meta or {}).get("branding", {})
    html = _HTML_SHELL.format(client=model.client,
                              primary=branding.get("primary_color", "#0B3D91"),
                              body=body, footer=branding.get("footer", "Confidential"))
    out = Path(out_dir) / f"{model.run_id}.html"
    out.write_text(html, encoding="utf-8")
    return out


def render_pdf(model: ReportModel, out_dir: str = "reports") -> Path:
    html_path = render_html(model, out_dir)
    out = Path(out_dir) / f"{model.run_id}.pdf"
    try:
        from weasyprint import HTML
    except Exception as e:
        raise NotImplementedError(
            "PDF needs WeasyPrint: pip install weasyprint "
            f"(HTML written to {html_path}). Import error: {e}")
    HTML(string=html_path.read_text(encoding="utf-8")).write_pdf(str(out))
    return out


def _markdown_to_html(md: str) -> str:
    try:
        import markdown
        return markdown.markdown(md, extensions=["tables"])
    except Exception:
        return f"<pre>{md}</pre>"
