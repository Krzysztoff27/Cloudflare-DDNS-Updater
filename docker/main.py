import logging
import os
import requests
import json
import time
from cloudflare import Cloudflare
from typing import Literal, Annotated
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)
    

class EnvironmentalVariables(BaseModel):
    api_token: str
    zone_id: str
    record_id: str
    name: str
    ttl: int
    type: str
    time_interval: int
    
    @field_validator("api_token", "zone_id", "record_id", "name", "ttl", "type", "time_interval")
    @classmethod
    def prevent_none_values(cls, v):
        if not v:
            raise ValueError(f"Parameter {v} cannot be an empty string!")
        return v


def setup_logger() -> None:
    
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    if log_level not in ("INFO", "DEBUG"):
        logger.error(f"Invalid LOG_LEVEL '{log_level}'\n Allowed log levels are INFO and DEBUG. Defaulting to INFO.")
    
    logging.basicConfig(
        level=getattr(logging, log_level), 
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",)
    
    logger.info("Starting Cloudflare Dynamic DNS updater")
    

def get_environmental_variables() -> EnvironmentalVariables:
    
    try:
        
        logger.debug("Trying to read environmental variables")
        
        environmental_variables = EnvironmentalVariables(
            api_token=os.environ.get("CLOUDFLARE_API_TOKEN", ""),
            zone_id=os.environ.get("ZONE_ID", ""),
            record_id=os.environ.get("RECORD_ID", ""),
            name=os.environ.get("NAME", ""),
            ttl=int(os.environ.get("TTL", "1")),
            type='A',
            # type=os.environ.get("TYPE", ""),
            time_interval=int(os.environ.get("TIME_INTERVAL", ""))
        )
        
        logger.debug(f"""
                     \nCLOUDFLARE_API_TOKEN: {environmental_variables.api_token}
                     \nZONE_ID: {environmental_variables.zone_id}
                     \nRECORD_ID: {environmental_variables.record_id}
                     \nNAME: {environmental_variables.name}
                     \nTTL: {environmental_variables.ttl}
                     \nTYPE: {environmental_variables.type}
                     \nTIME_INTERVAL: {environmental_variables.time_interval}
                     """)
        
        return environmental_variables
        
    except Exception as e:
        raise Exception(f"Could not read environmental variables:\n{e}")


def get_public_ip() -> str:
    
    logger.debug("Sending a request to ipify to retrieve public IP address")
    
    ipify_request = requests.get("https://api.ipify.org/")
    
    if (ipify_request.status_code != 200):
        logger.debug(ipify_request.text)
        logger.debug(ipify_request.status_code)
        logger.error(f"Failed to fetch Public IP from https://api.ipify.org/.\nStatus code: {ipify_request.status_code}\nResponse:n\n{ipify_request.json()}")
        return ""
    else:
        logger.debug(f"Public IP: {ipify_request.text}")
        return ipify_request.text


def update_cloudflare_record(env: EnvironmentalVariables) -> None:
    
        logger.debug("Creatinf Cloudflare API client")
    
        public_ip = get_public_ip()
        
        client = Cloudflare(api_token = env.api_token)
        
        # Type ignores are required because of the inapropriate way in which client.dns.records.edit() tries to match given arguments to one of the numerous provided overloads
        record_update_response = client.dns.records.edit(
            zone_id=env.zone_id,
            dns_record_id=env.record_id,
            name=env.name,
            ttl=env.ttl,
            type=env.type, # type: ignore
            content=public_ip
            ) # type: ignore
        
        logger.debug(record_update_response)
        
        if record_update_response is not None:
             logger.info(f"Updated record {env.record_id} in zone {env.zone_id} with an address {public_ip}")
        else:
            logger.error(f"Failed to update record {env.record_id} in zone {env.zone_id} with an address {public_ip}: Cloudflare returned a request response of type None")
        

def schedule_record_update(env: EnvironmentalVariables) -> None:
    
    next_run = time.monotonic()
    logger.debug(f"Scheduler - next_run: {next_run}")
    
    while True:
        try:
            update_cloudflare_record(env)
        except Exception as e:
            logger.error(f"Failed to update record {env.record_id} in zone {env.zone_id}:\n{e}")
            
        next_run += int(env.time_interval)
        logger.debug(f"Scheduler - next_run += time_interval: {next_run}")
        
        time.sleep(next_run - time.monotonic())
        logger.debug(f"Scheduler - time.sleep(): {next_run - time.monotonic()}")


def main():
    
    setup_logger()
        
    schedule_record_update(get_environmental_variables())


if __name__ == '__main__':
    main()