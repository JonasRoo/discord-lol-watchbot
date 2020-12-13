def _convert_champ_name(name: str) -> str:
    return "".join([c for c in name if c.isalpha()]).lower()


def is_valid_champ_name(name: str) -> bool:
    if not name.strip() or not any([c.isalpha() for c in name]):
        return False

    return True