def Main() -> None:
    from steam_parser import SteamParser

    steam_hentai: SteamParser = SteamParser()
    steam_hentai.set_url("https://store.steampowered.com/search")
    steam_hentai.parsing()


if __name__ == "__main__":
    Main()
