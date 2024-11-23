import unittest
import sqlite3
from unittest.mock import patch, MagicMock
import os
from wiki_crawler import init_db, save_link, is_link_saved, WikipediaParser, fetch_page, extract_links, crawl_links, process_url, set_db_name

class TestWikipediaCrawler(unittest.TestCase):

    def setUp(self):
        """Настройка базы данных для тестов."""
        set_db_name("test_links.db")  # Используем тестовую базу данных
        init_db()

    def tearDown(self):
        """Очистка базы данных после каждого теста."""
        if os.path.exists("test_links.db"):
            os.remove("test_links.db")

    def test_save_link(self):
        """Тест сохранения ссылки в базу данных."""
        link = "https://en.wikipedia.org/wiki/Python_(programming_language)"
        save_link(link)
        
        # Проверяем, что ссылка сохранена
        self.assertTrue(is_link_saved(link))

    def test_is_link_saved(self):
        """Тест проверки существования ссылки в базе данных."""
        link = "https://en.wikipedia.org/wiki/JavaScript"
        self.assertFalse(is_link_saved(link))
        
        # Сохраняем ссылку и проверяем снова
        save_link(link)
        self.assertTrue(is_link_saved(link))

    @patch('urllib.request.urlopen')
    def test_fetch_page_success(self, mock_urlopen):
        """Тест успешной загрузки страницы."""
        mock_urlopen.return_value.__enter__.return_value.read.return_value = b"<html><head></head><body><a href='/wiki/Python_(programming_language)'>Python</a></body></html>"

        url = "https://en.wikipedia.org/wiki/Programming_language"
        result = fetch_page(url)
        
        self.assertIn("Python", result)

    @patch('urllib.request.urlopen')
    def test_fetch_page_failure(self, mock_urlopen):
        """Тест неудачной загрузки страницы."""
        mock_urlopen.side_effect = Exception("Ошибка подключения")
        
        url = "https://en.wikipedia.org/wiki/Unknown"
        result = fetch_page(url)
        
        self.assertEqual(result, "")

    def test_extract_links(self):
        """Тест извлечения ссылок из HTML-страницы."""
        html_content = "<html><head></head><body><a href='/wiki/Python_(programming_language)'>Python</a></body></html>"
        parser = WikipediaParser()
        parser.feed(html_content)
        
        links = parser.get_links()
        
        self.assertEqual(len(links), 1)
        self.assertEqual(links, {"https://en.wikipedia.org/wiki/Python_(programming_language)"})

    @patch('wiki_crawler.extract_links')
    @patch('wiki_crawler.save_link')
    def test_process_url(self, mock_save_link, mock_extract_links):
        """Тест обработки URL и извлечения новых ссылок."""
        url = "https://en.wikipedia.org/wiki/Programming_language"
        mock_extract_links.return_value = {"https://en.wikipedia.org/wiki/Python_(programming_language)"}
        
        visited = set()
        next_to_visit = set()
        
        process_url(url, 1, visited, next_to_visit)
        
        # Проверяем, что ссылка была сохранена
        mock_save_link.assert_called_once_with(url)
        
        # Проверяем, что новая ссылка была добавлена в очередь
        self.assertIn("https://en.wikipedia.org/wiki/Python_(programming_language)", next_to_visit)

    @patch('wiki_crawler.process_url')
    def test_crawl_links(self, mock_process_url):
        """Тест обхода ссылок."""
        start_url = "https://en.wikipedia.org/wiki/Programming_language"
        crawl_links(start_url, depth=2)
        
        # Проверяем, что функция process_url была вызвана для начальной ссылки
        mock_process_url.assert_called_with(start_url, 1, set(), set())

if __name__ == '__main__':
    unittest.main()
