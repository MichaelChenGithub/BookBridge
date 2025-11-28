"""Item2Vec helpers to enrich OpenAI book candidates with similar titles."""

from __future__ import annotations

import json
import logging
import os
import re
import heapq
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence, Tuple

from google.cloud import storage
from gensim.models import KeyedVectors

LOG = logging.getLogger(__name__)

DEFAULT_BUCKET = os.getenv("BOOKBRIDGE_GCS_BUCKET") or "book_bridge"
DEFAULT_EMBEDDINGS_BLOB = os.getenv("BOOKBRIDGE_EMBEDDINGS_BLOB") or "models/item_embeddings.kv"
DEFAULT_TITLE_INDEX_BLOB = os.getenv("BOOKBRIDGE_TITLE_TO_ID_BLOB") or "indexes/title_to_id_index.json"
DEFAULT_METADATA_PREFIX = os.getenv("BOOKBRIDGE_METADATA_PREFIX") or "filtered_metadata"
DEFAULT_CACHE_DIR = Path(os.getenv("BOOKBRIDGE_CACHE_DIR") or "/tmp/bookbridge_cache")


class Item2VecError(RuntimeError):
    """Raised when item2vec assets or processing fails."""


@dataclass(frozen=True)
class Item2VecAssets:
    metadata_dir: Path
    title_index_path: Path
    embeddings_path: Path


def _normalize_title(title: str) -> str:
    if not title:
        return ""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def _has_files(directory: Path) -> bool:
    if not directory.exists():
        return False
    return any(directory.iterdir())


def _download_blob_if_needed(
    bucket: storage.Bucket, blob_name: str, destination: Path, force: bool
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        LOG.debug("Using cached asset at %s", destination)
        return
    LOG.info("Downloading %s to %s", blob_name, destination)
    blob = bucket.blob(blob_name)
    try:
        exists = blob.exists()
    except Exception as exc:
        raise Item2VecError(f"Error checking GCS object {blob_name}: {exc}") from exc
    if not exists:
        raise Item2VecError(f"GCS object not found: {blob_name}")
    try:
        blob.download_to_filename(destination)
    except Exception as exc:
        raise Item2VecError(f"Failed to download {blob_name}: {exc}") from exc


def _download_prefix_if_needed(
    bucket: storage.Bucket, prefix: str, destination_dir: Path, force: bool
) -> None:
    destination_dir.mkdir(parents=True, exist_ok=True)
    if _has_files(destination_dir) and not force:
        LOG.debug("Using cached metadata in %s", destination_dir)
        return

    normalized_prefix = prefix.rstrip("/") + "/"
    try:
        blobs = list(bucket.list_blobs(prefix=normalized_prefix))
    except Exception as exc:
        raise Item2VecError(f"Failed to list objects under {normalized_prefix}: {exc}") from exc

    if not blobs:
        raise Item2VecError(f"No objects found under prefix: {normalized_prefix}")

    for blob in blobs:
        if blob.name.endswith("/"):
            continue
        relative_name = Path(blob.name[len(normalized_prefix) :])
        target_path = destination_dir / relative_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        LOG.info("Downloading %s to %s", blob.name, target_path)
        try:
            blob.download_to_filename(target_path)
        except Exception as exc:
            raise Item2VecError(f"Failed to download {blob.name}: {exc}") from exc


def download_item2vec_assets(
    *,
    force: bool = False,
    include_metadata: bool = True,
    storage_client: storage.Client | None = None,
) -> Item2VecAssets:
    """
    Ensure item2vec assets are available locally, downloading from GCS if missing.

    Returns:
        Item2VecAssets with local paths to metadata, title index, and embeddings.
    """
    cache_dir = DEFAULT_CACHE_DIR
    metadata_dir = cache_dir / Path(DEFAULT_METADATA_PREFIX).name
    title_index_path = cache_dir / Path(DEFAULT_TITLE_INDEX_BLOB).name
    embeddings_path = cache_dir / Path(DEFAULT_EMBEDDINGS_BLOB).name

    assets = Item2VecAssets(
        metadata_dir=metadata_dir, title_index_path=title_index_path, embeddings_path=embeddings_path
    )

    needs_download = force or not (
        title_index_path.exists() and embeddings_path.exists() and (not include_metadata or _has_files(metadata_dir))
    )
    if not needs_download:
        return assets

    try:
        client = storage_client or storage.Client()
        bucket = client.bucket(DEFAULT_BUCKET)
    except Exception as exc:  # pragma: no cover - environment specific
        raise Item2VecError(f"Failed to init GCS client: {exc}") from exc

    _download_blob_if_needed(bucket, DEFAULT_TITLE_INDEX_BLOB, title_index_path, force)
    _download_blob_if_needed(bucket, DEFAULT_EMBEDDINGS_BLOB, embeddings_path, force)
    if include_metadata:
        _download_prefix_if_needed(bucket, DEFAULT_METADATA_PREFIX, metadata_dir, force)

    return assets


def _load_json(path: Path) -> MutableMapping[str, str]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise Item2VecError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise Item2VecError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, MutableMapping):
        raise Item2VecError(f"Expected mapping in {path}, got {type(data)}")
    return data


@lru_cache(maxsize=1)
def load_title_index(path: Path | str) -> Mapping[str, str]:
    """
    Load normalized title -> book_id mapping.

    Cached to avoid repeated disk reads in Cloud Run.
    """
    data = _load_json(Path(path))
    # Keys are pre-normalized, but normalize again defensively.
    return {_normalize_title(str(k)): str(v) for k, v in data.items()}


