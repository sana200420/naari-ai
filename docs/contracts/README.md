# Interface contracts

The JSON shapes that let four people build in parallel without waiting on
each other. Agree the shape here BEFORE implementing it.

- `retrieval.json` — what `search(query)` returns (Sana → Sabiha)
- `ask.json` — the `/ask` request and response (Sabiha → Tooba)

Changing a contract means a pull request that both sides approve.
