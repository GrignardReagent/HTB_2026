import re
from itertools import islice
from datasets import load_dataset

def get_city_messages(n, cities):

    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(c) for c in sorted(cities, key=len, reverse=True)) + r")\b",
        flags=re.IGNORECASE,
    )

    # load the default split as a streaming iterable so `ds` is an iterable of examples (not a DatasetDict)
    ds = load_dataset("alpindale/two-million-bluesky-posts", split="train", streaming=True)

    def _city_rows(iterable):
        for r in iterable:
            txt = r.get("text") or ""
            if pattern.search(txt):
                yield {"text": txt}
    return list(islice(_city_rows(ds), n))
