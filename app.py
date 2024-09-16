from bs4 import BeautifulSoup
import requests
import time
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]

def get_user_input():
    field = input("Enter Field: ")
    locations = input("Enter locations (comma-separated, e.g., Delhi,Noida,Bangalore): ").split(',')
    skills = []
    while True:
        skill_input = input("Enter Skill (type 'done' when finished): ")
        if skill_input.lower() == "done":
            break
        skills.append(skill_input)
    return field, locations, skills

def search_jobs(field, location, skills, max_results=10):
    page_no = 0
    results = []
    base_url = f'https://www.linkedin.com/jobs/search/?keywords={field}&location={location}'
    
    while len(results) < max_results:
        url = f'{base_url}&start={page_no * 25}'  # LinkedIn uses multiples of 25 for pagination
        print(f"Searching page {page_no + 1} for {location}")
        
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if response.status_code == 429:
                print("Rate limit reached. Waiting for 60 seconds before retrying...")
                time.sleep(60)
                continue
                
        except requests.RequestException as e:
            print(f"Error fetching page {page_no + 1} for {location}: {e}")
            break

        soup = BeautifulSoup(response.text, 'lxml')
        jobs = soup.find_all('div', class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card")
        
        print(f"Found {len(jobs)} job listings on this page")
        
        if not jobs:
            print("No more jobs found on this page.")
            break

        for job in jobs:
            job_info = process_job(job, skills)
            if job_info:
                results.append(job_info)
                if len(results) >= max_results:
                    return results

        page_no += 1
        delay = random.uniform(10, 20)
        print(f"Waiting for {delay:.2f} seconds before the next request...")
        time.sleep(delay)

    return results

def process_job(job, skills):
    title_elem = job.find('h3', class_="base-search-card__title")
    company_elem = job.find('h4', class_="base-search-card__subtitle")
    link_elem = job.find('a', class_="base-card__full-link")

    if title_elem and company_elem and link_elem:
        title = title_elem.text.strip()
        company = company_elem.text.strip()
        link = link_elem['href']

        # Fetch the job description
        try:
            job_response = requests.get(link, timeout=10)
            job_soup = BeautifulSoup(job_response.text, 'lxml')
            job_description = job_soup.find('div', class_="show-more-less-html__markup")
            if job_description:
                description_text = job_description.text.lower()
                matched_skills = [skill for skill in skills if skill.lower() in description_text]
                match_percentage = round((len(matched_skills) / len(skills)) * 100, 2)
            else:
                matched_skills = []
                match_percentage = 0
        except requests.RequestException:
            matched_skills = []
            match_percentage = 0

        return [title, company, match_percentage, matched_skills, link]
    
    return None

def main():
    field, locations, skills = get_user_input()
    all_results = []

    print("Searching for jobs... This might take a few minutes. Please wait.")
    
    for location in locations:
        print(f"Searching in {location.strip()}...")
        results = search_jobs(field, location.strip(), skills, max_results=5)
        results = [r + [location.strip()] for r in results]
        all_results.extend(results)
        time.sleep(random.uniform(20, 30))  # Longer delay between locations

    all_results.sort(key=lambda x: x[2], reverse=True)

    print("\nSearch complete. Here are the results:")
    for res in all_results:
        print(f"""
        Job Title: {res[0]}
        Employer: {res[1]}
        % Match: {res[2]}%
        Skills: {res[3]}
        Job Link: {res[4]}
        Location: {res[5]}
        """)

    print(f"Total results found: {len(all_results)}")

if __name__ == "__main__":
    main()