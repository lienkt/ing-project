# Labeling Field Reference

[Documentation index](README.md) · [Workflow and progress](feature-framework.md)

This guide lists every field in the current labeling form, its meaning, accepted values, and scale definitions. Labels and options match [frontend field definitions](../frontend/src/api/features.ts); validation limits follow the [backend schema](../backend/app/schemas/features.py).

## Before labeling

Review the original page, then record what it communicates rather than what you expect from the bank. Use the same viewing conditions and counting scope across your sample.

Recommended team conventions below are review guidance, not automated rules. Agree on whether navigation, footer, legal text, repeated content, and expanded accordions belong in your counting scope. Record exceptions in `labeling_notes`. The app does not define numerical thresholds for Short/Medium/Long or Small/Medium/Large; agree on these before comparing pages.

## Value rules

| Type | How to enter it |
| --- | --- |
| Count | Whole number from 0 to 2,147,483,647. Use 0 only when you checked and found none. |
| Boolean | Yes (`true`), No (`false`), or Not set (`null`). Unknown is not No. |
| Scale | Integer 1–5 using the exact definitions below. Higher does not universally mean better. |
| Choice | One listed option, or Not set. API values are case-sensitive. |
| Text | An observation or copied wording, within the stated character limit. |
| Date | Review date in `YYYY-MM-DD` format. |
| Derived | Calculated by the app; do not enter or send it in a draft request. |

All framework inputs may be left unset. Unknown and not applicable both use null; explain the distinction in notes. No automatic cross-field applicability rules clear other fields for you. A completed record may therefore contain missing values.

## Campaign context: three reused fields

These are edited in campaign basic information, not in the labeling form.

| Reference field | Stored/API field | Meaning |
| --- | --- | --- |
| `bank_name` | `campaign.bank_name` | Name of the bank publishing the page. |
| `product_category` | `campaign.project` | Shared category key, such as `current_account`, used to group comparisons. |
| `page_url` | `campaign.campaign_url` | Public HTTP(S) source page being reviewed. |

The remaining **68 fields** appear below: **67 stored inputs and one derived value**, across eight sections. Together with campaign context, they cover 71 reference fields.

## Sections

