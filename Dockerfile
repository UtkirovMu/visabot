# Railpack/Nixpacks o'rniga oddiy Docker build (Railway build vositasini yuklab olishga bog'liq emas)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Root bo'lmagan foydalanuvchi bilan ishlash (xavfsizlik)
RUN useradd --create-home --uid 10001 bot

# Tashqi paketlar yo'q — faqat bitta fayl
COPY bot.py .

USER bot

CMD ["python", "bot.py"]
