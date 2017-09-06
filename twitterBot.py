#Import objects for use later in the script...
import time
from termcolor import colored
import threading
import feedparser
import cgi
import HTMLParser
import os
import sys

#The time duration (in seconds) prior to first network
#dependency...
initializeTime = 180

#Store terminal color codes...
class colorCodes:
	OK = 'green'
	ERR = 'red'
	progress = 'yellow'

#The URL of the ODROID RSS feed...
URL = 'https://forum.odroid.com/feed.php'

#The interval between each attempted feed update poll...
pollUpdate = 1800

#Set Twitter API reference in global scope...
twitter = False

#Import information in preparation for Twitter API instance...
from twython import Twython
from keys import (
	consumer_key,
	consumer_secret,
	access_token,
	access_token_secret
)

#Program script main function...
def initialize():
	print __file__
	print str(os.path.dirname(__file__))
	try:
		logFile = open(os.path.dirname(__file__)+'/logFile.txt','a')
	except:
		logFile = open(os.path.dirname(__file__)+'/logFile.txt','w')

	logFile.write("=========================="+'\n')

	print colored('Initializing the program...',colorCodes.OK)
	logFile.write('Initializing the program...\n')
	#Set a time delay to allow the computer to reset its clock to
	#accurate time prior to making network requets...
	print colored('Waiting for clock caliboration...',colorCodes.OK)
	logFile.write('Waiting for clock caliboration...\n')
	#Set timeout to allow clock caliboration...
	time.sleep(initializeTime)
	#Create a Twitter API object instance...
	print colored('Connecting to Twitter...',colorCodes.OK)
	logFile.write('Connecting to Twitter...\n')
	try:
		global twitter
		twitter = Twython(
			consumer_key,
			consumer_secret,
			access_token,
			access_token_secret
		)
	except:
		print colored('Unable to connect to Twitter!',colorCodes.ERR)
		logFile.write('Unable to connect to Twitter!\n')


	print colored('Connected to Twitter!',colorCodes.OK)
	logFile.write('Connected to Twitter!\n')
	
	#Poll the RSS feed...
	pollRSS()
	return

def pollRSS():

	def tweet(RSS_POST):
		print colored('Now tweeting... '+RSS_POST.title+'\n',colorCodes.progress)
		message = RSS_POST.title[:144-len(RSS_POST.link)]+'\n'+RSS_POST.link
		try:
			twitter.update_status(status=message)
		except Exception, e:
			print colored('Error Tweeting the message. '+str(e),colorCodes.ERR)		
			logFile.write('Error Tweeting the message.'+str(e)+'\n')

		return

	print colored('Polling for new RSS information...',colorCodes.OK)

	#Load and parse the RSS feed...
	try:
		feed = feedparser.parse(URL)
	except:
		print colored('Error accessing and parsing from the specified URL!',colorCodes.ERR)

	#Open the ID storage file for both reading and writing...
	idFile = open('/home/odroid/twitterBot/v0.8/id/id.txt','r+')

	#Open the ID file...
	idFile.seek(0)
	#Read the ID file...
	lastPostedID = idFile.read()

	if lastPostedID == '':
		#ID file is empty...
		print colored('ID storage file is empty. Writing to file...',colorCodes.progress)
		#Write the ID of the oldest post to the ID storage file...
		print colored(feed.entries[-1].id,colorCodes.progress)
		idFile.seek(0)
		idFile.write(cgi.escape(feed.entries[-1].id))
		idFile.close()
		pollRSS()
	else:
		#The ID file contains an ID...

		#Loop through all entries and store the ID in the IDs list...
		IDs = []
		for entry in feed.entries:
			IDs.append(cgi.escape(entry.id))

		'''
		Loop through IDs starting with the index and end at 0...
		'''

		try:
			index = IDs.index(lastPostedID)
			if index > 0:
				for i in xrange(index,0,-1):
					tweet(feed.entries[i])

				#Update the ID file...
				print colored('Updating the ID file...',colorCodes.OK)
				idFile.seek(0)
				idFile.truncate()
				idFile.write(cgi.escape(feed.entries[0].id))
				idFile.close()
			else:
				print colored('There are no new RSS posts.',colorCodes.OK)
		except:
			#The last posted ID has no match in the list... 
			#Find the oldest post assuming the ID is above the 50 cap from the last interval...
			print colored(lastPostedID + ' was not found.',colorCodes.ERR)
			print colored('Writing the oldest ID to record...',colorCodes.progress)
			#Write the oldest RSS post entry ID to the ID file...
			idFile.seek(0)
			idFile.truncate()
			idFile.write(cgi.escape(feed.entries[-1].id))
			idFile.close()

	#Set this function to iterate again...
	threading.Timer(pollUpdate,pollRSS).start()

	return
	

initialize()
