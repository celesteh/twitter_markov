from twitter_markov import TwitterMarkov
import glob
import random
import os
import time
import re
import Levenshtein
import unicodedata

terms = ['#Trump2016', 'WomenForTrump', 'GenderEquity', '#Equality','global warming', 'climate hoax', 'climate hustle', 'nuclear war', 'nuclear bomb', 'hydrogen bomb', 'atomic bomb', 'warhead', 'ballistic missile','nuclear missile', 'nuke', 'nuclear arms', 'arms race','proliferation', 'launch codes', '#MAGA', '#PresidentTrump']
# 'climate change',

global unembelished
unembelished = ''

def massage(tweet):
    tweet = tweet.replace('great', 'grate') #Quirk
    tweet = tweet.replace('Great', 'Grate')
    tweet = tweet.replace('GREAT', 'GRATE')
    tweet = tweet.replace('programme', 'program') #americanise
    tweet = tweet.replace('Programme', 'Program') #americanise
    tweet = tweet.replace('PROGRAMME', 'PROGRAM') #americanise
    tweet = tweet.replace('RT : ', '') #Kill stray RT stuff
    tweet = tweet.replace('RT ', ' ')
    tweet = tweet.replace(' !', '') # stray punctuation
    tweet = re.sub('\s+via[\:]?\s+', ' ', tweet) # vias not helpful
    tweet = re.sub('\s+h\W+', '', tweet) #prevent stray h's
    tweet = re.sub('\s+f\W+', '', tweet) #prevent stray f's
    tweet = tweet.replace(' . ', ' ') # stray punctuation
    #tweet = tweet.replace(' : ', ' ')
    tweet = re.sub(r'\s+[\:\.\,\-\;\?\!\/\\]+\s*', ' ', tweet) # stray punctuation
    tweet = re.sub('\@[0-9A-Za-z\-\_]*', '', tweet) # strip mentions
    tweet = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', tweet)
    # strip urls
    #tweet = tweet.replace('https:', '')
    #tweet = tweet.replace('http:', '')
    tweet = re.sub('http[s]?[\:]?', '', tweet) # strip stray https
    tweet = re.sub('\sh[t]+', '', tweet)
    tweet = re.sub('\sh[t]?\s', ' ', tweet)
    tweet = re.sub('[0-9][0-9][0-9][0-9]?', '', tweet) #no phone numbers
    tweet = re.sub('^[^a-z0-9A-Z_\-\#\$\'\"\(]+', '', tweet) # strip leading punctuation
    tweet = re.sub('^\s+', '', tweet) # strip leading whitespace
    #tweet = re.sub('\s+\.+', ' ', tweet) #floating dots must die
    #tweet = re.sub('\s+\/+', ' ', tweet) # floating /s are also bad
    tweet = re.sub('\s+[^a-z0-9A-Z_\-\#\$\'\"\(]+', ' ', tweet) #floating punctuation
    tweet = re.sub(r'\s+[\#\.\?\!\'\"]+\s+',' ', tweet) #floating in spaces
    tweet = re.sub('\#\s+', ' ', tweet)
    #tweet = re.sub('\.\.\.+\s*\Z', '\n', tweet) # elipses must die

    tweet = re.sub('\.\.+', '.', tweet) # doubled punctuation
    tweet = re.sub('\,\,+', ',', tweet)
    tweet = re.sub('\'\'+', '\'', tweet)
    tweet = re.sub('\"\"+', '\"', tweet)
    tweet = re.sub('\;\;+', '\;', tweet)
    tweet = re.sub('\#\#+', '\#', tweet)
    # doubled ! is ok
    tweet = re.sub('\?+', '?!', tweet) #single ?s are insufficiently emotive

    #end = re.compile('\n\Z')
    #if not end.search(tweet):
    #    tweet = tweet+'\n'

    tweet = re.sub('\s+', ' ', tweet) #compress multiple spaces
    tweet = re.sub('\s+[\:\.\,\-\;\?\!\"\'\#]+\s*\Z', '', tweet) # strip trailing punctuation
    tweet = re.sub('\s+\Z', '', tweet) # strip trailing whitespace
    tweet = tweet + '\n'

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
    global unembelished

    history = tm.config.get('history')
    if tm.check_tweet(tweet):
        with open(history, 'r') as fp:
            tweet = strip_punct(tweet)
            for line in fp:
                if (tweet in strip_punct(line)) or Levenshtein.ratio(re.sub(r'\W+', '', tweet), re.sub(r'\W+', '', strip_punct(line))) >= LEVENSHTEIN_LIMIT:
                #if tweet in strip_punct(line):
                    print 'found in recent tweets: '+ tweet
                    return False #found in recent tweets
        #with open(history, 'a') as fp:
        #    fp.write(tweet+'\n')
        unembelished = tweet
        return True
    return False
