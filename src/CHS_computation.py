from collections import defaultdict
import math

# --- weights from earlier (edit if you like) ---
CHS_WEIGHTS = {
	"access_to_services": 0.09,
	"civic_engagement":   0.08,
	"education":          0.09,
	"jobs":               0.10,
	"community":          0.09,
	"environment":        0.09,
	"income":             0.10,
	"health":             0.12,
	"safety":             0.10,
	"housing":            0.08,
	"life_satisfaction":  0.06,
}
assert abs(sum(CHS_WEIGHTS.values()) - 1.0) < 1e-9

OECD_TOPICS = set(CHS_WEIGHTS.keys())

def _sentiment_to_sign(sent_label: str) -> int:
	"""Return +1 for Positive, 0 for Neutral, -1 for Negative."""
	s = (sent_label or "").strip().lower()
	if s.startswith("pos"):   return +1
	if s.startswith("neu"):   return 0
	if s.startswith("neg"):   return -1
	# default to neutral if unknown
	return 0

def _sentiment_to_signed_strength(sent_label: str, sent_score: float) -> float:
    """
    Convert sentiment output -> signed strength in [-1, 1].
    - Positive  -> +sent_score
    - Neutral   -> 0
    - Negative  -> -sent_score

    Assumes `sent_score` is the model's confidence for `sent_label` in [0,1].
    """
    s = (sent_label or "").strip().lower()
    p = max(0.0, min(1.0, float(sent_score)))  # clamp to [0,1]

    if s.startswith("pos"):
        return +p
    if s.startswith("neu"):
        return 0.0
    if s.startswith("neg"):
        return -p
    return 0.0  # unknown -> neutral

def compute_topic_signed_scores(texts, classify_fn, topk_mean=3, threshold=0.25):
    """
    Returns:
      topic_scores_raw: dict[topic] -> mean signed score in [-1, 1]
      details: per-post rows for debugging
    """
    per_topic_values = defaultdict(list)
    details = []

    for t in texts:
        out = classify_fn(t, topk_mean=topk_mean, threshold=threshold)
        pred_cat   = out.get("predicted_category", "none")
        pred_score = float(out.get("category_score", 0.0))

        sent = out.get("sentiment", {})
        sent_label = sent.get("label", "Neutral")
        sent_conf = float(sent.get("score", 0.0))
        sign_strength = _sentiment_to_signed_strength(sent_label, sent_conf)  # [-1,1]
        sign = sign_strength * float(pred_score)  # final signed category contribution

        # Only include valid OECD topics and confident predictions
        if pred_cat in OECD_TOPICS and pred_score > 0:
            signed = sign * pred_score  # in [-1, 1]
            per_topic_values[pred_cat].append(signed)
        else:
            # ignore 'none' or below-threshold/zero scores
            pass

        details.append({
            "text": t,
            "predicted_category": pred_cat,
            "category_score": pred_score,
            "sentiment": sent_label,
            "signed_score": sign * pred_score if pred_cat in OECD_TOPICS else 0.0,
        })

    # mean signed score per topic (fallback to 0 when no posts)
    topic_scores_raw = {
        topic: (sum(vals) / len(vals)) if len(vals) > 0 else 0.0
        for topic, vals in per_topic_values.items()
    }
    # ensure all topics present
    for topic in OECD_TOPICS:
        topic_scores_raw.setdefault(topic, 0.0)

    return topic_scores_raw, details

def normalize_topic_scores_0_10(topic_scores_raw):
    """
    Map mean signed scores from [-1, 1] -> [0, 10], rounded to 1 decimal place.
      -1 -> 0.0, 0 -> 5.0, +1 -> 10.0
    """
    # linear mapping to 0-10, rounded to 1 decimal place per topic
    topic_scores_0_10 = {
        k: round(((v + 1.0) / 2.0) * 10.0, 1)
        for k, v in topic_scores_raw.items()
    }
    return topic_scores_0_10

def compute_CHS(topic_scores_0_to_10: dict[str, float]) -> float:
	"""Weighted sum of topic scores (0–10) -> CHS (0–100)."""
	return sum(CHS_WEIGHTS[k] * topic_scores_0_to_10.get(k, 0.0) for k in CHS_WEIGHTS)


__all__ = [
	"CHS_WEIGHTS",
	"OECD_TOPICS",
	"_sentiment_to_sign",
	"compute_topic_signed_scores",
	"normalize_topic_scores_0_10",
	"compute_CHS",
]