1. [Identification & Metadata](#1-identification--metadata)
2. [Text & Content](#2-text--content)
3. [Messaging & Tone](#3-messaging--tone)
4. [Images & Visuals](#4-images--visuals)
5. [Colour & Design](#5-colour--design)
6. [Layout & Page Structure](#6-layout--page-structure)
7. [Call to Action](#7-call-to-action)
8. [Product & Value Proposition](#8-product--value-proposition)

## 1. Identification & Metadata

4 fields.

Bank type is an observation for this reviewed page, not a global catalog property. Use a team-agreed classification for Traditional, Challenger, and Neobank; the app does not assign types automatically. Copy the specific offer name into product_name, not its category. For a bilingual page, agree on the reviewed language version and record any ambiguity in notes.

### `bank_type`

Classify the bank type consistently.

**Allowed values:** `Traditional`, `Challenger`, `Neobank`, or unset.

### `product_name`

Copy the official displayed product name.

**Type:** text, at most 300 characters, or unset.

### `language`

Language of the analyzed page.

**Allowed values:** `Dutch`, `French`, `English`, `Other`, or unset.

### `capture_date`

Date the page was reviewed.

**Format:** `YYYY-MM-DD`, or unset. Record when you reviewed the page, not the campaign launch date.

## 2. Text & Content

9 fields.

Count a bullet list once regardless of how many bullets it contains. For example, three separate lists containing four bullets each give bullet_list_count = 3. Headline length counts words, not characters. Text density concerns the amount of text; information complexity concerns how hard it is to understand, so a short page can still be complex.

### `word_count`

Count main campaign/product-page content consistently.

**Type:** nonnegative whole-number count, or unset.

### `heading_count`

Count visible section/main headings.

**Type:** nonnegative whole-number count, or unset.

### `paragraph_count`

Count visible body paragraphs.

**Type:** nonnegative whole-number count, or unset.

### `bullet_list_count`

Count lists, not individual bullets.

**Type:** nonnegative whole-number count, or unset.

### `average_paragraph_length`

word_count / paragraph_count where applicable.

**Read-only calculation:** `word_count / paragraph_count` when both counts are recorded and paragraph_count is greater than zero; otherwise null. For example, 600 words / 12 paragraphs = 50. The UI rounds to two decimals; the API returns the unrounded value. Because the numerator is the page word count, this is the app’s ratio, not a separately measured mean of paragraph-only text.

### `headline_length`

Count words in primary headline.

**Type:** nonnegative whole-number count, or unset.

### `text_density`

Judge how text-heavy the page feels overall.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very little text |
| 2 | Low amount of text |
| 3 | Moderate amount of text |
| 4 | High amount of text |
| 5 | Very text-heavy page |

### `text_style`

Concise = short/direct; Detailed = extensive explanation.

**Allowed values:** `Concise`, `Balanced`, `Detailed`, or unset.

### `information_complexity`

Assess how difficult the information is to understand.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very simple |
| 2 | Simple |
| 3 | Moderate |
| 4 | Complex |
| 5 | Very complex |

## 3. Messaging & Tone

9 fields.

Distinguish a feature (“includes a debit card”) from a benefit (“pay conveniently every day”). Customer focus concerns needs; product focus concerns characteristics. main_message summarizes what the page says; value_proposition states why it asks the visitor to choose the offer. These are observations, not your recommendation.

### `tone_formality`

Assess language formality.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very casual |
| 2 | Mostly casual |
| 3 | Balanced |
| 4 | Mostly formal |
| 5 | Very formal |

### `tone_friendliness`

Assess warmth and conversational style.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Distant |
| 2 | Slightly friendly |
| 3 | Neutral/balanced |
| 4 | Friendly |
| 5 | Very friendly |

### `tone_persuasiveness`

Assess strength of selling/persuasion.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Purely informative |
| 2 | Mostly informative |
| 3 | Balanced |
| 4 | Persuasive |
| 5 | Highly persuasive |

### `emotional_vs_rational`

Emotional = feelings/lifestyle; Rational = facts/features/conditions.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Strongly emotional |
| 2 | Mostly emotional |
| 3 | Balanced |
| 4 | Mostly rational |
| 5 | Strongly rational |

### `customer_vs_product_focus`

Assess whether messaging starts from customer needs or product characteristics.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Strongly customer-focused |
| 2 | Mostly customer-focused |
| 3 | Balanced |
| 4 | Mostly product-focused |
| 5 | Strongly product-focused |

### `feature_vs_benefit_focus`

Feature = what product has; Benefit = what customer gains.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Strongly feature-focused |
| 2 | Mostly feature-focused |
| 3 | Balanced |
| 4 | Mostly benefit-focused |
| 5 | Strongly benefit-focused |

### `message_focus`

Choose the dominant messaging focus.

**Allowed values:** `Product`, `Feature`, `Benefit`, `Lifestyle`, `Price`, or unset.

### `main_message`

Summarize the central message without evaluating it.

**Type:** text, at most 10,000 characters, or unset.

### `value_proposition`

State the primary reason the page gives to choose the offer.

**Type:** text, at most 10,000 characters, or unset.

## 4. Images & Visuals

12 fields.

Count images containing people, not the number of people: one photograph showing four people gives people_image_count = 1. A hero is the opening section; it may exist without a hero image. When there is no hero image, record has_hero_image = No and hero_image_size = None. The choice None is an explicit observation and differs from an unset value.

### `image_count`

Count meaningful visible images consistently.

**Type:** nonnegative whole-number count, or unset.

### `has_hero_image`

Large primary image in the opening/hero area.

**Allowed values:** Yes, No, or Not set.

### `hero_image_size`

Judge relative size of main hero visual.

**Allowed values:** `None`, `Small`, `Medium`, `Large`, `Full-width`, or unset.

### `people_present`

Whether any main image/illustration contains people.

**Allowed values:** Yes, No, or Not set.

### `people_image_count`

Count separate images containing people.

**Type:** nonnegative whole-number count, or unset.

### `product_present`

Card, phone, banking app, product UI, etc.

**Allowed values:** Yes, No, or Not set.

### `illustration_present`

Non-photographic illustrations present.

**Allowed values:** Yes, No, or Not set.

### `icon_count`

Count meaningful communication icons.

**Type:** nonnegative whole-number count, or unset.

### `video_count`

Count embedded/visible videos.

**Type:** nonnegative whole-number count, or unset.

### `animation_present`

Animated illustrations, GIFs, motion elements, etc.

**Allowed values:** Yes, No, or Not set.

### `visual_style`

Choose dominant visual treatment.

**Allowed values:** `Photography`, `Illustration`, `3D`, `UI-Product`, `Mixed`, or unset.

### `visual_intensity`

Assess relative dominance of visuals over text.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Almost entirely text |
| 2 | Mostly text with a few visuals |
| 3 | Balanced text and visuals |
| 4 | Highly visual |
| 5 | Visuals dominate the page |

## 5. Colour & Design

7 fields.

Use a consistent color naming convention, such as “orange” or a measured hex value. Ignore tiny decorative variations when counting major colors. Colour contrast is a descriptive visual judgment here, not a measured accessibility contrast ratio or a compliance result. Visual consistency concerns repeated typography, spacing, imagery, and component treatment.

### `dominant_colour`

Record the visually dominant colour.

**Type:** text, at most 300 characters, or unset.

### `number_of_major_colours`

Ignore minor decorative colour variations.

**Type:** nonnegative whole-number count, or unset.

### `brand_colour_dominance`

How strongly recognizable brand colours dominate.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Brand colours barely visible |
| 2 | Limited use |
| 3 | Moderate use |
| 4 | Strong use |
| 5 | Brand colours dominate |

### `colour_contrast`

Assess visual contrast used to separate/highlight content.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very low |
| 2 | Low |
| 3 | Moderate |
| 4 | High |
| 5 | Very high |

### `design_complexity`

Assess number and complexity of competing design elements.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very minimal |
| 2 | Simple |
| 3 | Moderate |
| 4 | Complex |
| 5 | Very complex |

### `visual_consistency`

Assess consistency of visual language across the page.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very inconsistent |
| 2 | Somewhat inconsistent |
| 3 | Moderate |
| 4 | Consistent |
| 5 | Highly consistent |

### `attention_focus`

What attracts attention first/most strongly.

**Allowed values:** `Text`, `Image`, `CTA`, `Product`, `Mixed`, or unset.

## 6. Layout & Page Structure

10 fields.

A section is a meaningful content block, not every paragraph. An accordion is content that expands or collapses. Anchor navigation jumps to another section of the same page. Layout clarity concerns organization; scannability concerns how easily key points can be found without reading everything. Agree on viewport size and page-length thresholds across the team.

### `section_count`

Count meaningful page sections.

**Type:** nonnegative whole-number count, or unset.

### `page_length`

Use a team-agreed rule consistently.

**Allowed values:** `Short`, `Medium`, `Long`, or unset.

### `hero_section_present`

Whether a distinct opening hero section exists.

**Allowed values:** Yes, No, or Not set.

### `content_pattern`

Choose dominant page organization pattern.

**Allowed values:** `Text-first`, `Image-first`, `Alternating`, `Cards`, `Mixed`, or unset.

### `card_layout_present`

Whether information is presented in cards.

**Allowed values:** Yes, No, or Not set.

### `accordion_present`

Expandable/collapsible content present.

**Allowed values:** Yes, No, or Not set.

### `comparison_table_present`

Product/feature comparison table present.

**Allowed values:** Yes, No, or Not set.

### `navigation_anchor_present`

In-page anchor navigation present.

**Allowed values:** Yes, No, or Not set.

### `layout_clarity`

Assess how clearly the page is organized.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very confusing |
| 2 | Difficult to understand |
| 3 | Average |
| 4 | Clear |
| 5 | Very clear |

### `scannability`

How easily a visitor can scan and understand key sections/messages.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very difficult |
| 2 | Difficult |
| 3 | Average |
| 4 | Easy |
| 5 | Very easy |

## 7. Call to Action

6 fields.

A CTA asks the visitor to do something, such as open an account, apply, contact the bank, or calculate a quote. Agree on which action links count and whether repeated placements are counted separately. Copy the main CTA wording exactly. Above the fold means visible before scrolling at the agreed viewport; prominence describes visibility, not conversion performance.

### `cta_count`

Count meaningful conversion/action CTAs.

**Type:** nonnegative whole-number count, or unset.

### `primary_cta_text`

Copy exact main CTA text.

**Type:** text, at most 300 characters, or unset.

### `cta_above_fold`

Main CTA visible near initial viewport/opening section.

**Allowed values:** Yes, No, or Not set.

### `cta_repeated`

Whether primary/similar CTA appears repeatedly.

**Allowed values:** Yes, No, or Not set.

### `cta_prominence`

Assess visual prominence, not effectiveness.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very difficult to notice |
| 2 | Low visibility |
| 3 | Clearly visible |
| 4 | Highly prominent |
| 5 | Dominant action on the page |

### `cta_type`

Classify primary CTA intent.

**Allowed values:** `Apply`, `Buy`, `Open`, `Learn`, `Contact`, `Calculate`, `Other`, or unset.

## 8. Product & Value Proposition

11 fields.

A feature is a product capability; a benefit is a customer outcome. Count distinct claims consistently rather than counting repeated wording as new claims. For example, “mobile notifications” is a feature and “stay informed about spending” is a benefit. Record message-presence fields from explicit communication, not assumptions about the bank. If price_visible = No, leave price_prominence unset and explain why; the app does not enforce this relationship.

### `price_visible`

Price, fee, rate, or cost visibly communicated.

**Allowed values:** Yes, No, or Not set.

### `price_prominence`

Assess prominence only when price/rate is present.

**Type:** integer scale, 1–5.

| Score | Meaning |
| --- | --- |
| 1 | Very difficult to notice |
| 2 | Low visibility |
| 3 | Clearly visible |
| 4 | Highly prominent |
| 5 | Price dominates the communication |

### `promotion_present`

Temporary offer/bonus/promotion present.

**Allowed values:** Yes, No, or Not set.

### `benefit_count`

Count distinct customer outcomes/advantages.

**Type:** nonnegative whole-number count, or unset.

### `feature_count`

Count distinct product capabilities/characteristics.

**Type:** nonnegative whole-number count, or unset.

### `trust_message_present`

Explicit trust/reliability/reputation message.

**Allowed values:** Yes, No, or Not set.

### `security_message_present`

Explicit safety/security message.

**Allowed values:** Yes, No, or Not set.

### `convenience_message_present`

Explicit ease/convenience message.

**Allowed values:** Yes, No, or Not set.

### `digital_message_present`

Explicit digital/app/online experience message.

**Allowed values:** Yes, No, or Not set.

### `sustainability_message_present`

Explicit sustainability/environmental message.

**Allowed values:** Yes, No, or Not set.

### `main_value_driver`

Choose the dominant value driver.

**Allowed values:** `Price`, `Convenience`, `Security`, `Flexibility`, `Lifestyle`, `Digital`, `Service`, `Other`, or unset.

## Notes and system fields

| Field | Meaning | Editable during labeling? |
| --- | --- | --- |
| `labeling_notes` | Up to 10,000 characters explaining counting scope, uncertainty, exceptions, or inapplicability | Yes |
| `campaign_id` | Campaign linked to this feature record | No |
| `labeling_status` | Not Started, In Progress, or Completed | Through save/complete actions only |
| `source` | Record-level provenance: manual, automatic, or manual_override | No |
| `created_at`, `updated_at` | Record timestamps | No |

For progress calculation and save behavior, see [Feature framework](feature-framework.md).

## Final review checklist

- Confirm bank, source page, category, product, language, and review date.
- Check that counts follow the same scope as other pages in the sample.
- Distinguish missing observations from confirmed zero or No.
- Recheck scale direction: customer-to-product and feature-to-benefit run in different conceptual directions.
- Check dependent observations manually, such as no price with an unset price-prominence score.
- Explain uncertain or inapplicable fields in notes, then save or complete labeling.

For autosave, completion, and progress behavior, see [Feature framework](feature-framework.md). For requests and responses, see [API reference](api-reference.md#feature-labeling).
