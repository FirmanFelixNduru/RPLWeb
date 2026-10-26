"""Regression tests for ORM constraints and offline PostgreSQL DDL.

Run from backend: python -B -m unittest tests.test_metadata_constraints -v
The actual models are imported with dotenv loading and engine creation disabled.
No database connection or DDL execution is needed.
"""
import os
import unittest
from unittest.mock import patch

from sqlalchemy import CheckConstraint, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from tests import _pretty  # noqa: F401 (repository test output formatting)


with patch.dict(os.environ, {"DATABASE_URL": ""}), patch(
    "dotenv.load_dotenv", return_value=False
), patch(
    "sqlalchemy.create_engine",
    side_effect=AssertionError("Metadata tests must not create a database engine."),
) as create_engine_guard:
    from app.entities import Product, ProductTag, Tag

    create_engine_guard.assert_not_called()


class TestMetadataConstraints(unittest.TestCase):
    """Inspect actual table metadata without creating or querying tables."""

    def test_tag_has_trimmed_nonempty_name_constraint(self):
        checks = [
            constraint for constraint in Tag.__table__.constraints
            if isinstance(constraint, CheckConstraint)
            and constraint.name == "ck_tag_name_nonempty"
        ]
        self.assertEqual(len(checks), 1)
        self.assertIs(checks[0].table, Tag.__table__)

        # Compare the metadata expression with length(trim(tags.name)) > 0.
        # TRIM removes spaces before LENGTH tests whether anything remains.
        dialect = postgresql.dialect()
        expected = (func.length(func.trim(Tag.__table__.c.name)) > 0).compile(
            dialect=dialect,
            compile_kwargs={"literal_binds": True, "include_table": False},
        )
        actual = checks[0].sqltext.compile(dialect=dialect)
        self.assertEqual(" ".join(str(actual).split()), " ".join(str(expected).split()))

    def test_product_tag_has_no_name_constraint(self):
        for constraint in ProductTag.__table__.constraints:
            self.assertNotEqual(constraint.name, "ck_tag_name_nonempty")
            if isinstance(constraint, CheckConstraint):
                self.assertNotRegex(str(constraint.sqltext), r"\bname\b")

    def test_product_tag_preserves_composite_primary_key(self):
        table = ProductTag.__table__
        self.assertEqual(list(table.columns.keys()), ["product_id", "tag_id"])
        self.assertEqual(list(table.primary_key.columns.keys()), ["product_id", "tag_id"])
        self.assertFalse(table.c.product_id.nullable)
        self.assertFalse(table.c.tag_id.nullable)

    def test_product_tag_preserves_foreign_keys(self):
        foreign_keys = {
            (key.parent.name, key.target_fullname, key.ondelete)
            for key in ProductTag.__table__.foreign_keys
        }
        self.assertEqual(foreign_keys, {
            ("product_id", "products.id", "CASCADE"),
            ("tag_id", "tags.id", "CASCADE"),
        })

    def test_product_tag_preserves_pair_index(self):
        indexes = [
            index for index in ProductTag.__table__.indexes
            if index.name == "ix_product_tag_pair"
        ]
        self.assertEqual(len(indexes), 1)
        self.assertEqual(list(indexes[0].columns.keys()), ["product_id", "tag_id"])
        self.assertFalse(indexes[0].unique)

    def test_product_tag_preserves_bidirectional_relationship(self):
        self.assertIs(Tag.products.property.secondary, ProductTag.__table__)
        self.assertIs(Tag.products.property.mapper.class_, Product)
        self.assertEqual(Tag.products.property.back_populates, "tags")
        self.assertIs(Product.tags.property.secondary, ProductTag.__table__)
        self.assertIs(Product.tags.property.mapper.class_, Tag)
        self.assertEqual(Product.tags.property.back_populates, "products")

    def test_postgresql_ddl_places_name_constraint_only_on_tags(self):
        dialect = postgresql.dialect()
        tags_ddl = " ".join(str(CreateTable(Tag.__table__).compile(dialect=dialect)).split())
        product_tags_ddl = str(CreateTable(ProductTag.__table__).compile(dialect=dialect))
        self.assertIn(
            "CONSTRAINT ck_tag_name_nonempty CHECK (length(trim(name)) > 0)",
            tags_ddl,
        )
        self.assertNotIn("ck_tag_name_nonempty", product_tags_ddl)


if __name__ == "__main__":
    unittest.main(verbosity=2)
