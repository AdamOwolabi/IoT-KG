from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from util.folder_manager import create_folder
from util.content_saver import save_content, save_links
from util.media_downloader import ffmpeg_support
import json
import re
import threading
import requests

url = "https://www.amazon.com/Smart-Compatible-Assistant-Single-Pole-Certified/dp/B09JZ6W1BH/ref=sr_1_5?dib=eyJ2IjoiMSJ9.YyUdWlFCPDHj7fdR9KXAjgPXxKY87OcP1e_m7O_GJFEFwZx-9FtaiMjDOyIXbbewkED6bSEf7SlAbp97t-qKvpQFN-37BRXh0Ozgi-cM1NeaQXRk5AdWgSWfnmkWGvoWcsIqLUNfNKQO4L0j46Hswx_iySqHCFVmER7JU0h7WApptVAzBQSoP8fBbaZ_BDtSDMnRLE5ZiOg4UejwBKJAuq4U0lC1T8WIBeyJvBiROCZqaTm2Ywm7mEtNxHPj7GDhaOxmNpgddCMnm-wPzYveFbodxJelkM1dx7lV-B3XfdXorasTZ0B560jPfzm5hllKlIs_G8I_vulSNBNw9uecmnVUytn_jRynpXQAPd1p1-x8krhI14LGLYql2NA9X7VSKaZKvlMopcqRNzq6jRCC17c7rvwymbl8TUET056PZi2_sxiBSQdmO81Qrh-UrVZd.YtWOWkxWoG4rQ3k8FFahUql30YHM56CXzxuMtXkoqyg&dib_tag=se&keywords=smart+switches&qid=1737390483&sr=8-5"


#PARSE_LIST = ["$", "rating", "review", "recommendation", "deliver", "%", "quantity", "star", "ship", "return"]
TIME_PATTERN = r"^(?:[0-9]|[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$"
FORBIDDEN_NUMBERS = r"^\d+(\.\d+)?\+?$"
PRICE_PATTERN = r'[\$\€\£\₹]?\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
working_proxy = None
thread_lock = threading.Lock()
PROXIES = []
fake_useragent = UserAgent()

def download_proxy():
    """Fetches free HTTP proxies and saves them to a file."""
    try:
        response = requests.get("https://api.proxyscrape.com/v4/free-proxy-list/get?request=get_proxies&protocol=http&proxy_format=ipport&format=text&timeout=10000")
        response.raise_for_status()
        
        with open("proxies.txt", "w") as file:
            file.write(response.text.strip())  # Save proxies
        print("[✅] Proxies downloaded successfully.")

    except requests.exceptions.RequestException as e:
        print(f"[❌] Error downloading proxies: {e}")
    except IOError as e:
        print(f"[❌] Error writing to file: {e}")

def load_proxies():
    """Reads proxies from the file and formats them for requests/Selenium."""
    global PROXIES
    try:
        with open("proxies.txt", "r") as file:
            proxies = file.readlines()
        
        # Format proxies properly
        PROXIES = [f"http://{proxy.strip()}" for proxy in proxies if proxy.strip()]
        print(f"[📡] Loaded {len(PROXIES)} proxies.")

    except FileNotFoundError:
        print("[⚠] Proxy file not found. Downloading fresh proxies...")
        download_proxy()
        load_proxies()

def test_proxy(proxy):
    """Checks if a proxy is working by making a test request."""
    global working_proxy
    try:
        print(f"[🛰] Testing Proxy: {proxy}")
        response = requests.get("https://www.example.com", proxies={"http": proxy, "https": proxy}, timeout=5)
        
        if response.status_code == 200:
            with thread_lock:
                if working_proxy is None:  # First working proxy wins
                    working_proxy = proxy
                    print(f"[✅] Working Proxy Found: {proxy}")
    except requests.RequestException:
        pass  # Ignore failed proxy tests

