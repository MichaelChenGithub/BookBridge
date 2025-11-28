import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services import item2vec_client as i2v


class FakeBlob:
    def __init__(self, name: str, exists: bool = True):
        self.name = name
        self._exists = exists
        self.downloaded_to: list[Path] = []

    def exists(self) -> bool:
        return self._exists

    def download_to_filename(self, destination: Path) -> None:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(f"content:{self.name}")
        self.downloaded_to.append(destination)


class FakeBucket:
    def __init__(self, blobs: dict[str, FakeBlob]):
        self._blobs = blobs
        self.list_calls: list[str] = []
        self.requested: list[str] = []

    def blob(self, name: str) -> FakeBlob:
        self.requested.append(name)
        if name not in self._blobs:
            self._blobs[name] = FakeBlob(name, exists=False)
        return self._blobs[name]

    def list_blobs(self, prefix: str):
        self.list_calls.append(prefix)
        return [blob for name, blob in self._blobs.items() if name.startswith(prefix)]


class FakeClient:
    def __init__(self, bucket: FakeBucket):
        self._bucket = bucket
        self.bucket_names: list[str] = []

    def bucket(self, name: str) -> FakeBucket:
        self.bucket_names.append(name)
        return self._bucket


class FakeVectors:
    def __init__(self, neighbors_by_key: dict[str, list[tuple[str, float]]]):
        self._neighbors = neighbors_by_key
        self.key_to_index = {key: idx for idx, key in enumerate(neighbors_by_key)}

    def most_similar(self, key: str, topn: int = 10):
        return self._neighbors.get(key, [])[:topn]


