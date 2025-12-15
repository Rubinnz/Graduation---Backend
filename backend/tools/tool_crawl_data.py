import time, random, os, re, threading, queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pymongo.errors import BulkWriteError
from backend.db.mongo_client import db

raw = db["raw_tweets"]
raw.create_index([("query", 1), ("url", 1)], unique=True)

LOGS = []
def log(x):
    LOGS.append(str(x))
    print(x)

QUERIES = [
# "Vietnam travel experience","Vietnam trip review","Visiting Vietnam experience","Vietnam tourism review","Vietnam vacation experience","Backpacking Vietnam experience",
# "My Vietnam travel experience","My trip to Vietnam review","My first time in Vietnam",
# "When I visited Vietnam","During my Vietnam trip","I traveled to Vietnam","I went to Vietnam","I spent time in Vietnam","My time in Vietnam",
# "Vietnam made me feel","I felt in Vietnam","My feelings about Vietnam","Vietnam surprised me","Vietnam shocked me","Vietnam impressed me","Vietnam changed my mind",
# "Vietnam exceeded my expectations","I fell in love with Vietnam","Vietnam was emotional","Vietnam touched my heart","Vietnam made me happy","Vietnam made me uncomfortable","Vietnam made me nervous",

# "Vietnam is beautiful","Vietnam is amazing","Vietnam is underrated","Vietnam is unforgettable",
# "Vietnam is worth visiting","Things I loved about Vietnam","Best experience in Vietnam","My favorite part of Vietnam",
# "Why I loved Vietnam","Vietnam hospitality experience","Worst experience in Vietnam" ,"Things I hated about Vietnam",
# "Vietnam disappointed me","Vietnam travel problems","Vietnam travel issues","Vietnam travel scam",
# "Bad experience traveling Vietnam","Vietnam traffic nightmare","Vietnam food poisoning","Vietnam travel regret",
# "Hanoi travel experience","Hanoi Old Quarter experience","Crossing the street in Hanoi","Hanoi street food experience",
# "Hanoi nightlife experience", "Ho Chi Minh City travel experience","Saigon traffic experience","Saigon nightlife experience",
# "Bui Vien experience","Saigon street food","Da Nang travel experience","Da Nang beach experience","Da Nang food experience",

# "Hoi An travel experience","Hoi An old town experience","Hoi An night market",
# "Sapa travel experience","Sapa homestay experience","Sapa trekking experience",
# "Ha Giang Loop experience","Ha Giang motorbike trip","Ha Giang road experience",

# "Halong Bay cruise experience","Halong Bay tour review",
# "Ninh Binh travel experience","Ninh Binh boat ride",
# "Phu Quoc travel experience","Phu Quoc beach experience",

"Vietnam street food experience","Eating street food in Vietnam","Vietnam night market experience","Vietnam coffee culture experience",
"Vietnam sleeper bus experience","Vietnam train travel experience","Vietnam airport experience","Vietnam hotel experience","Vietnam Airbnb experience",
# "Vietnam motorbike experience","Riding a motorbike in Vietnam","Vietnam grab experience","Vietnam transportation experience",

# "Planning a Vietnam trip","Should I travel to Vietnam","Is Vietnam worth it","Vietnam travel advice","Vietnam travel tips",
# "Things to know before Vietnam","Mistakes traveling Vietnam","What surprised me in Vietnam","What shocked me in Vietnam"
]


PROFILES = [
    {"port": 9222, "dir": r"C:\ChromeScraper"},
    {"port": 9223, "dir": r"C:\ChromeScraper1"},
    {"port": 9224, "dir": r"C:\ChromeScraper2"},
    {"port": 9225, "dir": r"C:\ChromeScraper3"},
]

task_queue = queue.Queue()

LIMIT_PER_QUERY = int(os.getenv("CRAWL_LIMIT_PER_QUERY", 200))
STOP_AFTER_NO_NEW = int(os.getenv("CRAWL_STOP_AFTER_NO_NEW", 5))
PAUSE_LIMIT = int(os.getenv("CRAWL_PAUSE_LIMIT", 30))
HUMAN_PAUSE_PROB = float(os.getenv("CRAWL_HUMAN_PAUSE_PROB", 0.15))
HUMAN_PAUSE_MIN = float(os.getenv("CRAWL_HUMAN_PAUSE_MIN", 2))
HUMAN_PAUSE_MAX = float(os.getenv("CRAWL_HUMAN_PAUSE_MAX", 6))
SHORT_MOVE_PROB = float(os.getenv("CRAWL_SHORT_MOVE_PROB", 0.2))
SCROLL_SLEEP_MIN = float(os.getenv("CRAWL_SCROLL_SLEEP_MIN", 0.6))
SCROLL_SLEEP_MAX = float(os.getenv("CRAWL_SCROLL_SLEEP_MAX", 1.4))
BETWEEN_QUERY_SLEEP_MIN = float(os.getenv("CRAWL_BETWEEN_QUERY_SLEEP_MIN", 4))
BETWEEN_QUERY_SLEEP_MAX = float(os.getenv("CRAWL_BETWEEN_QUERY_SLEEP_MAX", 9))

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
]

VIET_PATTERN = re.compile(r"[ăâđêôơưĂÂĐÊÔƠƯ]")
def lang_ok(t):
    return not VIET_PATTERN.search(t)

