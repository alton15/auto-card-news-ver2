"""Render logo.html to PNG using Playwright."""
from pathlib import Path
from playwright.sync_api import sync_playwright

def main() -> None:
    logo_html = Path(__file__).parent / "logo.html"
    output_path = Path(__file__).parent / "logo.png"

    html_content = logo_html.read_text(encoding="utf-8")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 400, "height": 400})
        page.set_content(html_content, wait_until="networkidle")
        page.screenshot(path=str(output_path), type="png")
        browser.close()

    print(f"Logo saved to {output_path}")

if __name__ == "__main__":
    main()
