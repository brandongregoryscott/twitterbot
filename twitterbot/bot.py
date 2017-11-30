#!/usr/bin/env python3
# -*- coding: utf-8 -*- #
#
# bot.py
# ------

from __future__ import division
from __future__ import unicode_literals

import os
import sys
import codecs
import json
import logging
import twython
from twython import TwythonError
import time
import re
import random
import pickle as pickle

from http.client import IncompleteRead


def ignore(method):
    """
    Use the @ignore decorator on TwitterBot methods you wish to leave
    unimplemented, such as on_timeline and on_mention.
    """
    method.not_implemented = True
    return method


class TwitterBot:
    def __init__(self):
        self.config = {}

        self.custom_handlers = []

        self.config['reply_direct_mention_only'] = False
        self.config['reply_followers_only'] = True

        self.config['autofav_mentions'] = False
        self.config['autofav_keywords'] = []

        self.config['autofollow'] = False

        self.config['tweet_interval'] = 30 * 60
        self.config['tweet_interval_range'] = None

        self.config['reply_interval'] = 10
        self.config['reply_interval_range'] = None
        self.config['reply_chain_filtering'] = True
        self.config['reply_chain_limit'] = 3

        self.config['ignore_timeline_mentions'] = True

        self.config['logging_level'] = logging.DEBUG
        self.config['logging_format'] = '%(asctime)s | %(levelname)s: %(message)s'
        self.config['logging_datefmt'] = '%m/%d/%Y %I:%M:%S %p'
        self.config['storage'] = FileStorage()

        self.state = {}

        # call the custom initialization
        self.bot_init()

        self.api = twython.Twython(self.config['api_key'], self.config['api_secret'], self.config['access_key'],
                                   self.config['access_secret'])

        self.id = self.api.verify_credentials()["id"]
        self.screen_name = self.api.verify_credentials()["screen_name"]

        logging.basicConfig(filename=self.screen_name + '.log',
                            level=self.config['logging_level'],
                            format=self.config['logging_format'],
                            datefmt=self.config['logging_datefmt'])

        self.log = logging.getLogger(self.screen_name)
        self.log.setLevel(self.config['logging_level'])
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(fmt=self.config['logging_format'], datefmt=self.config['logging_datefmt']))
        stdout_handler.setLevel(logging.INFO)
        self.log.addHandler(stdout_handler)

        self.log.info('Initializing bot...')

        try:
            with self.config['storage'].read(self.screen_name) as f:
                self.state = pickle.load(f)

        except IOError:
            self.state['last_timeline_id'] = 1 if 'last_timeline_id' not in self.state.keys() else self.state[
                'last_timeline_id']
            self.state['last_mention_id'] = 1 if 'last_mention_id' not in self.state.keys() else self.state[
                'last_mention_id']

            self.state['last_timeline_time'] = 0 if 'last_mention_id' not in self.state.keys() else self.state[
                'last_mention_id']
            self.state['last_mention_time'] = 0 if 'last_mention_time' not in self.state.keys() else self.state[
                'last_mention_time']

            self.state['last_tweet_id'] = 1 if 'last_tweet_id' not in self.state.keys() else self.state['last_tweet_id']
            self.state['last_tweet_time'] = 1 if 'last_tweet_time' not in self.state.keys() else self.state[
                'last_tweet_time']

            self.state['last_reply_id'] = 0 if 'last_reply_id' not in self.state.keys() else self.state['last_reply_id']
            self.state['last_reply_time'] = 0 if 'last_reply_time' not in self.state.keys() else self.state[
                'last_reply_time']

            self.state['recent_timeline'] = []
            self.state['mention_queue'] = []

        self.state['friends'] = self.api.get_friends_ids()["ids"]
        self.state['followers'] = self.api.get_followers_ids()["ids"]
        self.state['new_followers'] = []
        self.state['last_follow_check'] = 0

        self.log.info('Bot initialized!')

    def bot_init(self):
        """
        Initialize custom state values for your bot.
        """
        raise NotImplementedError("You MUST have bot_init() implemented in your bot! What have you DONE!")

    def _tweet_url(self, tweet):
        return "http://twitter.com/" + tweet['user']['screen_name'] + "/status/" + tweet['id_str']

    def _save_state(self):
        with self.config['storage'].write(self.screen_name) as f:
            pickle.dump(self.state, f)
            self.log.info('Bot state saved')

    def on_scheduled_tweet(self):
        """
        Post a general tweet to own timeline.
        """
        # self.post_tweet(text)
        raise NotImplementedError("You need to implement this to tweet to timeline (or pass if you don't want to)!")

    def on_mention(self, tweet, prefix):
        """
        Perform some action upon receiving a mention.
        """
        # self.post_tweet(text)
        raise NotImplementedError("You need to implement this to reply to/fav mentions (or pass if you don't want to)!")

    def on_timeline(self, tweet, prefix):
        """
        Perform some action on a tweet on the timeline.
        """
        # self.post_tweet(text)
        raise NotImplementedError(
            "You need to implement this to reply to/fav timeline tweets (or pass if you don't want to)!")

    def on_follow(self, f_id):
        """
        Perform some action when followed.
        """
        if self.config['autofollow']:
            try:
                self.api.create_friendship(user_id=f_id, follow=True)
                self.state['friends'].append(f_id)
                self.log.info('Followed user id {}'.format(f_id))
            except TwythonError as e:
                self.log.error('Unable to follow user: {} {}'.format(e.error_code, e.msg))

            time.sleep(3)

        self.state['followers'].append(f_id)

    def post_tweet(self, text, reply_to=None, media=None):
        kwargs = dict()
        kwargs['status'] = text
        cmd = self.api.update_status

        try:
            self.log.info('Tweeting "{}"'.format(text))

            if media is not None:
                media_response = self.api.upload_media(media=media)
                kwargs['media_ids'] = [media_response["media_id"]]
                self.log.info("-- Uploaded media id {}".format(media_response["media_id"]))
            if reply_to:
                self.log.info("-- Responding to status {}".format(self._tweet_url(reply_to)))
                kwargs['in_reply_to_status_id'] = reply_to['id']
            else:
                self.log.info("-- Posting to own timeline")

            tweet = cmd(**kwargs)
            self.log.info('Status posted at {}'.format(self._tweet_url(tweet)))
            return True

        except TwythonError as e:
            self.log.error('Can\'t post status: {} {}'.format(e.error_code, e.msg))
            return False

    def favorite_tweet(self, tweet):
        try:
            self.log.info('Faving ' + self._tweet_url(tweet))
            self.api.create_favorite(id=tweet['id'])

        except TwythonError as e:
            self.log.error('Can\'t fav status: {} {}'.format(e.error_code, e.msg))

    def _ignore_method(self, method):
        return hasattr(method, 'not_implemented') and method.not_implemented

    def _handle_timeline(self):
        """
        Reads the latest tweets in the bots timeline and perform some action.
        self.recent_timeline
        """
        for tweet in self.state['recent_timeline']:
            prefix = self.get_mention_prefix(tweet)
            self.on_timeline(tweet, prefix)

            words = tweet.text.lower().split()
            if any(w in words for w in self.config['autofav_keywords']):
                self.favorite_tweet(tweet)

                # time.sleep(self.config['reply_interval'])

    def _handle_mentions(self):
        """
        Performs some action on the mentions in self.mention_queue
        """
        # TODO: only handle a certain number of mentions at a time?
        for mention in iter(self.state['mention_queue']):
            prefix = self.get_mention_prefix(mention)
            self.on_mention(mention, prefix)
            self.state['mention_queue'].remove(mention)

            if self.config['autofav_mentions']:
                self.favorite_tweet(mention)

                # time.sleep(self.config['reply_interval'])

    def get_mention_prefix(self, tweet):
        """
        Returns a string of users to @-mention when responding to a tweet.
        """
        mention_back = ['@' + tweet['user']['screen_name']]
        mention_back += [s for s in re.split('[^@\w]', tweet['text']) if
                         len(s) > 2 and s[0] == '@' and s[1:] != self.screen_name]

        if self.config['reply_followers_only']:
            mention_back = [s for s in mention_back if
                            s[1:] in self.state['followers'] or s == '@' + tweet['user']['screen_name']]

        return ' '.join(mention_back)

    def filter_reply_chain_tweets(self, timeline):
        filtered_list = timeline.copy()
        for tweet in timeline:
            reply_id = tweet['in_reply_to_status_id']
            reply_count = 0
            while reply_id is not None:
                try:
                    reply_status = self.api.show_status(id=reply_id)
                    reply_id = reply_status['in_reply_to_status_id']
                    if reply_status['user']['id'] == self.id:
                        reply_count += 1
                except TwythonError as e:
                    reply_id = None
                    self.log.error('Can\'t retrieve status {}: {} {}'.format(reply_id, e.error_code, e.msg))
            if reply_count >= self.config['reply_chain_limit']:
                self.log.info('Tweet id {} has past the reply chain limit, removing from queue'.format(tweet['id']))
                filtered_list.remove(tweet)
        return filtered_list

    def _check_mentions(self):
        """
        Checks mentions and loads most recent tweets into the mention queue
        """
        if self._ignore_method(self.on_mention):
            logging.debug('Ignoring mentions')
            return

        try:
            current_mentions = self.api.get_mentions_timeline(since_id=self.state['last_mention_id'], count=100)

            # direct mentions only?
            if self.config['reply_direct_mention_only']:
                current_mentions = [t for t in current_mentions if
                                    re.split('[^@\w]', t['text'])[0] == '@' + self.screen_name]

            if self.config['reply_chain_filtering']:
                current_mentions = self.filter_reply_chain_tweets(current_mentions)

            if len(current_mentions) != 0:
                self.state['last_mention_id'] = current_mentions[0]['id']

            self.state['last_mention_time'] = time.time()

            self.state['mention_queue'] += reversed(current_mentions)

            self.log.info('Mentions updated ({} retrieved, {} total in queue)'.format(len(current_mentions),
                                                                                      len(self.state['mention_queue'])))

        except TwythonError as e:
            self.log.error('Can\'t retrieve mentions: {} {}'.format(e.error_code, e.msg))

        except IncompleteRead as e:
            self.log.error('Incomplete read error -- skipping mentions update')

    def _check_timeline(self):
        """
        Checks timeline and loads most recent tweets into recent timeline
        """
        if self._ignore_method(self.on_timeline):
            logging.debug('Ignoring timeline')
            return

        try:
            current_timeline = self.api.get_home_timeline(count=200, since_id=self.state['last_timeline_id'])

            # remove my tweets
            current_timeline = [t for t in current_timeline if
                                t['user']['screen_name'].lower() != self.screen_name.lower()]

            # remove all tweets mentioning me
            current_timeline = [t for t in current_timeline if
                                not re.search('@' + self.screen_name, t['text'], flags=re.IGNORECASE)]

            if self.config['ignore_timeline_mentions']:
                # remove all tweets with mentions (heuristically)
                current_timeline = [t for t in current_timeline if '@' not in t['text']]

            if len(current_timeline) != 0:
                self.state['last_timeline_id'] = current_timeline[0]['id']

            self.state['last_timeline_time'] = time.time()

            self.state['recent_timeline'] = list(reversed(current_timeline))

            self.log.info('Timeline updated ({} retrieved)'.format(len(current_timeline)))

        except TwythonError as e:
            self.log.error('Can\'t retrieve timeline: {} {}'.format(e.error_code, e.msg))

        except IncompleteRead as e:
            self.log.error('Incomplete read error -- skipping timeline update')

    def _check_followers(self):
        """
        Checks followers.
        """
        self.log.info("Checking for new followers...")

        try:
            self.state['new_followers'] = [f_id for f_id in self.api.get_followers_ids()["ids"] if
                                           f_id not in self.state['followers']]

            self.config['last_follow_check'] = time.time()

        except TwythonError as e:
            self.log.error('Can\'t update followers: {} {}'.format(e.error_code, e.msg))

        except IncompleteRead as e:
            self.log.error('Incomplete read error -- skipping followers update')

    def _handle_followers(self):
        """
        Handles new followers.
        """
        for f_id in self.state['new_followers']:
            self.on_follow(f_id)

    def register_custom_handler(self, action, interval):
        """
        Register a custom action to run at some interval.
        """
        handler = dict()

        handler['action'] = action
        handler['interval'] = interval
        handler['last_run'] = 0

        self.custom_handlers.append(handler)

    def run(self):
        """
        Runs the bot! This probably shouldn't be in a "while True" lol.
        """
        while True:

            # check followers every 15 minutes
            # if self.autofollow and (time.time() - self.last_follow_check) > (15 * 60):
            if self.state['last_follow_check'] > (15 * 60):
                self._check_followers()
                self._handle_followers()

            # check mentions every minute-ish
            # if self.reply_to_mentions and (time.time() - self.last_mention_time) > 60:
            if (time.time() - self.state['last_mention_time']) > 60:
                self._check_mentions()
                self._handle_mentions()

            # tweet to timeline
            # if self.reply_to_timeline and (time.time() - self.last_mention_time) > 60:
            if (time.time() - self.state['last_timeline_time']) > 60:
                self._check_timeline()
                self._handle_timeline()

            # tweet to timeline on the correct interval
            if (time.time() - self.state['last_tweet_time']) > self.config['tweet_interval']:
                self.on_scheduled_tweet()

                # TODO: maybe this should only run if the above is successful...
                if self.config['tweet_interval_range'] is not None:
                    self.config['tweet_interval'] = random.randint(*self.config['tweet_interval_range'])

                self.log.info("Next tweet in {} seconds".format(self.config['tweet_interval']))
                self.state['last_tweet_time'] = time.time()

            # run custom action
            for handler in self.custom_handlers:
                if (time.time() - handler['last_run']) > handler['interval']:
                    handler['action']()
                    handler['last_run'] = time.time()

            # save current state
            self._save_state()

            self.log.info("Sleeping for a bit...")
            time.sleep(30)


class FileStorage(object):
    """
    Default storage adapter.

    Adapters must implement two methods: read(name) and write(name).
    """

    def read(self, name):
        """
        Return an IO-like object that will produce binary data when read from.
        If nothing is stored under the given name, raise IOError.
        """
        filename = self._get_filename(name)
        if os.path.exists(filename):
            logging.debug("Reading from {}".format(filename))
        else:
            logging.debug("{} doesn't exist".format(filename))
        return open(filename, 'rb')

    def write(self, name):
        """
        Return an IO-like object that will store binary data written to it.
        """
        filename = self._get_filename(name)
        if os.path.exists(filename):
            logging.debug("Overwriting {}".format(filename))
        else:
            logging.debug("Creating {}".format(filename))
        return open(filename, 'wb')

    def _get_filename(self, name):
        return '{}_state.pkl'.format(name)
