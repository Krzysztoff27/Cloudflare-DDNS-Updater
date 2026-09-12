# Cloudflare-DDNS-Updater
This repo holds the source code for a simple containerized Python app that uses the Cloudflare API to dynamically update a given record.

Right now it supports automatic update of a selected A Cloudflare record with a public IP sourced from https://api.ipify.org/.

# Prerequisites
1. [Cloudflare API Token](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/) with at least a `DNS Write` permission.
2. Cloudflare `zone_id` and `record_id` that can be obtained using the commands below
```
curl -s https://api.cloudflare.com/client/v4/zones -H "Authorization: Bearer <CLOUDFLARE_API_TOKEN>" | jq .

curl -s https://api.cloudflare.com/client/v4/zones/<ZONE_ID>/dns_records -H "Authorization: Bearer <CLOUDFLARE_API_TOKEN>" | jq .
```

# Environmental variables
- LOG_LEVEL
Sets the desired log level verbosity - can be either INFO or DEBUG. By default it is set to INFO.
- CLOUDLFARE_API_TOKEN
- ZONE_ID
- RECORD_ID
- NAME
The domain name set in the A record, eg. subdomain.mydomain.com
- TTL
TTL parameter of the record. By default it is set to Auto.
- TYPE
Type of the record to update. Right now only A type is supported - setting any other type will not change any functionality.
- TIME_INTERVAL
How often should the Public IP address be fetched.

# Building a container
A pre-built version of the container is provided with every release through GitHub Container Registry.

However, you are free to build your own container locally by using the `build.sh` script included in the repository. 

# Running
The container is run using the provided `docker-compose.yaml` file using the command below
```
docker compose -f docker-compose.yaml --env-file .env up -d
```

# Usage
The container will automatically start to periodically update the provided record. You can see the logs using:
```
docker logs dynamic-ddns-updater -f
```
