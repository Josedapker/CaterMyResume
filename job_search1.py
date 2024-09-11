from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import urllib.parse
from bs4 import BeautifulSoup
import csv
import os
from datetime import datetime

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

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

def scrape_job_card(driver, card):
    try:
        title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span[id^='jobTitle']").text
        company = card.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']").text
        location = card.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']").text
        
        title_link = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
        driver.execute_script("arguments[0].click();", title_link)
        
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "jobDescriptionText")))
        
        salary = driver.find_element(By.CSS_SELECTOR, "div[id='salaryInfoAndJobType']").text
        job_type = driver.find_element(By.CSS_SELECTOR, "div[data-testid='attribute_snippet_testid']").text
        date_posted = driver.find_element(By.CSS_SELECTOR, "span[data-testid='job-age']").text
        details = driver.find_element(By.ID, "jobDescriptionText").text
        company_rating = driver.find_element(By.CSS_SELECTOR, "div[data-testid='company-rating']").text
        
        driver.back()
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon")))
        
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
        print(f"Error processing job card: {e}")
        return None

def scrape_indeed(url):
    driver = setup_driver()
    driver.get(url)
    
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon")))
    except Exception as e:
        print(f"Error waiting for job cards to load: {e}")
        driver.quit()
        return []
    
    # Scroll to load all job cards
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Get the full page source
    page_source = driver.page_source
    
    # Use BeautifulSoup for parsing
    soup = BeautifulSoup(page_source, 'html.parser')
    
    job_cards = soup.find_all("div", class_="job_seen_beacon")
    print(f"Number of job cards found: {len(job_cards)}")
    
    job_listings = []
    for index, card in enumerate(job_cards, 1):
        print(f"Processing job card {index}/{len(job_cards)}")
        job = extract_job_details(card)
        if job:
            job_listings.append(job)
            print(f"Successfully processed job: {job['title']}")
        else:
            print(f"Failed to process job card {index}")
    
    driver.quit()
    return job_listings

def extract_job_details(card):
    try:
        title = card.find("h2", class_="jobTitle").text.strip()
        company = card.find("span", {"data-testid": "company-name"}).text.strip()
        location = card.find("div", {"data-testid": "text-location"}).text.strip()
        
        salary = card.find("div", class_="salary-snippet")
        salary = salary.text.strip() if salary else "Not provided"
        
        job_type = card.find("div", class_="attribute_snippet")
        job_type = job_type.text.strip() if job_type else "Not specified"
        
        date_posted = card.find("span", class_="date")
        date_posted = date_posted.text.strip() if date_posted else "Not available"
        
        snippet = card.find("div", class_="job-snippet")
        snippet = snippet.text.strip() if snippet else "No details available"
        
        apply_link = card.find("a", class_="jcs-JobTitle")
        apply_link = "https://www.indeed.com" + apply_link['href'] if apply_link else "Not available"
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "job_type": job_type,
            "date_posted": date_posted,
            "snippet": snippet,
            "apply_link": apply_link
        }
    except Exception as e:
        print(f"Error extracting job details: {e}")
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
        fieldnames = ['title', 'company', 'location', 'salary', 'job_type', 'date_posted', 'snippet', 'apply_link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for job in job_listings:
            writer.writerow(job)
    
    print(f"\nJob listings saved to {filename}")

def main():
    job_title, location = get_user_input()
    
    all_job_listings = []
    for start in range(0, 50, 10):  # Fetch first 5 pages
        url = build_indeed_url(job_title, location, start)
        print(f"\nSearching page {start//10 + 1} for {job_title} jobs in {location}...")
        job_listings = scrape_indeed(url)
        all_job_listings.extend(job_listings)
        if len(job_listings) < 10:  # If we get less than 10 results, we've reached the end
            break
    
    if all_job_listings:
        print("\nJob Listings:")
        for i, job in enumerate(all_job_listings, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Job Type: {job['job_type']}")
            print(f"   Date Posted: {job['date_posted']}")
            print(f"   Snippet: {job['snippet'][:200]}...")  # Print first 200 characters of snippet
            print(f"   Apply Link: {job['apply_link']}")
        
        # Save the job listings to a CSV file
        save_to_csv(all_job_listings, job_title, location)
    else:
        print("No job listings found.")

if __name__ == "__main__":
    main()