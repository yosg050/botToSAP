from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    ES5_USERNAME: str
    ES5_PASSWORD: str
    ES5_BPSET: str = (
        "https://sapes5.sapdevcenter.com/sap/opu/odata/iwbep/GWSAMPLE_BASIC/BusinessPartnerSet"
    )
    SAP_CLIENT: str = "002"
    
    REQUEST_TIMEOUT: float = 15.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()