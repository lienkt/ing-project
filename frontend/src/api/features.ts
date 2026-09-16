import { Campaign, request } from "./campaigns";

export const featureFields = [
  {
    "key": "bank_type",
    "kind": "enum",
    "section": "Identification & Metadata",
    "options": [
      "Traditional",
      "Challenger",
      "Neobank"
    ],
    "help": "Classify the bank type consistently"
  },
  {
    "key": "product_name",
    "kind": "text",
    "section": "Identification & Metadata",
    "help": "Copy the official displayed product name"
  },
  {
    "key": "language",
    "kind": "enum",
    "section": "Identification & Metadata",
    "options": [
      "Dutch",
      "French",
      "English",
      "Other"
    ],
    "help": "Language of the analyzed page"
  },
  {
    "key": "capture_date",
    "kind": "date",
    "section": "Identification & Metadata",
    "help": "Date the page was reviewed"
  },
  {
    "key": "word_count",
    "kind": "count",
    "section": "Text & Content",
    "help": "Count main campaign/product-page content consistently"
  },
  {
    "key": "heading_count",
    "kind": "count",
    "section": "Text & Content",
    "help": "Count visible section/main headings"
  },
  {
    "key": "paragraph_count",
    "kind": "count",
    "section": "Text & Content",
    "help": "Count visible body paragraphs"
  },
  {
    "key": "bullet_list_count",
    "kind": "count",
    "section": "Text & Content",
    "help": "Count lists, not individual bullets"
  },
  {
    "key": "average_paragraph_length",
    "kind": "derived",
    "section": "Text & Content",
    "help": "word_count / paragraph_count where applicable"
  },
  {
    "key": "headline_length",
    "kind": "count",
    "section": "Text & Content",
    "help": "Count words in primary headline"
  },
  {
    "key": "text_density",
    "kind": "scale",
    "section": "Text & Content",
    "descriptions": [
      "Very little text",
      "Low amount of text",
      "Moderate amount of text",
      "High amount of text",
      "Very text-heavy page"
    ],
    "help": "Judge how text-heavy the page feels overall"
  },
  {
    "key": "text_style",
    "kind": "enum",
    "section": "Text & Content",
    "options": [
      "Concise",
      "Balanced",
      "Detailed"
    ],
    "help": "Concise = short/direct; Detailed = extensive explanation"
  },
  {
    "key": "information_complexity",
    "kind": "scale",
    "section": "Text & Content",
    "descriptions": [
      "Very simple",
      "Simple",
      "Moderate",
      "Complex",
      "Very complex"
    ],
    "help": "Assess how difficult the information is to understand"
  },
  {
    "key": "tone_formality",
    "kind": "scale",
    "section": "Messaging & Tone",
    "descriptions": [
      "Very casual",
      "Mostly casual",
      "Balanced",
      "Mostly formal",
      "Very formal"
    ],
    "help": "Assess language formality"
  },
  {
    "key": "tone_friendliness",
    "kind": "scale",
    "section": "Messaging & Tone",
    "descriptions": [
      "Distant",
      "Slightly friendly",
      "Neutral/balanced",
      "Friendly",
      "Very friendly"
    ],
    "help": "Assess warmth and conversational style"
  },
  {
    "key": "tone_persuasiveness",
    "kind": "scale",
    "section": "Messaging & Tone",
    "descriptions": [
      "Purely informative",
      "Mostly informative",
      "Balanced",
      "Persuasive",
      "Highly persuasive"
    ],
    "help": "Assess strength of selling/persuasion"
  },
  {
    "key": "emotional_vs_rational",
    "kind": "scale",
    "section": "Messaging & Tone",
    "descriptions": [
      "Strongly emotional",
      "Mostly emotional",
      "Balanced",
      "Mostly rational",
      "Strongly rational"
    ],
    "help": "Emotional = feelings/lifestyle; Rational = facts/features/conditions"
  },
  {
    "key": "customer_vs_product_focus",
    "kind": "scale",
    "section": "Messaging & Tone",
    "descriptions": [
      "Strongly customer-focused",
      "Mostly customer-focused",
      "Balanced",
      "Mostly product-focused",
      "Strongly product-focused"
    ],
    "help": "Assess whether messaging starts from customer needs or product characteristics"
  },
  {
    "key": "feature_vs_benefit_focus",
    "kind": "scale",
    "section": "Messaging & Tone",
    "descriptions": [
      "Strongly feature-focused",
      "Mostly feature-focused",
      "Balanced",
      "Mostly benefit-focused",
      "Strongly benefit-focused"
    ],
    "help": "Feature = what product has; Benefit = what customer gains"
  },
  {
    "key": "message_focus",
    "kind": "enum",
    "section": "Messaging & Tone",
    "options": [
      "Product",
      "Feature",
      "Benefit",
      "Lifestyle",
      "Price"
    ],
    "help": "Choose the dominant messaging focus"
  },
  {
    "key": "main_message",
    "kind": "textarea",
    "section": "Messaging & Tone",
    "help": "Summarize the central message without evaluating it"
  },
  {
    "key": "value_proposition",
    "kind": "textarea",
    "section": "Messaging & Tone",
    "help": "State the primary reason the page gives to choose the offer"
  },
  {
    "key": "image_count",
    "kind": "count",
    "section": "Images & Visuals",
    "help": "Count meaningful visible images consistently"
  },
  {
    "key": "has_hero_image",
    "kind": "boolean",
    "section": "Images & Visuals",
    "help": "Large primary image in the opening/hero area"
  },
  {
    "key": "hero_image_size",
    "kind": "enum",
    "section": "Images & Visuals",
    "options": [
      "None",
      "Small",
      "Medium",
      "Large",
      "Full-width"
    ],
    "help": "Judge relative size of main hero visual"
  },
  {
    "key": "people_present",
    "kind": "boolean",
    "section": "Images & Visuals",
    "help": "Whether any main image/illustration contains people"
  },
  {
    "key": "people_image_count",
    "kind": "count",
    "section": "Images & Visuals",
    "help": "Count separate images containing people"
  },
  {
    "key": "product_present",
    "kind": "boolean",
    "section": "Images & Visuals",
    "help": "Card, phone, banking app, product UI, etc."
  },
  {
    "key": "illustration_present",
    "kind": "boolean",
    "section": "Images & Visuals",
    "help": "Non-photographic illustrations present"
  },
  {
    "key": "icon_count",
    "kind": "count",
    "section": "Images & Visuals",
    "help": "Count meaningful communication icons"
  },
  {
    "key": "video_count",
    "kind": "count",
    "section": "Images & Visuals",
    "help": "Count embedded/visible videos"
  },
  {
    "key": "animation_present",
    "kind": "boolean",
    "section": "Images & Visuals",
    "help": "Animated illustrations, GIFs, motion elements, etc."
  },
  {
    "key": "visual_style",
    "kind": "enum",
    "section": "Images & Visuals",
    "options": [
      "Photography",
      "Illustration",
      "3D",
      "UI-Product",
      "Mixed"
    ],
    "help": "Choose dominant visual treatment"
  },
  {
    "key": "visual_intensity",
    "kind": "scale",
    "section": "Images & Visuals",
    "descriptions": [
      "Almost entirely text",
      "Mostly text with a few visuals",
      "Balanced text and visuals",
      "Highly visual",
      "Visuals dominate the page"
    ],
    "help": "Assess relative dominance of visuals over text"
  },
  {
    "key": "dominant_colour",
    "kind": "text",
    "section": "Colour & Design",
    "help": "Record the visually dominant colour"
  },
  {
    "key": "number_of_major_colours",
    "kind": "count",
    "section": "Colour & Design",
    "help": "Ignore minor decorative colour variations"
  },
  {
    "key": "brand_colour_dominance",
    "kind": "scale",
    "section": "Colour & Design",
    "descriptions": [
      "Brand colours barely visible",
      "Limited use",
      "Moderate use",
      "Strong use",
      "Brand colours dominate"
    ],
    "help": "How strongly recognizable brand colours dominate"
  },
  {
    "key": "colour_contrast",
    "kind": "scale",
    "section": "Colour & Design",
    "descriptions": [
      "Very low",
      "Low",
      "Moderate",
      "High",
      "Very high"
    ],
    "help": "Assess visual contrast used to separate/highlight content"
  },
  {
    "key": "design_complexity",
    "kind": "scale",
    "section": "Colour & Design",
    "descriptions": [
      "Very minimal",
      "Simple",
      "Moderate",
      "Complex",
      "Very complex"
    ],
    "help": "Assess number and complexity of competing design elements"
  },
  {
    "key": "visual_consistency",
    "kind": "scale",
    "section": "Colour & Design",
    "descriptions": [
      "Very inconsistent",
      "Somewhat inconsistent",
      "Moderate",
      "Consistent",
      "Highly consistent"
    ],
    "help": "Assess consistency of visual language across the page"
  },
  {
    "key": "attention_focus",
    "kind": "enum",
    "section": "Colour & Design",
    "options": [
      "Text",
      "Image",
      "CTA",
      "Product",
      "Mixed"
    ],
    "help": "What attracts attention first/most strongly"
  },
  {
    "key": "section_count",
    "kind": "count",
    "section": "Layout & Page Structure",
    "help": "Count meaningful page sections"
  },
  {
    "key": "page_length",
    "kind": "enum",
    "section": "Layout & Page Structure",
    "options": [
      "Short",
      "Medium",
      "Long"
    ],
    "help": "Use a team-agreed rule consistently"
  },
  {
    "key": "hero_section_present",
    "kind": "boolean",
    "section": "Layout & Page Structure",
    "help": "Whether a distinct opening hero section exists"
  },
  {
    "key": "content_pattern",
    "kind": "enum",
    "section": "Layout & Page Structure",
    "options": [
      "Text-first",
      "Image-first",
      "Alternating",
      "Cards",
      "Mixed"
    ],
    "help": "Choose dominant page organization pattern"
  },
  {
    "key": "card_layout_present",
    "kind": "boolean",
    "section": "Layout & Page Structure",
    "help": "Whether information is presented in cards"
  },
  {
    "key": "accordion_present",
    "kind": "boolean",
    "section": "Layout & Page Structure",
    "help": "Expandable/collapsible content present"
  },
  {
    "key": "comparison_table_present",
    "kind": "boolean",
    "section": "Layout & Page Structure",
    "help": "Product/feature comparison table present"
  },
  {
    "key": "navigation_anchor_present",
    "kind": "boolean",
    "section": "Layout & Page Structure",
    "help": "In-page anchor navigation present"
  },
  {
    "key": "layout_clarity",
    "kind": "scale",
    "section": "Layout & Page Structure",
    "descriptions": [
      "Very confusing",
      "Difficult to understand",
      "Average",
      "Clear",
      "Very clear"
    ],
    "help": "Assess how clearly the page is organized"
  },
  {
    "key": "scannability",
    "kind": "scale",
    "section": "Layout & Page Structure",
    "descriptions": [
      "Very difficult",
      "Difficult",
      "Average",
      "Easy",
      "Very easy"
    ],
    "help": "How easily a visitor can scan and understand key sections/messages"
  },
  {
    "key": "cta_count",
    "kind": "count",
    "section": "Call to Action",
    "help": "Count meaningful conversion/action CTAs"
  },
  {
    "key": "primary_cta_text",
    "kind": "text",
    "section": "Call to Action",
    "help": "Copy exact main CTA text"
  },
  {
    "key": "cta_above_fold",
    "kind": "boolean",
    "section": "Call to Action",
    "help": "Main CTA visible near initial viewport/opening section"
  },
  {
    "key": "cta_repeated",
    "kind": "boolean",
    "section": "Call to Action",
    "help": "Whether primary/similar CTA appears repeatedly"
  },
  {
    "key": "cta_prominence",
    "kind": "scale",
    "section": "Call to Action",
    "descriptions": [
      "Very difficult to notice",
      "Low visibility",
      "Clearly visible",
      "Highly prominent",
      "Dominant action on the page"
    ],
    "help": "Assess visual prominence, not effectiveness"
  },
  {
    "key": "cta_type",
    "kind": "enum",
    "section": "Call to Action",
    "options": [
      "Apply",
      "Buy",
      "Open",
      "Learn",
      "Contact",
      "Calculate",
      "Other"
    ],
    "help": "Classify primary CTA intent"
  },
  {
    "key": "price_visible",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Price, fee, rate, or cost visibly communicated"
  },
  {
    "key": "price_prominence",
    "kind": "scale",
    "section": "Product & Value Proposition",
    "descriptions": [
      "Very difficult to notice",
      "Low visibility",
      "Clearly visible",
      "Highly prominent",
      "Price dominates the communication"
    ],
    "help": "Assess prominence only when price/rate is present"
  },
  {
    "key": "promotion_present",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Temporary offer/bonus/promotion present"
  },
  {
    "key": "benefit_count",
    "kind": "count",
    "section": "Product & Value Proposition",
    "help": "Count distinct customer outcomes/advantages"
  },
  {
    "key": "feature_count",
    "kind": "count",
    "section": "Product & Value Proposition",
    "help": "Count distinct product capabilities/characteristics"
  },
  {
    "key": "trust_message_present",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Explicit trust/reliability/reputation message"
  },
  {
    "key": "security_message_present",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Explicit safety/security message"
  },
  {
    "key": "convenience_message_present",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Explicit ease/convenience message"
  },
  {
    "key": "digital_message_present",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Explicit digital/app/online experience message"
  },
  {
    "key": "sustainability_message_present",
    "kind": "boolean",
    "section": "Product & Value Proposition",
    "help": "Explicit sustainability/environmental message"
  },
  {
    "key": "main_value_driver",
    "kind": "enum",
    "section": "Product & Value Proposition",
    "options": [
      "Price",
      "Convenience",
      "Security",
      "Flexibility",
      "Lifestyle",
      "Digital",
      "Service",
      "Other"
    ],
    "help": "Choose the dominant value driver"
  }
] as const;