@lru_cache(maxsize=1)
def load_embeddings(path: Path | str) -> KeyedVectors:
    """Load item2vec embeddings into memory (mmap for speed)."""
    try:
        return KeyedVectors.load(str(path), mmap="r")
    except FileNotFoundError as exc:
        raise Item2VecError(f"Embeddings file not found: {path}") from exc
    except Exception as exc:  # pragma: no cover - depends on local model file
        raise Item2VecError(f"Failed to load embeddings: {exc}") from exc


def _iter_metadata_files(directory: Path) -> List[Path]:
    """Return all JSON/JSONL files under the metadata directory."""
    if not directory.exists():
        raise Item2VecError(f"Metadata directory not found: {directory}")
    files = list(directory.rglob("*.json")) + list(directory.rglob("*.jsonl"))
    if not files:
        raise Item2VecError(f"No metadata files found under: {directory}")
    return files


@lru_cache(maxsize=1)
def load_metadata_index(metadata_dir: Path | str) -> Mapping[str, Dict[str, Any]]:
    """
    Load metadata into an asin -> metadata mapping.

    Cached so repeated lookups are fast in Cloud Run.
    """
    metadata_dir = Path(metadata_dir)
    index: Dict[str, Dict[str, Any]] = {}
    for path in _iter_metadata_files(metadata_dir):
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    asin = record.get("asin")
                    if asin:
                        index[str(asin)] = record
        except FileNotFoundError:
            continue
    if not index:
        raise Item2VecError(f"No metadata records loaded from: {metadata_dir}")
    return index


def _extract_primary_image(entry: Mapping[str, Any]) -> Any:
    img = entry.get("primary_image")
    if isinstance(img, dict):
        for key in ("large", "medium", "small", "thumbnail"):
            if key in img:
                return img[key]
    return img


def get_book_details(
    book_ids: Sequence[str], *, force_download: bool = False
) -> List[Dict[str, Any]]:
    """
    Resolve book IDs into frontend-friendly metadata from filtered_metadata.
    """
    assets = download_item2vec_assets(force=force_download, include_metadata=True)
    metadata = load_metadata_index(assets.metadata_dir)

    details: List[Dict[str, Any]] = []
    for book_id in book_ids:
        entry = metadata.get(book_id, {})
        details.append(
            {
                "asin": book_id,
                "title": entry.get("title", "Unknown Title"),
                "author_name": entry.get("author_name", "Unknown Author"),
                "average_rating": entry.get("average_rating"),
                "rating_number": entry.get("rating_number"),
                "primary_image": _extract_primary_image(entry),
            }
        )
    return details


def filter_existing_titles(
    recommendations: Sequence[Mapping[str, str] | str], title_index: Mapping[str, str]
) -> List[str]:
    """Filter OpenAI recommendations to those present in the catalog and return book IDs."""
    seen: set[str] = set()
    valid_ids: List[str] = []
    for rec in recommendations:
        raw_title = rec.get("title") if isinstance(rec, Mapping) else str(rec)
        normalized = _normalize_title(raw_title)
        if not normalized:
            continue
        book_id = title_index.get(normalized)
        if book_id and book_id not in seen:
            valid_ids.append(book_id)
            seen.add(book_id)
        else:
            LOG.debug("Title missing from catalog or duplicate: %s", raw_title)
    return valid_ids


def _collect_similar(
    model: KeyedVectors, seed_id: str, *, topn: int
) -> List[Tuple[str, float]]:
    if seed_id not in model.key_to_index:
        LOG.debug("Seed ID missing from embeddings: %s", seed_id)
        return []
    return model.most_similar(seed_id, topn=topn)


def rerank_with_item2vec(
    seed_book_ids: Sequence[str],
    model: KeyedVectors,
    *,
    topn_per_seed: int = 50,
    final_k: int = 10,
    include_seed_titles: bool = True,
    min_similarity: float = 0.8,
) -> List[str]:
    """
    Collect per-seed neighbors, keep the best similarity per book, and return a global top-K.
    """
    best_scores: Dict[str, float] = {}

    for seed_id in seed_book_ids:
        if include_seed_titles:
            existing = best_scores.get(seed_id)
            if existing is None or 1.0 > existing:
                best_scores[seed_id] = 1.0

        for rec_id, similarity in _collect_similar(model, seed_id, topn=topn_per_seed):
            if similarity < min_similarity:
                continue
            existing = best_scores.get(rec_id)
            if existing is None or similarity > existing:
                best_scores[rec_id] = similarity

    top_items = heapq.nlargest(final_k, best_scores.items(), key=lambda item: item[1])
    return [book_id for book_id, _ in top_items]


def get_final_book_ids(
    recommendations: Sequence[Mapping[str, str] | str],
    *,
    force_download: bool = False,
    topn_per_seed: int = 50,
    final_k: int = 10,
) -> List[str]:
    """
    Full pipeline: download assets (if needed), map titles to IDs, run item2vec reranking.

    Args:
        recommendations: Ordered list of candidate dicts or strings containing titles.
        force_download: Force a fresh pull from GCS even if files exist locally.
        topn_per_seed: Similarity fanout for each validated seed ID.
        final_k: Number of book IDs to return.
    """
    assets = download_item2vec_assets(force=force_download)
    title_index = load_title_index(assets.title_index_path)
    seed_ids = filter_existing_titles(recommendations, title_index)
    if not seed_ids:
        LOG.warning("No recommendations matched the catalog; returning empty result.")
        return []

    model = load_embeddings(assets.embeddings_path)
    return rerank_with_item2vec(seed_ids, model, topn_per_seed=topn_per_seed, final_k=final_k)
