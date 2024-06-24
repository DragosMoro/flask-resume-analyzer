import pickle
import re

from service.classifier_service.constants import hard_skills


def clean_resume(resumeText):
    resumeText = re.sub('<.*?>', ' ', resumeText)  # remove HTML tags
    resumeText = re.sub('http\S+\s*', ' ', resumeText)  # remove URLs
    resumeText = re.sub('RT|cc', ' ', resumeText)  # remove RT and cc
    resumeText = re.sub('#\S+', '', resumeText)  # remove hashtags
    resumeText = re.sub('@\S+', '  ', resumeText)  # remove mentions
    resumeText = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ',
                        resumeText)  # remove punctuations
    resumeText = re.sub(r'[^\x00-\x7f]', r' ', resumeText)  # remove non-ASCII chars
    resumeText = re.sub('\s+', ' ', resumeText)  # remove extra whitespace
    return resumeText.strip()  # remove spaces at the beginning and at the end of the string


def classify_resume(resume_text):
    cleaned_resume = clean_resume(resume_text)

    # Load the trained model, vectorizer, and label encoder
    with open("./service/classifier_service/model_logistic_regression.pkl", 'rb') as model_file, open(
            "./service/classifier_service/vectorizer_logistic_regression.pkl", 'rb') as vectorizer_file, open(
            "./service/classifier_service/label_encoder.pkl", 'rb') as le_file:
        clf = pickle.load(model_file)
        word_vectorizer = pickle.load(vectorizer_file)
        le = pickle.load(le_file)

    # Preprocess the text
    text_for_classification = [cleaned_resume]

    # Transform the text using the pre-trained TfidfVectorizer
    text_features = word_vectorizer.transform(text_for_classification)

    # Make predictions with probabilities
    probabilities = clf.predict_proba(text_features)
    top_categories_indices = (-probabilities[0]).argsort()[:3]  # Indices of top 3 categories
    top_categories = le.inverse_transform(top_categories_indices)  # Convert indices back to category labels
    top_probabilities = probabilities[
        0, top_categories_indices]  # Probabilities of top 3 categories  top_matches_with_probs = sorted(zip(top_categories, top_probabilities), key=lambda x: x[1], reverse=True)

    top_matches_with_probs = sorted(zip(top_categories, top_probabilities), key=lambda x: x[1], reverse=True)

    top_matches = {}

    # Populate the dictionary with categories as keys and corresponding skills as values
    for category, prob in top_matches_with_probs:
        combined_list = [prob] + hard_skills.get(category, [])
        top_matches[category] = combined_list
    return top_matches
