"""Proves the Phase 0 'done when': Sabiha can import FakeRetriever and get a
valid response without any model, index, or network."""

from retrieval.fake_retriever import FakeRetriever

REQUIRED_RESULT_KEYS = {
    "answer_id",
    "category",
    "sub_category",
    "question",
    "answer",
    "source",
    "score",
    "path",
}


def test_returns_three_hardcoded_rows():
    response = FakeRetriever().search("any query at all")
    assert len(response["results"]) == 3


def test_response_matches_retrieval_json_contract_shape():
    response = FakeRetriever().search("test")
    assert set(response.keys()) == {"query_normalised", "results", "latency_ms"}
    assert isinstance(response["latency_ms"], int)
    for row in response["results"]:
        assert set(row.keys()) == REQUIRED_RESULT_KEYS
        assert isinstance(row["answer_id"], int)
        assert isinstance(row["score"], float)


def test_normalises_the_query_internally():
    response = FakeRetriever().search("حَيض   جِي")
    assert response["query_normalised"] == "حيض جي"


def test_no_answer_id_repeated():
    response = FakeRetriever().search("x")
    ids = [row["answer_id"] for row in response["results"]]
    assert len(ids) == len(set(ids))
