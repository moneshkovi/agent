#!/usr/bin/env python
"""
Sample script demonstrating the usage of AI Job Matcher components
without the Streamlit UI
"""

from utils import ResumeParser, JobScraper, JobMatcher
import json
from pathlib import Path
import time
import argparse


def parse_resume(resume_path):
    """Parse a resume file and print extracted information."""
    parser = ResumeParser()
    print(f"Parsing resume: {resume_path}")
    
    resume_data = parser.parse_resume(resume_path)
    if "error" in resume_data:
        print(f"Error parsing resume: {resume_data['error']}")
        return None
        
    # Print extracted information
    print("\n===== EXTRACTED RESUME DATA =====")
    print(f"Name: {resume_data.get('name', 'Unknown')}")
    print(f"Location: {resume_data.get('location_preference', 'Not specified')}")
    
    print("\nDegrees:")
    for degree in resume_data.get('degrees', []):
        print(f"  - {degree}")
        
    print("\nSkills:")
    for skill in resume_data.get('skills', []):
        print(f"  - {skill}")
        
    print("\nExperience:")
    for i, exp in enumerate(resume_data.get('experience', [])):
        print(f"  [Entry {i+1}] {exp[:100]}...")
    
    return resume_data


def search_jobs(query, location, num_pages=2):
    """Search for jobs and return results."""
    scraper = JobScraper(cache_dir="./data/cache")
    print(f"\nSearching for '{query}' jobs in '{location}'...")
    
    start_time = time.time()
    jobs = scraper.scrape_jobs(query, location, num_pages=num_pages)
    elapsed_time = time.time() - start_time
    
    print(f"Found {len(jobs)} jobs in {elapsed_time:.1f} seconds")
    
    if jobs:
        print("\n===== SAMPLE JOB =====")
        job = jobs[0]
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")
        print(f"Snippet: {job['snippet'][:150]}...")
    
    return jobs


def match_jobs(resume_data, jobs, top_n=5):
    """Match jobs to resume and print top results."""
    matcher = JobMatcher()
    print("\nMatching jobs to resume...")
    
    start_time = time.time()
    matches = matcher.rank_jobs_for_resume(resume_data, jobs)
    elapsed_time = time.time() - start_time
    
    print(f"Ranked {len(matches)} jobs in {elapsed_time:.1f} seconds")
    
    print(f"\n===== TOP {top_n} MATCHES =====")
    for i, match in enumerate(matches[:top_n]):
        job = match['job']
        match_score = match['match_score']
        matching_skills = match['matching_skills']
        
        print(f"\n[{i+1}] {job['title']} at {job['company']}")
        print(f"    Score: {match_score:.2f}")
        print(f"    Location: {job['location']}")
        if matching_skills:
            print(f"    Matching Skills: {', '.join(matching_skills)}")
        print(f"    URL: {job['url']}")
        
    # Save matches to file
    output_file = Path("./data/latest_matches.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        # Convert to serializable format
        serializable_matches = []
        for match in matches[:top_n]:
            serializable_match = {
                "job": match["job"],
                "match_score": match["match_score"],
                "matching_skills": match["matching_skills"],
                "match_reasons": match["match_reasons"]
            }
            serializable_matches.append(serializable_match)
            
        json.dump(serializable_matches, f, indent=2)
    
    print(f"\nTop matches saved to {output_file}")
    
    return matches


def main():
    """Main function to demonstrate the job matcher functionality."""
    parser = argparse.ArgumentParser(description="AI Job Matcher - Command Line Interface")
    parser.add_argument("resume", help="Path to resume file (PDF or TXT)")
    parser.add_argument("--query", "-q", default="Entry-level Software Developer", 
                      help="Job search query (default: Entry-level Software Developer)")
    parser.add_argument("--location", "-l", default="United States",
                      help="Job location (default: United States)")
    parser.add_argument("--pages", "-p", type=int, default=2,
                      help="Number of pages to scrape (default: 2)")
    parser.add_argument("--matches", "-m", type=int, default=5,
                      help="Number of top matches to show (default: 5)")
    
    args = parser.parse_args()
    
    # Check if resume file exists
    if not Path(args.resume).exists():
        print(f"Error: Resume file '{args.resume}' not found")
        return
    
    # Parse resume
    resume_data = parse_resume(args.resume)
    if not resume_data:
        return
    
    # Search for jobs
    jobs = search_jobs(args.query, args.location, args.pages)
    if not jobs:
        print("No jobs found. Try a different search query or location.")
        return
    
    # Match jobs to resume
    matches = match_jobs(resume_data, jobs, args.matches)
    
    print("\nDone! You can now review the top matches and apply to the most relevant jobs.")


if __name__ == "__main__":
    main()