#--

def archive(tweet):

    global unembelished
    history = tm.config.get('history')
    #tweet = strip_punct(tweet)
    #print 'ready: ' + unembelished
    with open(history, 'a') as fp:
        fp.write(unembelished+'\n')
    print 'archived'
#--

def hashtags(tweet):

    tweet = re.sub('\s+NYC', ' #NYC', tweet, flags=re.I)
    #tweet = re.sub('\s+MAGA', ' #MAGA', tweet)
    #tweet = re.sub('\s+PA', ' #PA', tweet)
    tweet = re.sub('\s+NRA', ' #NRA', tweet, flags=re.I)
    tweet = re.sub('\s+GOP\W+', ' #GOP ', tweet, flags=re.I)
    tweet = re.sub('\s+New\s+York\s+Times', ' #NYTimes', tweet, flags=re.I)
    tweet = re.sub('\s+President\s*Trump', ' #PresidentTrump', tweet, count=1, flags=re.I)
    tweet = re.sub('\s+Only\s*Trump', ' #OnlyTrump', tweet, count=1, flags=re.I)
    tweet = re.sub('\s+Trump', ' #Trump', tweet, count=1, flags=re.I)
    tweet = re.sub('\s+tcot', ' #tcot ', tweet, flags=re.I)
    tweet = re.sub('\s+POTUS', ' #POTUS', tweet, flags=re.I)
    #tweet = re.sub('\s+TrumpTrain', ' #TrumpTrain', tweet)
    #tweet = re.sub('\s+CA', ' #CA', tweet)
    #tweet = re.sub('\s+FL', ' #FL', tweet)
    tweet = re.sub('\s+Indiana', ' #Indiana', tweet, flags=re.I)
    tweet = re.sub('\s+Colorado', ' #Colorado', tweet, flags=re.I)
    tweet = re.sub('\s+StopTheSteal', ' #StopTheSteal', tweet)
    tweet = re.sub('\s+StandWithSheriff', ' #StandWithSheriff', tweet)
    tweet = re.sub('\s+WakeUpAmerica', ' #WakeUpAmerica', tweet)
    #maga = re.compile('\s+MakeAmericaGrateAgain', re.I) #ignore case
    tweet = re.sub('\s+MakeAmericaGrateAgain', ' #MakeAmericaGrateAgain', tweet, flags=re.I)
    tweet = re.sub('\s+[\#]*realDonaldTrump', '\n@realDonaldTrump', tweet, flags=re.I)
    tweet = re.sub('\s+MAGA\W+', ' #MAGA! ', tweet, flags=re.I)

    # tags start with upper OR lowercase letters or numbers,
    # have some numbers or lower case letters
    # and have an Upper case in the middle somewhere
    print 'find tags'
    tags = re.findall('\s+[A-Z]*[0-9a-z]+[A-Z]+\w+', tweet)
    for tag in tags:
        print tag
        tag = re.sub('\s+', '', tag)
        tweet = tweet.replace(tag, ' #'+tag)



    print 'find states'
    # All 2 letter uper case pairs might be states, so hashtag them
    states = re.findall('\s+[A-Z][A-Z][\s\.\,\;\!\"\'\?]+', tweet)
    for state in states:
        print state
        state = re.sub('\s+', '', state)
        if state not in ('OF', 'AN', 'TO', 'QA', 'NO', 'ON', 'PM', 'AM', 'IT', 'DO'): #short words
            tweet = tweet.replace(state, ' #'+state+' ')

    tweet = re.sub(r'\s+[\#\.\?\!\'\"]+\s+',' ', tweet) #floating in spaces
    tweet = re.sub('\s\s+', ' ', tweet) #compress multiple spaces
    tweet = re.sub('\s+\Z', '', tweet) # strip trailing whitespace


    # If we've got extra space, let's add some #trump tags!
    if (len(tweet) <= 92) and ('#MakeAmericaGrateAgain' not in tweet) and random.choice(True, False):
        tweet = tweet + '\n#MakeAmericaGrateAgain'
    if (len(tweet) <= 92):
        tweet = tweet + '\n#Trump would do better'

    if (len(tweet) <= 97):
        if ('@realDonaldTrump' in tweet) or random.choice(True, False):
            tweet = tweet + '\n#WhatWouldTrumpDo'
        else:
            tweet = tweet + '\n@realDonaldTrump'

    if (len(tweet) <= 99) and ('#PresidentTrump' not in tweet):
        tweet = tweet + '\n#PresidentTrump'

    if len(tweet) <= 102:
        tweet = tweet + '\n#AlwaysTrump'

    if (len(tweet) <= 103):
        if ('#OnlyTrump' not in tweet):
            tweet = tweet + ' #OnlyTrump'
        else:
            tweet = tweet + '\n#TrumpTrain'

    if len(tweet) <= 104:
        tweet = tweet + ' #Trump2016'
    if len(tweet) <= 108:
        trump = re.compile('\#Trump\W+')
        #maga = re.compile('\#MAGA[\s\.\,\!\?\;]+')
        if (trump.search(tweet)) and ('#MAGA' not in tweet):
            tweet = tweet + ' #MAGA'
        else:
            tweet = tweet + ' #Trump'

    return tweet
