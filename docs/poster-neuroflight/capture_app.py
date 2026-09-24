# /// script
# requires-python = ">=3.13"
# dependencies = ["playwright>=1.63,<2"]
# ///
"""Capture a real NeuroFlight comparison for the printed poster."""

from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "app-comparison.png"
FULL = ROOT / "assets" / "app-comparison-full.png"


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True,
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        args=["--use-gl=angle", "--use-angle=swiftshader"],
    )
    page = browser.new_page(viewport={"width": 1920, "height": 1280}, device_scale_factor=4)
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    page.get_by_role("button", name="Ejecutar Misión").wait_for(state="visible")
    page.get_by_role("button", name="Lissajous").click()
    page.get_by_role("button", name="Ejecutar Misión").click()
    page.wait_for_function(
        """() => {
            const button = [...document.querySelectorAll('button')]
                .find(el => el.textContent?.includes('2. Comparación'));
            return button && !button.disabled;
        }""",
        timeout=120_000,
    )
    slider = page.locator('input[type="range"]')
    slider.click(position={"x": 380, "y": 5})
    page.mouse.move(950, 400)
    page.mouse.wheel(0, -520)
    page.wait_for_timeout(300)
    page.screenshot(path=str(FULL), full_page=True)
    page.screenshot(
        path=str(OUT),
        clip={"x": 330, "y": 80, "width": 1270, "height": 705},
    )
    print(OUT)
    print(page.locator("body").inner_text()[:2500])
    browser.close()
