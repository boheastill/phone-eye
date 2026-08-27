FROM python:3.12-slim
# adb = Android platform-tools client (talks to the phone over Wi-Fi/USB).
RUN apt-get update \
 && apt-get install -y --no-install-recommends adb \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
# No ENV baked in on purpose: ANDROID_SERIAL / PHONE_EYE_VISION_URL /
# PHONE_EYE_VISION_TOOL / PHONE_EYE_SHOTS are optional and have sane code
# defaults — set them via the client config that spawns this container,
# otherwise an empty value here would override the default with "".
ENTRYPOINT ["python", "server.py"]
