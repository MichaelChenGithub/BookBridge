#!/usr/bin/env python3
"""BookBridge ETL job for Dataproc.

This script prepares:
1) Item2Vec training corpus from verified Amazon book reviews.
2) Slimmed book metadata joined to the top-K popular books.

Defaults assume GCS paths inside a bucket, but all inputs/outputs can be
overridden via CLI flags for flexibility when testing or backfilling.
"""

import argparse
import logging
from typing import Tuple

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast

LOG = logging.getLogger("bookbridge_etl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BookBridge ETL for Dataproc")
    parser.add_argument(
        "--bucket",
        default="book_bridge",
        help="GCS bucket (without gs://) used for default input/output paths",
    )
    parser.add_argument(
        "--reviews-path",
        help="GCS path to reviews JSONL; defaults to gs://<bucket>/Books.jsonl",
    )
    parser.add_argument(
        "--meta-path",
        help="GCS path to metadata JSONL; defaults to gs://<bucket>/meta_Books.jsonl",
    )
    parser.add_argument(
        "--training-output",
        help="Output path for item2vec corpus; defaults to gs://<bucket>/item2vec_training_data",
    )
    parser.add_argument(
        "--metadata-output",
        help="Output path for filtered metadata; defaults to gs://<bucket>/filtered_metadata",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100_000,
        help="Number of most-reviewed verified books to keep",
    )
    parser.add_argument(
        "--min-sequence-length",
        type=int,
        default=3,
        help="Minimum user history length to keep for item2vec training",
    )
    parser.add_argument(
        "--app-name",
        default="BookBridge_ETL",
        help="Spark application name",
    )
    return parser.parse_args()


def setup_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        level=logging.INFO,
    )


def build_spark(app_name: str) -> SparkSession:
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    spark.conf.set("spark.sql.caseSensitive", "true")
    LOG.info("Spark version: %s", spark.version)
    return spark


def derive_paths(args: argparse.Namespace) -> Tuple[str, str, str, str]:
    bucket = args.bucket
    reviews_path = args.reviews_path or f"gs://{bucket}/Books.jsonl"
    meta_path = args.meta_path or f"gs://{bucket}/meta_Books.jsonl"
    training_output = args.training_output or f"gs://{bucket}/item2vec_training_data"
    metadata_output = args.metadata_output or f"gs://{bucket}/filtered_metadata"
    return reviews_path, meta_path, training_output, metadata_output


def compute_top_books(reviews_df: DataFrame, top_k: int) -> Tuple[DataFrame, DataFrame]:
    """Filter verified purchases and compute the top-K book ASINs."""
    verified_df = reviews_df.filter(F.col("verified_purchase") == True)
    top_books = (
        verified_df.groupBy("asin")
        .count()
        .orderBy(F.col("count").desc())
        .limit(top_k)
        .select("asin")
    )
    top_books.cache()
    cached = top_books.count()
    LOG.info("Cached %s top books from verified purchases", cached)
    return verified_df, top_books


def build_training_sequences(
    verified_reviews: DataFrame, top_books: DataFrame, min_len: int
) -> DataFrame:
    """Create space-separated ASIN sequences per user for item2vec."""
    filtered_reviews = verified_reviews.join(broadcast(top_books), "asin", "inner")
    sequences = (
        filtered_reviews.orderBy("timestamp")
        .groupBy("user_id")
        .agg(F.collect_list("asin").alias("item_sequence"))
        .filter(F.size(F.col("item_sequence")) >= min_len)
        .select(F.concat_ws(" ", "item_sequence").alias("sentence"))
    )
    total_sequences = sequences.count()
    LOG.info("Users with valid sequences: %s", total_sequences)
    return sequences


def clean_metadata(meta_df: DataFrame, top_books: DataFrame) -> DataFrame:
    """Trim metadata fields and join to top books."""
    cleaned = meta_df.select(
        F.col("parent_asin").alias("asin"),
        F.col("title"),
        F.col("main_category"),
        F.col("average_rating"),
        F.col("rating_number"),
        F.col("description"),
        F.col("categories"),
        F.col("author.name").alias("author_name"),
        F.col("images").getItem(0).alias("primary_image"),
    )
    filtered = cleaned.join(broadcast(top_books), "asin", "inner")
    return filtered.na.fill(
        {"title": "Unknown Title", "main_category": "Uncategorized", "author_name": "Unknown Author"}
    )


def write_training_data(training_df: DataFrame, output_path: str) -> None:
    LOG.info("Writing training corpus to %s", output_path)
    training_df.write.mode("overwrite").text(output_path, compression="gzip")


def write_metadata(filtered_meta: DataFrame, output_path: str) -> None:
    LOG.info("Writing filtered metadata to %s", output_path)
    filtered_meta.coalesce(1).write.mode("overwrite").json(output_path)


def main() -> None:
    args = parse_args()
    setup_logging()
    reviews_path, meta_path, training_output, metadata_output = derive_paths(args)

    spark = build_spark(args.app_name)
    try:
        LOG.info("Loading reviews from %s", reviews_path)
        reviews_df = spark.read.json(reviews_path)

        LOG.info("Loading metadata from %s", meta_path)
        meta_df = spark.read.json(meta_path)

        verified_reviews, top_books = compute_top_books(reviews_df, args.top_k)

        training_sequences = build_training_sequences(
            verified_reviews, top_books, args.min_sequence_length
        )
        write_training_data(training_sequences, training_output)

        filtered_meta = clean_metadata(meta_df, top_books)
        write_metadata(filtered_meta, metadata_output)
    finally:
        spark.stop()
        LOG.info("Spark application stopped")


if __name__ == "__main__":
    main()
