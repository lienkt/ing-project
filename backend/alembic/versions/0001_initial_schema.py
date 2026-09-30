"""Complete initial schema for a fresh installation.

This baseline replaces the previous migration chain. Use an empty database.
"""

from alembic import op
import sqlalchemy as sa

revision = "initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "banks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("normalized_name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name"),
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_name", sa.String(length=120), nullable=False),
        sa.Column("project", sa.String(length=40), nullable=False),
        sa.Column("campaign_url", sa.String(length=2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_campaigns_bank_name"), "campaigns", ["bank_name"], unique=False
    )
    op.create_index(
        op.f("ix_campaigns_project"), "campaigns", ["project"], unique=False
    )
    op.create_table(
        "deleted_sources",
        sa.Column("source_id", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
    )
    op.create_table(
        "projects",
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "user_sources",
        sa.Column("source_id", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("definition", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("source_url"),
    )
    op.create_table(
        "campaign_details",
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("campaign_name", sa.String(length=300), nullable=True),
        sa.Column("headline", sa.Text(), nullable=True),
        sa.Column("subheadline", sa.Text(), nullable=True),
        sa.Column("main_message", sa.Text(), nullable=True),
        sa.Column("cta_text", sa.String(length=300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("text_density", sa.String(length=40), nullable=True),
        sa.Column("tone", sa.String(length=120), nullable=True),
        sa.Column("feature_vs_benefit", sa.String(length=40), nullable=True),
        sa.Column("emotional_vs_rational", sa.String(length=40), nullable=True),
        sa.Column("customer_vs_product_focus", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id"),
    )
    op.create_table(
        "campaign_features",
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("bank_type", sa.String(length=20), nullable=True),
        sa.Column("product_name", sa.String(length=300), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("capture_date", sa.Date(), nullable=True),
        sa.Column("headline_length", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("heading_count", sa.Integer(), nullable=True),
        sa.Column("paragraph_count", sa.Integer(), nullable=True),
        sa.Column("bullet_list_count", sa.Integer(), nullable=True),
        sa.Column("text_density", sa.Integer(), nullable=True),
        sa.Column("text_style", sa.String(length=300), nullable=True),
        sa.Column("information_complexity", sa.Integer(), nullable=True),
        sa.Column("tone_formality", sa.Integer(), nullable=True),
        sa.Column("tone_friendliness", sa.Integer(), nullable=True),
        sa.Column("tone_persuasiveness", sa.Integer(), nullable=True),
        sa.Column("emotional_vs_rational", sa.Integer(), nullable=True),
        sa.Column("customer_vs_product_focus", sa.Integer(), nullable=True),
        sa.Column("feature_vs_benefit_focus", sa.Integer(), nullable=True),
        sa.Column("message_focus", sa.String(length=300), nullable=True),
        sa.Column("main_message", sa.Text(), nullable=True),
        sa.Column("value_proposition", sa.Text(), nullable=True),
        sa.Column("image_count", sa.Integer(), nullable=True),
        sa.Column("has_hero_image", sa.Boolean(), nullable=True),
        sa.Column("hero_image_size", sa.String(length=300), nullable=True),
        sa.Column("people_present", sa.Boolean(), nullable=True),
        sa.Column("people_image_count", sa.Integer(), nullable=True),
        sa.Column("product_present", sa.Boolean(), nullable=True),
        sa.Column("illustration_present", sa.Boolean(), nullable=True),
        sa.Column("icon_count", sa.Integer(), nullable=True),
        sa.Column("video_count", sa.Integer(), nullable=True),
        sa.Column("animation_present", sa.Boolean(), nullable=True),
        sa.Column("visual_style", sa.String(length=300), nullable=True),
        sa.Column("visual_intensity", sa.Integer(), nullable=True),
        sa.Column("dominant_colour", sa.String(length=300), nullable=True),
        sa.Column("number_of_major_colours", sa.Integer(), nullable=True),
        sa.Column("brand_colour_dominance", sa.Integer(), nullable=True),
        sa.Column("colour_contrast", sa.Integer(), nullable=True),
        sa.Column("design_complexity", sa.Integer(), nullable=True),
        sa.Column("visual_consistency", sa.Integer(), nullable=True),
        sa.Column("attention_focus", sa.String(length=300), nullable=True),
        sa.Column("section_count", sa.Integer(), nullable=True),
        sa.Column("page_length", sa.String(length=300), nullable=True),
        sa.Column("hero_section_present", sa.Boolean(), nullable=True),
        sa.Column("content_pattern", sa.String(length=300), nullable=True),
        sa.Column("card_layout_present", sa.Boolean(), nullable=True),
        sa.Column("accordion_present", sa.Boolean(), nullable=True),
        sa.Column("comparison_table_present", sa.Boolean(), nullable=True),
        sa.Column("navigation_anchor_present", sa.Boolean(), nullable=True),
        sa.Column("layout_clarity", sa.Integer(), nullable=True),
        sa.Column("scannability", sa.Integer(), nullable=True),
        sa.Column("cta_count", sa.Integer(), nullable=True),
        sa.Column("primary_cta_text", sa.String(length=300), nullable=True),
        sa.Column("cta_above_fold", sa.Boolean(), nullable=True),
        sa.Column("cta_repeated", sa.Boolean(), nullable=True),
        sa.Column("cta_prominence", sa.Integer(), nullable=True),
        sa.Column("cta_type", sa.String(length=300), nullable=True),
        sa.Column("price_visible", sa.Boolean(), nullable=True),
        sa.Column("price_prominence", sa.Integer(), nullable=True),
        sa.Column("promotion_present", sa.Boolean(), nullable=True),
        sa.Column("benefit_count", sa.Integer(), nullable=True),
        sa.Column("feature_count", sa.Integer(), nullable=True),
        sa.Column("trust_message_present", sa.Boolean(), nullable=True),
        sa.Column("security_message_present", sa.Boolean(), nullable=True),
        sa.Column("convenience_message_present", sa.Boolean(), nullable=True),
        sa.Column("digital_message_present", sa.Boolean(), nullable=True),
        sa.Column("sustainability_message_present", sa.Boolean(), nullable=True),
        sa.Column("main_value_driver", sa.String(length=300), nullable=True),
        sa.Column("labeling_notes", sa.Text(), nullable=True),
        sa.Column(
            "labeling_status",
            sa.String(length=20),
            server_default="Not Started",
            nullable=False,
        ),
        sa.Column(
            "source", sa.String(length=20), server_default="manual", nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "attention_focus IN ('Text', 'Image', 'CTA', 'Product', 'Mixed')",
            name="ck_cf_attention_focus",
        ),
        sa.CheckConstraint(
            "bank_type IN ('Traditional', 'Challenger', 'Neobank')",
            name="ck_cf_bank_type",
        ),
        sa.CheckConstraint(
            "content_pattern IN ('Text-first', 'Image-first', 'Alternating', 'Cards', 'Mixed')",
            name="ck_cf_content_pattern",
        ),
        sa.CheckConstraint(
            "cta_type IN ('Apply', 'Buy', 'Open', 'Learn', 'Contact', 'Calculate', 'Other')",
            name="ck_cf_cta_type",
        ),
        sa.CheckConstraint(
            "hero_image_size IN ('None', 'Small', 'Medium', 'Large', 'Full-width')",
            name="ck_cf_hero_image_size",
        ),
        sa.CheckConstraint(
            "labeling_status IN ('Not Started', 'In Progress', 'Completed')",
            name="ck_cf_labeling_status",
        ),
        sa.CheckConstraint(
            "language IN ('Dutch', 'French', 'English', 'Other')", name="ck_cf_language"
        ),
        sa.CheckConstraint(
            "main_value_driver IN ('Price', 'Convenience', 'Security', 'Flexibility', 'Lifestyle', 'Digital', 'Service', 'Other')",
            name="ck_cf_main_value_driver",
        ),
        sa.CheckConstraint(
            "message_focus IN ('Product', 'Feature', 'Benefit', 'Lifestyle', 'Price')",
            name="ck_cf_message_focus",
        ),
        sa.CheckConstraint(
            "page_length IN ('Short', 'Medium', 'Long')", name="ck_cf_page_length"
        ),
        sa.CheckConstraint(
            "source IN ('manual', 'automatic', 'manual_override')", name="ck_cf_source"
        ),
        sa.CheckConstraint(
            "text_style IN ('Concise', 'Balanced', 'Detailed')", name="ck_cf_text_style"
        ),
        sa.CheckConstraint(
            "visual_style IN ('Photography', 'Illustration', '3D', 'UI-Product', 'Mixed')",
            name="ck_cf_visual_style",
        ),
        sa.CheckConstraint("benefit_count >= 0", name="ck_cf_benefit_count"),
        sa.CheckConstraint(
            "brand_colour_dominance BETWEEN 1 AND 5",
            name="ck_cf_brand_colour_dominance",
        ),
        sa.CheckConstraint("bullet_list_count >= 0", name="ck_cf_bullet_list_count"),
        sa.CheckConstraint(
            "colour_contrast BETWEEN 1 AND 5", name="ck_cf_colour_contrast"
        ),
        sa.CheckConstraint("cta_count >= 0", name="ck_cf_cta_count"),
        sa.CheckConstraint(
            "cta_prominence BETWEEN 1 AND 5", name="ck_cf_cta_prominence"
        ),
        sa.CheckConstraint(
            "customer_vs_product_focus BETWEEN 1 AND 5",
            name="ck_cf_customer_vs_product_focus",
        ),
        sa.CheckConstraint(
            "design_complexity BETWEEN 1 AND 5", name="ck_cf_design_complexity"
        ),
        sa.CheckConstraint(
            "emotional_vs_rational BETWEEN 1 AND 5", name="ck_cf_emotional_vs_rational"
        ),
        sa.CheckConstraint("feature_count >= 0", name="ck_cf_feature_count"),
        sa.CheckConstraint(
            "feature_vs_benefit_focus BETWEEN 1 AND 5",
            name="ck_cf_feature_vs_benefit_focus",
        ),
        sa.CheckConstraint("heading_count >= 0", name="ck_cf_heading_count"),
        sa.CheckConstraint("headline_length >= 0", name="ck_cf_headline_length"),
        sa.CheckConstraint("icon_count >= 0", name="ck_cf_icon_count"),
        sa.CheckConstraint("image_count >= 0", name="ck_cf_image_count"),
        sa.CheckConstraint(
            "information_complexity BETWEEN 1 AND 5",
            name="ck_cf_information_complexity",
        ),
        sa.CheckConstraint(
            "layout_clarity BETWEEN 1 AND 5", name="ck_cf_layout_clarity"
        ),
        sa.CheckConstraint(
            "number_of_major_colours >= 0", name="ck_cf_number_of_major_colours"
        ),
        sa.CheckConstraint("paragraph_count >= 0", name="ck_cf_paragraph_count"),
        sa.CheckConstraint("people_image_count >= 0", name="ck_cf_people_image_count"),
        sa.CheckConstraint(
            "price_prominence BETWEEN 1 AND 5", name="ck_cf_price_prominence"
        ),
        sa.CheckConstraint("scannability BETWEEN 1 AND 5", name="ck_cf_scannability"),
        sa.CheckConstraint("section_count >= 0", name="ck_cf_section_count"),
        sa.CheckConstraint("text_density BETWEEN 1 AND 5", name="ck_cf_text_density"),
        sa.CheckConstraint(
            "tone_formality BETWEEN 1 AND 5", name="ck_cf_tone_formality"
        ),
        sa.CheckConstraint(
            "tone_friendliness BETWEEN 1 AND 5", name="ck_cf_tone_friendliness"
        ),
        sa.CheckConstraint(
            "tone_persuasiveness BETWEEN 1 AND 5", name="ck_cf_tone_persuasiveness"
        ),
        sa.CheckConstraint("video_count >= 0", name="ck_cf_video_count"),
        sa.CheckConstraint(
            "visual_consistency BETWEEN 1 AND 5", name="ck_cf_visual_consistency"
        ),
        sa.CheckConstraint(
            "visual_intensity BETWEEN 1 AND 5", name="ck_cf_visual_intensity"
        ),
        sa.CheckConstraint("word_count >= 0", name="ck_cf_word_count"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id"),
    )
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column(
            "source", sa.String(length=40), server_default="manual", nullable=False
        ),
        sa.Column("clarity_score", sa.Integer(), nullable=False),
        sa.Column("visual_score", sa.Integer(), nullable=False),
        sa.Column("benefit_score", sa.Integer(), nullable=False),
        sa.Column("cta_score", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("benefit_score BETWEEN 1 AND 5", name="ck_benefit_score"),
        sa.CheckConstraint("clarity_score BETWEEN 1 AND 5", name="ck_clarity_score"),
        sa.CheckConstraint("cta_score BETWEEN 1 AND 5", name="ck_cta_score"),
        sa.CheckConstraint("overall_score BETWEEN 1 AND 5", name="ck_overall_score"),
        sa.CheckConstraint("visual_score BETWEEN 1 AND 5", name="ck_visual_score"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id"),
    )
    op.create_table(
        "feature_proposals",
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=36), nullable=False),
        sa.Column("engine", sa.String(length=100), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("baseline", sa.JSON(), nullable=False),
        sa.Column("reviewed", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("campaign_id"),
    )
    op.create_table(
        "page_captures",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("page", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_page_captures_campaign_id"),
        "page_captures",
        ["campaign_id"],
        unique=False,
    )
    op.create_table(
        "source_imports",
        sa.Column("source_id", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("engine", sa.String(length=100), nullable=False),
        sa.Column("page", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("campaign_id"),
        sa.UniqueConstraint("source_url"),
    )

    banks = sa.table(
        "banks",
        sa.column("name", sa.String()),
        sa.column("normalized_name", sa.String()),
    )
    op.bulk_insert(
        banks,
        [
            {"name": name, "normalized_name": name.lower()}
            for name in ("ING", "KBC", "Belfius", "BNP Paribas Fortis")
        ],
    )
    projects = sa.table(
        "projects", sa.column("key", sa.String()), sa.column("name", sa.String())
    )
    op.bulk_insert(
        projects,
        [
            {"key": key, "name": key.replace("_", " ").title()}
            for key in (
                "credit_card",
                "savings_account",
                "current_account",
                "personal_loan",
                "mortgage",
                "insurance",
                "investment",
                "other",
            )
        ],
    )


def downgrade():
    op.drop_table("source_imports")
    op.drop_index(op.f("ix_page_captures_campaign_id"), table_name="page_captures")
    op.drop_table("page_captures")
    op.drop_table("feature_proposals")
    op.drop_table("evaluations")
    op.drop_table("campaign_features")
    op.drop_table("campaign_details")
    op.drop_table("user_sources")
    op.drop_table("projects")
    op.drop_table("deleted_sources")
    op.drop_index(op.f("ix_campaigns_project"), table_name="campaigns")
    op.drop_index(op.f("ix_campaigns_bank_name"), table_name="campaigns")
    op.drop_table("campaigns")
    op.drop_table("banks")
