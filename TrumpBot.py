from twitter_markov import TwitterMarkov
import glob
import random
import os
import time
import re
import Levenshtein
import unicodedata
import pynotify
import enchant


#this is just looking for partisan posts
terms = ['#Trump2016', '#Trump2020', 'WomenForTrump',  'global warming', 'climate hoax', 'climate hustle', '#MAGA', '#PresidentTrump', '#TrumpsArmy', 'AlwaysTrump', 'TrumpTrain', 'TrumpNation']

# these are subjects which are controversial in the election
issues = ['#tcot', '#pjnet','GenderEquity', '#Equality', 'climate change', 'nuclear war', 'nuclear bomb', 'hydrogen bomb', 'atomic bomb', 'warhead', 'ballistic missile','nuclear missile', 'nuke', 'nuclear arms', 'arms race','proliferation', 'launch codes', '#DeusExAtomica']

global unembelished
global dict
unembelished = ''

def defrag(tweet):

    # find and kill floating word fragments
    print 'de fragging'
    global dict
    words = tweet.split()
    case = re.compile('^\s*[^\#\@0-9][a-z]+[\.\,\;\!\?\'\" \t\n]*\Z') #all caps and numbers get a pass
    single = re.compile('^\s*[A-Za-z][\.\,\;\!\?\'\" \t\n]*\Z') #one letter
    for word in words:
        if case.search(word) or single.search(word):
            text = re.sub('\W+', '', word)
            if len(text) <= 5:
                if not dict.check(text):
                    print word
                    tweet = tweet.replace(word, ' ')
    return tweet

