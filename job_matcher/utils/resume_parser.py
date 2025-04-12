"""
Resume Parser Module
Extracts structured data from resumes in PDF or text format
"""

import re
import PyPDF2
import spacy
from pathlib import Path

# Load spaCy language model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not installed, provide guidance
    print("Downloading spaCy language model (first-time setup)...")
    import subprocess
    subprocess.call(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class ResumeParser:
    def __init__(self):
        self.common_degrees = [
            'bachelor', 'masters', 'phd', 'doctorate', 'bs', 'ba', 'mba', 'ms', 'ma',
            'b.s.', 'b.a.', 'm.b.a.', 'm.s.', 'm.a.', 'ph.d', 'b.tech', 'm.tech'
        ]
        
        self.common_tech_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php',
            'html', 'css', 'sql', 'nosql', 'react', 'angular', 'vue', 'node', 'django',
            'flask', 'express', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'git', 'ci/cd', 'tensorflow', 'pytorch', 'machine learning', 'ai', 'data science',
            'devops', 'agile', 'scrum', 'rest api', 'graphql'
        ]
        
        self.common_soft_skills = [
            'communication', 'teamwork', 'leadership', 'problem solving', 'critical thinking',
            'time management', 'project management', 'adaptability', 'creativity', 'analytical',
            'attention to detail'
        ]

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text()
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_name(self, text, doc=None):
        """Extract candidate name using NER."""
        if doc is None:
            doc = nlp(text[:1000])  # Process just the first 1000 chars for efficiency
        
        # Look for person names at the beginning of the resume
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Check if it's likely to be the resume owner (usually at the top)
                if ent.start_char < 500:  # Consider names in the first 500 chars
                    return ent.text
        
        # Fallback: Look for name patterns
        name_pattern = re.compile(r'^([A-Z][a-z]+ [A-Z][a-z]+)')
        match = name_pattern.search(text[:500].strip())
        if match:
            return match.group(1)
        
        return "Unknown"

    def extract_degrees(self, text):
        """Extract education details."""
        degrees = []
        
        # Find potential degree mentions
        for degree in self.common_degrees:
            pattern = re.compile(r'\b' + degree + r'[s]?\b', re.IGNORECASE)
            if pattern.search(text):
                # Get surrounding context (the line containing the degree)
                for line in text.split('\n'):
                    if pattern.search(line):
                        degrees.append(line.strip())
        
        return list(set(degrees))

    def extract_skills(self, text):
        """Extract technical and soft skills."""
        skills = []
        
        # Look for technical skills
        for skill in self.common_tech_skills:
            pattern = re.compile(r'\b' + re.escape(skill) + r'\b', re.IGNORECASE)
            if pattern.search(text):
                skills.append(skill)
        
        # Look for soft skills
        for skill in self.common_soft_skills:
            pattern = re.compile(r'\b' + re.escape(skill) + r'\b', re.IGNORECASE)
            if pattern.search(text):
                skills.append(skill)
        
        return skills

    def extract_experience(self, text, doc=None):
        """Extract work experience information."""
        if doc is None:
            doc = nlp(text)
            
        experiences = []
        
        # Look for sections that might contain experience
        experience_section = None
        
        # Common section headers for experience
        exp_headers = ['experience', 'work experience', 'professional experience', 
                     'employment history', 'work history']
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if this line is an experience section header
            if any(header in line_lower for header in exp_headers) and len(line) < 50:
                start_idx = i + 1
                end_idx = len(lines)
                
                # Find where the experience section ends (next section header)
                for j in range(start_idx, len(lines)):
                    # Potential section headers are usually short lines with specific keywords
                    if len(lines[j].strip()) < 50 and lines[j].strip() and \
                       any(keyword in lines[j].lower() for keyword in 
                           ['education', 'skills', 'projects', 'certification', 'references']):
                        end_idx = j
                        break
                
                # Extract the experience section
                experience_section = '\n'.join(lines[start_idx:end_idx])
                break
        
        if experience_section:
            # Split into potential experience entries
            for paragraph in re.split(r'\n\s*\n', experience_section):
                if len(paragraph.strip()) > 30:  # Ignore very short paragraphs
                    experiences.append(paragraph.strip())
            
        return experiences

    def extract_location_preference(self, text):
        """Extract potential location preferences."""
        doc = nlp(text)
        locations = []
        
        # Extract locations using NER
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:  # Geopolitical Entity or Location
                locations.append(ent.text)
        
        # Look specifically for location preferences in the text
        pref_indicators = [
            "willing to relocate", "prefer to work in", "location preference",
            "seeking positions in", "looking for opportunities in", "based in"
        ]
        
        text_lower = text.lower()
        for indicator in pref_indicators:
            if indicator in text_lower:
                # Get the sentence containing this indicator
                pattern = re.compile(r'[^.!?]*' + re.escape(indicator) + r'[^.!?]*[.!?]', re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    # Check if this sentence contains locations we've already found
                    sentence = match.group(0)
                    for loc in locations:
                        if loc.lower() in sentence.lower():
                            return loc
                    
                    # If no known location in the sentence, try to find one
                    sentence_doc = nlp(sentence)
                    for ent in sentence_doc.ents:
                        if ent.label_ in ["GPE", "LOC"]:
                            return ent.text
        
        # Return the most frequently mentioned location or the first one
        if locations:
            # Count occurrences
            location_counts = {}
            for loc in locations:
                location_counts[loc] = location_counts.get(loc, 0) + 1
            
            # Get the most mentioned location
            return max(location_counts.items(), key=lambda x: x[1])[0]
        
        return "Not specified"

    def parse_resume(self, file_path):
        """
        Main function to parse a resume file and extract structured information
        
        Args:
            file_path: Path to the resume file (PDF or text)
            
        Returns:
            A dictionary containing the structured resume information
        """
        path = Path(file_path)
        
        # Extract text based on file type
        if path.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        else:
            # Assume it's a text file
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            except Exception as e:
                print(f"Error reading text file: {e}")
                return {}
        
        if not text:
            return {"error": "Could not extract text from the provided file"}
        
        # Process with spaCy for NER and other analyses
        # Limit to first 30K characters for memory efficiency
        doc = nlp(text[:30000])
        
        # Extract information
        name = self.extract_name(text, doc)
        degrees = self.extract_degrees(text)
        skills = self.extract_skills(text)
        experience = self.extract_experience(text, doc)
        location = self.extract_location_preference(text)
        
        return {
            "name": name,
            "degrees": degrees,
            "skills": skills,
            "experience": experience,
            "location_preference": location,
            "raw_text": text  # Include raw text for any additional processing
        }

# Test function
if __name__ == "__main__":
    parser = ResumeParser()
    # For testing
    print("Resume Parser module loaded successfully. Use parse_resume(file_path) to process a resume.")
