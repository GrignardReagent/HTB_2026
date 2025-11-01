from transformers import pipeline
import numpy as np

# ==== OECD WELL-BEING TOPICS (exact names) ===================================

access_to_services_keywords = [
	"public services", "access", "availability", "waiting time", "appointment",
	"queue", "digital services", "online portal", "transport access", "bus route",
	"train frequency", "healthcare access", "school places", "childcare places",
	"broadband", "mobile signal", "coverage", "service outage", "customer service"
]

civic_engagement_keywords = [
	"vote", "voter turnout", "election", "referendum", "petition",
	"public consultation", "civic participation", "community meeting",
	"local council", "town hall", "governance", "transparency", "corruption",
	"public policy", "accountability", "trust in government", "civic duty"
]

education_keywords = [
	"education", "school", "teacher", "university", "college",
	"exam results", "grades", "literacy", "numeracy", "STEM", "curriculum",
	"training", "course", "apprenticeship", "skills", "lifelong learning",
	"tuition fees", "scholarship", "school places"
]

jobs_keywords = [
	"job", "employment", "unemployment", "hiring", "recruiting",
	"job market", "vacancy", "layoff", "redundancy", "promotion",
	"career", "job security", "workforce", "labour demand", "gig economy",
	"payroll", "underemployment"
]

community_keywords = [
	"community", "neighbourhood", "neighbors", "social support",
	"volunteering", "mutual aid", "local club", "association", "festival",
	"street party", "togetherness", "belonging", "isolation", "loneliness",
	"community centre", "food bank"
]

environment_keywords = [
	"air quality", "pollution", "smog", "PM2.5", "green space", "park",
	"recycling", "waste", "sustainability", "climate", "heatwave", "storm",
	"flood", "drought", "biodiversity", "water quality", "noise pollution",
	"emissions", "low-emission zone", "tree planting"
]

income_keywords = [
	"income", "salary", "wage", "earnings", "pay rise", "bonus",
	"purchasing power", "poverty", "low income", "cost of living",
	"affordability", "inequality", "wealth", "savings", "net worth",
	"investment", "financial security", "disposable income"
]

health_keywords = [
	"health", "healthcare", "hospital", "clinic", "GP", "doctor", "nurse",
	"waiting list", "appointment", "A&E", "emergency department",
	"mental health", "wellbeing", "life expectancy", "vaccination",
	"public health", "disease", "screening", "preventive care", "fitness"
]

safety_keywords = [
	"safety", "crime", "burglary", "assault", "robbery", "knife crime",
	"violent crime", "police", "emergency", "911", "999",
	"traffic accident", "dangerous", "safe streets", "CCTV", "fear of crime"
]

housing_keywords = [
	"housing", "rent", "mortgage", "home ownership", "housing cost",
	"affordable housing", "social housing", "council house", "flat search",
	"property price", "eviction", "housing shortage", "tenants", "landlord",
	"apartment market", "overcrowding"
]

life_satisfaction_keywords = [
	"life satisfaction", "satisfied with life", "happiness", "happy",
	"wellbeing", "quality of life", "content", "fulfilled", "optimistic",
	"hopeful", "thriving", "life is good", "overall satisfaction"
]

# Optional: mapping for your loop-based classifiers
OECD_CATEGORIES = {
	"access_to_services": access_to_services_keywords,
	"civic_engagement": civic_engagement_keywords,
	"education": education_keywords,
	"jobs": jobs_keywords,
	"community": community_keywords,
	"environment": environment_keywords,
	"income": income_keywords,
	"health": health_keywords,
	"safety": safety_keywords,
	"housing": housing_keywords,
	"life_satisfaction": life_satisfaction_keywords,
}


# 2) Models -------------------------------------------------------------------
# Zero-shot for relevance 
zshot = pipeline("zero-shot-classification", model="roberta-large-mnli", device_map="auto")

# Sentiment (optional, for CHS sub-scores)
sentiment_clf = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device_map="auto")


# 3) Category scoring helpers -------------------------------------------------
def score_category(text: str, labels, topk_mean: int | None = None):
	"""
	topk_mean: number of keywords to average for final category score
	Returns: dict(score=float, best_label=str, label_scores=list[(label,score)])
	Uses multi_label=True so scores are independent sigmoids per label.
	"""
	out = zshot(text, candidate_labels=labels, multi_label=True)
	label_scores = list(zip(out["labels"], out["scores"]))
	# sort high -> low
	label_scores.sort(key=lambda x: x[1], reverse=True)

	if topk_mean and topk_mean > 1:
		k = min(topk_mean, len(label_scores))
		agg = float(np.mean([s for _, s in label_scores[:k]]))
	else:
		agg = float(label_scores[0][1])  # max

	return {
		"score": agg,
		"best_label": label_scores[0][0],
		"label_scores": label_scores
	}

def classify_citypulse_topic(text: str, topk_mean: int | None = None, threshold: float = 0.25):
	"""
	Scores all categories and returns the best category if it clears threshold.
	"""
	cat_results = {}
	for cat, labels in OECD_CATEGORIES.items():
		r = score_category(text, labels, topk_mean=topk_mean)
		cat_results[cat] = r

	# pick best category
	best_cat = max(cat_results.items(), key=lambda kv: kv[1]["score"])
	cat_name, cat_info = best_cat

	is_confident = cat_info["score"] >= threshold
	return {
		"predicted_category": cat_name if is_confident else "none",
		"category_score": cat_info["score"],
		"top_keyword": cat_info["best_label"],
		"all_category_scores": {k: v["score"] for k, v in cat_results.items()},
		"explanation_top3_keywords": cat_info["label_scores"][:3]
	}

def classify_with_sentiment(text: str, **kwargs):
	topic = classify_citypulse_topic(text, **kwargs)
	sent = sentiment_clf(text)[0]  # {'label': 'Positive'|'Negative'|'Neutral', 'score': p}
	topic["sentiment"] = sent
	return topic


__all__ = [
	"OECD_CATEGORIES",
	"score_category",
	"classify_citypulse_topic",
	"classify_with_sentiment",
	"zshot",
	"sentiment_clf",
]
