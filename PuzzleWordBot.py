#!/usr/bin/env python3

import discord
from discord.ext import commands
from discord.ext.commands import Bot, AutoShardedBot
from discord.utils import get

import re
import json
import random
import time
import operator
import string
import asyncio
import click

from datetime import datetime

# For compare list is the same
import collections

## mysql
import pymysql.cursors
from config import config

token = config.discord.token
channelID = config.discord.channelID
ownerID = config.discord.ownerID
REWARD = 200
ENABLE_REWARD = True

DBHOST = config.mysql.host
DBUSER = config.mysql.user
DBNAME = config.mysql.dbname
DBPASS = config.mysql.password

# word file names
WORDLIST_1 = config.listfile.file1
WORDLIST_2 = config.listfile.file2
WORDLIST_3 = config.listfile.file3

BADWORD_1 = config.listfile.badword1

bot = AutoShardedBot(command_prefix=['.', '!', '?'], case_insensitive=True)
bot.remove_command("help")

IN_PUZZLEWORD = False
conn = None

def openConnection():
    global conn
    try:
        if conn is None:
            conn = pymysql.connect(DBHOST, user=DBUSER, passwd=DBPASS, db=DBNAME, charset='utf8', cursorclass=pymysql.cursors.DictCursor, connect_timeout=5)
        elif (not conn.open):
            conn = pymysql.connect(DBHOST, user=DBUSER, passwd=DBPASS, db=DBNAME, charset='utf8', cursorclass=pymysql.cursors.DictCursor, connect_timeout=5)    
    except:
        print("ERROR: Unexpected error: Could not connect to MySql instance.")
        sys.exit()


def load_words():
    wordList = []
    with open(WORDLIST_1) as word_file:
        valid_words = set(word_file.read().split())
    for item in valid_words:
        if config.listfile.minlen <= len(item) <= config.listfile.maxlen and re.match('[a-zA-Z]+', item):
            wordList.append(item)

    with open(WORDLIST_2) as word_file:
        valid_words = set(word_file.read().split())
    for item in valid_words:
        if config.listfile.minlen <= len(item) <= config.listfile.maxlen and re.match('[a-zA-Z]+', item):
            wordList.append(item)

    with open(WORDLIST_3) as word_file:
        valid_words = set(word_file.read().split())
    for item in valid_words:
        if config.listfile.minlen <= len(item) <= config.listfile.maxlen and re.match('[a-zA-Z]+', item):
            wordList.append(item)

    badword_list = []
    with open(BADWORD_1) as word_file:
        badword_list = set(word_file.read().split())

    print('Word from dict: '+str(len(wordList)))
    newWordList = [x for x in wordList if x not in badword_list]
    print('Word after bad word:'+str(len(newWordList))) 
    return newWordList


english_words = load_words()
q = None

ignore = {ord(c): None for c in string.punctuation}
random.seed(time.time())
print('We ve got: '+str(len(english_words))+' words to play.')

class question(object):
    def __init__(self):
        global english_words
        _q = random.choice(english_words)
        char_list = list(_q)
        # Check if the random shuffle is same as the answer
        while _q.upper() == (''.join(char_list)).upper() or ("-" in char_list):
            random.shuffle(char_list)
        for n, i in enumerate(char_list):
            if i != ' ':
                char_list[n] = ':regional_indicator_'+i+':'
            else:
                char_list[n] = ':white_medium_square:'
        self.question = ' '.join(char_list)
        self.answer = _q
        self.answer = str(self.answer).translate(ignore)
        self.hint = False
        self.hint2 = False
        print('Puzzled word: ' + _q.upper())
        print('Puzzle Answer: ' + self.answer.upper())

    def checkPuzzle(self, message):
        global english_words
        msg = message.content.translate(ignore)
        if len(msg) != len(self.answer):
            return False
        if msg.lower() in english_words:
            if collections.Counter(list(msg.upper())) == collections.Counter(list(self.answer.upper())):
                return True
            else:
                return False
        else:
            return False


    def LastQuestionNumb(self):
        openConnection()
        try:
            with conn.cursor() as cursor:
                sql = """ SELECT * FROM `puzzleBot_asked` ORDER BY `id` DESC LIMIT 1 """
                cursor.execute(sql,)
                LastQ = cursor.fetchone()
                if LastQ:
                    return LastQ['id'] + 1
                else:
                    return 1
        finally:
            conn.close()


def get_trivia_num(message):
    return 30


