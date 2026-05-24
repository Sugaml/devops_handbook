FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 go build -o /app .

FROM alpine:3.20
RUN apk add --no-cache ca-certificates
COPY --from=builder /app /usr/local/bin/app
EXPOSE 8080
USER nobody
ENTRYPOINT ["/usr/local/bin/app"]
