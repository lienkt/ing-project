"""Run message and tone analysis for every configured bank URL."""

import argparse
import json
import time
from pathlib import Path

if __package__:
    from ..config_messages import MIN_WORDS, PRODUCT_UNSPECIFIED
    from .function_messages import (
        DEBUG_DIR,
        calculate_features,
        count_words,
        has_enough_content,
        infer_product,
        print_source,
        render_page,
    )
else:
    from config_messages import MIN_WORDS, PRODUCT_UNSPECIFIED
    from backend.text_and_content.function_messages import (
        DEBUG_DIR,
        calculate_features,
        count_words,
        has_enough_content,
        infer_product,
        print_source,
        render_page,
    )


URL_FILE = Path(__file__).with_name("product_urls.json")
OUTPUT_FILE = Path("all_banks_message_and_tone.json")


def load_bank_urls(path: Path = URL_FILE) -> list[tuple[str, str, str, bool]]:
    """Load (bank, product, url, product_specified) from the product URL file.

    Each entry looks like:
    {"bank": "ING", "product": "savings account", "url": "https://..."}
    The "product" field is optional. When it's missing, main() falls back to
    guessing the category from the page itself (see infer_product) so the
    output still has something to compare across banks.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("urls", [])
    bank_urls = [
        (
            entry["bank"],
            entry.get("product") or PRODUCT_UNSPECIFIED,
            entry["url"],
            bool(entry.get("product")),
        )
        for entry in entries
        if isinstance(entry, dict) and entry.get("bank") and entry.get("url")
    ]

    if not bank_urls:
        raise ValueError(f"No bank URLs found in {path}")
    return bank_urls


def warn_if_products_differ(products: list[str], stage: str) -> None:
    """Warn when the banks are not being compared on the same product."""
    still_unspecified = sum(1 for product in products if product == PRODUCT_UNSPECIFIED)
    distinct = {product for product in products if product != PRODUCT_UNSPECIFIED}
    if still_unspecified:
        print(
            f"WARNING: {still_unspecified} of {len(products)} entries still have no "
            f"product ({stage}), so comparability across banks can't be fully checked."
        )
    if len(distinct) > 1:
        print(
            "WARNING: the banks are not compared on the same product "
            f"({', '.join(sorted(distinct))}). Differences in tone may reflect "
            "the product, not the bank."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run message and tone analysis for configured bank URLs."
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="BANK",
        help=(
            "Only (re-)process banks whose name contains one of these strings "
            "(case-insensitive). Useful for re-running banks that errored out "
            "last time without redoing the whole list. Other banks keep their "
            "existing entry from the output file, if present."
        ),
    )
    parser.add_argument(
        "--raw-scores",
        action="store_true",
        help=(
            "Include the 'raw_scores' debug object in each output entry. "
            "Off by default, since it's only needed to tune SCALE_RANGES in "
            "config_messages.py, not for reading the results."
        ),
    )
    return parser.parse_args()


def load_previous_results(path: Path = OUTPUT_FILE) -> dict[str, dict]:
    """Load prior results keyed by bank name, if an output file exists."""
    if not path.exists():
        return {}
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {entry["bank"]: entry for entry in previous if "bank" in entry}


def save_results(results: list[dict]) -> None:
    """Write results to disk now, so a crash mid-run does not lose progress."""
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    bank_urls = load_bank_urls()
    warn_if_products_differ([product for _, product, _, _ in bank_urls], stage="before scraping")

    previous_results = load_previous_results()
    only = [name.lower() for name in args.only] if args.only else None

    results = []
    started = time.monotonic()
    for index, (bank_name, product, url, product_specified) in enumerate(bank_urls, start=1):
        if only is not None and not any(name in bank_name.lower() for name in only):
            if bank_name in previous_results:
                results.append(previous_results[bank_name])
                print(f"[{index}/{len(bank_urls)}] Skipping {bank_name} (kept previous result).")
            continue

        print(
            f"\n{'=' * 70}\n"
            f"[{index}/{len(bank_urls)}] Processing {bank_name} ({product})\n"
            f"{url}\n"
            f"{'=' * 70}"
        )
        entry = {"bank": bank_name, "product": product, "url": url}
        try:
            source = render_page(url)
            print_source(source, bank_name, url)
            if not has_enough_content(source):
                words = count_words(source["text"])
                raise ValueError(
                    f"Only {words} words extracted (minimum {MIN_WORDS}); no "
                    f"scores calculated. See {DEBUG_DIR}/ to see what the browser saw."
                )
            if not product_specified:
                guess = infer_product(url, source)
                entry["product"] = guess
                label = guess if guess != PRODUCT_UNSPECIFIED else "no match"
                print(f"No product set in product_urls.json; guessed: {label}.")
            features = calculate_features(source)
            if not args.raw_scores:
                features.pop("raw_scores", None)
            results.append({**entry, **features})
            print("Analysis completed.")
        except Exception as error:  # noqa: BLE001 - continue processing other banks.
            print(f"ERROR: {error}")
            results.append({**entry, "error": str(error)})

        save_results(results)  # persist after every bank, not just at the end

    failed = sum(1 for result in results if "error" in result)
    elapsed = time.monotonic() - started
    warn_if_products_differ(
        [result["product"] for result in results if "error" not in result],
        stage="after scraping",
    )
    print(
        f"\n{'=' * 70}\n"
        f"ANALYSIS COMPLETE\n"
        f"{'=' * 70}\n"
        f"URLs processed: {len(bank_urls)} ({failed} failed)\n"
        f"Elapsed: {elapsed:.0f}s\n"
        f"Output: {OUTPUT_FILE}\n"
        f"{'=' * 70}"
    )


if __name__ == "__main__":
    main()