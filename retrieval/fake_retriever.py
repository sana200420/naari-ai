"""A retriever that needs no model, no index, and no network.

Lets Sabiha build and test the /api pipeline against a real import today,
without waiting on the actual bge-m3 + Qdrant retrieval stack. Returns the
exact shape documented in docs/contracts/retrieval.json.

    from retrieval.fake_retriever import FakeRetriever
    results = FakeRetriever().search("any query string")
"""

import time

from retrieval.normalize import normalize_sd

_FAKE_ROWS = [
    {
        "answer_id": 1,
        "category": "حيض جي صحت ۽ مدت",
        "sub_category": "سائيڪل جي بنياديات ۽ ڇا عام آهي",
        "question": "حيض جي چڪر ڇا آهي؟",
        "answer": (
            "حيض واري صورتحال جي دور ۾ هڪ مهيني هارمونل عمل uterine استر ٺهي ٿو "
            "۽ ان کان پوءِ ان حملا ممڪن نه آهن ته وهندو."
        ),
        "source": "WHO - https://www.who.int/news-room/fact-sheets/detail/menstrual-health-and-hygiene",
        "score": 0.91,
        "path": "sindhi_dense",
    },
    {
        "answer_id": 502,
        "category": "حمل ۽ ماءُ جي صحت",
        "sub_category": "حمل جي تصديق ۽ شروعاتي حمل",
        "question": "عام طور تي حمل جي پهرين نشاني ڇا هوندي آهي؟",
        "answer": (
            "گھڻين عورتن لاءِ پهرين نشاني ماهواري جو نه اچڻ هوندي آهي۔ "
            "ٿڪاوت محسوس ٿيڻ، طبيعت خراب لڳڻ يا ڇاتين ۾ سور به شروعات ۾ ٿي سگهي ٿو۔"
        ),
        "source": "https://www.who.int/news/item/07-11-2016-new-guidelines-on-antenatal-care-for-a-positive-pregnancy-experience",
        "score": 0.77,
        "path": "sindhi_sparse",
    },
    {
        "answer_id": 1502,
        "category": "ويجنل ۽ ذاتي صفائي",
        "sub_category": "روزاني انٽيميٽ حفظان صحت جي بنياديات",
        "question": "اندام جي علائقي کي ڪيترا ڀيرا ڌوئڻ گهرجي؟",
        "answer": (
            "ڏينهن ۾ هڪ ڀيرو گرم پاڻي سان گڏ عام طور تي ڪافي آهي. "
            "وولوا (ٻاهرئين حصي) کي آسانيءَ سان ڌوئي سگھجي ٿو."
        ),
        "source": "https://www.nhs.uk/live-well/sexual-health/",
        "score": 0.52,
        "path": "english_dense",
    },
]


class FakeRetriever:
    """Drop-in stand-in for the real retriever. Same shape, no dependencies."""

    def search(self, query: str) -> dict:
        start = time.perf_counter()
        query_normalised = normalize_sd(query)
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {
            "query_normalised": query_normalised,
            "results": list(_FAKE_ROWS),
            "latency_ms": latency_ms,
        }
