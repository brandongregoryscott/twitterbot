# twitterbot

## Installation

This forked version of the [twitterbot](https://github.com/thricedotted/twitterbot.git) repository uses
[Twython](https://twython.readthedocs.io/en/latest/) instead of [Tweepy](https://github.com/tweepy/tweepy) and has
been modified to use Python 3 friendly code.

I recommend setting it up in a virtualenv, because, well, yeah.

``` bash
mkdir bots && cd bots
virtualenv venv && source venv/bin/activate
pip install tweepy
git clone https://github.com/brandongregoryscott/twitterbot.git
cd twitterbot && python setup.py install && cd ..
```

Cool! you're ready to start using twitterbot!


## Getting Started

1. Follow Steps 3-5 of [this bot
   tutorial](http://blog.boodoo.co/how-to-make-an-_ebooks/) to create an
   account and obtain credentials for your bot.

2. Copy the template folder from `twitterbot/examples/template` to wherever
   you'd like to make your bot, e.g. `cp -r twitterbot/examples/template
   my_awesome_bot`.

3. Open the template file in `my_awesome_bot` in your favorite text editor.
   Many default values are filled in, but you MUST provide your API/access
   keys/secrets in the configuration in this part. There are also several
   other options which you can change or delete if you're okay with the
   defaults. This version allows you to modify the state dictionary as well,
   if you require that functionality (for example, modifying the last_mention_id).

4. The methods `on_scheduled_tweet`, `on_mention`, and `on_timeline` are what
   define the behavior of your bot, and deal with making public tweets to your
   timeline, handling mentions, and handling tweets on your home timeline
   (e.g., from accounts your bot follows) respectively.

   Some methods that are useful here:
   ```
   self.post_tweet(text)                    # post some tweet
   self.post_tweet(text, reply_to=tweet)    # respond to a tweet

   self.favorite(tweet)                     # favorite a tweet

   self.log(message)                        # write something to the log file
   ```

   Remember to remove the `NotImplementedError` exceptions once you've
   implemented these! (I hope this line saves you as much grief as it would
   have saved me, ha.)

5. Once you've written your bot's behavior, run the bot using `python
   mytwitterbot.py &` (or whatever you're calling the file) in this directory.
   A log file corresponding to the bot's Twitter handle should be created; you
   can watch it with `tail -f <bot's name>.log`.

Check the `examples` folder for some silly simple examples.
