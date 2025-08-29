import yaml

def get_config() -> dict:
    with open('app_config/config.yaml', "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def set_config(config: dict) -> bool:
    with open('app_config/config.yaml', "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
    return True

CONFIG = get_config()

