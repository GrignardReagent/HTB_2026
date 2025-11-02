#!/usr/bin/env python3
"""
Run CHS analysis using sampled posts from the two-million Bluesky dataset.

This script:
- loads `api_1.json` to extract `city_names` (preserve order, drop duplicates),
- calls `get_city_messages(10000, cities=city_names)` to get up to 10k posts that mention any city,
- groups the sampled posts per city (simple regex word-boundary match),
- computes overall topic scores and CHS per city using the same helpers as `run_batch_analysis.py`,
- writes results to `results/api_1_analysis_2mn.json`.

Notes:
- A post may match multiple city names and will be included for each matched city.
- The sampled posts do not include timestamps, so timeseries is left empty.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import json
import argparse
import re

try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **_kw):
        return x

import numpy as np

# import local helpers
from src.get_city_messages import get_city_messages

ROOT = Path('.')
DATA_PATH = ROOT / 'api_1.json'
OUT_DIR = ROOT / 'results'
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / 'api_1_analysis_2mn.json'


def ts_to_iso(ts):
    try:
        return datetime.fromtimestamp(int(ts)).isoformat() + 'Z'
    except Exception:
        return ''


# Copied/adapted helpers from run_batch_analysis.py
def batch_classify_texts(texts, zshot, sentiment_clf, OECD_CATEGORIES, topk_mean=None, threshold=0.25, batch_size=32):
    T = len(texts)
    cat_scores = {cat: [0.0] * T for cat in OECD_CATEGORIES.keys()}
    cat_best_label = {cat: [None] * T for cat in OECD_CATEGORIES.keys()}
    cat_label_scores = {cat: [None] * T for cat in OECD_CATEGORIES.keys()}

    # 1) For each category, run zshot on texts in chunks
    for cat, labels in OECD_CATEGORIES.items():
        for start in range(0, T, batch_size):
            batch_texts = texts[start:start+batch_size]
            results = zshot(batch_texts, candidate_labels=labels, multi_label=True, batch_size=batch_size)
            for idx, out in enumerate(results, start=start):
                label_scores = list(zip(out["labels"], out["scores"]))
                label_scores.sort(key=lambda x: x[1], reverse=True)
                if topk_mean and topk_mean > 1:
                    k = min(topk_mean, len(label_scores))
                    agg = float(np.mean([s for _, s in label_scores[:k]]))
                else:
                    agg = float(label_scores[0][1])
                cat_scores[cat][idx] = agg
                cat_best_label[cat][idx] = label_scores[0][0]
                cat_label_scores[cat][idx] = label_scores

    # 2) Sentiment for all texts in batches
    sent_results = []
    for start in range(0, T, batch_size):
        batch_texts = texts[start:start+batch_size]
        sent_batch = sentiment_clf(batch_texts, batch_size=batch_size)
        sent_results.extend(sent_batch)

    # 3) Build per-text outputs
    outputs = []
    for i in range(T):
        per_cat = {cat: cat_scores[cat][i] for cat in OECD_CATEGORIES.keys()}
        best_cat, best_score = max(per_cat.items(), key=lambda kv: kv[1])
        is_confident = best_score >= threshold
        out = {
            "predicted_category": best_cat if is_confident else "none",
            "category_score": best_score,
            "top_keyword": cat_best_label[best_cat][i],
            "all_category_scores": per_cat,
            "explanation_top3_keywords": cat_label_scores[best_cat][i][:3] if cat_label_scores[best_cat][i] is not None else [],
            "sentiment": sent_results[i],
        }
        outputs.append(out)
    return outputs


def batch_compute_topic_signed_scores(texts, OECD_TOPICS, batch_classify_fn, topk_mean=3, threshold=0.25, batch_size=32):
    outs = batch_classify_fn(texts, topk_mean=topk_mean, threshold=threshold, batch_size=batch_size)
    per_topic_values = defaultdict(list)
    details = []

    def _sentiment_to_sign(sent_label: str) -> int:
        s = (sent_label or "").strip().lower()
        if s.startswith("pos"): return +1
        if s.startswith("neu"): return 0
        if s.startswith("neg"): return -1
        return 0

    for text, out in zip(texts, outs):
        pred_cat = out.get("predicted_category", "none")
        pred_score = float(out.get("category_score", 0.0))
        sent_label = out.get("sentiment", {}).get("label", "Neutral")
        sign = _sentiment_to_sign(sent_label)
        if pred_cat in OECD_TOPICS and pred_score > 0:
            signed = sign * pred_score
            per_topic_values[pred_cat].append(signed)
        details.append({
            "text": text,
            "predicted_category": pred_cat,
            "category_score": pred_score,
            "sentiment": sent_label,
            "signed_score": sign * pred_score if pred_cat in OECD_TOPICS else 0.0,
        })
    topic_scores_raw = {topic: (sum(vals)/len(vals)) if vals else 0.0 for topic, vals in per_topic_values.items()}
    for topic in OECD_TOPICS:
        topic_scores_raw.setdefault(topic, 0.0)
    return topic_scores_raw, details


def main(args):
    try:
        import src.classify_sentiment as cs
        from src.CHS_computation import OECD_TOPICS, normalize_topic_scores_0_10, compute_CHS
    except Exception as e:
        raise RuntimeError('Could not import pipeline modules. Ensure your PYTHONPATH and dependencies are installed.') from e

    # load api_1.json and extract city names
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    city_names = [entry.get('city', '') for entry in data if 'city' in entry]
    seen = set()
    city_names = [c for c in city_names if c and (c not in seen and not seen.add(c))]

    print(f"Extracted {len(city_names)} city names")

    # sample posts that mention any of the cities
    print('Sampling posts from the two-million bluesky dataset (this may take some time)')
    sampled_posts = get_city_messages(args.n_samples, cities=city_names)
    print(f"Retrieved {len(sampled_posts)} sampled posts")

    results_batch = []

    # For each city, filter sampled posts that mention that city and run analysis
    for city in tqdm(city_names, desc='Cities (sampled)'):
        pat = re.compile(r"\b" + re.escape(city) + r"\b", flags=re.IGNORECASE)
        texts_all = [p.get('text', '') for p in sampled_posts if pat.search(p.get('text', ''))]

        if texts_all:
            raw_overall, details_overall = batch_compute_topic_signed_scores(
                texts_all,
                OECD_TOPICS,
                lambda texts, topk_mean=args.topk_mean, threshold=args.threshold, batch_size=args.batch_size: batch_classify_texts(
                    texts, cs.zshot, cs.sentiment_clf, cs.OECD_CATEGORIES, topk_mean=topk_mean, threshold=threshold, batch_size=batch_size
                ),
                topk_mean=args.topk_mean,
                threshold=args.threshold,
                batch_size=args.batch_size,
            )
            topic_0_10 = normalize_topic_scores_0_10(raw_overall)
            chs = compute_CHS(topic_0_10)
        else:
            topic_0_10 = {t: 0.0 for t in OECD_TOPICS}
            chs = 0.0

        results_batch.append({
            'city': city,
            'n_sampled_posts': len(texts_all),
            'overall_topic_scores_0_10': topic_0_10,
            'overall_chs': chs,
        })

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results_batch, f, ensure_ascii=False, indent=2)

    # brief summary
    for r in results_batch[:20]:
        print(r['city'], 'n_sampled_posts=', r['n_sampled_posts'], 'overall_chs=', round(r['overall_chs'], 2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run CHS over sampled posts from the two-million Bluesky dataset')
    parser.add_argument('--n-samples', type=int, default=10000, dest='n_samples', help='Number of sampled posts to retrieve from the two-million dataset')
    parser.add_argument('--batch-size', type=int, default=32, dest='batch_size', help='Model batch size')
    parser.add_argument('--topk-mean', type=int, default=3, dest='topk_mean', help='Top-k mean for category score aggregation')
    parser.add_argument('--threshold', type=float, default=0.25, dest='threshold', help='Category confidence threshold')
    args = parser.parse_args()
    main(args)
