import requests, sys, bs4
import webbrowser
from colors import red, green
from prettytable import PrettyTable

#global vars
al = None
href = None
size = None
title = None
age = None
seeders = None
leechers = None

#support link
link = 'https://kickass.to/usearch/'
#main link
actualLink = None
#query to get them in descending order
query = '/?field=seeders&sorder=desc'

def entry_point(args):
	'''
	Make the request
	'''
	if len(args) > 1:
		global actualLink
		actualLink = link + '%20'.join(args[1:]) + query
	else:
		sys.exit('invalid number of arguments -> usage: dtor <tags>')

	result = requests.get(actualLink)
	#check response
	try:
		result.raise_for_status()
	except Exception as exc:
		sys.exit('invalid request. ' + str(exc))
	return 	bs4.BeautifulSoup(result.text)

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def format_title(text):
	return text[0:35]+'...' if len(text) > 35 else text

def format_seeders(text):
	return green(text) if num(text) > 50 else red(text)

def format_leechers(text):
	return green(text) if num(text) > 20 else red(text)

def new_search(contentFromSearch):
	#We need to get data in the following format:
	#   TorrentName - Size - Age - Seed - Leech
	global al
	al = [tag.get_text() for tag in contentFromSearch.find_all('td', {'class':'center'})]
	global href
	href = [tag_a.get('href') for tag_a in contentFromSearch.find_all('a', {'title':'Download torrent file'})]
	global size
	size = [tag_td.get_text() for tag_td in contentFromSearch.find_all('td', {'class':'nobr'}) ]
    global title
	title = [tag_a.get_text() for tag_a in contentFromSearch.find_all('a', {'class':'cellMainLink'})]
    global age
	age = al[2::5]
    global seeders
	seeders = al[3::5]
    global leechers
	leechers = al[4::5]
	#creating table with data
	table = PrettyTable(['ID', 'Torrent_Name', 'Size', 'Age', 'Seeds', 'Leechers'])
	for idx in range(10 if len(title) > 10 else len(title)):
		table.add_row([str(idx+1), format_title(title[idx]), size[idx], age[idx], format_seeders(seeders[idx]), format_leechers(leechers[idx])])
	return table

def download_torr(cmdParts):
	torrFile = requests.get(href[int(cmdParts[1])])
	try:
		torrFile.raise_for_status()
	except Exception:
		print('Download was not completed..')
	actualTorrentFile = open(title[int(cmdParts[1])]+'.torrent', 'wb')
	for chunk in torrFile.iter_content(100000):
		actualTorrentFile.write(chunk)

def open_web_page():
	'''
	open the webpage that shows the entire search
	'''
	webbrowser.open(actualLink)

def list_all_cmd():
	'''
	Shows all options.
	'''
	print('--search {tags} -> New search with specified tags.')
	print('--download [id] -> List all commands.')
	print('--webpage       -> Open the webpage with the entire results.')
	print('--exit          -> Exit application.')	
	print('--help          -> List all commands.')

def cmd(_cmd):
	'''
	Simple choice according to the received command
	'''
	if _cmd == '--help':
		list_all_cmd()
	elif '--download' in _cmd:
		download_torr(_cmd.split(' '))
	elif _cmd == '--webpage':
		open_web_page()
	elif '--search' in _cmd:
		print(new_search(entry_point(_cmd.split(' '))))
	elif _cmd == '--exit':
		global wantsToExit
		wantsToExit=True
	else:
		print("Comando Inválido !")

#script part
wantsToExit = False
print(new_search(entry_point(sys.argv)))
while wantsToExit is not True:
	cmd(input('>> '))