def find_working_proxy():
    """Tests multiple proxies in parallel to find one that works."""
    global working_proxy
    threads = []

    for proxy in PROXIES:
        thread = threading.Thread(target=test_proxy, args=(proxy,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()  # Wait for all threads to finish

    return working_proxy

def local_access(url):
    print("[🌐] Checking URL without proxy")
    try:
        headers = {"User-Agent": fake_useragent.random}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            page_text = response.text.lower()
            if "captcha" in page_text or "verification" in page_text or "verify you are human" in page_text:
                print("[🤖] Bot Protected")
                return False
        elif response.status_code == 403:
            print("[❌] Local access forbidden (403).")
            return False
        elif response.status_code == 503:
            print("[❌] Local access unavailable (503).")
            return False
        elif response.status_code == 429:
            print("[❌] Local access rate limited (429).")
            return False
        elif response.status_code == 404:
            print("[❌] Local access not found (404).")
            return False
        else:
            print(f"[❌] Local access failed with status code: {response.status_code}")
            return False
        
    except requests.RequestException as e:
        print(f"[❌] Error during local access: {e}")
        return False

def scrape_website(url):

    # Selenium WebDriver Configuration
    options = Options()
    options.headless = True
    fake_useragent = UserAgent()
    options.add_argument(f'user-agent={fake_useragent.random}')
    options.add_argument("--headless")  # Run headless
    options.add_argument("--no-sandbox")  # Necessary for some restricted environments
    options.add_argument("--disable-dev-shm-usage")  # Overcome resource limitations
        
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    html = driver.page_source

    # Parse the HTML code with Beautiful Soup
    soup = BeautifulSoup(html, 'html.parser')
    
    # Create a dynamic folder based on the URL's hostname
    subfolder = create_folder(driver)
    
    # Extract and join the text content
    print('[✅] Extracting Text')
    text_elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'p'])
    #text_content = ' '.join([elem.get_text(strip=True) for elem in text_elements])
    text_content = '\n'.join([elem.get_text() for elem in text_elements])

    # Extract and serialize the text content of code elements
    print('[✅] Extracting Code')
    code_elements = soup.find_all('code')
    code_content = json.dumps([elem.get_text(strip=True) for elem in code_elements])

    # Extract the src attributes of video elements
    print('[✅] Extracting Images')
    image_elements = soup.find_all('img')
    image_content = []
    for image in image_elements:
        image_src = image.get('src')
        if image_src:
            image_content.append(image_src)
        source = image.find('source')
        for source in image.find_all('source'):
            src = source.get('src')
            if src:
                image_content.append(src)

    # Extract and download the video links
    print('[✅] Extracting Video')
    video_elements = soup.find_all('video')
    video_links = []
    video_content = []

    for i, video in enumerate(video_elements):
        src = video.get('src')
        if src:
            full_video_url = urljoin(url, src)
            video_links.append(full_video_url)
            video_content.append(ffmpeg_support(full_video_url, subfolder['video'], 'video', index=i))
        source = video.find('source')
        for source in video.find_all('source'):
            src = source.get('src')
            if src:
                full_video_url = urljoin(url, src)
                video_links.append(full_video_url)
                video_content.append(ffmpeg_support(full_video_url, subfolder['video'], 'video', index=i))
    # Filter out any empty transcriptions and join the remaining ones into a single string.
    video_content = " ".join([transcription for transcription in video_content if transcription.strip()])

    print('[💆‍♂️] Video Content Baby: ', video_content)

    return text_content, image_content, code_content, video_content

def preprocess(text_content):
    parsed_lines = []
    clean_lines = []
    no_duplicates = []

    # removing the duplicates
    for line in text_content.split("\n"):
        no_duplicates.append(line.strip())

    no_duplicates = list(set(no_duplicates))

    for line in no_duplicates:
        new_line = []
        for word in line.split():

            """if not bool(re.match(PRICE_PATTERN, word)):
                new_line.append(word)"""

            # removes prices and percentages
            if not word.startswith("$") and not word.endswith("%") and not bool(re.match(TIME_PATTERN, word)):
                new_line.append(word)

        parsed_lines.append(" ".join(new_line))

    for line in parsed_lines:
        
        # parsed out any lines with less than or equal to 2 words
        if len(line.split()) > 2:
            clean_lines.append(line)
    
    return "\n".join(clean_lines)



    """for line in no_duplicates:
        parse = False

        # invalid if any of the key words are in the line of text
        for item in PARSE_LIST:
            if item in line or item.capitalize() in line or item.upper() in line:
                parse = True
                break

        # invalid if its a rating
        if "out of" in line and "stars" in line:
            parse = True

        if line.isdigit() or line.isnumeric() or line.isdecimal():
            parse = True
        
        for item in line.split():
            # invalid if it shows something in time format
            if bool(re.match(TIME_PATTERN, item)):
                parse = True
                break

        if re.match(FORBIDDEN_NUMBERS, line):
            parse = True
        
        if parse == False:
            clean_lines.append(line)"""

    #return "\n".join(no_duplicates)


def numTokens(text_content):
    num_tokens = 0

    for line in text_content.split("\n"):
        num_tokens += len(line)
    
    return num_tokens