def massage(tweet):

    tweet = tweet.replace('great', 'grate') #Quirk
    tweet = tweet.replace('Great', 'Grate')
    tweet = tweet.replace('GREAT', 'GRATE')
    tweet = tweet.replace('programme', 'program') #americanise
    tweet = tweet.replace('Programme', 'Program') #americanise
    tweet = tweet.replace('PROGRAMME', 'PROGRAM') #americanise
    tweet = re.sub('^RT\s*[:]?\s+','', tweet)
    #tweet = re.sub('RT[ ]?[:]?\w+', ' ', tweet)
    #tweet = tweet.replace('RT : ', '') #Kill stray RT stuff
    #tweet = tweet.replace('RT ', ' ')
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
    tweet = re.sub('[0-9][0-9][0-9][ \-]?[0-9][0-9][0-9][0-9]', '', tweet) #no phone numbers
    tweet = re.sub('^[^a-z0-9A-Z_\-\#\$\'\"\(]+', '', tweet) # strip leading punctuation
    tweet = re.sub('^\s+', '', tweet) # strip leading whitespace
    #tweet = re.sub('\s+\.+', ' ', tweet) #floating dots must die
    #tweet = re.sub('\s+\/+', ' ', tweet) # floating /s are also bad
    tweet = re.sub('\s+[^a-z0-9A-Z_\-\#\$\'\"\(]+', ' ', tweet) #floating punctuation
    tweet = re.sub(r'\s+[\#\.\?\!\'\"]+\s+',' ', tweet) #floating in spaces
    tweet = re.sub('\#\s+', ' ', tweet)
    #tweet = re.sub('\.\.\.+\s*\Z', '\n', tweet) # elipses must die

    #weird punct before end of line
    tweet = re.sub('[,:\-]+\!', '!', tweet)
    tweet = re.sub('[,:\-]+\?', '?', tweet)
    tweet = re.sub('[,:\-]+\.', '\.', tweet)

    tweet = re.sub('\.\.+', '.', tweet) # doubled punctuation
    tweet = re.sub('\,\,+', ',', tweet)
    tweet = re.sub('\'\'+', '\'', tweet)
    tweet = re.sub('\"\"+', '\"', tweet)
    tweet = re.sub('\;\;+', '\;', tweet)
    tweet = re.sub('\#\#+', '\#', tweet)
    # doubled ! is ok tripled is enough, though
    tweet = re.sub('\!\!\!\!+', '!!!', tweet)
    tweet = re.sub('\?+', '?!', tweet) #single ?s are insufficiently emotive
    tweet = re.sub('\?\!+', '?!', tweet) #don't grow

    #end = re.compile('\n\Z')
    #if not end.search(tweet):
    #    tweet = tweet+'\n'

    tweet = re.sub('\s+', ' ', tweet) #compress multiple spaces
    tweet = re.sub('\s+[\:\.\,\-\;\?\!\"\'\#]+\s*\Z', '', tweet) # strip trailing punctuation
    tweet = re.sub('\s+\Z', '', tweet) # strip trailing whitespace
    tweet = re.sub('^\s+', '', tweet) # strip leading whitespace
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
    tweet = re.sub('\s+RNC', ' #RNC', tweet, flags=re.I)
    tweet = re.sub('\s+pjnet', ' #PJNET', tweet, flags=re.I)
    tweet = re.sub('\s+New\s+York\s+Times', ' #NYTimes', tweet, flags=re.I)
    tweet = re.sub('\s+President\s*Trump', ' #PresidentTrump', tweet, count=1, flags=re.I)
    tweet = re.sub('\s+Only\s*Trump', ' #OnlyTrump', tweet, count=1, flags=re.I)
    tweet = tweet.replace(' TRUMP', ' #TRUMP') # all caps special case
    tweet = re.sub('\s+Trump', ' #Trump', tweet, count=1, flags=re.I)
    tweet = re.sub('^Trump', ' #Trump', tweet, count=1, flags=re.I)
    tweet = re.sub('\s+tcot', ' #tcot ', tweet, flags=re.I)
    tweet = re.sub('\s+LeaveEU', ' #LeaveEU ', tweet, flags=re.I)
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
    tweet = re.sub('\s+[\#]*Trump2016\W+', ' #Trump2020 ', tweet, flags=re.I)

    # tags start with upper OR lowercase letters or numbers,
    # have some numbers or lower case letters
    # and have an Upper case in the middle somewhere
    print 'find tags'
    tags = re.findall('\s+[A-Z]*[0-9a-z]+[A-Z]+\w+', tweet)
    for tag in tags:
        print tag
        tag = re.sub('\s+', '', tag)
        tweet = tweet.replace(tag, ' #'+tag+' ')
    tags = re.findall('^[A-Z]*[0-9a-z]+[A-Z]+\w+', tweet)
    for tag in tags:
        print tag
        tag = re.sub('\s+', '', tag)
        tweet = tweet.replace(tag, ' #'+tag+' ')



    print 'find states'
    # All 2 letter uper case pairs might be states, so hashtag them
    states = re.findall('\s+[A-Z][A-Z][\s\.\,\;\!\"\'\?]+', tweet)
    for state in states:
        print state
        state = re.sub('\s+', '', state)
        if state not in ('OF', 'AN', 'TO', 'QA', 'NO', 'ON', 'PM', 'AM', 'IT', 'DO', 'MR', 'GO'): #short words
            tweet = tweet.replace(state, ' #'+state+' ')

    tweet = re.sub(r'\s+[\#\.\?\!\'\"]+\s+',' ', tweet) #floating in spaces
    tweet = re.sub('\s\s+', ' ', tweet) #compress multiple spaces
    tweet = re.sub('\s+\Z', '', tweet) # strip trailing whitespace


    # If we've got extra space, let's add some #trump tags!
    #if (len(tweet) <= 92) and ('#MakeAmericaGrateAgain' not in tweet) and ('#Trump' in tweet):
    #    tweet = tweet + '\n#MakeAmericaGrateAgain'
    if (len(tweet) <= 92):
        if ('#Trump' not in tweet):
            tweet = tweet + random.choice(['\n#TrumpStrong!','\n#Trump is mighty',
                    '\nStrength thru #Trump!','\nTrust in #Trump!',
                    '\n#Trump is different.', '\n#Trump is special!',
                    '\n#Trump will save us!','\nTurn to #Trump!','\nFaith in #Trump!',
                    '\n#Trump will fix this.', '\n#Trump is grate',
                    '\n#Trump is doing better', '\n#Trump will fix it.', '\nWe need #Trump.',
                    '\n#Trump has solutions.', '\n#Trump will make deals',
                    '\n#Trump has answers.','\n#Trump is grate',
                    '\n#Trump is grate.', '\nSmart ppl love #Trump', '\nHelp us, #Trump!',
                    '\nIn #Trump we trust!', '\n#God bless #Trump!', '\n#Trump needs us!',
                    '\nPower thru #Trump', '\n#Trump for GRATENESS!', '\n#Trump is #MAGA',
                    '\n#Trump makes US grate', '\n#Trumpocalypse Now!!!',
                    '', '', '' ,'', '', '', ''])
        else:
            if ('#MakeAmericaGrateAgain' not in tweet):
                tweet = tweet + '\n#MakeAmericaGrateAgain'

    if (len(tweet) <= 97):
        if ('@realDonaldTrump' in tweet) or ('#Trump' not in tweet):
            tweet = tweet + '\n#WhatWouldTrumpDo'
        else:
            tweet = tweet + '\n@realDonaldTrump'

    if (len(tweet) <= 99) and ('#PresidentTrump' not in tweet):
        tweet = tweet + '\n#PresidentTrump'

    if len(tweet) <= 102 and ('#AlwaysTrump' not in tweet):
        tweet = tweet + '\n#AlwaysTrump'

    if (len(tweet) <= 103):
        if ('#OnlyTrump' not in tweet):
            tweet = tweet + '\n#OnlyTrump'
        else:
            tweet = tweet + random.choice(['\n#TrumpTrain', '\n#TrumpTrain', '\n#TrumpTrain', '\n#TrustTrump'])

    if len(tweet) <= 104:
        tweet = tweet + ' #Trump2020'
    if len(tweet) <= 108:
        trump = re.compile('\#Trump\W+')
        #maga = re.compile('\#MAGA[\s\.\,\!\?\;]+')
        if (trump.search(tweet)) and ('#MAGA' not in tweet):
            tweet = tweet + '\n#MAGA'
        else:
            tweet = tweet + '\n#Trump'

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

    return size
