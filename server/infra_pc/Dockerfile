FROM alpine:3.19

# Install dependencies
RUN apk add --no-cache \
    nginx \
    nginx-mod-rtmp \
    ca-certificates \
    gettext \
    openssl \
    pcre \
    curl

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/cache/nginx /tmp/hls /tmp/dash

# Expose ports
EXPOSE 1935 8080

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
