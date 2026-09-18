import csv
import json
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
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

from backend.app.crawling.crawling import BANK_URLS_FILE
from backend.app.scraping.scrape_text_features_bel import scrape_page

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')

DEBUG_CLASSIFIER = True
CATEGORIZED_PAGES_FILE = BANK_URLS_FILE.with_name("bank_page_categories.csv")

BANK_PRODUCT_CATEGORIES = {
    "fr":[
        "Autre produit",
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
        "Andere produkt",
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
        "Other product",
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

def clean_text(text) -> str:
    stop_words = stopwords.words('english')
    tokens = word_tokenize(text)
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
    clean_tokens = [word for word in filtered_tokens if word not in string.punctuation]
    return " ".join(clean_tokens)

def categorize_page(page_url:str, classifier) -> tuple[str,float]:
    # Scrape page and clean text
    time0 = time.time()
    text = scrape_page(page_url)["paragraphs"]
    if DEBUG_CLASSIFIER:
        time1 = time.time()
        print(f"scraping : {time1-time0} s")
    text = " ".join(text)
    text = clean_text(text)
    # Classify page in category
    lang = detect(text)
    labels = BANK_PRODUCT_CATEGORIES[lang]
    if DEBUG_CLASSIFIER:
        time2 = time.time()
        print(f"cleaning : {time2-time1} s")
    result = classifier(text, 
                        candidate_labels=labels,
                        hypothesis_template="This banking page is about {}.",
                        truncation=True,
                        max_length=256)
    if DEBUG_CLASSIFIER:
        time3 = time.time()
        print(f"classify : {time3-time2} s")
    # return category with highest score
    return result['labels'][0], result['scores'][0], lang


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


def categorize_bank_pages(output_file: Path = CATEGORIZED_PAGES_FILE) -> dict:
    bank_pages = load_bank_pages()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["url", "category", "score", "lang"]
    with output_file.open("w", newline="", encoding="utf-8") as csv_file:
        csv.DictWriter(csv_file, fieldnames=fieldnames).writeheader()

    # Initialize the zero-shot classifier
    model_name1 = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    model_name2 = "typeform/distilbert-base-uncased-mnli" # smaller and faster but less accurate model
    model_name = model_name2 if DEBUG_CLASSIFIER else model_name1
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
        bar = progressbar.ProgressBar(maxval=len(pages), 
                                      widgets=[f"Categorize urls of bank {bank} : ", 
                                                progressbar.Bar('=', '[', ']'), ' ', 
                                                progressbar.Percentage(), ' '*20])
        bar.start()
        for num, page in enumerate(pages):
            bar.update(num)
            category, score, lang = categorize_page(page, classifier)
            bank_pages_cat[bank].append({
                "url": page,
                "category": category,
                "score": score,
                "lang" : lang
            })
            if DEBUG_CLASSIFIER:
                print(f"url:{page} \n category:{category} \t score:{score:.4f}")
        bar.finish()
        with output_file.open("a", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writerows(bank_pages_cat[bank])
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

def main():
    if DEBUG_CLASSIFIER:
        categorize_test()
    bank_pages = categorize_bank_pages()


if __name__ == "__main__":
    main()