#--

def de_dup(corpus, max=20000):

    # remove duplicates from the corpus by writing the whole thing
    # into a dictionary. Make the tweet the key and the data is the
    # line number on which it was last found

    # Put the keys into an array, ordered by the data
    # Truncate anything below a cutoff (old lines timeout)

    # Output the array to a text file


    #tmp= '/tmp/courpus.txt'
    count =0
    start=0
    #successful = False
    tweets = {}
    sorted = []

    with open(corpus, 'r') as fp:
        for line in fp:
            line = massage(line)
            tweets[str(line)] = count
            count = count + 1

    size = len(tweets.keys())
    sorted = [None] * count
    for tweet,order in tweets.items():
        sorted[order] = tweet

    compressed = [None] * (size + 1)
    index = 0
    for tweet in sorted:
        if tweet:
            compressed[index] = tweet
            index = index + 1

    if (size > max):
        start = size - max
        compressed = compressed[start: ]

    os.remove(corpus)
    with open(corpus, 'w') as fp:
        for tweet in compressed:
            if tweet:
                fp.write(tweet)
#--

def learn():

    print 'learning....\n'


    tm.learn_peer()
    time.sleep(1)

    for query in terms:
        print query
        tm.learn_search(query)
        time.sleep(3)

    tm.learn_peer() #pick up new ones since search terms
    time.sleep(1)

    print 'de-duping'

    de_dup(tm.config.get('corpus'),tm.config.get('corpus_size'))

# --

random.seed()

tm = TwitterMarkov('example_screen_name', '/home/celesteh/Dropbox/debbie/gifs/twitter_markov/corpus.txt', config_file='/home/celesteh/Dropbox/debbie/gifs/twitter_markov/bots.yaml')

gifs = tm.config.get('gifs')
files = glob.glob((str(gifs) +'/out*.gif'))
if len(files) < 15:
    print 'WARNING: make more gifs!'
filename = random.choice(files)

print 'file is ' + filename +'\n'


learn()

state_size = tm.config.get('state_size')
probability = random.triangular()
if(probability > 0.9):
    state_size = max(2, state_size -3)
else:
    if(probability > 0.8):
        state_size = max(2, state_size -2)
    else:
        if (probability > 0.7):
            state_size = max(2, state_size -1)
print 'state_size is ' + str(state_size)

tm.models = tm._setup_models(tm.corpora, state_size)

print 'composing....\n'
tweet = tm.compose()

tries = 1

print 'checking...\n'
while not check(tweet):
    if (tries % 10) == 0:
        learn()
    tweet = tm.compose()
    tries = tries + 1

de_dup(tm.config.get('history'), tm.config.get('history_size'))

tweet = massage(tweet)
tweet = hashtags(tweet)

print 'tweet is: ' + tweet + '\n'

tm.api.update_with_media(filename, tweet)

print 'uploaded\n'

archive(tweet)
os.remove(filename)
