#!/usr/bin/env python3
"""
Use Selenium to get all page names from Coppermind, then use Special:Export to download
"""

import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


def setup_driver():
    """Setup Chrome driver with options to avoid detection"""
    chrome_options = Options()

    # Uncomment to run headless (no browser window)
    # chrome_options.add_argument('--headless')

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # User agent
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)

    # Hide webdriver property
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


def get_all_pages_selenium():
    """Use Selenium to navigate through Special:AllPages and collect all page titles"""
    driver = setup_driver()
    all_pages = []

    try:
        base_url = "https://coppermind.net/wiki/Special:AllPages"

        print("Opening Coppermind wiki...")
        driver.get(base_url)

        # Wait for Cloudflare check to complete
        print("Waiting for Cloudflare check...")
        time.sleep(5)

        # Check if we got through
        if "Just a moment" in driver.page_source:
            print("Still on Cloudflare challenge page, waiting longer...")
            time.sleep(10)

        print("Starting to collect page names...\n")

        page_num = 1
        while True:
            print(f"Processing page {page_num} of Special:AllPages...")

            # Wait for the page list to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "mw-allpages-body"))
                )
            except:
                print(
                    "Could not find page list - might be blocked or page structure changed"
                )
                break

            # Find all page links in the current view
            page_links = driver.find_elements(
                By.CSS_SELECTOR, ".mw-allpages-body ul li a"
            )

            if not page_links:
                print("No page links found")
                break

            # Extract page titles
            batch_titles = [link.text for link in page_links if link.text]
            all_pages.extend(batch_titles)
            print(f"  Found {len(batch_titles)} pages (total: {len(all_pages)})")

            # Look for "Next page" link - try multiple selectors
            try:
                # Try different ways to find the next link
                next_link = None

                # Method 1: Link text
                try:
                    next_link = driver.find_element(By.LINK_TEXT, "Next page")
                except:
                    pass

                # Method 2: Partial link text
                if not next_link:
                    try:
                        next_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Next")
                    except:
                        pass

                if next_link:
                    print("  Clicking next page...")
                    next_link.click()
                    time.sleep(3)  # Increased wait time
                    page_num += 1
                else:
                    print("\nNo more pages - reached the end!")
                    break

            except Exception as e:
                print(f"\nError finding next page: {e}")
                print("Reached the end or encountered an error")
                break

        print(f"\n✓ Total pages collected: {len(all_pages)}")
        return all_pages

    except Exception as e:
        print(f"Error during scraping: {e}")
        return all_pages

    finally:
        driver.quit()


def export_via_special_export(page_titles):
    """Use Selenium to submit all pages via Special:Export and download XML"""
    driver = setup_driver()

    try:
        export_url = "https://coppermind.net/wiki/Special:Export"

        print("\n" + "=" * 60)
        print("Exporting pages via Special:Export...")
        print("=" * 60)

        driver.get(export_url)

        # Wait for Cloudflare
        print("Waiting for page to load...")
        time.sleep(5)

        # Prepare page list (newline separated)
        pages_text = "\n".join(page_titles)

        print(f"Adding {len(page_titles)} pages to export form...")

        textarea = driver.find_element(By.ID, "mw-input-pages")
        actions = ActionChains(driver)
        actions.move_to_element(textarea).click().send_keys(pages_text).perform()

        # Click export button
        export_button = driver.find_element(
            By.CSS_SELECTOR, "button[type='submit'][value='Export']"
        )
        export_button.click()

        # Wait for download to start (Chrome will download automatically)
        print("\nWaiting for download to complete...")
        print("The file should download to your browser's default download folder")
        print("Look for a file like 'coppermind.net-*.xml'")

        # Keep browser open for a bit to ensure download completes
        time.sleep(30)

        print("\n✓ Export submitted successfully!")
        print("Check your Downloads folder for the XML file")
        return True

    except Exception as e:
        print(f"Error during export: {e}")
        return False

    finally:
        driver.quit()


def save_page_list(page_titles, filename="page_list.txt"):
    """Save page titles to a text file as backup"""
    output_path = Path("./data") / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(page_titles))

    print(f"\n✓ Saved page list to {output_path}")
    print("You can use this file to manually paste into Special:Export if needed")


def main():
    print("=" * 60)
    print("Coppermind Wiki Export with Selenium")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Use Selenium to get all page names from Special:AllPages")
    print("2. Use Special:Export to download all pages as XML")
    print("=" * 60)

    # Step 1: Get all page names
    print("\nStep 1: Collecting all page names...")
    page_titles = get_all_pages_selenium()

    if not page_titles:
        print("\n❌ Failed to collect page names")
        return

    # Save as backup
    save_page_list(page_titles)

    # Step 2: Export via Special:Export
    print("\nStep 2: Exporting all pages...")
    user_input = input("\nProceed with export? This will open a browser. (y/n): ")

    if user_input.lower() == "y":
        success = export_via_special_export(page_titles)

        if success:
            print("\n" + "=" * 60)
            print("Export complete!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Find the downloaded XML file in your Downloads folder")
            print("2. Move it to backend/data/xml_exports/")
            print("3. Run the XML ingestion script to load into vector DB")
        else:
            print("\n❌ Export failed")
            print("You can manually export using the saved page list:")
            print("1. Open https://coppermind.net/wiki/Special:Export")
            print("2. Copy contents from data/page_list.txt")
            print("3. Paste into the text box and click Export")
    else:
        print("\nSkipped export. Use data/page_list.txt to manually export later.")


if __name__ == "__main__":
    main()
