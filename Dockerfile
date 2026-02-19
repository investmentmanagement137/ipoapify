FROM apify/actor-python-playwright:3.11

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .actor/ ./.actor/

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app/src"

CMD ["python3", "-m", "src.main"]
