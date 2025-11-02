import datasets
import pandas as pd
import transformers

import shap

# load the model and tokenizer
tokenizer = transformers.AutoTokenizer.from_pretrained("nateraw/bert-base-uncased-emotion", use_fast=True)
model = transformers.AutoModelForSequenceClassification.from_pretrained("nateraw/bert-base-uncased-emotion")

# build a pipeline object to do predictions
pred = transformers.pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    return_all_scores=True,
)

explainer = shap.Explainer(pred)
shap_values = explainer(["thank you to cr0129 who has been on duty today and responding to emergency 9️⃣9️⃣9️⃣ calls, alongside #secambulance #crowborough #hartfield #rotherfield #wadhurst #withyham #community #charity #volunteer"])

shap.plots.text(shap_values)
