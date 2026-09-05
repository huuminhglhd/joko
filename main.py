import os
import sys
import time
import random
import logging
import subprocess
import tkinter as tk
from pathlib import Path
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException


def copy_to_clipboard(text: str):
    """Copy string (including Emojis and non-BMP chars) to Windows clipboard."""
    try:
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
    except Exception:
        try:
            process = subprocess.Popen('clip', stdin=subprocess.PIPE, shell=True)
            process.communicate(input=text.encode('utf-16le'))
        except Exception:
            pass

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Define Base Paths using pathlib for OS cross-compatibility
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
EXCEL_PATH = DATA_DIR / "content_schedule.xlsx"
VIDEOS_DIR = BASE_DIR / "Videos"
PROFILE_DIR = BASE_DIR / "chrome_profile"


def setup_environment():
    """Ensure all required directories and a dummy Excel file exist if missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate a sample Excel file if it doesn't exist
    if not EXCEL_PATH.exists():
        sample_data = {
            "ID": [1, 2],
            "Caption": ["Check out my new video! #viral", "Automation test video 🚀 #python"],
            "Filename": ["video1.mp4", "video2.mp4"],
            "Status": ["Pending", "Pending"]
        }
        df_sample = pd.DataFrame(sample_data)
        df_sample.to_excel(EXCEL_PATH, index=False)
        logging.info(f"Created sample Excel file at: {EXCEL_PATH}")


def random_delay(min_sec=3, max_sec=7):
    """Pause execution for a random duration to simulate human actions."""
    delay = random.uniform(min_sec, max_sec)
    logging.info(f"Waiting for {delay:.2f} seconds...")
    time.sleep(delay)


def init_browser():
    """Initialize undetected-chromedriver with a persistent profile."""
    options = uc.ChromeOptions()
    
    # Browser optimizations & settings
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")

    profile_path = str(PROFILE_DIR.resolve())
    logging.info(f"Starting undetected Chrome driver with profile at: {profile_path}...")
    
    try:
        driver = uc.Chrome(
            options=options, 
            user_data_dir=profile_path,
            version_main=150,
            use_subprocess=True
        )
    except Exception as e:
        logging.warning(f"Version 150 init fallback: {e}")
        driver = uc.Chrome(
            options=options, 
            user_data_dir=profile_path,
            use_subprocess=True
        )
    return driver


def load_schedule():
    """Read and validate the Excel schedule file."""
    if not EXCEL_PATH.exists():
        logging.error(f"Excel file not found at {EXCEL_PATH}")
        return None

    try:
        df = pd.read_excel(EXCEL_PATH)
        required_cols = {"ID", "Caption", "Filename", "Status"}
        if not required_cols.issubset(df.columns):
            logging.error(f"Excel file missing required columns: {required_cols - set(df.columns)}")
            return None
        return df
    except Exception as e:
        logging.error(f"Error loading Excel file: {e}")
        return None


def upload_single_video(driver, video_path: Path, caption: str):
    """Automate the upload flow on TikTok Creator Studio."""
    upload_url = "https://www.tiktok.com/tiktokstudio/upload"
    
    # Only navigate if not already on the upload page or if on error page
    current_url = driver.current_url.lower()
    if "tiktokstudio/upload" not in current_url and "tiktok.com/upload" not in current_url:
        logging.info(f"Navigating to {upload_url}...")
        driver.get(upload_url)
        random_delay(3, 5)
    elif "403" in driver.title or "denied" in driver.page_source.lower():
        logging.info(f"403 detected, reloading {upload_url}...")
        driver.get(upload_url)
        random_delay(3, 5)

    wait = WebDriverWait(driver, 60)

    # Step 1: Wait for file input element (serves as page & login verification)
    logging.info("Locating file input element...")
    file_input = wait.until(
        EC.presence_of_element_located((By.XPATH, '//input[@type="file"]'))
    )

    # Step 2: Upload video file by providing absolute path
    logging.info(f"Uploading file: {video_path.name}")
    file_input.send_keys(str(video_path.resolve()))

    # Step 3: Wait for video upload processing to complete
    logging.info("Waiting for video upload to process...")
    
    # Wait until caption container / editor is present & ready
    caption_box = wait.until(
        EC.presence_of_element_located((
            By.XPATH,
            '//div[contains(@class, "DraftEditor-editorContainer")]//div[@contenteditable="true"] '
            '| //div[contains(@class, "caption-input")]//textarea '
            '| //div[@contenteditable="true"]'
        ))
    )
    random_delay(3, 5)

    # Step 4: Input Caption with automatic StaleElement retry handling
    logging.info(f"Filling caption: '{caption}'")
    caption_xpath = (
        '//div[contains(@class, "DraftEditor-editorContainer")]//div[@contenteditable="true"] '
        '| //div[contains(@class, "caption-input")]//textarea '
        '| //div[@contenteditable="true"]'
    )
    
    for attempt in range(3):
        try:
            # Re-locate caption box dynamically to avoid stale element reference
            caption_box = driver.find_element(By.XPATH, caption_xpath)

            # Dismiss any Joyride / onboarding overlay popups if present
            try:
                driver.execute_script("""
                    document.querySelectorAll('.react-joyride__overlay, .react-joyride__tooltip, [class*="joyride"]').forEach(el => el.remove());
                """)
            except Exception:
                pass

            driver.execute_script("arguments[0].focus(); arguments[0].click();", caption_box)
            random_delay(1, 2)

            # Clear pre-filled text if present (Ctrl+A -> Backspace)
            caption_box.send_keys(Keys.CONTROL + "a")
            caption_box.send_keys(Keys.BACKSPACE)
            random_delay(1, 2)

            # Insert caption with full Emoji support
            try:
                driver.execute_script("document.execCommand('insertText', false, arguments[0]);", caption)
            except Exception:
                pass

            copy_to_clipboard(caption)
            caption_box.send_keys(Keys.CONTROL + "v")
            break
        except Exception as e:
            logging.warning(f"Retrying caption input due to DOM re-render ({e}). Attempt {attempt + 1}/3")
            random_delay(2, 3)

    random_delay(3, 5)

    # Step 5: Wait for Post / Đăng button to be enabled (video fully processed)
    logging.info("Waiting for video processing to finish and Post button to be enabled...")
    post_xpath = (
        '//button[not(@disabled) and not(contains(@class, "disabled")) and '
        '(descendant-or-self::*[text()="Post" or text()="Đăng" or contains(text(), "Post") or contains(text(), "Đăng")])]'
    )
    
    # Wait up to 120s for video processing to complete
    wait_post = WebDriverWait(driver, 120)
    post_button = wait_post.until(
        EC.presence_of_element_located((By.XPATH, post_xpath))
    )

    # Scroll Post button into view and clean up any popups
    driver.execute_script("""
        document.querySelectorAll('.react-joyride__overlay, .react-joyride__tooltip').forEach(el => el.remove());
        arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
    """, post_button)
    random_delay(2, 3)

    logging.info("Clicking Post button...")
    try:
        post_button.click()
    except Exception:
        driver.execute_script("arguments[0].click();", post_button)

    # Step 6: Check for confirmation popups (e.g., "Post anyway" / "Vẫn đăng" or "Exit" modal)
    logging.info("Checking for confirmation popups (Copyright check / Post anyway / Exit modal)...")
    for _ in range(4):
        random_delay(2, 3)
        
        # 6a. Click "Post anyway" / "Vẫn đăng" / "Confirm" if copyright check modal appears
        try:
            confirm_xpath = (
                '//button[descendant-or-self::*[text()="Post anyway" or text()="Vẫn đăng" '
                'or text()="Confirm" or text()="Xác nhận" or contains(text(), "Post anyway") '
                'or contains(text(), "Vẫn đăng")]]'
            )
            confirm_buttons = driver.find_elements(By.XPATH, confirm_xpath)
            if confirm_buttons:
                logging.info("Secondary confirmation modal found ('Post anyway'). Clicking confirm...")
                driver.execute_script("arguments[0].click();", confirm_buttons[0])
        except Exception:
            pass

        # 6b. If "Are you sure you want to exit?" modal appears, click "Cancel" so upload is NOT cancelled!
        try:
            if "sure you want to exit" in driver.page_source.lower():
                exit_cancel_xpath = '//button[descendant-or-self::*[text()="Cancel" or contains(text(), "Cancel")]]'
                cancel_btn = driver.find_elements(By.XPATH, exit_cancel_xpath)
                if cancel_btn:
                    logging.info("'Are you sure you want to exit?' modal detected. Clicking 'Cancel' to continue posting...")
                    driver.execute_script("arguments[0].click();", cancel_btn[0])
        except Exception:
            pass

    # Step 7: Wait for final TikTok upload success indicator ("Upload another video" / "Manage your posts")
    logging.info("Waiting for final upload confirmation on TikTok...")
    wait_success = WebDriverWait(driver, 25)
    try:
        wait_success.until(
            EC.presence_of_element_located((
                By.XPATH,
                '//*[contains(text(), "Upload another video") or contains(text(), "Manage your posts") '
                'or contains(text(), "Tải lên video khác") or contains(text(), "Quản lý bài viết")]'
            ))
        )
        logging.info("Received official TikTok post success confirmation!")
    except Exception:
        logging.info("Waiting extra buffer time for network upload completion...")
        random_delay(12, 18)

    logging.info("Video post action completed successfully.")


def main():
    setup_environment()
    df = load_schedule()

    if df is None:
        logging.error("Exiting due to missing or invalid schedule file.")
        return

    # Filter rows with 'Pending' status (case-insensitive)
    pending_mask = df["Status"].astype(str).str.strip().str.lower() == "pending"
    pending_df = df[pending_mask]

    if pending_df.empty:
        logging.info("No videos with 'Pending' status found.")
        return

    logging.info(f"Found {len(pending_df)} pending video(s) to process.")

    driver = None
    try:
        driver = init_browser()
        
        # Initial login check
        driver.get("https://www.tiktok.com/tiktokstudio/upload")
        print("\n" + "=" * 65)
        print("ATTENTION: If you are running this for the first time or not logged in,")
        print("please complete manual login (QR code / Login form) in Chrome now.")
        print("Press ENTER in this terminal once logged in and ready to proceed.")
        print("=" * 65 + "\n")
        input("--> Press ENTER to start processing pending uploads: ")

        for idx, row in pending_df.iterrows():
            item_id = row["ID"]
            caption = str(row["Caption"]) if pd.notna(row["Caption"]) else ""
            filename = str(row["Filename"])
            video_path = VIDEOS_DIR / filename

            logging.info(f"\n--- [Processing Row ID: {item_id}] File: {filename} ---")

            # Check if physical file exists
            if not video_path.exists():
                logging.error(f"Video file missing: '{video_path}'. Skipping ID {item_id}.")
                continue

            try:
                # Execute upload workflow
                upload_single_video(driver, video_path, caption)

                # Update row status to 'Posted' and immediately persist to Excel
                df.at[idx, "Status"] = "Posted"
                df.to_excel(EXCEL_PATH, index=False)
                logging.info(f"Updated Status for ID {item_id} to 'Posted' in Excel.")

                # Wait between posts to mimic human activity
                random_delay(5, 10)

            except Exception as e:
                logging.error(f"Failed to upload ID {item_id} ({filename}): {e}", exc_info=False)
                logging.info("Skipping to next pending video...")
                continue

    except Exception as e:
        logging.critical(f"Critical execution error: {e}", exc_info=True)

    finally:
        if driver:
            logging.info("Closing browser...")
            try:
                driver.quit()
            except Exception:
                pass
        logging.info("Automation process finished.")


if __name__ == "__main__":
    main()
