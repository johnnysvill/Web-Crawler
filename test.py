import sqlite3
import urlib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

def init_db():
    """Создает базу данных и таблицу для хранения данных."""
    with sqlite3.connect("links.db") as conn:
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
    with sqlite3.connect("links.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO links (url) VALUES (?)", (link,))
        conn.commit()

def is_link_saved(link: str) -> bool:
    """Проверяет, сохранена ли ссылка в базе данных."""
    with sqlite3.connect("links.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM links WHERE url = ?", (link,))
        return cursor.fetchone() is not None

def fetch_page(url: str) -> str:
    """Загружает HTML-страницу с таймаутом."""
    try:
        with urlib.request.urlopen(url, timeout=5) as response:
              return response.read().decode("utf-8")
    except Exception as e:
        print(f"Ошибка загрузки страницы {url}: {e}")
        return ""

class WikipediaParser(HTMLParser):
    """Парсер для извлечения ссылок из HTML-кода страницы Википедии."""

    def __init__(self) -> None:
        super().__init__()
        self.found_links = set()

    def handle_starttag(self, tag: str, attrs: list) -> None:
         """Обрабатывает каждый тег <a>, извлекает ссылку, если она начинается с /wiki/."""
         if tag == "a":
             for attr_name, attr_value in attrs:
                 if attr_name == "href" and attr_value and attr_value.startswith("/wiki/"):
                     self.found_links.add(urljoin("https://en.wikipedia.org", attr_value))

    def get_links(self) -> set:
        """Возвращает все найденные ссылки."""
        return self.found_links

def extract_links(url:str) -> Set[str]:
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
        cursor.executemany("INSERT OR IGNORE INTO links (url) VALUES (?)", ((links,) for link in links))
        conn.commit()

def crawl_links(start_url: str, depth: int = 6) -> None:
    """Рекурсивно собирает ссылки с параллельной обработкой и логированием."""
    visited = set()
    to_visit = {start_url}

    for current_depth in range(depth):
        logger.info(f"Глубина {current_depth + 1}/{depth}")
        next_to_visit = set()
        futures  = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for url in to_visit:
                if url not in visited and not is_link_saved(url):
                    logger.info(f"Глубина {current_depth + 1): Обработка: {url}")
                    futures.append(executor.submit(process_url, url, current_depth + 1, visited, next_to_visit))

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
    logger.info(f"Глубина {depth}: Найдено {len{links}} новых ссылок на {url}")

def main() -> None:
    import sys
    if len(sys.argv) != 2:
        logger.error("Использование python script.py <ссылка_на_статью>")
        sys.exit(1)

    start_url = sys.argv[1]
    init_db()
    logger.info(f"Начало обработки статьи: {start_url}")
    crawl_links(start_url)
    logger.info("Обработка завершена.")

if __name__=="__main__":
    main()
