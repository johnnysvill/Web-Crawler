# Wikipedia Crawler CLI

Данный проект представляет собой CLI утилиту для рекурсивного обхода страниц Википедии и сбора уникальных ссылок на другие статьи. Программа сохраняет найденные ссылки в базе данных SQLite, и продолжает обрабатывать страницы до достижения глубины 6.

Для ускорения обработки ссылок и параллельной обработки нескольких страниц одновременно, программа использует многопоточность, которая реализована с использованием стандартной библиотеки threading. По умолчанию число потоков выставлено 50. При необходимости можно регулировать их количество, меняя параметр MAX_WORKERS = 50 (12-я строка) в файле wiki_crawler.py.

## Установка и использование
1. Для развертывания проекта клонируйте репозиторий:
```bash
git clone https://github.com/johnnysvill/Web-Crawler.git
cd Web-Crawler
```

2. Убедитесь, что установлен Python версии 3.10+:
```bash
python --version
```

3. Для запуска основного скрипта для обхода страниц используйте следующую команду:
```bash
python wiki_crawler.py "URL"
```
Вместо URL вставьте вашу ссылку на Википедию. Например:
```bash
python wiki_crawler.py "https://en.wikipedia.org/wiki/Web_crawler"
```

## Тесты
Программа покрыта специальными тестами, которые проверяют следующие аспекты работы программы:
1. Инициализация базы данных - проверка корректности создания базы данных и таблиц.
2. Сохранение и проверка ссылок в базе данных - тестирование того, что найденные ссылки правильно сохраняются в базе и что они уникальны.
3. Загрузка HTML-страниц - проверка корректности загрузки и обработки страниц.
4. Извлечение ссылок из HTML-кода - тестирование правильности извлечения всех ссылок из HTML-кода страницы.
5. Рекурсивный обход и сохранение ссылок - тестирование корректности рекурсивного обхода и сохранения ссылок до заданной глубины.

Для запуска тестов используйте следующую команду:
```bash
python -m unittest test_wiki_crawler.py
```

