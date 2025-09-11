# Build stage
FROM golang:1.21 AS builder

# Install required build tools
RUN apt-get update && apt-get install -y git

# Clone Traefik source
WORKDIR /go/src/github.com/traefik
RUN git clone --depth 1 --branch v3.0.4 https://github.com/traefik/traefik.git

# Build Traefik with plugins
WORKDIR /go/src/github.com/traefik/traefik

# Install required plugins
RUN go install github.com/traefik/plugindemo@latest
RUN go install github.com/traefik/plugins/...

# Build Traefik with plugins
RUN CGO_ENABLED=0 go build -o /traefik \
    -ldflags="-w -s -X 'github.com/traefik/traefik/v2/pkg/version.Version=v3.0.4'" \
    ./cmd/traefik

# Final stage
FROM traefik:v3.0.4

# Install required tools
RUN apk add --no-cache git build-base

# Copy the custom Traefik binary
COPY --from=builder /traefik /usr/local/bin/traefik

# Create plugins directory
RUN mkdir -p /plugins

# Copy plugin installation script
COPY install-plugins.sh /usr/local/bin/install-plugins.sh
RUN chmod +x /usr/local/bin/install-plugins.sh

# Install plugins
RUN /usr/local/bin/install-plugins.sh

# Set entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["traefik"]
