import json
import random
import requests
from dotenv import load_dotenv
import os

common_skills = ["Python", "Java", "SQL", "React"]
load_dotenv()
def fetch_course_details(skill, position=0):
    API_URL = os.getenv("API_URL")
    AUTHORIZATION = os.getenv("AUTHORIZATION")
    url = f"{API_URL}?search={skill}&ordering=relevance"
    headers = {
        "Authorization": AUTHORIZATION,
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data["results"]:
            course = data["results"][position]
            instructor = course.get("visible_instructors")[0] if course.get("visible_instructors") else {"title": "Unknown"}
            return {
                "title": course.get("title"),
                "imageUrl": course.get("image_480x270"),
                "courseUrl": "https://www.udemy.com" + course.get("url"),
                "instructorName": instructor.get("title")
            }
    else:
        return {"error": "Failed to fetch course details", "statusCode": response.status_code}

def get_course_details(missing_skills):
    if not missing_skills:
        missing_skills = common_skills

    prepared_skills = random.sample(missing_skills, min(len(missing_skills), 4))
    extra_skills = []
    if len(prepared_skills) ==1:
        for i in range(1,4):
            extra_skills.append(fetch_course_details(missing_skills[0], i))

    if len(prepared_skills) == 2:
        for i in range(1,3):
            extra_skills.append(fetch_course_details(missing_skills[0], 1))
            extra_skills.append(fetch_course_details(missing_skills[1], 1))

    if len(prepared_skills) == 3:
        for i in range(1,2):
            extra_skills.append(fetch_course_details(missing_skills[0], 1))

    courses_list = [fetch_course_details(skill) for skill in prepared_skills]
    courses_list += extra_skills
    courses_list = [course for course in courses_list if not course.get("error")]
    return  courses_list


