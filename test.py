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

def save_links(link: str) -> None:
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
