import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn import metrics
import re
import nltk
import pickle
from nltk.corpus import stopwords
import string
from wordcloud import WordCloud

nltk.download('stopwords')
nltk.download('punkt')


resumeDataSet = pd.read_csv('../data/dataset.csv', encoding='utf-8')

resumeDataSet[ 'cleaned_resume' ] = ''
resumeDataSet.head()
resumeDataSet.info()


def cleanResume(resumeText):
    resumeText = re.sub('<.*?>', ' ', resumeText)  # remove HTML tags
    resumeText = re.sub('http\S+\s*', ' ', resumeText)  # remove URLs
    resumeText = re.sub('RT|cc', ' ', resumeText)  # remove RT and cc
    resumeText = re.sub('#\S+', '', resumeText)  # remove hashtags
    resumeText = re.sub('@\S+', '  ', resumeText)  # remove mentions
    resumeText = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ',
                        resumeText)  # remove punctuations
    resumeText = re.sub(r'[^\x00-\x7f]', r' ', resumeText)  # remove non-ASCII chars
    resumeText = re.sub('\s+', ' ', resumeText)  # remove extra whitespace
    return resumeText.strip()


resumeDataSet[ 'cleaned_resume' ] = resumeDataSet.Resume.apply(lambda x: cleanResume(x))

oneSetOfStopWords = set(stopwords.words('english') + [ '``', "''", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" ])
totalWords = [ ]
Sentences = resumeDataSet[ 'Resume' ].values
cleanedSentences = ""

for records in Sentences:
    cleanedText = cleanResume(records)
    cleanedSentences += cleanedText
    requiredWords = nltk.word_tokenize(cleanedText)
    for word in requiredWords:
        if word not in oneSetOfStopWords and word not in string.punctuation:
            totalWords.append(word)

wordfreqdist = nltk.FreqDist(totalWords)
mostcommon = wordfreqdist.most_common(50)
print(mostcommon)

wc = WordCloud().generate(cleanedSentences)
var_mod = [ 'Category' ]
le = LabelEncoder()
for i in var_mod:
    resumeDataSet[ i ] = le.fit_transform(resumeDataSet[ i ])

requiredText = resumeDataSet[ 'cleaned_resume' ].values
requiredTarget = resumeDataSet[ 'Category' ].values

word_vectorizer = TfidfVectorizer(sublinear_tf=True, stop_words='english')
word_vectorizer.fit(requiredText)
WordFeatures = word_vectorizer.transform(requiredText)

print("Feature completed .....")
X_train, X_test, y_train, y_test = train_test_split(WordFeatures, requiredTarget, random_state=42, test_size=0.2,
                                                    shuffle=True, stratify=requiredTarget)
print(X_train.shape)
print(X_test.shape)

# Logistic Regression with OneVsRestClassifier
clf = OneVsRestClassifier(LogisticRegression(class_weight='balanced'))
clf.fit(X_train, y_train)

prediction = clf.predict(X_test)

print("\nMetrics for Logistic Regression model:")
print("Accuracy: ", metrics.accuracy_score(y_test, prediction))
print("F1 Score: ", metrics.f1_score(y_test, prediction, average='macro'))
print("Precision: ", metrics.precision_score(y_test, prediction, average='macro'))
print("Recall: ", metrics.recall_score(y_test, prediction, average='macro'))

# Accuracy on training and test set
print(f"Accuracy of Logistic Regression on training set: {clf.score(X_train, y_train)}")
print(f"Accuracy of Logistic Regression on test set: {clf.score(X_test, y_test)}")

with open('../model_logistic_regression.pkl', 'wb') as model_file, \
        open('../vectorizer_logistic_regression.pkl', 'wb') as vectorizer_file, \
        open('../label_encoder.pkl', 'wb') as le_file:
    pickle.dump(clf, model_file)
    pickle.dump(word_vectorizer, vectorizer_file)
    pickle.dump(le, le_file)
