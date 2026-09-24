import json
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from transformers import MarianMTModel, MarianTokenizer
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from langdetect import detect
import torch
#import requests
#from bs4 import BeautifulSoup
import progressbar
import time
from functools import lru_cache

from backend.app.crawling.crawling import BANK_URLS_FILE
from backend.app.scraping.scrape_text_features_bel import scrape_page

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')

DEBUG_CLASSIFIER = True
BANK_URLS_SUBSET_FILE = BANK_URLS_FILE.with_name("bank_urls_subset.json")
CATEGORIZED_PAGES_FILE = BANK_URLS_FILE.with_name("bank_page_categories.json")
BEST_CATEGORIZED_PAGES_FILE = BANK_URLS_FILE.with_name("best_bank_page_categories.json")

BANK_FOCUS_URLS = {
    "ING" : "www.ing.be/en/individuals/",
    "KBC" : "www.kbc.be/retail/en/",
    "Belfius" : "www.belfius.be/site/retail/fr/produits/",
    "BNP" : "www.bnpparibasfortis.be/en/public/individuals/",
    "Argenta" : "www.argenta.be/fr/",
    "Crelan" : "www.crelan.be/nl/particulieren/"
}

BANK_PRODUCT_CATEGORIES = {
    "fr":[
        "Pas un produit bancaire",
        "Compte courant / Compte à vue",
        "Compte courant jeunes",
        "Carte de crédit",
        "Compte d'épargne",
        "Compte à terme",
        "Épargne-pension",
        "Crédit auto",
        "Crédit rénovation / énergie",
        "Crédit confort",
        "Crédit hypothécaire",
        "Crédit pont",
        "Assurance auto",
        "Assurance habitation",
        "Assurance familiale",
        "Assurance voyage",
        "Assurance solde restant dû",
        "Plan d'investissement",
        "Compte-titres"
    ],
    "nl": [
        "Niet een bank produkt",
        "Zichtrekening",
        "Jongerenrekening",
        "Kredietkaart",
        "Spaarrekening",
        "Termijnrekening",
        "Pensioensparen",
        "Autolening",
        "Renovatie- en energielening",
        "Persoonlijke lening",
        "Woonkrediet",
        "Overbruggingskrediet",
        "Autoverzekering",
        "Brandverzekering",
        "Familiale verzekering",
        "Reisverzekering",
        "Schuldsaldoverzekering",
        "Beleggingsplan",
        "Effectenrekening"
    ],
    "en" : [
        "Not a bank product",
        "Current account",
        "Youth current account",
        "Credit card",
        "Savings account",
        "Term account",
        "Pension saving plan",
        "Vehicle loan",
        "Renovation & eco-energy loan",
        "Multi-purpose loan",
        "Mortgage loan",
        "Bridge loan",
        "Car insurance",
        "Home insurance",
        "Family insurance",
        "Travel insurance",
        "Outstanding balance insurance",
        "Investment fund / regular saving plan",
        "Online trading & securities account"
    ]
}

"""
def scrape_page(page_url:str) -> str:
    # scrape page_url and return text
    response = requests.get(page_url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = ""
    for data in soup.find_all("p"):
        text = text + " " + data.get_text()
    return text
"""

@lru_cache(maxsize=2)
def load_translation_model(model_name: str):
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name, use_safetensors=False)
    return tokenizer, model

def clean_text(text) -> str:
    stop_words = stopwords.words('english')
    tokens = word_tokenize(text)
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
    clean_tokens = [word for word in filtered_tokens if word not in string.punctuation]
    return " ".join(clean_tokens)

