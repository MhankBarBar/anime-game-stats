from typing import List

import bs4
import genshin
import requests


class GetCodes:
    BASE_URL: str = "https://www.pockettactics.com/"

    GAME_CODES: dict = {
        "genshin": "genshin-impact",
        "hkrpg": "honkai-star-rail"
    }

    def get_codes(self, game: str = "genshin") -> List[str]:
        url = self._build_url(game)
        response = self._send_request(url)
        soup = self._parse_html(response)
        parsed_codes = self._extract_codes(soup, game)

        active_codes = [code.text.strip() for code in parsed_codes]
        return active_codes

    async def redeem_code(self, client: genshin.Client, code: str, game: genshin.Game = "genshin") -> None:
        try:
            file = f"files/redeemed_codes_{game}.txt"
            with open(file, "r") as f:
                codes = f.read().splitlines()
            if code not in codes:
                await client.redeem_code(code, game=game)
                with open(file, "a") as f:
                    f.write(f"{code}\n")
        except (genshin.RedemptionClaimed, genshin.RedemptionInvalid, genshin.RedemptionException):
            pass

    def _build_url(self, game: str) -> str:
        game_slug = self.GAME_CODES.get(game, "")
        if not game_slug:
            raise Exception(f"Game {game} is not supported")
        return f"{self.BASE_URL}{game_slug}/codes"

    def _send_request(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _parse_html(self, html: str) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(html, "html.parser")
        return soup.find("div", {"class": "entry-content"})

    def _extract_codes(self, soup: bs4.BeautifulSoup, game: str) -> List[bs4.element.Tag]:
        if game == "genshin":
            codes = soup.find_all("ul")[1].find_all("strong")
        else:
            codes = soup.find("ul").find_all("strong")
        return codes
