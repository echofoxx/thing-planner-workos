FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY assets /usr/share/nginx/html/assets
COPY data /usr/share/nginx/html/data
COPY docs /usr/share/nginx/html/docs
COPY VERSION.txt /usr/share/nginx/html/VERSION.txt
EXPOSE 80
