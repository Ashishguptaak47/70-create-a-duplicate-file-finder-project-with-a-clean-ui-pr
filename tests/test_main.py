import os
import tempfile
import pytest
from main import app, compute_hash, find_duplicates

@pytest.fixture

def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_compute_hash():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(b"hello world")
        tf_path = tf.name
    try:
        h1 = compute_hash(tf_path)
        h2 = compute_hash(tf_path)
        assert h1 == h2
        assert len(h1) == 32
    finally:
        os.unlink(tf_path)

def test_find_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "file1.txt")
        f2 = os.path.join(tmpdir, "file2.txt")
        f3 = os.path.join(tmpdir, "file3.txt")

        content = b"identical content"
        with open(f1, "wb") as f:
            f.write(content)
        with open(f2, "wb") as f:
            f.write(content)
        with open(f3, "wb") as f:
            f.write(b"unique content")

        duplicates = find_duplicates(tmpdir)
        assert len(duplicates) == 1
        dup_paths = list(duplicates.values())[0]
        assert sorted(dup_paths) == sorted([f1, f2])

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Duplicate File Finder" in response.data