def spam_retry(driver):
    for _ in range(random.randint(2, 4)):
        try:
            driver.find_element(By.XPATH, "//span[text()='Retry']/ancestor::button").click()
            time.sleep(random.uniform(4, 8))
            if "Something went wrong" not in driver.page_source:
                return True
        except:
            break
    return False

def handle_block(driver, level):
    time.sleep(random.uniform(35 + level * 5, 60 + level * 8))
    if spam_retry(driver):
        return max(1, level * 0.65)
    return None

def fake_human_behavior(driver):
    if random.random() < HUMAN_PAUSE_PROB:
        time.sleep(random.uniform(HUMAN_PAUSE_MIN, HUMAN_PAUSE_MAX))
        return True
    if random.random() < SHORT_MOVE_PROB:
        try:
            ActionChains(driver).move_by_offset(
                random.randint(-20, 20), random.randint(-20, 20)
            ).perform()
        except MoveTargetOutOfBoundsException:
            pass
    if random.random() < 0.4:
        driver.execute_script(f"window.scrollBy(0,{random.randint(10,60)});")
    return False

def fake_scroll(driver, level):
    r = random.random()
    if r < 0.60:
        driver.execute_script(f"window.scrollBy(0,{random.randint(900,2000)});")
    elif r < 0.82:
        driver.execute_script(f"window.scrollBy(0,-{random.randint(250,700)});")
    else:
        d = random.randint(1600,3000)
        u = random.randint(200,500)
        driver.execute_script(f"window.scrollBy(0,{d});")
        time.sleep(random.uniform(0.15,0.35))
        driver.execute_script(f"window.scrollBy(0,-{u});")
    paused = fake_human_behavior(driver)
    time.sleep(random.uniform(SCROLL_SLEEP_MIN, SCROLL_SLEEP_MAX))
    return paused

def setup_driver(profile):
    os.makedirs(profile["dir"], exist_ok=True)
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1200,900")
    options.add_argument(f"--user-data-dir={profile['dir']}")
    options.add_argument(f"user-agent={random.choice(UA_LIST)}")
    service = Service(ChromeDriverManager().install(), port=profile["port"])
    return webdriver.Chrome(service=service, options=options)

def open_search(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )
    except:
        time.sleep(5)

def crawl_query(driver, QUERY):
    seen = set()
    url = f"https://x.com/search?q={QUERY.replace(' ','%20')}&src=typed_query"
    open_search(driver, url)
    count = raw.count_documents({"query": QUERY})
    no_new = 0
    level = 1.0
    pause_count = 0
    while count < LIMIT_PER_QUERY:
        try:
            html = driver.page_source
        except:
            open_search(driver, url)
            continue
        if "Something went wrong" in html or "Rate limit exceeded" in html:
            new_level = handle_block(driver, level)
            if new_level is None:
                log(f"[BLOCKED] {QUERY}")
                return False
            level = new_level
            fake_scroll(driver, level)
            continue
        try:
            tweets = driver.find_elements(By.CSS_SELECTOR, "article")
        except:
            tweets = []
        if not tweets:
            no_new += 1
            if no_new >= STOP_AFTER_NO_NEW:
                break
            time.sleep(4)
            continue
        before = count
        batch = []
        for t in tweets:
            try:
                text = t.find_element(By.CSS_SELECTOR, "div[data-testid='tweetText']").text.strip()
                href = t.find_element(By.CSS_SELECTOR, "a[href*='/status/']").get_attribute("href")
                url_final = "https://x.com" + href if href.startswith("/") else href
            except:
                continue
            if url_final in seen or not lang_ok(text):
                continue
            seen.add(url_final)
            try:
                ts = t.find_element(By.TAG_NAME, "time").get_attribute("datetime")
            except:
                ts = None
            try:
                user = t.find_element(By.CSS_SELECTOR, "div[data-testid='User-Name']").text.strip()
            except:
                user = None
            batch.append({
                "query": QUERY,
                "tweet": text,
                "username": user,
                "time": ts,
                "url": url_final
            })
        if batch:
            try:
                result = raw.insert_many(batch, ordered=False)
                inserted = len(result.inserted_ids)
            except BulkWriteError as e:
                inserted = e.details.get("nInserted", 0)
            count += inserted
            log(f"[{QUERY}] {count}/{LIMIT_PER_QUERY}")
        if count == before:
            no_new += 1
            if no_new >= STOP_AFTER_NO_NEW:
                break
        else:
            no_new = 0
        if fake_scroll(driver, level):
            pause_count += 1
            if pause_count >= PAUSE_LIMIT:
                break
        level = max(1, level * 0.87)
    return True

def worker_thread(profile):
    driver = setup_driver(profile)
    try:
        while True:
            try:
                q = task_queue.get_nowait()
            except queue.Empty:
                break
            log(f"[THREAD {profile['port']}] START {q}")
            ok = crawl_query(driver, q)
            if not ok:
                log(f"[THREAD {profile['port']}] SKIP {q}")
                continue
            log(f"[THREAD {profile['port']}] DONE {q}")
            time.sleep(random.uniform(BETWEEN_QUERY_SLEEP_MIN, BETWEEN_QUERY_SLEEP_MAX))
    finally:
        driver.quit()

def crawl_all():
    LOGS.clear()
    while not task_queue.empty():
        task_queue.get()
    for q in QUERIES:
        task_queue.put(q)
    threads = []
    for profile in PROFILES:
        t = threading.Thread(target=worker_thread, args=(profile,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    log("All threads finished.")
    return LOGS

def crawl_data():
    return crawl_all()

if __name__ == "__main__":
    crawl_all()