def test_download_item2vec_assets_hits_gcs(monkeypatch, tmp_path):
    # Arrange defaults to point at temp cache.
    monkeypatch.setattr(i2v, "DEFAULT_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(i2v, "DEFAULT_BUCKET", "book_bridge")
    monkeypatch.setattr(i2v, "DEFAULT_EMBEDDINGS_BLOB", "models/item_embeddings.kv")
    monkeypatch.setattr(i2v, "DEFAULT_TITLE_INDEX_BLOB", "models/title_to_id.json")
    monkeypatch.setattr(i2v, "DEFAULT_METADATA_PREFIX", "filtered_metadata")

    blobs = {
        "models/item_embeddings.kv": FakeBlob("models/item_embeddings.kv"),
        "models/title_to_id.json": FakeBlob("models/title_to_id.json"),
        "filtered_metadata/meta.json": FakeBlob("filtered_metadata/meta.json"),
    }
    bucket = FakeBucket(blobs)
    client = FakeClient(bucket)

    assets = i2v.download_item2vec_assets(force=True, storage_client=client)

    # Ensures client.bucket called and downloads executed.
    assert client.bucket_names == ["book_bridge"]
    assert Path(blobs["models/item_embeddings.kv"].downloaded_to[0]).exists()
    assert Path(blobs["models/title_to_id.json"].downloaded_to[0]).exists()
    assert Path(blobs["filtered_metadata/meta.json"].downloaded_to[0]).exists()
    # Returned paths should match cache layout.
    assert assets.embeddings_path.name == "item_embeddings.kv"
    assert assets.title_index_path.name == "title_to_id.json"
    assert assets.metadata_dir.name == "filtered_metadata"


def test_download_item2vec_assets_uses_cache_when_present(monkeypatch, tmp_path):
    monkeypatch.setattr(i2v, "DEFAULT_CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(i2v, "DEFAULT_BUCKET", "book_bridge")
    monkeypatch.setattr(i2v, "DEFAULT_EMBEDDINGS_BLOB", "models/item_embeddings.kv")
    monkeypatch.setattr(i2v, "DEFAULT_TITLE_INDEX_BLOB", "models/title_to_id.json")
    monkeypatch.setattr(i2v, "DEFAULT_METADATA_PREFIX", "filtered_metadata")

    # Pre-create cached files to bypass downloads.
    cache_dir = i2v.DEFAULT_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "item_embeddings.kv").write_text("cached-embed")
    (cache_dir / "title_to_id.json").write_text("{}")
    meta_dir = cache_dir / "filtered_metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "meta.json").write_text("cached-meta")

    # Any attempt to download would raise.
    def _fail(*args, **kwargs):
        raise AssertionError("Should not download when cache exists")

    monkeypatch.setattr(i2v, "_download_blob_if_needed", _fail)
    monkeypatch.setattr(i2v, "_download_prefix_if_needed", _fail)

    assets = i2v.download_item2vec_assets(force=False, storage_client=FakeClient(FakeBucket({})))

    assert assets.embeddings_path.read_text() == "cached-embed"
    assert assets.title_index_path.read_text() == "{}"
    assert (assets.metadata_dir / "meta.json").read_text() == "cached-meta"


def test_download_blob_if_needed_respects_force(monkeypatch, tmp_path):
    blob = FakeBlob("models/item_embeddings.kv")
    bucket = FakeBucket({"models/item_embeddings.kv": blob})

    target = tmp_path / "item_embeddings.kv"
    target.write_text("existing")

    # Should skip when force=False
    i2v._download_blob_if_needed(bucket, "models/item_embeddings.kv", target, force=False)
    assert blob.downloaded_to == []

    # Should download when force=True
    i2v._download_blob_if_needed(bucket, "models/item_embeddings.kv", target, force=True)
    assert blob.downloaded_to != []


def test_filter_existing_titles_dedupes_and_orders():
    title_index = {"dune": "ID1", "thewayofkings": "ID2"}
    recs = [{"title": "Dune"}, {"title": "Dune "}, {"title": "The Way of Kings"}]

    result = i2v.filter_existing_titles(recs, title_index)

    assert result == ["ID1", "ID2"]


def test_collect_similar_handles_missing_seed():
    neighbors = {"A": [("B", 0.5)]}
    model = FakeVectors(neighbors)

    assert i2v._collect_similar(model, "MISSING", topn=5) == []
    assert i2v._collect_similar(model, "A", topn=1) == [("B", 0.5)]


def test_rerank_with_item2vec_simple_similarity_and_threshold():
    neighbors = {
        "A": [("X", 0.9), ("B", 0.1)],
        "B": [("X", 0.2), ("C", 0.8)],
    }
    model = FakeVectors(neighbors)

    ranked = i2v.rerank_with_item2vec(["A", "B"], model, topn_per_seed=2, final_k=4)

    # Seeds included (similarity 1.0), low-sim items filtered (<0.8), and ties broken by id.
    assert ranked == ["A", "B", "X", "C"]


def test_recommend_book_ids_full_pipeline(monkeypatch):
    assets = i2v.Item2VecAssets(
        metadata_dir=Path("/tmp/metadata"),
        title_index_path=Path("/tmp/title_to_id.json"),
        embeddings_path=Path("/tmp/item_embeddings.kv"),
    )

    monkeypatch.setattr(i2v, "download_item2vec_assets", lambda force=False: assets)
    monkeypatch.setattr(i2v, "load_title_index", lambda path: {"dune": "BOOK_DUNE"})
    monkeypatch.setattr(i2v, "load_embeddings", lambda path: FakeVectors({"BOOK_DUNE": [("BOOK_X", 0.8)]}))

    recs = [{"title": "Dune"}, {"title": "Unknown"}]

    result = i2v.get_final_book_ids(recs, final_k=3)

    assert result == ["BOOK_DUNE", "BOOK_X"]


def test_recommend_book_ids_returns_empty_when_no_matches(monkeypatch):
    assets = i2v.Item2VecAssets(
        metadata_dir=Path("/tmp/metadata"),
        title_index_path=Path("/tmp/title_to_id.json"),
        embeddings_path=Path("/tmp/item_embeddings.kv"),
    )
    monkeypatch.setattr(i2v, "download_item2vec_assets", lambda force=False: assets)
    monkeypatch.setattr(i2v, "load_title_index", lambda path: {})

    result = i2v.get_final_book_ids([{"title": "Unknown"}])

    assert result == []


def test_get_book_details_uses_metadata(monkeypatch, tmp_path):
    meta_dir = tmp_path / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "asin": "BOOK1",
        "title": "Title One",
        "author_name": "Author A",
        "average_rating": 4.5,
        "rating_number": 123,
        "primary_image": {"large": "http://image-large"},
    }
    (meta_dir / "part-000.json").write_text(json.dumps(record) + "\n")

    assets = i2v.Item2VecAssets(
        metadata_dir=meta_dir,
        title_index_path=Path("/tmp/title_to_id.json"),
        embeddings_path=Path("/tmp/item_embeddings.kv"),
    )

    monkeypatch.setattr(
        i2v, "download_item2vec_assets", lambda force=False, include_metadata=True: assets
    )
    i2v.load_metadata_index.cache_clear()

    details = i2v.get_book_details(["BOOK1", "BOOK2"])
    i2v.load_metadata_index.cache_clear()

    assert details[0]["title"] == "Title One"
    assert details[0]["author_name"] == "Author A"
    assert details[0]["average_rating"] == 4.5
    assert details[0]["rating_number"] == 123
    assert details[0]["primary_image"] == "http://image-large"
    # Missing book gets defaults and preserved asin.
    assert details[1]["asin"] == "BOOK2"
    assert details[1]["title"] == "Unknown Title"