@bot.event
async def on_ready():
    print("Hello, I am Puzzle Word Game Bot!")
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    print("Guilds: {}".format(len(bot.guilds)))
    print("Users: {}".format(sum([x.member_count for x in bot.guilds])))
    game = discord.Game(name="Puzzle Word")
    await bot.change_presence(status=discord.Status.online, activity=game)


@bot.event
async def on_shard_ready(shard_id):
    print(f'Shard {shard_id} connected')


@bot.event
async def on_message(message):
    global IN_PUZZLEWORD, q, ownerID
    if message.content.upper().startswith('.REBOOT') and message.author.id == ownerID:
        await message.author.send('```Rebooting....```')
        try:
            bot.unload_extension(module)
            bot.load_extension(module)
        except Exception as e:
            print(f'```py\n{traceback.format_exc()}\n```')
        else:
            print('\N{OK HAND SIGN}')
    if not IN_PUZZLEWORD and len(message.content) > 0 and message.channel.id == channelID and message.author.id != bot.user.id:
        numNo = 0
        IN_PUZZLEWORD = True
        players = {}
        q = question()
        #print(q.question)
        HiScoreMsg = None
        # select top 3
        openConnection()
        try:
            with conn.cursor() as cursor:
                sql = """ SELECT * FROM `puzzleBot_score` ORDER BY `score` DESC LIMIT 3 """
                cursor.execute(sql,)
                highScoreUser = cursor.fetchall()
                HiScoreMsg = '**Current High score**:\n'
                for m in highScoreUser:
                    user = bot.get_user(id=int(m['user_id']))
                    if user:
                        HiScoreMsg = HiScoreMsg + '`' + user.name + '`' + ': `' + str(m['score']) + ' pts` | '
        finally:
            conn.close()

        await message.channel.send('**OK, Puzzle Game has begun!**')
        x = get_trivia_num(message.content)
        await message.channel.send('```css\n'
                                'You have %d seconds to win each puzzle.```' % x)
        await message.channel.send(f'{HiScoreMsg}')
        await message.channel.send('#'+str('{:,.0f}'.format(q.LastQuestionNumb()))+' New word puzzle: '+ q.question + '\n')
        i = 0
        while IN_PUZZLEWORD:
            def check(m):
                return m.channel == bot.get_channel(int(channelID))
            msg = None
            try:
                msg = await bot.wait_for('message', timeout=30, check=check)
            except asyncio.TimeoutError:
                msg = None
            else:
                pass
            if msg is None:
                numNo += 1
                await message.channel.send(
                                        '```css\n'
                                        'Too slow! The answer was %s.```' %
                                        (q.answer.upper()))
                openConnection()
                try:
                    with conn.cursor() as cursor:
                        current_Date = datetime.now()
                        score_value = 1
                        correct_answer = q.answer
                        question_str = q.question
                        sql = """ INSERT INTO `puzzleBot_asked` (`question`, `correct_answer`, `score_value`, `inserted_date`) 
                                  VALUES (%s, %s, %s, %s) """
                        cursor.execute(sql, (question_str, correct_answer, score_value, current_Date,))
                        conn.commit()
                finally:
                    conn.close()

                if numNo >= 4:
                    q = None
                    await message.channel.send('**No one plays. Game stopped**\n')
                    await message.channel.send(f'{HiScoreMsg}')
                    IN_PUZZLEWORD = False
                    numNo = 0
                    break
                else:
                    q = question()
                    await message.channel.send('#'+str('{:,.0f}'.format(q.LastQuestionNumb()))+' **New word puzzle**: '+ q.question + '\n')
            elif msg.author == bot.user:
                continue
            elif q.checkPuzzle(msg):
                answer_str = msg.content.upper()
                await msg.channel.send('**Correct, %s!**```css\n The answer is: %s.```' %
                                          (msg.author.mention, answer_str))
                if ENABLE_REWARD:
                    await msg.channel.send('.tip %s %s REWARD' % (str(REWARD), msg.author.mention))
                openConnection()
                try:
                    with conn.cursor() as cursor:
                        current_Date = datetime.now()
                        score_value = 1
                        winner_id = msg.author.id
                        winner_name = msg.author.name
                        correct_answer = answer_str
                        question_str = q.question
                        sql = """ INSERT INTO `puzzleBot_asked` (`question`, `correct_answer`, `winner_name`, `winner_id`, `score_value`, `inserted_date`) 
                                  VALUES (%s, %s, %s, %s, %s, %s) """
                        cursor.execute(sql, (question_str, correct_answer, winner_name, winner_id, score_value, current_Date,))
                        conn.commit()
                        ## update or insert score table
                        sql = """ SELECT * FROM `puzzleBot_score` WHERE `user_id`=%s ORDER BY `sid` DESC LIMIT 1 """
                        cursor.execute(sql, (str(winner_id),))
                        userScore = cursor.fetchone()
                        if userScore is None:
                            #insert
                            sql = """ INSERT INTO `puzzleBot_score` (`user_id`, `total_win`, `score`, `last_scored`, `name`) 
                                      VALUES (%s, %s, %s, %s, %s) """
                            cursor.execute(sql, (str(winner_id), 1, score_value, current_Date, winner_name,))
                            conn.commit()
                        else:
                            #update	
                            sql = """ UPDATE `puzzleBot_score` SET `score`=`score` + 1, `total_win`=`total_win` + 1, `last_scored` = %s, `name` = %s 
                                      WHERE `user_id`=%s """
                            cursor.execute(sql, (current_Date, winner_name, str(winner_id),))
                            conn.commit()
                            # select top 3
                            sql = """ SELECT * FROM `puzzleBot_score` ORDER BY `score` DESC LIMIT 5 """
                            cursor.execute(sql,)
                            highScoreUser = cursor.fetchall()
                            HiScoreMsg = '**Current High score**:\n'
                            if len(highScoreUser) == 0:
                                HiScoreMsg = HiScoreMsg + "`None.`"
                            else:
                                for m in highScoreUser:
                                    user = bot.get_user(id=int(m['user_id']))
                                    if user:
                                        HiScoreMsg = HiScoreMsg + '`' + str(user.name) + '`' + ': `' + str(m['score']) + 'pts` | '
                             #print(HiScoreMsg)
                finally:
                    conn.close()

                try:
                    players[msg.author.nick] += 1
                except KeyError:
                    players[msg.author.nick] = 1
                scores = sorted(players.items(), key=operator.itemgetter(1))
                await msg.channel.send('**New puzzle will start in 30 seconds!**')
                q = None
                await asyncio.sleep(30)
                q = question()
                await msg.channel.send('#'+str('{:,.0f}'.format(q.LastQuestionNumb()))+' **New word puzzle**: ' + q.question + '\n')
                i += 1
            elif msg.content.upper() == '.TOP':
                await message.channel.send(f'{HiScoreMsg}')
            if i > 0:
                if scores[-1][1] >= x:
                    await msg.channel.send('We got a winner! Congrats @%s'
                                        % scores[-1][0])
                    IN_PUZZLEWORD = False
                    break
    # Do not remove this, otherwise, command not working.
    await bot.process_commands(message)


