from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def scrape_indeed(driver, job_title, location):
    url = f"https://www.indeed.com/jobs?q={job_title}&l={location}&fromage=14"
    driver.get(url)
    
    # Random delay between 2 and 5 seconds
    time.sleep(random.uniform(2, 5))
    
    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")
    
    # Wait for the page to load
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "job_seen_beacon")))
    except Exception as e:
        print(f"Timeout waiting for page to load: {e}")
        print("Page source:")
        print(driver.page_source)
        return []
    
    # Give the page a little more time to load dynamic content
    time.sleep(random.uniform(3, 7))
    
    job_listings = []
    job_cards = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
    print(f"\nNumber of job cards found: {len(job_cards)}")
    
    for card in job_cards:
        try:
            title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span[id^='jobTitle']").text
            company = card.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']").text
            location = card.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']").text
            
            details_element = card.find_element(By.CSS_SELECTOR, "div.css-9446fg ul")
            details = details_element.text if details_element else "No details available"
            
            job_listings.append({
                "title": title,
                "company": company,
                "location": location,
                "details": details
            })
        except Exception as e:
            print(f"Error processing job card: {e}")
    
    print(f"\nSuccessfully extracted {len(job_listings)} job listings")
    return job_listings

def main():
    job_title = "Data Analyst"
    location = "Florida"
    
    driver = setup_driver()
    
    try:
        print(f"\nSearching for {job_title} jobs in {location}...")
        job_listings = scrape_indeed(driver, job_title, location)
        
        if job_listings:
            print("\nJob Listings:")
            for i, job in enumerate(job_listings, 1):
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Details: {job['details'][:200]}...")  # Print first 200 characters of details
        else:
            print("No job listings found.")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()