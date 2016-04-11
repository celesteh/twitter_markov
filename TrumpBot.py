from twitter_markov import TwitterMarkov
import glob
import random
import os
import time
import re
import Levenshtein
import unicodedata

def massage(tweet):
    tweet = tweet.replace('great', 'grate')
    tweet = tweet.replace('Great', 'Grate')
    tweet = tweet.replace('GREAT', 'GRATE')
    tweet = tweet.replace('RT : ', '')
    tweet = tweet.replace('RT ', ' ')
    tweet = tweet.replace(' !', '')
    tweet = re.sub('\s+via[\:]?\s+', ' ', tweet)
    tweet = re.sub('\s+h\W+', '', tweet)
    tweet = re.sub('\s+f\W+', '', tweet)
    tweet = tweet.replace(' . ', ' ')
    #tweet = tweet.replace(' : ', ' ')
    tweet = re.sub('\s+\:\s+', ' ', tweet)
    tweet = re.sub('\@[0-9A-Za-z\-\_]*', '', tweet)
    tweet = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', tweet)
    #tweet = tweet.replace('https:', '')
    #tweet = tweet.replace('http:', '')
    tweet = re.sub('http[s]?[\:]?', '', tweet)
    tweet = re.sub('\sh[t]+', '', tweet)
    tweet = re.sub('\sh[t]?\s', ' ', tweet)
    tweet = re.sub('[0-9][0-9][0-9][0-9]?', '', tweet) #no phone numbers
    tweet = re.sub('^\W', '', tweet)
    tweet = re.sub('^\s+', '', tweet)
    tweet = re.sub('\s+\.+', ' ', tweet)
    tweet = re.sub('\s+\/+', ' ', tweet)
    tweet = re.sub('\s+[^a-z0-9A-Z_\-\#\$]+', ' ', tweet)
    tweet = re.sub('\.\.\.+\s*\Z', '', tweet)

    tweet = re.sub('\s\s+', ' ', tweet)
    tweet = re.sub('[ \t\r\f\v]+\Z', '', tweet)

    return tweet
#--

def strip_punct(text):
    text = text.strip().lower()
    text = re.sub('[\?\.\:\!\,\\\/\;\#\@\'\"\&]', '', text)
    if type(text) is not str:
        utext = unicodedata.normalize('NFKD', text).encode('ascii','ignore')
        text = utext
    return text
#--

def check(tweet):

    #passed = False
    LEVENSHTEIN_LIMIT = 0.70

    history = tm.config.get('history')
    if tm.check_tweet(tweet):
        with open(history, 'r') as fp:
            tweet = strip_punct(tweet)
            for line in fp:
                if (tweet in strip_punct(line)) or Levenshtein.ratio(re.sub(r'\W+', '', tweet), re.sub(r'\W+', '', strip_punct(line))) >= LEVENSHTEIN_LIMIT:
                #if tweet in strip_punct(line):
                    print 'found in recent tweets: '+ tweet
                    return False #found in recent tweets
        with open(history, 'a') as fp:
            fp.write(tweet+'\n')
        return True
    return False
#--

