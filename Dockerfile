FROM python:3.10-slim-bullseye

RUN pip install pmaw matplotlib

WORKDIR /app

CMD exec python3 commentface_counting.py > all_cdf_results.txt
