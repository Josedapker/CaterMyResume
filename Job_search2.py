from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
import random
import urllib.parse
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime
from selenium.webdriver.chrome.options import Options

def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_user_input():
    job_title = input("Enter the job title you're looking for: ")
    location = input("Enter the location (city, state, or 'remote'): ")
    
    # We'll keep the advanced filters question, but we won't use it for now
    input("Do you want to use advanced filters? (yes/no): ")  # This input is ignored
    
    return job_title, location

def build_indeed_url(job_title, location, start=0):
    base_url = "https://www.indeed.com/jobs?"
    params = {
        'q': job_title,
        'l': location,
        'fromage': '14',  # Last 14 days
        'start': start
    }
    
    return base_url + urllib.parse.urlencode(params)

def scrape_indeed(url):
    driver = setup_driver()
    driver.get(url)
    
    job_listings = []
    page_number = 1
    
    while True:
        print(f"\nProcessing page {page_number}")
        time.sleep(5)  # Wait for the page to load completely
        
        # Get the page source and parse it with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all job cards
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        if not job_cards:
            print("No job cards found on this page.")
            break
        
        print(f"Number of job cards found: {len(job_cards)}")
        
        for card in job_cards:
            job = extract_job_info(card)
            if job:
                job_listings.append(job)
        
        # Check if there's a next page
        try:
            next_page = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-testid="pagination-page-next"]'))
            )
            next_page.click()
            page_number += 1
        except:
            print("No more pages to scrape.")
            break
    
    driver.quit()
    return job_listings

def extract_job_info(card):
    try:
        title = card.find('h2', class_='jobTitle').text.strip()
        company = card.find('span', class_='companyName').text.strip()
        location = card.find('div', class_='companyLocation').text.strip()
        
        salary = card.find('div', class_='salary-snippet')
        salary = salary.text.strip() if salary else "Not specified"
        
        job_type = card.find('div', class_='attribute_snippet')
        job_type = job_type.text.strip() if job_type else "Not specified"
        
        date_posted = card.find('span', class_='date')
        date_posted = date_posted.text.strip() if date_posted else "Not specified"
        
        details = card.find('div', class_='job-snippet')
        details = details.text.strip() if details else "Not available"
        
        company_rating = card.find('span', class_='ratingNumber')
        company_rating = company_rating.text.strip() if company_rating else "Not specified"
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "job_type": job_type,
            "date_posted": date_posted,
            "details": details,
            "company_rating": company_rating
        }
    except Exception as e:
        print(f"Error extracting job info: {e}")
        return None

def save_to_csv(job_listings, job_title, location):
    # Create a directory for the CSV files if it doesn't exist
    directory = "job_search_results"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generate a filename based on the current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{directory}/{job_title}_{location}_{timestamp}.csv"
    
    # Write the job listings to the CSV file
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'company', 'location', 'salary', 'job_type', 'date_posted', 'details', 'company_rating']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for job in job_listings:
            writer.writerow(job)
    
    print(f"\nJob listings saved to {filename}")

def main():
    job_title, location = get_user_input()
    
    url = build_indeed_url(job_title, location)
    print(f"\nSearching for {job_title} jobs in {location}...")
    all_job_listings = scrape_indeed(url)
    
    if all_job_listings:
        print("\nJob Listings:")
        for i, job in enumerate(all_job_listings, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Job Type: {job['job_type']}")
            print(f"   Date Posted: {job['date_posted']}")
            print(f"   Company Rating: {job['company_rating']}")
            print(f"   Details: {job['details'][:200]}...")  # Print first 200 characters of details
        
        # Save the job listings to a CSV file
        save_to_csv(all_job_listings, job_title, location)
    else:
        print("No job listings found.")

if __name__ == "__main__":
    main()