@bot.command(pass_context=True, name='hint')
async def hint(ctx):
    global channelID, q
    if IN_PUZZLEWORD and ctx.message.channel.id == channelID and ctx.message.author.id != bot.user.id:
        if q is None:
            await ctx.send('There is no new puzzle yet.')
        else:
            if q.hint == True and q.hint2 == True:
                await ctx.send('I already gave hint..')
                return
            elif q.hint == True and q.hint2 == False:
                puzzle_str = q.answer.upper()
                char_list = list(puzzle_str)
                for n, i in enumerate(char_list):
                    if i != ' ':
                        if ((n + 1) % 3 == 0 and n > 0) or n == 0 or n == 4 or n == 7 or n == 10:
                            char_list[n] = ':regional_indicator_'+i.lower()+':'
                        else:
                            char_list[n] = ':white_medium_square:'
                    else:
                        char_list[n] = ':white_medium_square:'
                answer_str = ' '.join(char_list)
                q.hint = True
                q.hint2 = True
                await ctx.send(f'**Second Hint**\n{answer_str}')
                return
            else:
                puzzle_str = q.answer.upper()
                char_list = list(puzzle_str)
                for n, i in enumerate(char_list):
                    if i != ' ':
                        if (n + 1) % 3 == 0 and n > 0:
                            char_list[n] = ':regional_indicator_'+i.lower()+':'
                        else:
                            char_list[n] = ':white_medium_square:'
                    else:
                        char_list[n] = ':white_medium_square:'
                answer_str = ' '.join(char_list)
                q.hint = True
                await ctx.send(f'**First Hint**\n{answer_str}')
                return


@click.command()
def main():
    bot.run(token)


if __name__ == '__main__':
    main()
