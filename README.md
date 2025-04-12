# AI Job Matcher

An AI-powered job matching application that helps early-career job seekers find relevant opportunities by matching their resume to job listings.

## Features

- Resume parsing (PDF or text)
- Automatic extraction of name, skills, education, experience, and location preferences
- Job scraping from Indeed
- AI-powered semantic matching between resume and job listings using sentence-transformers
- Match scoring with detailed breakdown of matching reasons
- Clean, user-friendly Streamlit interface
- Ability to download job matches as CSV

## Setup

1. Clone this repository or download the files
2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install the required dependencies
```bash
pip install -r requirements.txt
```
4. Download the spaCy language model
```bash
python -m spacy download en_core_web_sm
```

## Running the Application

```bash
cd job_matcher
streamlit run app.py
```

The application will be available at http://localhost:8501 in your web browser.

## How to Use

1. **Upload Your Resume**: Use the sidebar to upload your PDF or text resume
2. **Review Parsed Information**: Check the "Resume Review" tab to ensure your information was extracted correctly
3. **Set Job Search Parameters**: Choose job type, location, and search preferences
4. **Find Matching Jobs**: Click the "Find Matching Jobs" button to see your top matches
5. **Review Matches**: Browse through ranked job matches with detailed matching scores and reasons
6. **Download Results**: Use the download button to save your matches as a CSV file

## Project Structure

```
job_matcher/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Project dependencies
├── data/                  # Directory for cached and uploaded files
│   ├── cache/             # Cached job search results
│   └── uploads/           # Uploaded resumes
└── utils/                 # Utility modules
    ├── __init__.py        # Package initializer
    ├── resume_parser.py   # Resume parsing functionality
    ├── job_scraper.py     # Job scraping functionality
    └── job_matcher.py     # AI matching functionality
```

## Technologies Used

- **Streamlit**: Web interface
- **Sentence-Transformers**: Semantic matching between resume and jobs
- **PyPDF2**: PDF parsing
- **spaCy**: NLP for entity recognition and text processing
- **BeautifulSoup4**: Web scraping
- **Pandas**: Data handling and CSV export

## Limitations

- Web scraping is subject to website changes and may require updates
- Resume parsing accuracy depends on the format and structure of the resume
- Job searches are limited to Indeed (more sources can be added)
- No persistent user accounts (all data is stored locally)

## Future Improvements

- Add support for more job boards (LinkedIn, Glassdoor, etc.)
- Implement custom resume parser training for better extraction
- Add interactive feedback to improve matching algorithm
- Create email alert system for new matching jobs
- Add interview preparation suggestions based on job requirements

## License

This project is for educational purposes only. Use responsibly and be aware of the terms of service of any websites you scrape.
