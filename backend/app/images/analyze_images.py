import json
import os
import cv2
import easyocr
import numpy as np
import time
import html
import re
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel, Field
from sklearn.cluster import KMeans
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv
from pathlib import Path

import requests
from bs4 import BeautifulSoup

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ==========================================
# 1. Pydantic Schemas for Gemini Structured Output
# ==========================================
class BrandSafety(BaseModel):
    is_safe: bool = Field(
        description="False if explicit content, violence, hate symbols, or high visual risk is present."
    )
    flags: list[str] = Field(
        description="Specific flags raised (e.g., 'adult', 'medical', 'weapons', 'brand_risk'). Empty if clean."
    )


class TargetAudience(BaseModel):
    perceived_age_group: str = Field(
        description="Target demographic (e.g., 'Gen Z', 'Young Professionals', 'Parents', 'Seniors')"
    )
    lifestyle_vibe: str = Field(
        description="Visual aesthetic style (e.g., 'Minimalist', 'High-energy Luxury', 'Casual Outdoor')"
    )


class HighLevelMarketingFeatures(BaseModel):
    product_category: str = Field(
        description="Primary product/service category (e.g., 'Footwear', 'SaaS Platform', 'Skincare')"
    )
    secondary_tags: list[str] = Field(
        description="Sub-categories, context tags, or product features observed."
    )
    perceived_emotion: str = Field(
        description="Dominant emotional appeal (e.g., 'Joy', 'Urgency', 'Calm/Trust', 'Excitement')"
    )
    brand_logos: list[str] = Field(
        description="Visible logos, brand names, or identifiable trade marks detected."
    )
    brand_safety: BrandSafety
    target_audience: TargetAudience
    value_proposition_summary: str = Field(
        description="One-sentence summary of what the ad or image visually communicates."
    )


# ==========================================
# 2. Unified Extractor (OpenCV + Gemini Free Tier)
# ==========================================
class GeminiMarketingExtractorSingleImage:

    def __init__(self, url:str, api_key: str | None = None):
        """Initializes OpenCV/OCR and the Google GenAI Client."""
        # Initialize EasyOCR once
        self.url = url
        self.ocr_reader = easyocr.Reader(["en"], gpu=False)

        # Initialize Google GenAI Client
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable or parameter is required."
            )

        self.ai_client = genai.Client(api_key=api_key)

    def extract_brand_and_category(self):
      # 1. Parse the URL components
        parsed_url = urlparse(self.url)

        # 2. Extract 'ing' from the domain (netloc)
        # e.g., 'www.ing.be' -> splits by '.' -> gets 'ing'
        domain_parts = parsed_url.netloc.split(".")
        brand = domain_parts[1] if len(domain_parts) > 1 else domain_parts[0]

        # 3. Extract the credit card category from the path segments
        # Split path by '/' and filter out empty strings
        path_segments = [seg for seg in parsed_url.path.split("/") if seg]
        # path_segments will be: ['fr', 'particuliers', 'cartes-de-credit', 'carte-de-credit-visa']

        # You can grab specific indices or search for keywords
        category = path_segments[2] if len(path_segments) > 2 else None
        full_card_path = path_segments[3] if len(path_segments) > 3 else None

        print(f"Brand: {brand}")
        print(f"Category: {category}")
        print(f"Full Card Path: {full_card_path}")
        return brand, category

    def _extract_low_level_features(
        self, image_path: str, num_colors: int = 3
    ) -> dict:
        """Extracts low-level computer vision metrics via OpenCV & EasyOCR."""
        try:
            with Image.open(image_path) as image:
                img_rgb = np.array(image.convert("RGB"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Could not load image at path: {image_path}") from exc
        
        # OpenCV uses BGR ordering
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        height, width, _ = img_rgb.shape
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # 1. Structural Dimensions
        aspect_ratio = round(width / height, 2)

        # 2. Color & Tone Metrics
        brightness = round(float(np.mean(img_hsv[:, :, 2])), 2)
        saturation = round(float(np.mean(img_hsv[:, :, 1])), 2)

        # Dominant Colors via K-Means Clustering
        pixels = img_rgb.reshape(-1, 3)
        kmeans = KMeans(n_clusters=num_colors, n_init=5, random_state=42).fit(
            pixels
        )
        hex_colors = [
            f"#{r:02x}{g:02x}{b:02x}"
            for r, g, b in kmeans.cluster_centers_.astype(int)
        ]

        # 3. Contrast & Visual Complexity
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        contrast_rms = round(float(gray.std()), 2)

        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(edges > 0)) / (height * width)

        # 4. Text Overlay & Coverage (OCR)
        ocr_results = self.ocr_reader.readtext(img_rgb)
        total_text_area = 0
        detected_texts = []

        for bbox, text, prob in ocr_results:
            if prob > 0.3:
                detected_texts.append(text)
                pt1, pt2, pt3, pt4 = bbox
                box_w = max(pt2[0], pt3[0]) - min(pt1[0], pt4[0])
                box_h = max(pt3[1], pt4[1]) - min(pt1[1], pt2[1])
                total_text_area += box_w * box_h

        text_coverage_pct = round((total_text_area / (width * height)) * 100, 2)

        return {
            "dimensions": {"width": width, "height": height},
            "aspect_ratio": aspect_ratio,
            "brightness": brightness,
            "saturation": saturation,
            "dominant_colors": hex_colors,
            "contrast_rms": contrast_rms,
            "visual_clutter_score": round(edge_density, 4),
            "text_coverage_pct": text_coverage_pct,
            "ocr_copy_count": len(detected_texts),
            "ocr_detected_copy": detected_texts,
        }

    def _extract_gemini_features(
        self, image_path: str
    ) -> HighLevelMarketingFeatures:
        """Extracts high-level marketing attributes via Gemini (Free Tier Model) using Pydantic schema enforcement."""
        pil_image = Image.open(image_path)
        brand, category = self.extract_brand_and_category()
        prompt = (
            "Analyze this marketing image. Categorize the product, "
            "assess brand safety, detect logos, and analyze emotional tone, "
            f"value proposition, and target demographic appeal in the context of {brand} and product category {category}"
        )

        # Call Gemini using Structured Output (gemini-2.5-flash or gemini-3-flash)
        for attempt in range(3):
            try:
                response = self.ai_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[pil_image, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=HighLevelMarketingFeatures,
                    ),
                )
                break
            except Exception as exc:
                if "503" not in str(exc) or attempt == 2:
                    raise
                time.sleep(2 ** attempt)

        # Parse JSON output into Pydantic model
        parsed_json = json.loads(response.text)
        return HighLevelMarketingFeatures(**parsed_json)

    def analyze_image(self, image_path: str) -> dict:
        """Pipeline entry point combining local CV metrics and Gemini Free Vision analysis."""
        cv_metrics = self._extract_low_level_features(image_path)
        gemini_analysis = self._extract_gemini_features(image_path)

        return {
            "low_level_metrics": cv_metrics,
            "semantic_analysis": gemini_analysis.model_dump(),
        }

