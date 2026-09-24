# /// script
# requires-python = ">=3.13"
# dependencies = ["playwright>=1.63,<2"]
# ///
"""Export the NeuroFlight poster as a single 75 x 105 cm PDF page."""

from pathlib import Path

from playwright.sync_api import sync_playwright


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "poster.html"
OUTPUT = HERE / "poster-neuroflight.pdf"


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True,
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    page = browser.new_page(viewport={"width": 2840, "height": 3970}, device_scale_factor=1)
    page.goto(SOURCE.as_uri(), wait_until="networkidle")
    page.evaluate("document.fonts.ready")
    images = page.locator("img").evaluate_all(
        "els => els.map(el => ({src: el.getAttribute('src'), ok: el.complete && el.naturalWidth > 0}))"
    )
    if any(not image["ok"] for image in images):
        raise RuntimeError(f"Poster has missing images: {images}")
    geometry = page.evaluate(
        """() => [...document.querySelectorAll('.panel')].map(panel => ({
          section: panel.classList[1],
          panelBottom: panel.getBoundingClientRect().bottom,
          contentBottom: Math.max(...[...panel.children].map(el => el.getBoundingClientRect().bottom))
        }))"""
    )
    overflow = [item for item in geometry if item["contentBottom"] > item["panelBottom"] - 5]
    if overflow:
        raise RuntimeError(f"Poster sections overflow: {overflow}")
    page.pdf(path=str(OUTPUT), prefer_css_page_size=True, print_background=True)
    print(OUTPUT)
    print(geometry)
    browser.close()