def hashtags(tweet):

    tweet = re.sub('\s+NYC', ' #NYC', tweet)
    tweet = re.sub('\s+MAGA', ' #MAGA', tweet)
    tweet = re.sub('\s+PA', ' #PA', tweet)
    tweet = re.sub('\s+NRA', ' #NRA', tweet)
    tweet = re.sub('\s+GOP', ' #GOP', tweet)
    tweet = re.sub('\s+President\s*Trump', ' #PresidentTrump', tweet)
    tweet = re.sub('\s+Trump', ' #Trump', tweet)
    tweet = re.sub('\s+tcot', ' #tcot ', tweet)
    #tweet = re.sub('\s+TrumpTrain', ' #TrumpTrain', tweet)
    tweet = re.sub('\s+CA', ' #CA', tweet)
    tweet = re.sub('\s+FL', ' #FL', tweet)
    tweet = re.sub('\s+Indiana', ' #Indiana', tweet)
    tweet = re.sub('\s+StopTheSteal', ' #StopTheSteal', tweet)
    tweet = re.sub('\s+StandWithSheriff', ' #StandWithSheriff', tweet)
    tweet = re.sub('\s+WakeUpAmerica', ' #WakeUpAmerica', tweet)
    tweet = re.sub('\s+MakeAmericaGrateAgain', ' #MakeAmericaGrateAgain', tweet)

    tags = re.findall(r'\s+[A-Z]*[0-9a-z]+[A-Z]+\w+', tweet)
    for tag in tags:
        tweet.replace(tag, ' #'+tag)

    states = re.findall(r'\s+[A-Z][A-Z]\s+', tweet)
    for state in states:
        tweet.replace(state, ' #'+state+' ')

    if len(tweet) <= 93:
        tweet = tweet + '\n#MakeAmericaGrateAgain'
    if len(tweet) <= 99:
        tweet = tweet + '\n@realDonaldTrump'
    if len(tweet) <= 100:
        tweet = tweet + '\n#PresidentTrump'
    if len(tweet) <= 103:
        tweet = tweet + ' #AlwaysTrump'
    if len(tweet) <= 104:
        tweet = tweet + ' #OnlyTrump'
    if len(tweet) <= 105:
        tweet = tweet + ' #Trump2016'
    if len(tweet) <= 109:
        tweet = tweet + ' #Trump'

    return tweet
#--

def de_dup(corpus, max=10000):

    #tmp= '/tmp/courpus.txt'
    count =0
    start=0
    #successful = False
    tweets = {}
    sorted = []

    with open(corpus, 'r') as fp:
        for line in fp:
            line = massage(line)
            tweets[line] = count
            count = count + 1

    sorted = [None] * count
    for tweet,order in tweets.items():
        sorted[order] = tweet

    if (count > max):
        start = count - max
        sorted = sorted[start: ]

    os.remove(corpus)
    with open(corpus, 'w') as fp:
        for tweet in sorted:
            if tweet:
                fp.write(tweet)
#--

def learn():

    print 'learning....\n'
    tm.learn_peer()
    time.sleep(1)
    tm.learn_search(search='nuclear war')
    time.sleep(1)
    tm.learn_search(search='nuclear bomb')
    time.sleep(1)
    tm.learn_search(search='nuclear missile')
    time.sleep(1)
    tm.learn_search(search='nuclear arms')
    time.sleep(1)
    tm.learn_search(search='proliferation')
    time.sleep(1)
    tm.learn_search('climate change')
    time.sleep(1)
    tm.learn_search('#MAGA')
    time.sleep(1)
    tm.learn_search('climate hoax')
    time.sleep(1)
    tm.learn_search('global warming')
    time.sleep(1)
    tm.learn_search('nuke')
    time.sleep(1)

    print 'de-duping'

    de_dup(tm.config.get('corpus'))

# --


tm = TwitterMarkov('example_screen_name', '/home/celesteh/Dropbox/debbie/gifs/twitter_markov/corpus.txt', config_file='/home/celesteh/Dropbox/debbie/gifs/twitter_markov/bots.yaml')

gifs = tm.config.get('gifs')
files = glob.glob((str(gifs) +'/out*.gif'))
filename = random.choice(files)

print 'file is ' + filename +'\n'


learn()

print 'composing....\n'
tweet = tm.compose(max_len=116)

tries = 1

print 'checking...\n'
while not check(tweet):
    if (tries % 500) == 0:
        learn()
    tweet = tm.compose(max_len=116)
    tries = tries + 1

de_dup(tm.config.get('history'), 200)

tweet = massage(tweet)
tweet = hashtags(tweet)

print 'tweet is: ' + tweet + '\n'

tm.api.update_with_media(filename, tweet)

print 'uploaded\n'

os.remove(filename)
