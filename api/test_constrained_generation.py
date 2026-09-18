"""If retrieved context is deliberately irrelevant, model must refuse,
not answer from its own knowledge."""

def test_model_refuses_with_irrelevant_context(monkeypatch):
    import api.pipeline as p

    fake_chunks = [{"text": "The capital of France is Paris."}]
    query = "Is it normal to have heavy bleeding after delivery?"

    response = p.generate(query=query, chunks=fake_chunks)

    print("\n\n=== ACTUAL RESPONSE ===")
    print(response)
    print("=======================\n")

    refusal_markers = ["نہیں", "معلومات", "معاف", "not enough", "cannot answer",
                        "don't know", "ناهي", "نه ٿو", "ڄاڻ"]
    assert any(m in response for m in refusal_markers), \
        f"Model answered from its own knowledge instead of refusing: {response}"