"""
def extract_first_image(page_url: str, output_path: Path) -> Path:
    response = requests.get(page_url, timeout=30)
    response.raise_for_status()
    print(response.url)
    print(len(response.text))
    print("https://assets.ing.com/transform/f5db0de6-b498-4708-b69f-74984eaa42cb/Female-hiker-shows-muscles-on-mountain-top?io=transform:fill,width:1440,height:480&amp;quality=75&amp;rev=1764750529000" in response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    image_url = next(
        (
            urljoin(page_url, image["src"])
            for image in soup.find_all("img", src=True)
            if image["src"].startswith("https://")
            and not urlparse(image["src"]).path.lower().endswith(".svg")
        ),
        None,
    )

    if image_url is None:
        raise ValueError("No suitable image found")

    image_response = requests.get(image_url, timeout=30)
    image_response.raise_for_status()

    output_path.write_bytes(image_response.content)
    return output_path
"""

def extract_first_image_url(page_url: str) -> str:
    response = requests.get(
        page_url,
        #headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    page_html = html.unescape(response.text)

    def first_non_svg_url(urls):
        for candidate in urls:
            image_url = urljoin(page_url, candidate.strip())
            parsed_url = urlparse(image_url)
            if parsed_url.scheme in {"http", "https"} and not parsed_url.path.lower().endswith(
                ".svg"
            ):
                return image_url
        return None

    soup = BeautifulSoup(page_html, "html.parser")
    for image in soup.find_all("img"):
        image_url = first_non_svg_url(
            image.get(attribute)
            for attribute in ("src", "data-src", "data-lazy-src")
            if image.get(attribute)
        )
        if image_url:
            return image_url

    # ING sometimes puts the first image in a preload link before rendering an
    # <img> element in JavaScript.
    preload_urls = (
        link.get("href")
        for link in soup.find_all("link", href=True)
        if link.get("as", "").lower() == "image"
    )
    image_url = first_non_svg_url(preload_urls)
    if image_url:
        return image_url

    # Some JavaScript-rendered pages expose the image only through social
    # preview metadata in the initial HTML response.
    metadata_urls = (
        meta.get("content")
        for meta in soup.find_all("meta", content=True)
        if meta.get("property", "").lower() in {"og:image", "twitter:image"}
        or meta.get("name", "").lower() == "twitter:image"
    )
    image_url = first_non_svg_url(metadata_urls)
    if image_url:
        return image_url

    raise ValueError(
        f"No suitable image found. Response length: {len(response.text)}"
    )

def download_image(image_url: str, output_path: Path) -> Path:
    response = requests.get(
        image_url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()

    output_path.write_bytes(response.content)
    return output_path

# ==========================================
# 3. Execution Script
# ==========================================
if __name__ == "__main__":
    #sample_image = Path(__file__).parent / "ing-visa.jpg"
    #sample_image = Path(__file__).parent / "ing-young-saving-account.jpg"

    #url = "https://www.ing.be/fr/particuliers/cartes-de-credit/carte-de-credit-visa"
    #url = "https://www.ing.be/en/individuals/investing/ing-self-invest"
    #url = "https://www.belfius.be/site/retail/fr/produits/paiement/carte-de-credit-et-prepayee"
    #url = "https://www.belfius.be/site/retail/fr/produits/investir/investisseur-debutant"
    #url = "https://www.kbc.be/retail/en/investments/investment-plan.html?zone=topnav#"
    url = "https://www.kbc.be/retail/en/payments/payment-cards/credit-cards/kbc-credit-card.html"

    image_url = extract_first_image_url(url)
    print(image_url)

    extracted_image = Path(__file__).parent / "extracted_image.jpg"
    out_path = download_image(image_url, extracted_image)
    print(out_path)

    extractor = GeminiMarketingExtractorSingleImage(url=url,api_key=api_key)

    try:
        report = extractor.analyze_image(str(extracted_image))
        output_file = Path(__file__).parent / "image_description.json"
        output_file.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Saved image description to {output_file}")

    except Exception as e:
        print(f"Pipeline execution failed: {e}")