# imports
import spacy
from spacy.matcher import PhraseMatcher

# load default skills data base
from skill_extractor.general_params import SKILL_DB
# import skill extractor
from skill_extractor.skill_extractor_class import SkillExtractor

# init params of skill extractor
nlp = spacy.load("en_core_web_lg")
# init skill extractor
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

# extract skills from job_description
job_description = """
John Doe is a results-driven Java Developer with over 5 years of experience in designing, developing, and maintaining high-performance Java applications. Currently employed at XYZ Tech Solutions in New York, NY, since June 2019, he has developed and maintained Java-based applications ensuring high performance, scalability, and reliability, collaborated with cross-functional teams to design and implement new features, and utilized Spring Framework and Hibernate for application development. He has also conducted code reviews, provided mentorship to junior developers, implemented RESTful APIs, and integrated third-party services while participating in Agile/Scrum development processes. Notably, he reduced application response time by 30% through performance tuning and led the migration of legacy systems to a modern Java-based microservices architecture. Previously, at ABC Corp in San Francisco, CA (July 2016 – May 2019), he designed and implemented Java applications for the finance sector, focusing on robustness and security, developed custom modules using Java SE/EE, Spring Boot, and Hibernate, worked closely with QA teams to identify and resolve bugs, and created and maintained documentation for all code and applications. He also developed unit tests using JUnit and Mockito, delivering multiple projects ahead of schedule and enhancing data processing speed by 25% through efficient algorithm implementation. John holds a Bachelor of Science in Computer Science from the University of California, Berkeley, graduated in May 2016. His technical skills include proficiency in Java, JavaScript, SQL, Spring, Spring Boot, Hibernate, Struts, Eclipse, IntelliJ IDEA, Maven, Jenkins, Docker, MySQL, PostgreSQL, MongoDB, RESTful APIs, Microservices, Agile/Scrum, and Git. He is an Oracle Certified Professional, Java SE 8 Programmer, and a Certified Scrum Developer (CSD). His projects include developing an inventory management system using Java, Spring Boot, and Hibernate, and leading a team in creating an online banking application with microservices architecture. John has attended the JavaOne Conference in 2020 and completed an Advanced Java Programming course on Coursera. References are available upon request.
"""

# annotations = skill_extractor.annotate(job_description)

text = skill_extractor.read_text_from_file('text.txt')
pdf_text = skill_extractor.read_text_from_pdf('My_Resume.pdf')

text_skills = skill_extractor.extract_skills(text)
pdf_skills = skill_extractor.extract_skills(pdf_text)
skill_extractor.compare_skills(text_skills, pdf_skills)