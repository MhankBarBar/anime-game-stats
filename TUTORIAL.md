# Anime Game Stats

Anime Game Stats is a Python script that retrieves statistics and information from anime games, specifically Genshin Impact and a game called HSR. It utilizes the genshin library to interact with the Hoyolab API and retrieve data such as user stats, achievements, rewards, and character showcases. The retrieved data is then rendered using a Jinja2 template to generate an HTML report.

## Features

- Retrieves Genshin Impact user stats including full stats, Spiral Abyss progress, diary, daily rewards, and character showcases.
- Retrieves HSR (Star Rail) user stats including user stats, character details, diary, forgotten hall challenge, daily rewards, and character showcases (todo).
- Claims daily rewards for both games and redeems codes for extra rewards.
- Generates an HTML report using a Jinja2 template.

## Getting Started

To use Anime Game Stats, you can follow these steps:

### Fork this repository by clicking the "Fork" button on the top right corner of this page. This will create a copy of the repository in your GitHub account.

### How to get Cookies?
Using username and password
1. Run `python -m genshin login`.
2. Press the Login button and solve a captcha.
3. Copy cookies.

![image](https://github.com/user-attachments/assets/7e7b7d70-3f68-426c-a481-9c0ca0ca5a39)


### Create a repository secret

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/5fd34244-bca2-4c9a-afad-c12fca91134d)

### Paste your cookies in the repository secret

![image](https://github.com/user-attachments/assets/1085893e-c2a6-4716-ab5e-201a357cf8bf)


For now the cookies is just supported for genshin and hsr at the same account.

### Give Action Write Permissoion

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/152ee424-6db1-4933-9fa9-26fe0327eac7)

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/6ee01665-903d-4337-9b47-591a5dc693d5)

### Run the action manually

![image](https://github.com/MhankBarBar/anime-game-stats/assets/55822959/dae0ea7f-3386-467a-9fd5-fb12d5878022)


And you're set! From now on the repo will claim any new codes and redeem the daily check-in rewards at Hoyolab for you every 12 hours!

## Costumization
You can customize the `template.html` file to modify the appearance and layout of the generated HTML report.

## Acknowledgments
- [genshin](https://github.com/thesadru/genshin.py) library by thesadru for Genshin Impact, HSR and Honkai Impact 3rd API integration.

## Credits
This repository is the clone of [genshin-stats](https://github.com/thesadru/genshin-stats) and [kiizuha-genshin](https://github.com/rushkii/kiizuha-genshin).

Mine just add some changes, many thanks for them.
