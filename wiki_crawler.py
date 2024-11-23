import sqlite3
import urllib.request
import urllib.parse
import logging
from html.parser import HTMLParser
from typing import Set, List
from concurrent.futures import ThreadPoolExecutor

# Константы
WIKIPEDIA_BASE_URL = "https://en.wikipedia.org"
DB_NAME = "links.db"
MAX_WORKERS = 50  # Максимальное количество потоков

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def set_db_name(db_name: str) -> None:
    """Устанавливает имя базы данных."""
    global DB_NAME
    DB_NAME = db_name

def init_db() -> None:
    """Создаёт базу данных и таблицу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE
            )
        """)
        conn.commit()

def save_link(link: str) -> None:
    """Сохраняет уникальную ссылку в базу данных."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO links (url) VALUES (?)", (link,))
        conn.commit()

def is_link_saved(link: str) -> bool:
    """Проверяет, сохранена ли ссылка в базе данных."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM links WHERE url = ?", (link,))
        return cursor.fetchone() is not None

class WikipediaParser(HTMLParser):
    """HTML-парсер для извлечения ссылок."""
    def __init__(self) -> None:
        super().__init__()
        self.found_links: Set[str] = set()

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        if tag == "a":
            for attr_name, attr_value in attrs:
                if attr_name == "href" and attr_value and attr_value.startswith("/wiki/") and ":" not in attr_value:
                    self.found_links.add(urllib.parse.urljoin(WIKIPEDIA_BASE_URL, attr_value))

    def get_links(self) -> Set[str]:
        return self.found_links

def fetch_page(url: str) -> str:
    """Загружает HTML-страницу с таймаутом."""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        logger.error(f"Ошибка загрузки страницы {url}: {e}")
        return ""

def extract_links(url: str) -> Set[str]:
    """Извлекает ссылки из HTML-страницы."""
    html_content = fetch_page(url)
    if not html_content:
        return set()
    
    parser = WikipediaParser()
    parser.feed(html_content)
    return parser.get_links()

def save_links_batch(links: Set[str]) -> None:
    """Сохраняет ссылки пакетами."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.executemany("INSERT OR IGNORE INTO links (url) VALUES (?)", ((link,) for link in links))
        conn.commit()

def crawl_links(start_url: str, depth: int = 6) -> None:
    """Рекурсивно собирает ссылки с параллельной обработкой и логированием."""
    visited = set()
    to_visit = {start_url}
    
    for current_depth in range(depth):
        logger.info(f"Глубина {current_depth + 1}/{depth}")
        next_to_visit = set()
        futures = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for url in to_visit:
                if url not in visited and not is_link_saved(url):
                    logger.info(f"Глубина {current_depth + 1}: Обработка: {url}")
                    futures.append(executor.submit(process_url, url, current_depth + 1, visited, next_to_visit))
            
            # Ожидаем завершения всех задач
            for future in futures:
                future.result()

        to_visit = next_to_visit

def process_url(url: str, depth: int, visited: Set[str], next_to_visit: Set[str]) -> None:
    """Обрабатывает URL: загружает его, сохраняет и извлекает новые ссылки."""
    if url in visited:
        return
    
    visited.add(url)
    save_link(url)
    logger.info(f"Глубина {depth}: Сохранена ссылка: {url}")
    
    links = extract_links(url)
    next_to_visit.update(links - visited)
    logger.info(f"Глубина {depth}: Найдено {len(links)} новых ссылок на {url}")

def main() -> None:
    import sys
    if len(sys.argv) != 2:
        logger.error("Использование: python script.py <ссылка_на_статью>")
        sys.exit(1)

    start_url = sys.argv[1]
    init_db()
    logger.info(f"Начало обработки статьи: {start_url}")
    crawl_links(start_url)
    logger.info("Обработка завершена.")

if __name__ == "__main__":
    main()

