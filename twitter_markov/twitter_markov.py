# -*- coding: utf-8 -*-
# Copyright 2014-2015 Neil Freeman contact@fakeisthenewreal.org
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals, print_function
import os
import re
import logging
from random import choice
from collections import Iterable
import Levenshtein
import markovify.text
import twitter_bot_utils as tbu
from wordfilter import Wordfilter
from . import checking
import unicodedata

LEVENSHTEIN_LIMIT = 0.70


class TwitterMarkov(object):

    """Posts markov-generated text to twitter"""

    default_model = None
    _recently_tweeted = []
    last_tweet = None

    def __init__(self, screen_name, corpus=None, **kwargs):
        '''
        :screen_name User name to post as
        :corpus Text file to read to generate text.
        :api tweepy.API object
        :dry_run boolean If set, TwitterMarkov won't actually post tweets.
        '''
        if 'api' in kwargs:
            self.api = kwargs.pop('api')
        else:
            self.api = tbu.API(screen_name=screen_name, **kwargs)

        try:
            self.log = self.api.logger
        except AttributeError:
            self.log = logging.getLogger(screen_name)

        self.screen_name = screen_name
        self.config = self.api.config

        self.dry_run = kwargs.pop('dry_run', False)

        try:
            corpus = corpus or self.config.get('corpus')

            if isinstance(corpus, basestring):
                corpora = [corpus]

            elif isinstance(corpus, Iterable):
                corpora = corpus

            else:
                raise RuntimeError('Unable to find any corpora!')

            self.corpora = [b for b in corpora if b is not None]

            self.log.debug('%s, %s', screen_name, self.corpora)

            state_size = kwargs.get('state_size', self.config.get('state_size'))

            self.models = self._setup_models(self.corpora, state_size)

        except RuntimeError as e:
            self.log.error(e)
            raise e

        self.log.debug('models: %s', list(self.models.keys()))

        blacklist = kwargs.get('blacklist') or self.config.get('blacklist', [])
        self.wordfilter = Wordfilter()
        self.wordfilter.add_words(blacklist)

        self.last_tweet = (self.api.user_timeline(count=1))[0]
        self.last_tweet = self.last_tweet.id

        if kwargs.get('learn', True):
            self.learn_parent()

    def _setup_models(self, corpora, state_size):
        """
        Given a list of paths to corpus text files, set up markovify models for each.
        These models are returned in a dict, (with the basename as key).
        """
        self.log.debug('setting up models')
        out = dict()

        state_size = state_size or 3

        try:
            for pth in corpora:
                corpus_path = os.path.expanduser(pth)
                name = os.path.basename(corpus_path)

                with open(corpus_path) as m:
                    out[name] = markovify.text.NewlineText(m.read(), state_size=state_size)

        except AttributeError as e:
            self.log.error(e)
            self.log.error("Probably couldn't find the model file.")
            raise e

        except IOError as e:
            self.log.error(e)
            self.log.error('Error reading %s', corpus_path)
            raise e

        self.default_model = os.path.basename(corpora[0])

        return out

    @property
    def recently_tweeted(self):
        if len(self._recently_tweeted) == 0:
            #recent_tweets = self.api.user_timeline(self.screen_name, count=self.config.get('checkback', 20))
            recent_tweets = self.api.user_timeline()
            self._recently_tweeted = [x.text for x in recent_tweets]

        return self._recently_tweeted



    def check_tweet(self, text):
        text = text.strip().lower()

        if len(text) == 0:
            self.log.info("Rejected (empty)")
            return False

        if self.wordfilter.blacklisted(text):
            self.log.info("Rejected (blacklisted)")
            self.log.info(text)
            return False

        for line in self.recently_tweeted:
            if text in line.strip().lower():
                self.log.info("Rejected (Identical)")
                return False

            if Levenshtein.ratio(re.sub(r'\W+', '', text), re.sub(r'\W+', '', line.lower())) >= LEVENSHTEIN_LIMIT:
                self.log.info("Rejected (Levenshtein.ratio)")
                return False

        return True

    def reply_all(self, model=None, **kwargs):
        mentions = self.api.mentions_timeline(since_id=self.api.last_reply)
        self.log.info('%replying to all...')
        self.log.debug('%s mentions found', len(mentions))

        for status in mentions:
            self.reply(status, model, **kwargs)

    def reply(self, status, model=None, **kwargs):
        self.log.debug('Replying to a mention')

        if status.user.screen_name == self.screen_name:
            self.log.debug('Not replying to self')
            return

        text = self.compose(model, max_len=138 - len(status.user.screen_name), **kwargs)

        reply = '@' + status.user.screen_name + ' ' + text

        self.log.info(reply)
        self._update(reply, in_reply=status.id_str)

    def tweet(self, model=None, **kwargs):
        text = self.compose(model, **kwargs)

        self.log.info(text)
        self._update(text)

    def _update(self, tweet, in_reply=None):
        if not self.dry_run:
            self.api.update_status(status=tweet, in_reply_to_status_id=in_reply)

    def compose(self, model=None, max_len=None, **kwargs):
        '''Format a tweet with a reply.'''

        max_len = min(140, (max_len or self.config.get('tweet_size')))
        model = self.models[model or self.default_model]

        eols = '.!?'#'.?!/:;,'
        text = ''

        while True:
            sent = model.make_sentence(**kwargs)

            if not sent:
                continue

            # convert to unicode in Python 2
            if hasattr(sent, 'decode'):
                sent = sent.decode('utf8')

            # Add eol delimiter if one is missing
            if sent[-1] not in eols and (sent[-2] not in eols and sent[-1] not in u'"\'’”〞❞'):
                sent = sent + choice('?..!!!') #'.!?'

            if len(text) + len(sent) < max_len - 1:
                text = (text + ' ' + sent).strip()

            else:
                # Check tweet against blacklist and recent tweets
                if self.check_tweet(text):
                    # checked out: break and return
                    break
                else:
                    # didn't check out, start over
                    text = ''

        self.log.debug('TwitterMarkov: %s', text)

        return text

    def learn_peer(self, corpus=None, peer=None):
        '''Add recent tweets from peers to corpus'''
        peer = peer or self.config.get('peer')
        corpus = corpus or self.corpora[0]

        if not peer:
            self.log.debug('Cannot teach: missing parent or tweets')
            return

        tweets = self.api.home_timeline(count=150, since_id=self.last_tweet)
        #self.api.user_timeline(parent, since_id=self.api.last_tweet)
        #print(tweets[0])

        try:
            gen = checking.generator(tweets,
                                     no_mentions=self.config.get('filter_mentions'),
                                     no_hashtags=self.config.get('filter_hashtags'),
                                     no_urls=self.config.get('filter_urls'),
                                     no_media=self.config.get('filter_media'),
                                     no_symbols=self.config.get('filter_symbols'),
                                     no_badwords=self.config.get('filter_parent_badwords', True),
                                     no_retweets=self.config.get('no_retweets'),
                                     no_replies=self.config.get('no_replies')
                                    )

            #print str(gen)
            #print 'foo'
            #self.log.error(gen.next())

            self.log.debug('%s is learning', corpus)

            with open(corpus, 'a') as f:
                for tweet in gen:
                    try:
                        #utweet = unicode(tweet, "utf-8")
                        #f.write(str(tweet)+'\n')
                        utweet = unicodedata.normalize('NFKD', tweet).encode('ascii','ignore')
                        utweet = re.sub('\s+', ' ', utweet)
                        f.write(utweet+'\n')
                    except UnicodeEncodeError as e:
                        self.log.error(tweet)
                #f.writelines(tweet+ '\n' for tweet in gen)

        except IOError as e:
            self.log.error('Learning failed for %s', corpus)
            self.log.error(e)


    def learn_search(self, search=None, corpus=None):
        '''Add recent tweets from search to corpus'''
        #search = 'nuclear war'
        search = search or self.config.get('search')
        corpus = corpus or self.corpora[0]

        if not search:
            self.log.debug('Cannot teach: missing search or tweets')
            return

        #tweets = self.api.home_timeline(count=150)
        #self.api.user_timeline(parent, since_id=self.api.last_tweet)
        #print(tweets[0])
        tweets =  self.api.search(search, since_id=self.last_tweet)

        try:
            gen = checking.generator(tweets,
                                     no_mentions=self.config.get('filter_mentions'),
                                     no_hashtags=self.config.get('filter_hashtags'),
                                     no_urls=self.config.get('filter_urls'),
                                     no_media=self.config.get('filter_media'),
                                     no_symbols=self.config.get('filter_symbols'),
                                     no_badwords=self.config.get('filter_parent_badwords', True),
                                     no_retweets=self.config.get('no_retweets'),
                                     no_replies=self.config.get('no_replies')
                                    )

            #print str(gen)
            #print 'foo'
            #self.log.error(gen.next())

            self.log.debug('%s is learning', corpus)

            with open(corpus, 'a') as f:
                for tweet in gen:
                    try:
                        #utweet = unicode(tweet, "utf-8")
                        #f.write(str(tweet)+'\n')
                        utweet = unicodedata.normalize('NFKD', tweet).encode('ascii','ignore')
                        utweet = re.sub('\s+', ' ', utweet)
                        f.write(utweet+'\n')
                    except UnicodeEncodeError as e:
                        self.log.error(tweet)
                #f.writelines(tweet+ '\n' for tweet in gen)

        except IOError as e:
            self.log.error('Learning failed for %s', corpus)
            self.log.error(e)


    def learn_parent(self, corpus=None, parent=None):
        '''Add recent tweets from @parent to corpus'''
        parent = parent or self.config.get('parent')
        corpus = corpus or self.corpora[0]

        if not parent or not last_tweet:
            self.log.debug('Cannot teach: missing parent or tweets')
            return

        tweets = self.api.user_timeline(parent, since_id=self.last_tweet)

        try:
            gen = checking.generator(tweets,
                                     no_mentions=self.config.get('filter_mentions'),
                                     no_hashtags=self.config.get('filter_hashtags'),
                                     no_urls=self.config.get('filter_urls'),
                                     no_media=self.config.get('filter_media'),
                                     no_symbols=self.config.get('filter_symbols'),
                                     no_badwords=self.config.get('filter_parent_badwords', True),
                                     no_retweets=self.config.get('no_retweets'),
                                     no_replies=self.config.get('no_replies')
                                    )

            self.log.debug('%s is learning', corpus)

            with open(corpus, 'a') as f:
                f.writelines(tweet + '\n' for tweet in gen)

        except IOError as e:
            self.log.error('Learning failed for %s', corpus)
            self.log.error(e)