def translate_to_en(src_text: str, lang: str) -> str:
    if lang == "en":
        return src_text
    if lang == "fr":
        model_name = "Helsinki-NLP/opus-mt-fr-en"
    elif lang == "nl":
        model_name = "Helsinki-NLP/opus-mt-nl-en"
    else:
        print(f"Language {lang} not supported for translation")
        return src_text
    tokenizer, model = load_translation_model(model_name)
    # Tokenize input
    inputs = tokenizer(src_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    # Generate translation output
    translated = model.generate(**inputs)
    # Decode tokens back into string
    decoded_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
    return decoded_text[0]

def categorize_page(page_url:str, classifier) -> tuple[str,float]:
    # Scrape page
    time0 = time.time()
    text = scrape_page(page_url)
    text = " ".join(text["headings"]) + " " + text["paragraphs"][0] + " " + text["paragraphs"][1]
    if DEBUG_CLASSIFIER:
        print("text : ",text)
        time1 = time.time()
        print(f"* scraping : {time1-time0} s")
    # Clean text
    text = clean_text(text)
    if DEBUG_CLASSIFIER:
        print("- cleaned text : ",text)
    if text == "":
        return "", 0., ""
    # Translate text
    lang = detect(text)
    if lang not in ["fr", "nl", "en"]:
        return "", 0., ""
    trans_text = translate_to_en(text, lang)
    if DEBUG_CLASSIFIER:
        print("- translated text : ",text)
    trans_lang="en"
    labels = BANK_PRODUCT_CATEGORIES[trans_lang]
    if DEBUG_CLASSIFIER:
        time2 = time.time()
        print(f"* cleaning and translating: {time2-time1} s")
    # Classify page in category
    hypothesis_template = {"fr":"Cette page bancaire concerne {}.",
                           "nl":"Deze bankpagina gaat over {}.",
                           "en":"This banking page is about {}."}
    result = classifier(trans_text,
                        candidate_labels=labels,
                        hypothesis_template=hypothesis_template[trans_lang],
                        truncation=True,
                        max_length=256)
    if DEBUG_CLASSIFIER:
        time3 = time.time()
        print(f"* classify : {time3-time2} s")
    # return category with highest score
    idx = BANK_PRODUCT_CATEGORIES[trans_lang].index(result['labels'][0])
    return BANK_PRODUCT_CATEGORIES[lang][idx], result['scores'][0], lang


def load_bank_pages(input_file: Path = BANK_URLS_FILE) -> dict[str, list[str]]:
    """Load the bank-to-page-URLs mapping written by the crawler."""
    try:
        bank_pages = json.loads(input_file.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Bank URL file not found: {input_file}. Run the crawler first."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {input_file}: {exc}") from exc

    if not isinstance(bank_pages, dict) or not all(
        isinstance(bank, str) and isinstance(urls, list)
        and all(isinstance(url, str) for url in urls)
        for bank, urls in bank_pages.items()
    ):
        raise ValueError("bank_urls.json must contain an object of bank names and URL lists")
    return bank_pages


def _save_categorized_pages(results: dict, output_file: Path) -> None:
    """Save all completed banks as a valid JSON object."""
    temporary_file = output_file.with_suffix(f"{output_file.suffix}.tmp")
    temporary_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_file.replace(output_file)


def categorize_bank_pages(output_file: Path = CATEGORIZED_PAGES_FILE) -> dict:
    input_file = BANK_URLS_SUBSET_FILE if DEBUG_CLASSIFIER else BANK_URLS_FILE
    bank_pages = load_bank_pages(input_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    _save_categorized_pages({}, output_file)

    # Initialize the zero-shot classifier
    model_name1 = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    model_name2 = "typeform/distilbert-base-uncased-mnli" # smaller and faster but less accurate model
    #model_name3 = "morit/french_xlm_xnli" # model trained on multiple languages / needs pytorch 2.6
    model_name = model_name1 if DEBUG_CLASSIFIER else model_name1
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.model_max_length = 512
    classifier = pipeline(
        task="zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        truncation=True,
        max_length=256,
        framework="pt",
        device="cpu",
        dtype=torch.float32,
        )
    bank_pages_cat = {}
    for bank, pages in bank_pages.items():
        bank_pages_cat[bank] = []
        if bank in BANK_FOCUS_URLS:
            pages = [page for page in pages if (BANK_FOCUS_URLS[bank] in page)]
        bar = progressbar.ProgressBar(maxval=len(pages), 
                                      widgets=[f"Categorize urls of bank {bank} : ", 
                                                progressbar.Bar('=', '[', ']'), ' ', 
                                                progressbar.Percentage(), ' '*20])
        bar.start()
        for num, page in enumerate(pages):
            bar.update(num)
            category, score, lang = categorize_page(page, classifier)
            if category == "":
                continue
            bank_pages_cat[bank].append({
                "url": page,
                "category": category,
                "score": score,
                "lang" : lang
            })
            if DEBUG_CLASSIFIER:
                print(f"url:{page} \n category:{category} \t score:{score:.4f}")
        bar.finish()
        _save_categorized_pages(bank_pages_cat, output_file)
        print(f"Saved {len(bank_pages_cat[bank])} {bank} results to {output_file}")
    return bank_pages_cat

def categorize_test():
    model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.model_max_length = 512
    classifier = pipeline(
        task="zero-shot-classification",
        model=model,
        tokenizer=tokenizer,
        truncation=True,
        max_length=512,
        framework="pt",
        device="cpu",
        dtype=torch.float32,
        )
    text="Free bank account for children and teens aged 8 to 17 Give your child the confidence to manage their money with a free ING Go to 18 current account"
    lang = detect(text)
    labels = BANK_PRODUCT_CATEGORIES[lang]
    result = classifier(text, 
                        candidate_labels=labels,
                        hypothesis_template="This banking page is about {}.",
                        truncation=True,
                        max_length=512)
    print("labels:",result['labels'])
    print("scores:",result['scores'])

def get_urls_with_highest_scores(bank_pages_cat : dict, output_file: Path = BEST_CATEGORIZED_PAGES_FILE) -> dict:
    urls_with_highest_scores = {}
    for bank, pages in bank_pages_cat.items():
        urls_with_highest_scores[bank] = {}
        for page in pages:
            lang = page["lang"]
            cat = page["category"]
            url = page["url"]
            score = page["score"]
            if lang not in urls_with_highest_scores[bank]:
                urls_with_highest_scores[bank][lang] = {}
            if cat not in urls_with_highest_scores[bank][lang] or urls_with_highest_scores[bank][lang][cat+"_score"] < score:
                urls_with_highest_scores[bank][lang][cat] = url
                urls_with_highest_scores[bank][lang][cat+"_score"] = score
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(urls_with_highest_scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Printed urls with highest_scores in output file {output_file}.")
    return urls_with_highest_scores

def main():
    if DEBUG_CLASSIFIER:
        categorize_test()
    bank_pages_cat = categorize_bank_pages()
    get_urls_with_highest_scores(bank_pages_cat)

if __name__ == "__main__":
    main()
