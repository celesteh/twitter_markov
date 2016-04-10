from twitter_markov import TwitterMarkov
import glob
import random
import os
import time
import re

def massage(tweet):
    tweet = tweet.replace('great', 'grate')
    tweet = tweet.replace('Great', 'Grate')
    tweet = tweet.replace('GREAT', 'GRATE')
    tweet = re.sub('\@[0-9A-Za-z\-\_]?', '', tweet)
    tweet = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', tweet)

    if len(tweet) <= 93:
        tweet = tweet + ' #MakeAmericaGrateAgain'
    if len(tweet) <= 99:
        tweet = tweet + ' @realDonaldTrump'
    if len(tweet) <= 100:
        tweet = tweet + ' #PresidentTrump'
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

files = glob.glob('../out*.gif')
filename = random.choice(files)

print 'file is ' + filename +'\n'

tm = TwitterMarkov('example_screen_name', 'corpus.txt', config_file='bots.yaml')
print 'learning....\n'
tm.learn_peer()
print 'composing....\n'
tweet = tm.compose(max_len=116)


print 'checking...\n'
while not tm.check_tweet(tweet):
    tweet = tm.compose(max_len=116)

tweet = massage(tweet)

print 'tweet is ' + tweet + '\n'

tm.api.update_with_media(filename, tweet)

print 'uploaded\n'

os.remove(filename)
