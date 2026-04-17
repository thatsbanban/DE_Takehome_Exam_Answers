import pandas as pd
import boto3
import os
from ftplib import FTP
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime


S3_BUCKET_NAME = "DE_results"
FTP_HOST = "ftp.dlptest.com"
FTP_USER = "dlpuser"
FTP_PASS = "rNrKYTX9g7z3RgJRmxWuGHbeu"
LOCAL_FILE = "all_quotes.csv"

def run_scraper():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service() 
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    scraped_quotes = []

    try:
        driver.get("https://quotes.toscrape.com/search.aspx")
        wait = WebDriverWait(driver, 15)

        author_elem = wait.until(EC.presence_of_element_located((By.ID, "author")))
        dropdown_author = Select(author_elem)
        authors = [option.text for option in dropdown_author.options if "--" not in option.text]

        for author in authors:
            print(f"Processing Author: {author}")
            dropdown_author = Select(driver.find_element(By.ID, "author"))
            dropdown_author.select_by_visible_text(author)
            
            wait.until(EC.presence_of_element_located((By.ID, "tag")))
            dropdown_tags = Select(driver.find_element(By.ID, "tag"))
            tags = [option.text for option in dropdown_tags.options if "--" not in option.text]

            for tag in tags:
                dropdown_tags = Select(driver.find_element(By.ID, "tag"))
                dropdown_tags.select_by_visible_text(tag)

                submit_button = driver.find_element(By.NAME, "submit_button")
                driver.execute_script("arguments[0].click();", submit_button)
            
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "content")))
                listed_quotes = driver.find_elements(By.CLASS_NAME, "quote")

                for q in listed_quotes:
                    scraped_quotes.append({
                        "Author": author,
                        "Tag": tag,
                        "Quote": q.find_element(By.CLASS_NAME, "content").text
                    })

        df = pd.DataFrame(scraped_quotes)
        df.to_csv(LOCAL_FILE, index=False, encoding="utf-8-sig")
        print(f"Scraping complete. File saved to {LOCAL_FILE}")
        return True

    except Exception as e:
        print(f"Error during scraping: {e}")
        return False
    finally:
        driver.quit()

def upload_to_s3():
    try:
        print("Uploading to S3...")
        s3 = boto3.client('s3')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        s3_key = f"scraped_data/{timestamp}_{LOCAL_FILE}"
        s3.upload_file(LOCAL_FILE, S3_BUCKET_NAME, s3_key)
        print(f"Uploaded to S3: {s3_key}")
    except Exception as e:
        print(f"S3 Upload failed: {e}")

def upload_to_ftp():
    try:
        print("Uploading to FTP...")
        with FTP(FTP_HOST) as ftp:
            ftp.login(user=FTP_USER, passwd=FTP_PASS)
            with open(LOCAL_FILE, 'rb') as f:
                ftp.storbinary(f"STOR {LOCAL_FILE}", f)
        print("FTP Upload successful.")
    except Exception as e:
        print(f"FTP Upload failed: {e}")

if __name__ == "__main__":
    if run_scraper():
        upload_to_s3()
        upload_to_ftp()
        if os.path.exists(LOCAL_FILE):
            os.remove(LOCAL_FILE)