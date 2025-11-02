negative_emotions = ['sadness', 'anger', 'fear']
positive_emotions = ['joy', 'love']

import json
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
import shap

positive_words = set()
negative_words = set()

with open('emotions.jsonl', 'r') as f:
    for line in f:
        city = json.loads(line)
        for post in city['posts']:
            emotions = post['emotions']
            neg_score = sum([emotions[emo] for emo in negative_emotions])
            pos_score = sum([emotions[emo] for emo in positive_emotions])
            if neg_score < 0.9 and pos_score < 0.9:
                continue
            if neg_score > pos_score:
                negative_words.update([word for word in nltk.word_tokenize(post['text'].lower()) if word.isalpha() and word not in stop_words])
            else:
                positive_words.update([word for word in nltk.word_tokenize(post['text'].lower()) if word.isalpha() and word not in stop_words])

neutral_words = positive_words & negative_words
positive_words = positive_words - neutral_words
negative_words = negative_words - neutral_words
print("Positive words:", ', '.join(positive_words))
print("Negative words:", ', '.join(negative_words))
