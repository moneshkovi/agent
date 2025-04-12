"""
Job Matcher - AI-powered job matching application
Helps users find early-career job opportunities by matching their resume to job listings.
"""

import os
import time
import streamlit as st
import pandas as pd
from pathlib import Path

# Import our utility classes
from utils import ResumeParser, JobScraper, JobMatcher

# Set page configuration
st.set_page_config(
    page_title="AI Job Matcher",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create data directories if they don't exist
DATA_DIR = Path("data")
UPLOAD_DIR = DATA_DIR / "uploads"
CACHE_DIR = DATA_DIR / "cache"

for dir_path in [DATA_DIR, UPLOAD_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def apply_custom_style():
    """Apply custom CSS styling."""
    st.markdown("""
    <style>
    .job-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .match-score {
        font-weight: bold;
        color: #2a7de1;
    }
    .match-reason {
        margin: 5px 0;
        font-size: 0.9em;
    }
    .matching-skill {
        background-color: #e1f5fe;
        border-radius: 15px;
        padding: 2px 8px;
        margin-right: 5px;
        font-size: 0.8em;
        display: inline-block;
        margin-bottom: 5px;
    }
    .app-header {
        text-align: center;
        margin-bottom: 20px;
    }
    .section-header {
        margin-top: 30px;
        margin-bottom: 10px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    .resume-section {
        background-color: #f5f5f5;
        border-left: 4px solid #2a7de1;
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 0 10px 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)


def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk and return the path."""
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(file_path)


def display_resume_data(resume_data):
    """Display parsed resume data in a readable format."""
    # Name
    st.subheader(resume_data.get('name', 'Unknown Name'))
    
    # Location preference
    location = resume_data.get('location_preference', 'Not specified')
    st.write(f"📍 **Location preference:** {location}")
    
    # Education
    st.markdown('<div class="section-header">🎓 Education</div>', unsafe_allow_html=True)
    degrees = resume_data.get('degrees', [])
    if degrees:
        st.markdown('<div class="resume-section">', unsafe_allow_html=True)
        for degree in degrees:
            st.write(f"• {degree}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No education information extracted")
    
    # Skills
    st.markdown('<div class="section-header">🛠️ Skills</div>', unsafe_allow_html=True)
    skills = resume_data.get('skills', [])
    if skills:
        st.markdown('<div class="resume-section">', unsafe_allow_html=True)
        # Display skills in a more compact format
        col1, col2, col3 = st.columns(3)
        skills_per_col = len(skills) // 3 + 1
        
        for i, skill in enumerate(skills):
            if i < skills_per_col:
                col1.write(f"• {skill}")
            elif i < skills_per_col * 2:
                col2.write(f"• {skill}")
            else:
                col3.write(f"• {skill}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No skills extracted")
    
    # Experience
    st.markdown('<div class="section-header">💼 Experience</div>', unsafe_allow_html=True)
    experiences = resume_data.get('experience', [])
    if experiences:
        st.markdown('<div class="resume-section">', unsafe_allow_html=True)
        for exp in experiences:
            st.write(exp)
            st.write("---")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No experience information extracted")


def display_job_matches(job_matches, num_matches=10):
    """Display matched jobs with scores and reasons."""
    if not job_matches:
        st.warning("No job matches found")
        return
    
    # Limit to requested number of matches
    top_matches = job_matches[:num_matches]
    
    for match in top_matches:
        job = match['job']
        match_score = match['match_score']
        match_reasons = match['match_reasons']
        matching_skills = match['matching_skills']
        
        # Create a job card with HTML/CSS styling
        st.markdown(f"""
        <div class="job-card">
            <h3>{job['title']}</h3>
            <h4>{job['company']} - {job['location']}</h4>
            <p><span class="match-score">Match Score: {match_score:.2f}</span></p>
            
            <p class="match-reason">{match_reasons['overall']}</p>
            <p class="match-reason">{match_reasons['skills']}</p>
            <p class="match-reason">{match_reasons['experience']}</p>
            
            <div>
                {''.join([f'<span class="matching-skill">{skill}</span>' for skill in matching_skills])}
            </div>
            
            <p>{job['snippet']}</p>
            
            <a href="{job['url']}" target="_blank">View Job</a>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application function."""
    apply_custom_style()
    
    # App header
    st.markdown('<div class="app-header">', unsafe_allow_html=True)
    st.title("💼 AI Job Matcher")
    st.subheader("Match your resume to early-career job opportunities")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialize session state for storing data between reruns
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
    if 'job_matches' not in st.session_state:
        st.session_state.job_matches = None
    if 'search_complete' not in st.session_state:
        st.session_state.search_complete = False
    
    # Sidebar for input controls
    with st.sidebar:
        st.header("Resume Upload")
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'txt'])
        
        if uploaded_file is not None:
            with st.spinner("Parsing your resume..."):
                # Save file locally
                file_path = save_uploaded_file(uploaded_file)
                
                # Parse resume
                parser = ResumeParser()
                resume_data = parser.parse_resume(file_path)
                
                if "error" in resume_data:
                    st.error(f"Error parsing resume: {resume_data['error']}")
                else:
                    st.session_state.resume_data = resume_data
                    st.success("Resume successfully parsed!")
        
        # Job search parameters
        st.header("Job Search Parameters")
        
        job_types = [
            "Entry-level Software Developer",
            "Junior Data Analyst",
            "Marketing Assistant",
            "Sales Representative",
            "Customer Service Associate",
            "HR Assistant",
            "Financial Analyst",
            "Administrative Assistant",
            "Project Coordinator",
            "Research Assistant",
            "Custom..."
        ]
        
        job_type_selection = st.selectbox("Job Type", job_types)
        
        if job_type_selection == "Custom...":
            job_query = st.text_input("Enter Job Title/Keywords")
        else:
            job_query = job_type_selection
        
        location = st.text_input("Location (City, State or Remote)")
        if not location:
            location = "United States"  # Default
        
        num_jobs = st.slider("Number of jobs to scrape", 10, 100, 30)
        num_matches = st.slider("Number of top matches to display", 5, 20, 10)
        
        # Start search button
        search_button = st.button("Find Matching Jobs")
        
        if search_button:
            if not st.session_state.resume_data:
                st.error("Please upload a resume first")
            elif not job_query:
                st.error("Please provide job search parameters")
            else:
                # Clear previous search results
                st.session_state.job_matches = None
                st.session_state.search_complete = False
                
                # Indicate we need to perform search in main area after sidebar processing
                st.session_state.perform_search = True
                st.session_state.search_params = {
                    "job_query": job_query,
                    "location": location,
                    "num_jobs": num_jobs,
                    "num_matches": num_matches
                }
    
    # Main content area
    if st.session_state.resume_data is None:
        # Show instructions when no resume is uploaded
        st.info("""
        ### How to use AI Job Matcher
        
        1. **Upload your resume** (PDF or text file) in the sidebar
        2. Review the parsed information for accuracy
        3. **Set job search parameters** in the sidebar
        4. Click "Find Matching Jobs" to match your profile with job listings
        5. Review your top job matches with detailed matching scores
        
        #### Why Use AI Job Matcher?
        
        Finding the right job early in your career can be challenging. This tool uses AI to:
        
        - Extract your skills, experience, and qualifications from your resume
        - Find relevant job openings from popular job sites
        - Calculate how well each job matches your profile
        - Rank jobs based on the match and provide detailed reasons
        
        Get started by uploading your resume in the sidebar!
        """)
    else:
        # Two main tabs: Resume Review and Job Matches
        tab1, tab2 = st.tabs(["Resume Review", "Job Matches"])
        
        with tab1:
            st.header("Your Parsed Resume")
            st.write("Review the information extracted from your resume for accuracy.")
            display_resume_data(st.session_state.resume_data)
            
        with tab2:
            st.header("Job Matches")
            
            # Check if we need to perform a search
            if hasattr(st.session_state, 'perform_search') and st.session_state.perform_search:
                params = st.session_state.search_params
                
                with st.spinner(f"Searching for {params['job_query']} jobs in {params['location']}..."):
                    # Scrape jobs
                    scraper = JobScraper(cache_dir=str(CACHE_DIR))
                    jobs = scraper.scrape_jobs(
                        params['job_query'], 
                        params['location'], 
                        num_pages=params['num_jobs']//10)
                    
                    if jobs:
                        st.info(f"Found {len(jobs)} job listings. Calculating matches...")
                        
                        # Match jobs to resume
                        matcher = JobMatcher()
                        job_matches = matcher.rank_jobs_for_resume(
                            st.session_state.resume_data, 
                            jobs)
                        
                        st.session_state.job_matches = job_matches
                        st.session_state.num_matches_to_show = params['num_matches']
                    else:
                        st.error("No jobs found. Try different search parameters.")
                    
                    # Reset search flag
                    st.session_state.perform_search = False
                    st.session_state.search_complete = True
            
            # Display job matches if available
            if st.session_state.job_matches:
                download_data = []
                for match in st.session_state.job_matches:
                    job = match['job']
                    download_data.append({
                        "Title": job['title'],
                        "Company": job['company'],
                        "Location": job['location'],
                        "Match Score": f"{match['match_score']:.2f}",
                        "URL": job['url']
                    })
                
                # Create download button for job matches
                df = pd.DataFrame(download_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Job Matches as CSV",
                    data=csv,
                    file_name="job_matches.csv",
                    mime="text/csv",
                )
                
                # Show matches
                display_job_matches(
                    st.session_state.job_matches, 
                    st.session_state.num_matches_to_show
                )
            elif st.session_state.search_complete:
                st.warning("No matching jobs found. Try adjusting your search parameters.")
            else:
                st.info("Enter search parameters and click 'Find Matching Jobs' to see results.")


if __name__ == "__main__":
    main()
