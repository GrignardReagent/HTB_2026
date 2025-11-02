#!/usr/bin/env python3
"""
Run batched analysis over api_1.json and write results/api_1_analysis_batched.json

This script preserves the variable names and logic from your notebook's batched workflow.
It uses the `src` modules (`src.classify_sentiment`, `src.CHS_computation`).
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import json
import argparse
import os

try:
    from tqdm import tqdm
except Exception:
    def tqdm(x, **_kw):
        return x

import numpy as np

ROOT = Path('.')
DATA_PATH = ROOT / 'api_1.json'
OUT_DIR = ROOT / 'results'
OUT_DIR.mkdir(exist_ok=True)
OUT_FILE = OUT_DIR / 'api_1_analysis_batched_2.json'
OUT_FILE_PARTIAL = OUT_DIR / (OUT_FILE.stem + '.partial.json')

def ts_to_iso(ts):
    try:
        return datetime.fromtimestamp(int(ts)).isoformat() + 'Z'
    except Exception:
        return ''


def batch_classify_texts(texts, zshot, sentiment_clf, OECD_CATEGORIES, topk_mean=None, threshold=0.25, batch_size=32):
    """
    Return list of dicts equivalent to classify_with_sentiment(text).
    - texts: list[str]
    - zshot, sentiment_clf, OECD_CATEGORIES: objects imported from src.classify_sentiment
    - topk_mean: passed to label aggregation
    - batch_size: model batch size for pipeline
    """
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

    # 3) Build per-text outputs (same keys as classify_with_sentiment)
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
    """
    Returns (topic_scores_raw, details)
    - topic_scores_raw: dict[topic] -> mean signed score in [-1, 1]
    - details: list of per-post dicts
    """
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
    # import transformers-backed pipelines and helpers from src
    try:
        import src.classify_sentiment as cs
        from src.CHS_computation import OECD_TOPICS, normalize_topic_scores_0_10, compute_CHS
    except Exception as e:
        raise RuntimeError('Could not import pipeline modules. Ensure your PYTHONPATH and dependencies (transformers) are installed.') from e

    # load data
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # stream results to a partial output file so we can add iteratively
    # We write a JSON array incrementally into OUT_FILE_PARTIAL and atomically
    # rename it to OUT_FILE when finished.
    first = True
    preview = []  # keep a small preview of first results for summary
    fout = open(OUT_FILE_PARTIAL, 'w', encoding='utf-8')
    fout.write('[\n')

    for city in tqdm(data, desc='Cities (batch)'):
        city_name = city.get('city')
        posts = city.get('posts', []) or []
        texts_all = [p.get('text', '') for p in posts if p.get('text')]

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

            outs = batch_classify_texts(texts_all, cs.zshot, cs.sentiment_clf, cs.OECD_CATEGORIES, topk_mean=args.topk_mean, threshold=args.threshold, batch_size=args.batch_size)
            timeseries = []
            posts_sorted = sorted(posts, key=lambda p: p.get('posted_at_timestamp', 0))
            for p, out in zip(posts_sorted, outs):
                ts = p.get('posted_at_timestamp')
                text = p.get('text', '')
                pred_cat = out.get('predicted_category', 'none')
                pred_score = float(out.get('category_score', 0.0))
                sent_label = out.get('sentiment', {}).get('label', 'Neutral')
                s = (sent_label or '').strip().lower()
                if s.startswith('pos'): sign = +1
                elif s.startswith('neu'): sign = 0
                elif s.startswith('neg'): sign = -1
                else: sign = 0
                signed = sign * pred_score
                per_post_raw = {t: 0.0 for t in OECD_TOPICS}
                if pred_cat in OECD_TOPICS:
                    per_post_raw[pred_cat] = signed
                per_post_0_10 = normalize_topic_scores_0_10(per_post_raw)
                chs_post = compute_CHS(per_post_0_10)

                timeseries.append({
                    'posted_at_timestamp': ts,
                    'iso': ts_to_iso(ts) if ts is not None else '',
                    'topic_scores_0_10': per_post_0_10,
                    'chs': chs_post,
                    'text': text,
                })
        else:
            topic_0_10 = {t: 0.0 for t in OECD_TOPICS}
            chs = 0.0
            timeseries = []

        out_obj = {
            'city': city_name,
            'lat': city.get('lat'),
            'lng': city.get('lng'),
            'n_posts': len(posts),
            'overall_topic_scores_0_10': topic_0_10,
            'overall_chs': chs,
            'timeseries': timeseries,
        }

        # write comma-separated JSON objects into the array in the partial file
        if not first:
            fout.write(',\n')
        json.dump(out_obj, fout, ensure_ascii=False)
        fout.flush()
        try:
            os.fsync(fout.fileno())
        except Exception:
            # fsync may not be available on some platforms; ignore if it fails
            pass
        first = False

        if len(preview) < 5:
            preview.append(out_obj)

    # close out the JSON array and atomically move the partial file into place
    fout.write('\n]\n')
    fout.close()
    try:
        os.replace(OUT_FILE_PARTIAL, OUT_FILE)
    except Exception:
        # fallback to rename if replace is not available
        os.rename(OUT_FILE_PARTIAL, OUT_FILE)

    # brief summary (first few cities processed)
    for r in preview:
        print(r['city'], 'n_posts=', r['n_posts'], 'overall_chs=', round(r['overall_chs'], 1))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run batched CHS analysis over api_1.json')
    parser.add_argument('--batch-size', type=int, default=32, dest='batch_size', help='Model batch size')
    parser.add_argument('--topk-mean', type=int, default=3, dest='topk_mean', help='Top-k mean for category score aggregation')
    parser.add_argument('--threshold', type=float, default=0.25, dest='threshold', help='Category confidence threshold')
    args = parser.parse_args()
    main(args)
