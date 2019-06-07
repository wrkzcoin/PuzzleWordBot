# PuzzleWordBot
PuzzleWordBot Game in WrkzCoin discord

Word list from: <https://github.com/jnoodle/English-Vocabulary-Word-List> and http://www.mit.edu/~ecprice/wordlist.10000

We steal the Profane-words list from <https://github.com/zacanger/profane-words> to filter and exclude from word list.

**Installation**

1) Get pip3 modules install via `pip3 install module_names`

2) Create MySQL / MariaDB. Load database structure from `puzzlewordbot.sql`

2) Copy `config.yml.example` to `config.yml` and edit it as necessary including new bot token, channelID, etc.

3) Run `python3 PuzzleWordBot.py`

4) Invite bot to your server.

5) Play by typing any word in channel ID you defined in `config.yml`