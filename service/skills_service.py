from collections import Counter
import PyPDF2
import pandas as pd
from nltk.tokenize import word_tokenize
from itertools import combinations
import service.s3_service as s3_service


hard_skills = pd.read_csv('E:\\TrabaGo\\trabago-backend\\resume-analyzer\\data\\hard_skills.csv')[ 'Hard Skills' ].dropna().tolist()
soft_skills = pd.read_csv('E:\\TrabaGo\\trabago-backend\\resume-analyzer\\data\\soft_skills.csv')[ 'Soft Skills' ].dropna().tolist()
hard_skills_tokens = [set(word_tokenize(skill.lower())) for skill in hard_skills]
soft_skills_tokens = [set(word_tokenize(skill.lower())) for skill in soft_skills]


# Update the extract_skills function to use spaCy
# def extract_skills(job_description):
#     job_doc = nlp(job_description.lower())
#     job_tokens = set(token.text for token in job_doc if not token.is_stop and not token.is_punct)
#
#     hard_skills_in_job = [skill for skill, skill_tokens in zip(hard_skills, hard_skills_tokens) if skill_tokens.issubset(job_tokens)]
#     soft_skills_in_job = [skill for skill, skill_tokens in zip(soft_skills, soft_skills_tokens) if skill_tokens.issubset(job_tokens)]
#
#     return hard_skills_in_job, soft_skills_in_job

# Update the function to tokenize skills using spaCy
# hard_skills_tokens = [set(token.text for token in nlp(skill.lower()) if not token.is_stop and not token.is_punct) for skill in hard_skills]
# soft_skills_tokens = [set(token.text for token in nlp(skill.lower()) if not token.is_stop and not token.is_punct) for skill in soft_skills]

def extract_skills(job_description):
    job_tokens = set(word_tokenize(job_description.lower()))

    hard_skills_in_job = [skill for skill, skill_tokens in zip(hard_skills, hard_skills_tokens) if skill_tokens.issubset(job_tokens)]

    soft_skills_in_job = [skill for skill, skill_tokens in zip(soft_skills, soft_skills_tokens) if skill_tokens.issubset(job_tokens)]

    return hard_skills_in_job, soft_skills_in_job

def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1) + len(set2) - intersection
    return intersection / union

def extract_and_count_tokens(text):
    tokens = word_tokenize(text.lower())
    return Counter(tokens)

def deduplicate_skills(skills, threshold):
    skills_tokens = [set(word_tokenize(skill)) for skill in skills]
    duplicates = []
    for (skill1, tokens1), (skill2, tokens2) in combinations(zip(skills, skills_tokens), 2):
        if jaccard_similarity(tokens1, tokens2) > threshold:
            duplicates.append(skill2)
    return [skill for skill in skills if skill not in duplicates]

# def find_potential_hard_skills(job_tokens, hard_skills, threshold=0.2):
#     potential_hard_skills = []
#     for keyword in job_tokens:
#         if keyword in model.wv:
#             keyword_vector = model.wv[keyword]
#             for hard_skill in hard_skills:
#                 if hard_skill in model.wv:
#                     hard_skill_vector = model.wv[hard_skill]
#                     if cosine_similarity([keyword_vector], [hard_skill_vector]) > threshold:
#                         potential_hard_skills.append(keyword)
#                         break
#     return potential_hard_skills
#

def read_job_description(text_file_path):
    with open(text_file_path, 'r') as file:
        return file.read()


def read_resume(file_stream):
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        resume_text = ''
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
        return resume_text
    except Exception as e:
        return str(e)


def extract_skills_from_resume(resume_file_name, job_description):

    resume, _ = s3_service.get_file(resume_file_name)
    if resume:
        resume = read_resume(resume)

    hard_skills_in_job, soft_skills_in_job = extract_skills(job_description)
    hard_skills_in_job = deduplicate_skills(hard_skills_in_job, 0.9)
    soft_skills_in_job = deduplicate_skills(soft_skills_in_job, 0.2)
    hard_skills_in_resume, soft_skills_in_resume = extract_skills(resume)
    hard_skills_in_resume = deduplicate_skills(hard_skills_in_resume, 0.9)
    soft_skills_in_resume = deduplicate_skills(soft_skills_in_resume, 0.2)

    hard_skills_in_job = list(set(hard_skills_in_job))
    soft_skills_in_job = list(set(soft_skills_in_job))

    hard_skills_in_resume = list(set(hard_skills_in_resume))
    soft_skills_in_resume = list(set(soft_skills_in_resume))

    hard_skills_in_job_set = set(hard_skills_in_job)
    soft_skills_in_job_set = set(soft_skills_in_job)
    hard_skills_in_resume_set = set(hard_skills_in_resume)
    soft_skills_in_resume_set = set(soft_skills_in_resume)
    missing_hard_skills = list(hard_skills_in_job_set - hard_skills_in_resume_set)
    missing_soft_skills = list(soft_skills_in_job_set - soft_skills_in_resume_set)

    return {
        "missing_hard_skills": missing_hard_skills,
        "missing_soft_skills": missing_soft_skills
    }