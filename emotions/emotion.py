from transformers import pipeline
import json
import tqdm

classifier = pipeline("text-classification",model='bhadresh-savani/distilbert-base-uncased-emotion', return_all_scores=True)

data = json.load(open('api_1.json', 'r'))
for city in data:
    for post in tqdm.tqdm(city['posts']):
        text = post['text']
        results = classifier(text)
        emotions = {item['label']: item['score'] for item in results[0]}
        post['emotions'] = emotions
    with open('emotions.jsonl', 'a', encoding='utf-8') as outfile:
        outfile.write(json.dumps(city) + '\n')
