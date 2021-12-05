FROM alpine
ENV UWSGI_NCPUS "$UWSGI_NCPUS"
RUN mkdir /dist
WORKDIR /dist
RUN adduser -S www-data
RUN apk add --update --no-cache py3-flask py3-pip py3-pyzbar py3-exifread py3-pillow uwsgi-python3 py3-reportlab py3-qrcode && pip install --no-cache-dir whitenoise pylabels
ADD . /dist/
EXPOSE 8800
ENTRYPOINT ["/usr/sbin/uwsgi", "--ini", "uwsgi.conf"]
