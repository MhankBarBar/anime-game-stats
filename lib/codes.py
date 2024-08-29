from time import sleep
from typing import List

import bs4
import genshin
import requests


def _get_file_path(game: genshin.Game) -> str:
    match game:
        case genshin.Game.GENSHIN:
            return "files/redeemed_genshin_codes.txt"
        case genshin.Game.STARRAIL:
            return "files/redeemed_starrail_codes.txt"
        case genshin.Game.ZZZ:
            return "files/redeemed_zzz_codes.txt"


class GetCodes:
    HSR_URL: str = "https://www.eurogamer.net/honkai-star-rail-codes-livestream-active-working-how-to-redeem-9321"
    GENSHIN_URL: str = "https://www.eurogamer.net/genshin-impact-codes-livestream-active-working-how-to-redeem-9026"
    ZZZ_URL: str = "https://www.eurogamer.net/zenless-zone-zero-codes-how-to-redeem"
    urls = {
        genshin.Game.GENSHIN: GENSHIN_URL,
        genshin.Game.STARRAIL: HSR_URL,
        genshin.Game.ZZZ: ZZZ_URL
    }
    titles = {
        genshin.Game.STARRAIL: "honkai star rail codes",
        genshin.Game.GENSHIN: "genshin impact codes",
        genshin.Game.ZZZ: "zenless zone zero codes"
    }

    def get_codes(self, game: genshin.Game = genshin.Game.GENSHIN) -> List[str]:
        url = self._build_url(game)
        response = self._send_request(url)
        soup = self._parse_html(response)
        codes = self._extract_codes(soup, game)

        active_codes = [code for code in codes]

        return active_codes

    def _check_codes(self, codes: List[str], game: genshin.Game = genshin.Game.GENSHIN) -> List[str]:
        file = _get_file_path(game)
        with open(file, "r") as f:
            codes_redeemed = f.read().splitlines()
        return [x for x in codes if x not in codes_redeemed]

    async def redeem_codes(
            self, client: genshin.Client, game: genshin.Game = genshin.Game.GENSHIN
    ) -> None:
        codes = self.get_codes(game)
        active_codes = self._check_codes(codes, game)
        file = _get_file_path(game)
        for code in active_codes:
            try:
                await client.redeem_code(code, game=game)
            except (genshin.RedemptionClaimed, genshin.RedemptionInvalid, genshin.GenshinException,
                    genshin.RedemptionException, genshin.InvalidCookies):
                pass
            finally:
                with open(file, "a") as f:
                    f.write(f"{code}\n")
            sleep(6)

    def _build_url(self, game: genshin.Game) -> str:
        return self.urls[game]

    def _send_request(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _parse_html(self, html: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(html, "html.parser")

    def _extract_codes(self, soup: bs4.BeautifulSoup, game: genshin.Game) -> List[str]:
        codes: list[str] = []
        div = soup.find("div", {"class": "article_body"})
        h2s = div.find_all("h2")
        uls = div.find_all("ul")
        lis = []
        uls.remove(uls[0])

        for i, h2 in enumerate(h2s):
            if (
                    "livestream" in h2.text.strip().lower() or
                    self.titles[game] in h2.text.strip().lower()
            ):
                ul = uls[i]
                lis.extend(ul.find_all("li"))

        for li in lis:
            if li.strong is not None:
                codes.append(li.strong.text.strip())

        return codes
