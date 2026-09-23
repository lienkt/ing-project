"""Capture original page evidence before destructive text cleanup."""

import json
import shutil
from pathlib import Path
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2] / "data" / "captures"


DOM_SCRIPT = """() => {
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
        }"""


def artifact_path(artifact_id: str, filename: str) -> Path:
    folder = str(UUID(artifact_id))
    path = ROOT / folder / filename
    if not path.exists():
        # Read artifacts saved under an older storage namespace.
        previous = list(ROOT.glob(f"*/{folder}/{filename}"))
        if len(previous) == 1:
            return previous[0]
    return path


async def capture_evidence(page) -> str:
    artifact_id = str(uuid4())
    folder = artifact_path(artifact_id, "screenshot.png").parent
    folder.mkdir(parents=True, exist_ok=False)
    try:
        await page.screenshot(path=str(folder / "screenshot.png"), full_page=True)
        # outerHTML alone loses open shadow roots. Store each root separately.
        dom = await page.evaluate(DOM_SCRIPT)
        (folder / "dom.json").write_text(
            json.dumps(dom, ensure_ascii=False), encoding="utf-8"
        )
    except BaseException:
        for item in folder.iterdir():
            item.unlink()
        folder.rmdir()
        raise
    return artifact_id


def capture_evidence_sync(page) -> str:
    """Save the same PageCapture artifacts from the message renderer."""

    artifact_id = str(uuid4())
    folder = artifact_path(artifact_id, "screenshot.png").parent
    folder.mkdir(parents=True, exist_ok=False)
    try:
        page.screenshot(path=str(folder / "screenshot.png"), full_page=True)
        (folder / "dom.json").write_text(
            json.dumps(page.evaluate(DOM_SCRIPT), ensure_ascii=False), encoding="utf-8"
        )
    except BaseException:
        shutil.rmtree(folder)
        raise
    return artifact_id
