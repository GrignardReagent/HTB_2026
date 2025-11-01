import asyncio
import json
from flask import Flask, jsonify
import websockets
import pandas as pd
import nltk
import datetime
import math
import re
from src.classify_sentiment import classify_with_sentiment
from src.CHS_computation import compute_topic_signed_scores, normalize_topic_scores_0_10, compute_CHS

app = Flask(__name__)

counts = {}
n_lines_read = 0
lock = False

@app.route("/")
def hello_world():
  read_from_file()
  counts = calculate_city_scores()
  counts_ = [{'city': city, 'score': city_stuff['score'], 'posts': city_stuff['posts'], 'lat': cities_df[(cities_df['city'] == city) & (cities_df['iso2'] == 'GB')]['lat'].values[0], 'lng': cities_df[(cities_df['city'] == city) & (cities_df['iso2'] == 'GB')]['lng'].values[0]} for city, city_stuff in counts.items()]
  counts_.sort(key=lambda x: x['score'], reverse=True)
  return jsonify(counts_)

def calculate_city_scores():
  current_time = int(datetime.datetime.now().timestamp())
  for city, city_stuff in counts.items():
    score = 0
    posts_keep = []
    for post in city_stuff['posts']:
      seconds_passed = max(0, current_time - post['posted_at_timestamp'])
      if seconds_passed < 3600:
        posts_keep.append(post)
        score += math.exp(-0.001919 * seconds_passed)
    counts[city]['score'] = score
    counts[city]['posts'] = posts_keep

  return counts

nltk.download('stopwords')
stopwords = nltk.corpus.stopwords.words('english')
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

cities_df = pd.read_csv('simplemaps_worldcities_basicv1.901/worldcities.csv')
# remove stopwords cities from dataframe
cities_df = cities_df[~cities_df['city'].str.lower().isin(stopwords)]
# remove cities name less than 4 characters
cities_df = cities_df[cities_df['city'].str.len() >= 4]
# sort by length descending
cities_df = cities_df.sort_values(by='city', key=lambda x: x.str.len(), ascending=False)

uri = "wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post"

def read_from_file():
  global lock
  if lock:
    return
  lock = True
  with open('city_mentions.jsonl', 'r', encoding='utf-8') as infile:
    global n_lines_read
    for _ in range(n_lines_read):
      next(infile)
    for message in infile:
      n_lines_read += 1
      data = json.loads(message)
      if 'commit' in data and 'record' in data['commit'] and 'text' in data['commit']['record']:
        text = data['commit']['record']['text'].lower()
        for city in cities_df['city']:
          if city.lower() not in text:
            continue
          match = re.search(r'\b' + re.escape(city.lower()) + r'\b', text)
          if match:
            if city in cities_df['city'][cities_df['iso2'] == 'GB'].values:
              pass
            else:
              continue
            if 'createdAt' in data['commit']['record']:
              posted_at = data['commit']['record']['createdAt']
            else:
              break
            posted_at_timestamp: int = int(datetime.datetime.fromisoformat(posted_at.replace('Z', '+00:00')).timestamp())
            global counts
            post_item = {'posted_at_timestamp': posted_at_timestamp, 'text': text}
            counts[city]['posts'].append(post_item) if city in counts else counts.update({city: {'posts': [post_item]}})
            break
  lock = False

if __name__ == "__main__":
    app.run(debug=True, port=5001)
