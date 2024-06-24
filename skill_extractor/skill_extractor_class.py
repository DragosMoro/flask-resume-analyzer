# native packs
#
# installed packs
import difflib

import PyPDF2
from PyPDF2 import PdfReader

from service import s3_service
# my packs
from skill_extractor.text_class import Text
from skill_extractor.matcher_class import Matchers, SkillsGetter
from skill_extractor.utils import Utils


class SkillExtractor:
    def __init__(
            self,
            nlp,
            skills_db,
            phraseMatcher,
    ):
        # params
        self.nlp = nlp
        self.skills_db = skills_db
        self.phraseMatcher = phraseMatcher

        # load matchers: all
        self.matchers = Matchers(
            self.nlp,
            self.skills_db,
            self.phraseMatcher,
            # self.stop_words
        ).load_matchers()

        # init skill getters
        self.skill_getters = SkillsGetter(self.nlp)

        # init utils
        self.utils = Utils(self.nlp, self.skills_db)
        return

    def annotate(
            self,
            text: str,
            tresh: float = 1.0
    ) -> dict:

        # create text object
        text_obj = Text(text, self.nlp)
        # get matches
        skills_full, text_obj = self.skill_getters.get_full_match_skills(
            text_obj, self.matchers[ 'full_matcher' ])
        # tests

        skills_abv, text_obj = self.skill_getters.get_abv_match_skills(
            text_obj, self.matchers[ 'abv_matcher' ])
        skills_uni_full, text_obj = self.skill_getters.get_full_uni_match_skills(
            text_obj, self.matchers[ 'full_uni_matcher' ])

        skills_low_form, text_obj = self.skill_getters.get_low_match_skills(
            text_obj, self.matchers[ 'low_form_matcher' ])

        skills_on_token = self.skill_getters.get_token_match_skills(
            text_obj, self.matchers[ 'token_matcher' ])
        full_sk = skills_full + skills_abv
        # process pseudo submatchers output conflicts
        to_process = skills_on_token + skills_low_form + skills_uni_full
        process_n_gram = self.utils.process_n_gram(to_process, text_obj)
        return {
            'text': text_obj.transformed_text,
            'results': {
                'full_matches': full_sk,
                'ngram_scored': [ match for match in process_n_gram if match[ 'score' ] >= tresh ],

            }
        }

    def extract_skills(self, text: str, similarity_threshold=0.8) -> dict:
        """Extracts and returns unique hard and soft skills from the text.

        Parameters
        ----------
        text : str
            The target text.
        similarity_threshold : float
            Threshold for considering two skills as similar, by default 0.8.

        Returns
        -------
        dict
            Dictionary with 'hard_skills' and 'soft_skills' as keys.
        """
        results = self.annotate(text)
        hard_skills = [ ]
        soft_skills = [ ]

        for match_type in results[ 'results' ].keys():
            for match in results[ 'results' ][ match_type ]:
                skill_id = match[ 'skill_id' ]
                skill_name = self.skills_db[ skill_id ][ 'skill_name' ]
                skill_type = self.skills_db[ skill_id ][ 'skill_type' ]
                if skill_type == 'Hard Skill':
                    hard_skills.append(skill_name)
                elif skill_type == 'Soft Skill':
                    soft_skills.append(skill_name)

        hard_skills = self._remove_duplicates_and_similars(hard_skills, similarity_threshold)
        soft_skills = self._remove_duplicates_and_similars(soft_skills, similarity_threshold)

        return {
            'hard_skills': hard_skills,
            'soft_skills': soft_skills
        }

    def _remove_duplicates_and_similars(self, skills, similarity_threshold):
        """Remove duplicate and similar skills from a list.

        Parameters
        ----------
        skills : list
            List of skill names.
        similarity_threshold : float
            Threshold for considering two skills as similar.

        Returns
        -------
        list
            List of unique skill names.
        """
        unique_skills = list(set(skills))  # Remove exact duplicates
        filtered_skills = [ ]

        while unique_skills:
            current_skill = unique_skills.pop(0)
            filtered_skills.append(current_skill)
            if unique_skills:  # Check if there are remaining skills to compare
                similar_skills = difflib.get_close_matches(current_skill, unique_skills, n=len(unique_skills),
                                                           cutoff=similarity_threshold)
                for skill in similar_skills:
                    unique_skills.remove(skill)

        return filtered_skills

    def read_text_from_file(self, file_path: str) -> str:
        """Reads text from a file.

        Parameters
        ----------
        file_path : str
            The path to the text file.

        Returns
        -------
        str
            The text content of the file.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def read_resume(self, file_stream):
        try:
            pdf_reader = PyPDF2.PdfReader(file_stream)
            resume_text = ''
            for page in pdf_reader.pages:
                resume_text += page.extract_text()
            return resume_text
        except Exception as e:
            return str(e)

    def compare_skills(self, text_skills: dict, pdf_skills: dict):
        """Compares skills between two texts and prints those that are unique to each.

        Parameters
        ----------
        text_skills : dict
            Skills extracted from the text file.
        pdf_skills : dict
            Skills extracted from the PDF file.
        """
        unique_to_text_hard = set(text_skills[ 'hard_skills' ]) - set(pdf_skills[ 'hard_skills' ])
        # unique_to_pdf_hard = set(pdf_skills[ 'hard_skills' ]) - set(text_skills[ 'hard_skills' ])

        unique_to_text_soft = set(text_skills[ 'soft_skills' ]) - set(pdf_skills[ 'soft_skills' ])
        # unique_to_pdf_soft = set(pdf_skills[ 'soft_skills' ]) - set(text_skills[ 'soft_skills' ])


        # print("\nHard Skills unique to PDF file:")
        # for skill in unique_to_pdf_hard:
        #     print(f"- {skill}")

        return {"missing_hard_skills": list(unique_to_text_hard), "missing_soft_skills": list(unique_to_text_soft)}
        # print("\nSoft Skills unique to PDF file:")
        # for skill in unique_to_pdf_soft:
        #     print(f"- {skill}")

    def process_resume_and_job_description(self, resume, job_description):
        job_skills = self.extract_skills(job_description)
        resume_skills = self.extract_skills(resume)
        return self.compare_skills(job_skills, resume_skills)