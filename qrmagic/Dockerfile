FROM alpine
RUN mkdir /dist
WORKDIR /dist
RUN adduser -S www-data
RUN apk add --update --no-cache py3-wheel py3-flask py3-pip py3-pyzbar py3-exifread py3-pillow py3-reportlab py3-tqdm uwsgi-python3 && pip install --no-cache-dir whitenoise pylabels qrcode
ADD . /dist/
ENV PORT 8800
EXPOSE $PORT
ENTRYPOINT ["/usr/sbin/uwsgi", "--ini", "uwsgi.conf"]
