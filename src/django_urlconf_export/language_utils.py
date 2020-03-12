def includes_country(language):
    language_parts = language.split("-")
    if len(language_parts) == 1:
        return False
    if len(language_parts) == 2:
        return True
    raise ValueError(f"Invalid language code {language}")


def get_without_country(language):
    if not includes_country(language):
        return language
    return language.split("-")[0]
