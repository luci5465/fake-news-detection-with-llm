Fake news detection using LLMs 

نصب پکیج‌ها:
pip install -r requirements.txt


اجرای تک‌مرحله‌ای: 
python crawler/persian_crawler.py
python parser/content_cleaner.py
python index/index_builder.py
python index/inverted_index.py
python graph/graph_builder.py
python llm/embedder.py
python test/test_fake_news.py

crawler → clean → index → graph → llm → verdict