#--

def learn(state_size=3, propoganda=True):

    print 'learning....\n'

    tm.learn_peer()
    time.sleep(5)

    for query in terms:
        #print query
        tm.learn_search(query)
        time.sleep(3)

    for query in issues:
        #print query
        tm.learn_search(query, tm.config.get('issues'))
        time.sleep(3)

    tm.learn_peer() #pick up new ones since search terms
    time.sleep(1)

    print 'de-duping'


    # Is one of the copora files truncated?
    target = tm.config.get('corpus_size')
    cpsize = de_dup(tm.config.get('corpus'), target)
    issize = de_dup(tm.config.get('issues'), target)

    if propoganda:
        size = cpsize
    else :
        size = issize

    if (size < (target / 10)):
        state_size = coherence(int(state_size * 0.6))
    else :
        if (size < (target /2)):
            state_size = coherence(int(state_size - 1))



    if propoganda:
        print 'propogranda'
        #tm = TwitterMarkov('example_screen_name', '/home/celesteh/Dropbox/debbie/gifs/twitter_markov/issues.txt', config_file='/home/celesteh/Dropbox/debbie/gifs/twitter_markov/bots.yaml')
        model = None
        tm.models = tm._setup_models(tm.corpora, state_size)

    else:
        print 'issues'
        model = os.path.basename(tm.config.get('issues'))
        #tm = TwitterMarkov('example_screen_name', '/home/celesteh/Dropbox/debbie/gifs/twitter_markov/corpus.txt', config_file='/home/celesteh/Dropbox/debbie/gifs/twitter_markov/bots.yaml')
        tm.models = tm._setup_models([tm.config.get('issues')], state_size)

    return model
# --

def coherence(state_sz):
    probability = random.random() #random.triangular()
    if(probability > 0.9):
        state_sz = max(2, state_sz -4)
    else:
        if(probability > 0.8):
            state_sz = max(2, state_sz -3)
        else:
            if(probability > 0.7):
                state_sz = max(2, state_sz -2)
            else:
                if (probability > 0.6):
                    state_sz = max(2, state_sz -1)
    print 'state_sz is ' + str(state_sz)
    return state_sz

#--

random.seed()
tm = TwitterMarkov('example_screen_name', '/home/celesteh/Dropbox/debbie/gifs/twitter_markov/corpus.txt', config_file='/home/celesteh/Dropbox/debbie/gifs/twitter_markov/bots.yaml')


dict = enchant.DictWithPWL("en_US",tm.config.get('dictionary_words')) #load dictionary

gifs = tm.config.get('gifs')
files = glob.glob((str(gifs) +'/out*.gif'))
if len(files) < 15:
    if len(files) == 1:
        title = 'Last Gif'
        remain = 'This is the last tweet you can send.'
    else:
        title = 'Low Gifs'
        remain = 'There are only '+ str(len(files)) + ' gifs remianing.'

    print 'WARNING: make more gifs!\n' + remain
    pynotify.init("TrumpBot.py")
    notification = pynotify.Notification('Low Gifs', remain, None)
    notification.set_urgency(pynotify.URGENCY_NORMAL)
    try:
        notification.show()
    except Exception, e:
        print str(e)
filename = random.choice(files)

print 'file is ' + filename +'\n'


state_size = coherence(tm.config.get('state_size'))


length = None
propoganda = (random.random() <= 0.4)
if not propoganda:
    #state_size = coherence(5)
    length = 92

try:
    model = learn(state_size, propoganda)
except IOError as e:
    exit(0)

#tm.models = tm._setup_models(tm.corpora, state_size)


print 'composing....\n'
tweet = tm.compose(model = model, max_len=length)

tries = 1

print 'checking...\n'
while not check(tweet):
    if (tries % 10) == 0:
        state_size = coherence(state_size -1) #coherence(state_size)
        try:
            model = learn(state_size, propoganda)
        except IOError as e:
            exit(0)

        #tm.models = tm._setup_models(tm.corpora, state_size)

    tweet = tm.compose(model = model, max_len=length)
    tries = tries + 1
    random.seed()
try:
    de_dup(tm.config.get('history'), tm.config.get('history_size'))
except IOError as e:
    exit(0)

tweet = massage(tweet)
tweet = defrag(tweet)
tweet = hashtags(tweet)

print 'tweet is: ' + tweet + '\n'

tm.api.update_with_media(filename, tweet)

print 'uploaded\n'

archive(tweet)
os.remove(filename)