export type FeatureKey = typeof featureFields[number]["key"];
type Definition = typeof featureFields[number];
type Value<F extends Definition> = F extends {kind: "scale" | "count" | "derived"} ? number : F extends {kind: "boolean"} ? boolean : F extends {options: readonly (infer O)[]} ? O : string;
export type FeatureValues = { [F in Definition as F["key"]]: Value<F> | null };
export type FeatureInput = FeatureValues & {labeling_notes: string | null};
export type LabelingStatus = "Not Started" | "In Progress" | "Completed";
export type FeatureRecord = FeatureInput & {campaign_id: number; labeling_status: LabelingStatus; source: "manual" | "automatic" | "manual_override"; created_at: string; updated_at: string};
export type FeatureResponse = {campaign: Campaign; features: FeatureRecord | null; labeling_status: LabelingStatus; progress: number; missing_fields: FeatureKey[]};
export const emptyFeatures = Object.fromEntries(featureFields.map(f => [f.key, null])) as FeatureValues;
export const isFilled = (value: unknown) => value !== null && value !== undefined && (typeof value !== "string" || value.trim() !== "");
export const getFeatures = (id: string) => request<FeatureResponse>(`/campaigns/${id}/features`);
export const withDerivedValues = (data: FeatureInput): FeatureInput => ({
  ...data,
  average_paragraph_length: data.word_count !== null && data.paragraph_count !== null && data.paragraph_count > 0
    ? data.word_count / data.paragraph_count : null,
});
export const saveFeatures = (id: string, data: Partial<FeatureInput>) => {
  const { average_paragraph_length: _derived, ...input } = data;
  return request<FeatureResponse>(`/campaigns/${id}/features`, "PUT", input);
};
export const completeFeatures = (id: string, confirm_incomplete: boolean) => request<FeatureResponse>(`/campaigns/${id}/features/complete`, "POST", {confirm_incomplete});
