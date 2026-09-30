"""Initial PostgreSQL schema for CompareBuy

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Brands
    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brands_name'), 'brands', ['name'], unique=True)

    # 2. Products
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('price', sa.BigInteger(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('release_year', sa.Integer(), nullable=True),
        sa.Column('score_performance', sa.Integer(), nullable=True),
        sa.Column('score_camera', sa.Integer(), nullable=True),
        sa.Column('score_battery', sa.Integer(), nullable=True),
        sa.Column('score_display', sa.Integer(), nullable=True),
        sa.Column('score_build_quality', sa.Integer(), nullable=True),
        sa.Column('score_value', sa.Integer(), nullable=True),
        sa.Column('score_audio', sa.Integer(), nullable=True),
        sa.Column('score_software', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint('price >= 0', name='ck_product_price_non_negative'),
        sa.CheckConstraint('release_year >= 1900', name='ck_product_release_year_valid'),
        sa.CheckConstraint('score_performance >= 0 AND score_performance <= 100', name='ck_product_score_perf'),
        sa.CheckConstraint('score_camera >= 0 AND score_camera <= 100', name='ck_product_score_cam'),
        sa.CheckConstraint('score_battery >= 0 AND score_battery <= 100', name='ck_product_score_batt'),
        sa.CheckConstraint('score_display >= 0 AND score_display <= 100', name='ck_product_score_disp'),
        sa.CheckConstraint('score_build_quality >= 0 AND score_build_quality <= 100', name='ck_product_score_build'),
        sa.CheckConstraint('score_value >= 0 AND score_value <= 100', name='ck_product_score_val'),
        sa.CheckConstraint('score_audio >= 0 AND score_audio <= 100', name='ck_product_score_aud'),
        sa.CheckConstraint('score_software >= 0 AND score_software <= 100', name='ck_product_score_soft'),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_brand_id'), 'products', ['brand_id'], unique=False)
    op.create_index(op.f('ix_products_category'), 'products', ['category'], unique=False)
    op.create_index(op.f('ix_products_is_active'), 'products', ['is_active'], unique=False)
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_index(op.f('ix_products_price'), 'products', ['price'], unique=False)

    # 3. ProductSpecs
    op.create_table(
        'product_specs',
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('specifications', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id')
    )

    # 4. ReviewSentiment
    op.create_table(
        'review_sentiments',
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('total_reviews', sa.Integer(), nullable=True),
        sa.Column('pros', sa.JSON(), nullable=True),
        sa.Column('cons', sa.JSON(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint('overall_score >= 0.0 AND overall_score <= 5.0', name='ck_review_overall_score'),
        sa.CheckConstraint('total_reviews >= 0', name='ck_review_total_reviews'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id')
    )

    # 5. WarrantyInfo
    op.create_table(
        'warranty_infos',
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('duration_months', sa.Integer(), nullable=True),
        sa.Column('coverage', sa.Text(), nullable=True),
        sa.Column('claim_ease', sa.Integer(), nullable=True),
        sa.Column('official_service_centers', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint('duration_months >= 0', name='ck_warranty_duration_months'),
        sa.CheckConstraint('claim_ease >= 1 AND claim_ease <= 10', name='ck_warranty_claim_ease'),
        sa.CheckConstraint('official_service_centers >= 0', name='ck_warranty_service_centers'),
        sa.CheckConstraint('score >= 0.0 AND score <= 100.0', name='ck_warranty_score_range'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id')
    )

    # 6. Tags
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)

    # 7. ProductTag
    op.create_table(
        'product_tags',
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id', 'tag_id')
    )
    op.create_index('ix_product_tag_pair', 'product_tags', ['product_id', 'tag_id'], unique=False)

    # 8. Marketplaces
    op.create_table(
        'marketplaces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_marketplaces_code'), 'marketplaces', ['code'], unique=True)

    # 9. MarketplaceLinks
    op.create_table(
        'marketplace_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('marketplace_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['marketplace_id'], ['marketplaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('product_id', 'marketplace_id', name='uq_product_marketplace_link')
    )

    # 10. MarketplacePrices
    op.create_table(
        'marketplace_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.String(length=50), nullable=False),
        sa.Column('marketplace_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.BigInteger(), nullable=False),
        sa.Column('seller', sa.String(length=255), nullable=True),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('available', sa.Boolean(), nullable=True),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('captured_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('price > 0', name='ck_marketplace_price_positive'),
        sa.ForeignKeyConstraint(['marketplace_id'], ['marketplaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_product_mkt_captured', 'marketplace_prices', ['product_id', 'marketplace_id', 'captured_at'], unique=False)


def downgrade() -> None:
    op.drop_table('marketplace_prices')
    op.drop_table('marketplace_links')
    op.drop_table('marketplaces')
    op.drop_table('product_tags')
    op.drop_table('tags')
    op.drop_table('warranty_infos')
    op.drop_table('review_sentiments')
    op.drop_table('product_specs')
    op.drop_table('products')
    op.drop_table('brands')
