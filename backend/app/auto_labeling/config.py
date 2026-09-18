"""HOW TO ADD A NEW SUPPORTED CASE:
1. Implement the function in functions.py (or one bank file).
2. Test it.
3. Add build_case_key(bank, category, product, language): function below.
4. The API and UI automatically recognize it. Never register a TODO function.
"""

from app.schemas.automation import build_case_key
from app.auto_labeling.functions import label_demo_page, label_ing_youth_account_en

# Independent of scraping support: KBC collection works, KBC auto labeling does not.
AUTO_LABEL_SUPPORT = {
    build_case_key("ING", "Current Account", "ING Youth Account", "EN"): label_ing_youth_account_en,
    build_case_key(
        "ING", "Current Account", "ING example current account", "EN"
    ): label_demo_page,
}
