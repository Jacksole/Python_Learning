##IMPORTS
import tweepy
import json
import re
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier

#Loading Creds  
with open (r'C:\Users\ljack099\AppData\Local\Programs\Python\Python36-32\Python Twitter\Naughty_n_Nice\twitter_auth.json') as f:
	keys = json.load(f)

consumer_key = keys['consumer_key']
consumer_secret = keys['consumer_secret']
access_token = keys['access_token']
access_token_secret = keys['access_token_secret']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#An empty list to store the live tweets you will be reading from the Twitter stream
tweets = []

##TWITTER STREAM
class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        tweets.append(status.text.rstrip())
        if len(tweets) > 200:
            myStream.disconnect()

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)

# myStream.filter(track=["Christmas"], languages=['en'])

pos_emojis = [chr(uni) for uni in [128537, 10084, 128525, 128147, 128535, 9786, 128522, 128539, 128149, 128512, 128515, 128538]]
neg_emojis = [chr(uni) for uni in [9785, 128533, 128553, 128530, 128544, 128528, 128550, 128547, 128555, 128534, 128542, 128148, 128546, 128543]]
# netural_emojis = [chr(uni) for uni in 
all_emojis = list(pos_emojis + neg_emojis)

##FETCH SOME TWEETS
myStream.filter(track=all_emojis, languages=['en'])

def store_tweets(file, tweets):
    with open('tweets.txt', 'r',  encoding='utf8') as f:
        old_tweets = f.readlines()
        
    all_tweets = tweets + old_tweets
    all_tweets = list(set(all_tweets))
    all_tweets = [tweet.replace('\n','')+"\n" for tweet in all_tweets]

    with open('tweets.txt', 'w', encoding='utf8') as f:
        f.writelines(all_tweets)

    return all_tweets

##Cleaning Tweet Stream
def clean_tweets(tweets):
    tweets = [tweet.rstrip() for tweet in tweets]
    tweets = [re.sub(r'@\S+', '', tweet) for tweet in tweets]
    tweets = [re.sub(r'http\S+', '', tweet) for tweet in tweets]
    tweets = [tweet.translate({ord(char): '' for char in string.punctuation}) for tweet in tweets]
    return tweets

##Sorting Tweets
def sort_tweets(tweets):
    positive_tweets = [tweet for tweet in tweets if set(tweet) & set(pos_emojis)]
    negative_tweets = [tweet for tweet in tweets if set(tweet) & set(neg_emojis)]
    positive_tweets = [re.sub(r'[^\x00-\x7F]+','', tweet) for tweet in positive_tweets]
    negative_tweets = [re.sub(r'[^\x00-\x7F]+','', tweet) for tweet in negative_tweets]
    return positive_tweets, negative_tweets

##Parsing Tweets 
def parse_tweets(words):
    words = words.lower()
    words = word_tokenize(words)
    words = [word for word in words if word not in stopwords.words("english")]
    word_dictionary = dict([(word, True) for word in words])
    return word_dictionary

## Traning
def train_classifier(positive_tweets, negative_tweets):
    positive_tweets = [(parse_tweets(tweet),'positive') for tweet in positive_tweets]
    negative_tweets = [(parse_tweets(tweet),'negative') for tweet in negative_tweets]
    fraction_pos =  round(len(positive_tweets) * 0.9)
    fraction_neg =  round(len(negative_tweets) * 0.9)

    train_set = negative_tweets[:fraction_pos] + positive_tweets[:fraction_pos]
    test_set =  negative_tweets[fraction_neg:] + positive_tweets[fraction_neg:]
    classifier = NaiveBayesClassifier.train(train_set)
    accuracy = nltk.classify.util.accuracy(classifier, test_set)
    return classifier, accuracy

## Calculating naughtiness
def calculate_naughty(classifier, accuracy, user):
    user_tweets = api.user_timeline(screen_name = user ,count=200)
    user_tweets = [tweet.text for tweet in user_tweets]
    user_tweets = clean_tweets(user_tweets)

    rating = [classifier.classify(parse_tweets(tweet)) for tweet in user_tweets]
    percent_naughty = rating.count('negative') / len(rating)

    if percent_naughty > 0.5:
        print(user, 'is', percent_naughty * 100, "percent NAUGHTY, with an accuracy of ", accuracy * 100)
    else:
        print(user, 'is', percent_naughty * 100, "percent NICE, with an accuracy of ", accuracy * 100)
    return rating
    
#Execute
tweets = store_tweets('tweets.txt', tweets)
tweets = clean_tweets(tweets)
pos_tweets, neg_tweets = sort_tweets(tweets)
classifier, accuracy = train_classifier(pos_tweets, neg_tweets)
calculate_naughty(classifier, accuracy, 'ImCaramelKitten')
