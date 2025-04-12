"""
Job Matcher Module
Uses sentence transformers to compare resumes with job listings and rank matches
"""

import numpy as np
from sentence_transformers import SentenceTransformer


class JobMatcher:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the job matcher with a sentence transformer model.
        Args:
            model_name: Name of the sentence transformer model to use
        """
        # Initialize the model (will download if not cached)
        print(f"Loading sentence transformer model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            print(f"Error loading model: {e}")
            raise
        
        # Match reason templates
        self.reason_templates = {
            "skills": "Skills match: {}",
            "experience": "Experience relevance: {}",
            "education": "Education match: {}",
            "location": "Location match: {}",
            "title": "Job title match: {}",
            "overall": "Overall match score: {:.2f}/1.00"
        }
        
        # Weights for different components
        self.weights = {
            "skills": 0.35,
            "experience": 0.30,
            "education": 0.15,
            "location": 0.10,
            "title": 0.10
        }

    def _preprocess_resume(self, resume_data):
        """
        Extract and format relevant data from the resume for matching.
        
        Args:
            resume_data: Dictionary containing parsed resume data
            
        Returns:
            Dictionary with processed resume data for matching
        """
        processed_resume = {}
        
        # Extract skills as a joined string
        processed_resume['skills_text'] = ', '.join(resume_data.get('skills', []))
        
        # Format experience as a single text block
        experience_list = resume_data.get('experience', [])
        processed_resume['experience_text'] = ' '.join(experience_list)
        
        # Format education as a joined string
        processed_resume['education_text'] = ' '.join(resume_data.get('degrees', []))
        
        # Get location preference
        processed_resume['location'] = resume_data.get('location_preference', '')
        
        # Create a comprehensive profile combining all information
        full_profile = []
        if resume_data.get('name'):
            full_profile.append(f"Name: {resume_data['name']}")
        if processed_resume['skills_text']:
            full_profile.append(f"Skills: {processed_resume['skills_text']}")
        if processed_resume['experience_text']:
            full_profile.append(f"Experience: {processed_resume['experience_text']}")
        if processed_resume['education_text']:
            full_profile.append(f"Education: {processed_resume['education_text']}")
        if processed_resume['location']:
            full_profile.append(f"Location: {processed_resume['location']}")
        
        processed_resume['full_profile'] = ' '.join(full_profile)
        
        return processed_resume

    def _preprocess_job(self, job):
        """
        Extract and format relevant data from job listing for matching.
        
        Args:
            job: Dictionary containing job listing data
            
        Returns:
            Dictionary with processed job data for matching
        """
        processed_job = {}
        
        # Get job title
        processed_job['title'] = job.get('title', '')
        
        # Get job location
        processed_job['location'] = job.get('location', '')
        
        # Get job description - prefer full description if available
        description = job.get('full_description', '') or job.get('snippet', '')
        processed_job['description'] = description
        
        # Get company name
        processed_job['company'] = job.get('company', '')
        
        # Create consolidated text representation of the job
        full_job_text = [
            f"Title: {processed_job['title']}",
            f"Company: {processed_job['company']}",
            f"Location: {processed_job['location']}",
            f"Description: {processed_job['description']}"
        ]
        
        processed_job['full_text'] = ' '.join(full_job_text)
        
        return processed_job

    def calculate_similarity(self, text1, text2):
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1, text2: Strings to compare
            
        Returns:
            Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0
            
        # Encode both texts
        embedding1 = self.model.encode(text1, convert_to_numpy=True)
        embedding2 = self.model.encode(text2, convert_to_numpy=True)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        
        return float(similarity)

    def match_job_to_resume(self, resume_data, job):
        """
        Calculate how well a job matches a resume.
        
        Args:
            resume_data: Dictionary containing parsed resume data
            job: Dictionary containing job data
            
        Returns:
            Dictionary with match score and reasons
        """
        # Preprocess inputs
        processed_resume = self._preprocess_resume(resume_data)
        processed_job = self._preprocess_job(job)
        
        scores = {}
        reasons = {}
        
        # Match skills
        skills_similarity = self.calculate_similarity(
            processed_resume['skills_text'],
            processed_job['description']
        )
        scores['skills'] = skills_similarity
        
        reason_quality = "excellent" if skills_similarity > 0.8 else \
                        "strong" if skills_similarity > 0.6 else \
                        "good" if skills_similarity > 0.4 else \
                        "moderate" if skills_similarity > 0.2 else "limited"
                        
        reasons['skills'] = self.reason_templates['skills'].format(reason_quality)
        
        # Match experience
        exp_similarity = self.calculate_similarity(
            processed_resume['experience_text'],
            processed_job['description']
        )
        scores['experience'] = exp_similarity
        
        reason_quality = "excellent" if exp_similarity > 0.8 else \
                        "strong" if exp_similarity > 0.6 else \
                        "good" if exp_similarity > 0.4 else \
                        "moderate" if exp_similarity > 0.2 else "limited"
                        
        reasons['experience'] = self.reason_templates['experience'].format(reason_quality)
        
        # Match education
        edu_similarity = self.calculate_similarity(
            processed_resume['education_text'],
            processed_job['description']
        )
        scores['education'] = edu_similarity
        
        reason_quality = "excellent" if edu_similarity > 0.8 else \
                        "strong" if edu_similarity > 0.6 else \
                        "good" if edu_similarity > 0.4 else \
                        "moderate" if edu_similarity > 0.2 else "limited"
                        
        reasons['education'] = self.reason_templates['education'].format(reason_quality)
        
        # Match location
        if processed_resume['location'] and processed_job['location']:
            loc_similarity = self.calculate_similarity(
                processed_resume['location'],
                processed_job['location']
            )
        else:
            loc_similarity = 0.5  # Neutral if location preference not specified
        
        scores['location'] = loc_similarity
        
        reason_quality = "excellent" if loc_similarity > 0.8 else \
                        "strong" if loc_similarity > 0.6 else \
                        "good" if loc_similarity > 0.4 else \
                        "moderate" if loc_similarity > 0.2 else "limited"
                        
        reasons['location'] = self.reason_templates['location'].format(reason_quality)
        
        # Match job title
        title_similarity = self.calculate_similarity(
            processed_resume['full_profile'],
            processed_job['title']
        )
        scores['title'] = title_similarity
        
        reason_quality = "excellent" if title_similarity > 0.8 else \
                        "strong" if title_similarity > 0.6 else \
                        "good" if title_similarity > 0.4 else \
                        "moderate" if title_similarity > 0.2 else "limited"
                        
        reasons['title'] = self.reason_templates['title'].format(reason_quality)
        
        # Calculate weighted average score
        overall_score = sum(scores[k] * self.weights[k] for k in self.weights)
        reasons['overall'] = self.reason_templates['overall'].format(overall_score)
        
        # Extract key skills that match
        job_desc_lower = processed_job['description'].lower()
        matching_skills = []
        for skill in resume_data.get('skills', []):
            if skill.lower() in job_desc_lower:
                matching_skills.append(skill)
        
        # Return match results
        return {
            'job': job,
            'match_score': overall_score,
            'component_scores': scores,
            'match_reasons': reasons,
            'matching_skills': matching_skills
        }

    def rank_jobs_for_resume(self, resume_data, jobs):
        """
        Rank a list of jobs based on how well they match a resume.
        
        Args:
            resume_data: Dictionary containing parsed resume data
            jobs: List of job dictionaries
            
        Returns:
            List of job matches sorted by match score (highest first)
        """
        job_matches = []
        
        print(f"Ranking {len(jobs)} jobs for resume match...")
        for job in jobs:
            match = self.match_job_to_resume(resume_data, job)
            job_matches.append(match)
        
        # Sort by match score (descending)
        ranked_matches = sorted(job_matches, key=lambda x: x['match_score'], reverse=True)
        
        return ranked_matches

# Test function
if __name__ == "__main__":
    print("Job Matcher module loaded successfully.")
