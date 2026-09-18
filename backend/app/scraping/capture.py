"""Capture original page evidence before destructive text cleanup."""

import json
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import settings

ROOT = Path(__file__).resolve().parents[2] / "data" / "captures"


def artifact_path(artifact_id: str, filename: str) -> Path:
    return ROOT / settings.data_mode / str(UUID(artifact_id)) / filename


async def capture_evidence(page) -> str:
    artifact_id = str(uuid4())
    folder = artifact_path(artifact_id, "screenshot.png").parent
    folder.mkdir(parents=True, exist_ok=False)
    try:
        await page.screenshot(path=str(folder / "screenshot.png"), full_page=True)
        # outerHTML alone loses open shadow roots. Store each root separately.
        dom = await page.evaluate("""() => {
            const roots = [];
            function visit(root, path) {
                for (const [i, el] of [...root.querySelectorAll('*')].entries()) {
                    if (el.shadowRoot) {
                        const key = path + '/' + el.tagName.toLowerCase() + '[' + i + ']';
                        roots.push({host: key, html: el.shadowRoot.innerHTML});
                        visit(el.shadowRoot, key);
                    }
                }
            }
            visit(document, 'document');
            return {html: document.documentElement.outerHTML, shadow_roots: roots,
                    url: location.href, viewport: {width: innerWidth, height: innerHeight},
                    state: 'as rendered; accordions not automatically expanded'};
        }""")
        (folder / "dom.json").write_text(
            json.dumps(dom, ensure_ascii=False), encoding="utf-8"
        )
    except BaseException:
        for item in folder.iterdir():
            item.unlink()
        folder.rmdir()
        raise
    return artifact_id
