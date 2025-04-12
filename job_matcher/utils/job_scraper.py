"""
Job Scraper Module
Scrapes entry-level job listings from popular job boards
"""

import requests
import time
import random
import json
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from pathlib import Path


class JobScraper:
    def __init__(self, cache_dir=None):
        """
        Initialize the job scraper.
        Args:
            cache_dir: Directory to store scraped jobs cache
        """
        self.ua = UserAgent()
        # Create cache directory if specified
        self.cache_dir = cache_dir
        if self.cache_dir:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
            self.cache_file = Path(self.cache_dir) / "job_cache.json"
        
        # Sleep ranges (in seconds) to appear more human-like when scraping
        self.page_sleep_range = (2, 5)
        self.request_sleep_range = (1, 3)

    def _get_headers(self):
        """Generate random headers for requests to avoid detection."""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _random_sleep(self, range_tuple=None):
        """Sleep for a random amount of time within the given range."""
        if not range_tuple:
            range_tuple = self.request_sleep_range
        time.sleep(random.uniform(*range_tuple))

    def _save_to_cache(self, jobs, query, location):
        """Save scraped jobs to cache file."""
        if not self.cache_dir:
            return
            
        cache_data = {}
        # Load existing cache if it exists
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # If cache is corrupted or missing, start with empty cache
                cache_data = {}
        
        # Create a cache key from query and location
        cache_key = f"{query}_{location}".lower().replace(' ', '_')
        
        # Update cache with new data
        cache_data[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "location": location,
            "jobs": jobs
        }
        
        # Save updated cache
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    
    def _load_from_cache(self, query, location):
        """Load jobs from cache if they exist and are recent."""
        if not self.cache_dir or not self.cache_file.exists():
            return None
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Create a cache key from query and location
            cache_key = f"{query}_{location}".lower().replace(' ', '_')
            
            if cache_key in cache_data:
                # Check if cache is less than 24 hours old
                cache_time = datetime.fromisoformat(cache_data[cache_key]["timestamp"])
                time_diff = (datetime.now() - cache_time).total_seconds() / 3600
                
                if time_diff < 24:  # Less than 24 hours old
                    print(f"Loading {len(cache_data[cache_key]['jobs'])} jobs from cache")
                    return cache_data[cache_key]["jobs"]
        
        except (json.JSONDecodeError, KeyError, ValueError, FileNotFoundError):
            # If any error occurs, proceed with fresh scraping
            pass
            
        return None

    def scrape_indeed(self, query, location="United States", num_pages=3):
        """
        Scrape jobs from Indeed.
        
        Args:
            query: Job search query (e.g. "entry level software developer")
            location: Location to search in
            num_pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        # Check cache first
        cached_jobs = self._load_from_cache(query, location)
        if cached_jobs:
            return cached_jobs
            
        jobs = []
        
        # Format query for URL
        formatted_query = query.replace(' ', '+')
        formatted_location = location.replace(' ', '+')
        
        for page in range(num_pages):
            start_val = page * 10  # Indeed uses 10 jobs per page
            
            url = f"https://www.indeed.com/jobs?q={formatted_query}&l={formatted_location}&sort=date&start={start_val}"
            
            try:
                print(f"Scraping Indeed page {page+1}/{num_pages}")
                response = requests.get(url, headers=self._get_headers())
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    job_cards = soup.select('div.job_seen_beacon')
                    
                    if not job_cards:
                        # Indeed changes their HTML structure frequently
                        # Try alternate selectors
                        job_cards = soup.select('div.jobsearch-SerpJobCard') or \
                                   soup.select('div.tapItem') or \
                                   soup.select('div[data-testid="job-card"]')
                    
                    for job_card in job_cards:
                        job = {}
                        
                        # Extract title - try different possible selectors
                        title_elem = job_card.select_one('h2.jobTitle') or \
                                    job_card.select_one('a.jobtitle') or \
                                    job_card.select_one('h2.title') or \
                                    job_card.select_one('h2 a')
                                    
                        if title_elem:
                            # Get text from span child if it exists, otherwise use the h2 text
                            span = title_elem.select_one('span')
                            job['title'] = span.text.strip() if span else title_elem.text.strip()
                        else:
                            job['title'] = "Unknown Position"
                            
                        # Extract company
                        company_elem = job_card.select_one('span.companyName') or \
                                      job_card.select_one('div.company') or \
                                      job_card.select_one('[data-testid="company-name"]')
                                      
                        job['company'] = company_elem.text.strip() if company_elem else "Unknown Company"
                        
                        # Extract location
                        location_elem = job_card.select_one('div.companyLocation') or \
                                       job_card.select_one('.location') or \
                                       job_card.select_one('[data-testid="text-location"]')
                                       
                        job['location'] = location_elem.text.strip() if location_elem else "Unknown Location"
                        
                        # Extract job link
                        link_elem = job_card.select_one('a[id^="job_"]') or \
                                   job_card.select_one('a.jobtitle') or \
                                   job_card.select_one('h2 a')
                                   
                        if link_elem and 'href' in link_elem.attrs:
                            href = link_elem['href']
                            # Some links are relative, add domain if needed
                            if href.startswith('/'):
                                job['url'] = f"https://www.indeed.com{href}"
                            else:
                                job['url'] = href
                        else:
                            job['url'] = ""
                        
                        # Extract date posted
                        date_elem = job_card.select_one('span.date') or \
                                   job_card.select_one('.result-link-bar-container .date') or \
                                   job_card.select_one('[data-testid="text-date"]')
                                   
                        job['date_posted'] = date_elem.text.strip() if date_elem else ""
                        
                        # Extract snippet/description
                        snippet_elem = job_card.select_one('.job-snippet') or \
                                     job_card.select_one('.summary') or \
                                     job_card.select_one('[data-testid="job-snippet"]')
                                     
                        job['snippet'] = snippet_elem.text.strip() if snippet_elem else ""
                        
                        # Extract salary if available
                        salary_elem = job_card.select_one('.salary-snippet') or \
                                     job_card.select_one('.salaryText') or \
                                     job_card.select_one('[data-testid="text-salary"]')
                                     
                        job['salary'] = salary_elem.text.strip() if salary_elem else "Not specified"
                        
                        # Add job source info
                        job['source'] = 'Indeed'
                        job['query'] = query
                        job['full_description'] = ""  # Will be populated when needed
                        
                        jobs.append(job)
                
                # Sleep before next page to avoid rate limiting
                self._random_sleep(self.page_sleep_range)
                
            except Exception as e:
                print(f"Error scraping Indeed page {page+1}: {e}")
                continue
                
        # Save to cache
        self._save_to_cache(jobs, query, location)
        
        return jobs
    
    def get_full_description(self, job):
        """
        Fetch the full job description by visiting the job URL.
        Updates the job object in place.
        
        Args:
            job: Job dictionary with 'url' field
            
        Returns:
            Updated job dictionary with full description
        """
        # If we already have the full description or URL is missing, return as is
        if job.get('full_description') or not job.get('url'):
            return job
            
        try:
            response = requests.get(job['url'], headers=self._get_headers())
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try different selectors for job description
                description_elem = soup.select_one('#jobDescriptionText') or \
                                  soup.select_one('.jobsearch-jobDescriptionText') or \
                                  soup.select_one('.description')
                                  
                if description_elem:
                    job['full_description'] = description_elem.text.strip()
                    
                # Random sleep to avoid rate limiting
                self._random_sleep()
                
        except Exception as e:
            print(f"Error fetching full description: {e}")
            
        return job

    def scrape_jobs(self, query, location="United States", source="indeed", num_pages=3):
        """
        Main method to scrape jobs from specified source.
        
        Args:
            query: Job search query
            location: Location to search in
            source: Source to scrape from ('indeed' or others in the future)
            num_pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        if source.lower() == 'indeed':
            return self.scrape_indeed(query, location, num_pages)
        else:
            raise ValueError(f"Unsupported job source: {source}")

# Test function
if __name__ == "__main__":
    scraper = JobScraper(cache_dir="./data")
    print("Job Scraper module loaded successfully.")
    
    # Test scraping (uncomment to test)
    # jobs = scraper.scrape_jobs("entry level software developer", "Remote")
    # print(f"Found {len(jobs)} jobs")
    # if jobs:
    #     print("Sample job:", jobs[0])
