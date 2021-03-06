import requests, sys, bs4
import webbrowser, argparse, collections, threading
from colors import red, green
from prettytable import PrettyTable
import re

#global vars
al = None
href = None
size = None
title = None
age = None
seeders = None
leechers = None

html_space = '%20'

#dict of objects
torrents_found = {}

#support link
link = 'https://kickass.unblocked.red/usearch/'
#main link
actual_link = None
#query to get them in descending order
query = '/?field=seeders&sorder=desc'


class Torrent:
    '''
    The representation of a torrent.
    '''
    def __init__(self, id, name, size, age, seeds, leechers):
        self.id = id
        self.name = name
        self.size = size
        self.age = age
        self.seeds = seeds
        self.leechers = leechers

    def __str__(self):
        return self.id + " - " + self.name + " - " + self.size + " - " + self.age + " - " + self.seeds + " - " + self.leechers


class AsyncDownload(threading.Thread):
    '''
    Class that is used to download a torrent async.
    '''
    def __init__(self, id_of_torrent):
        threading.Thread.__init__(self)
        self.id_of_torrent = id_of_torrent

    def run(self):
        try:
            print("Debug: " + href[self.id_of_torrent])
            valid_tor_url = self.transform_into_valid_url(href[self.id_of_torrent])
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36"}
            torr_file = requests.get(valid_tor_url, headers)
            torr_file.raise_for_status()
        except Exception as e:
        	print(e)
        	return
        actual_torrent_file = open(title[self.id_of_torrent] + '.torrent', 'wb')
        for chunk in torr_file.iter_content(100000):
            actual_torrent_file.write(chunk)

    def transform_into_valid_url(self, url):
    	'''
    	The url might be from torcache or some other service.
    	The problem is it needs to start with a valid scheme
    	such as 'http//'.
    	'''
    	return "http://" + url[2:] 



def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def parse_link(words):
    global actual_link
    if len(words):
        actual_link = link + html_space.join(words) + query
    else:
        actual_link = link + words + query

def format_title(text):
    return text[0:25]+'...' if len(text) > 25 else text

def format_seeders(text):
    return green(text) if num(text) > 50 else red(text)

def format_leechers(text):
    return green(text) if num(text) > 20 else red(text)

def make_http_request(args=None):
    '''
    Make the request
    '''
    if args:
        parse_link(args)
    result = requests.get(actual_link)
    try:
        result.raise_for_status()
    except Exception as exc:
        sys.exit('Invalid Request. ' + str(exc))
        return #need to test the consequences of this return
    return 	bs4.BeautifulSoup((result.text).encode('cp850','replace'), "html.parser")

def parse_search_results(content):
    '''
    Given html content, performs a kind of parsing in order to
    retrive the important content.
    Builds objects with following info:
        TorrentName - Size - Age - Seed - Leech
    Associated with the command "--search"
    '''
    global al

    al = [tag.get_text() for tag in content.find_all('td',{'class':'center'})]
    global href
    href = [tag_a.get('href') for tag_a in content.find_all('a',{'title':'Download torrent file'})]
    global size
    size = [tag_td.get_text() for tag_td in content.find_all('td',{'class':'nobr'}) ]
    global title
    title = [tag_a.get_text() for tag_a in content.find_all('a',{'class':'cellMainLink'})]
    global age
    age = al[2::5]
    global seeders
    seeders = al[3::5]
    global leechers
    leechers = al[4::5]
    #creating table with data
    table = PrettyTable(['ID', 'Torrent_Name', 'Size', 'Age', 'Seeds','Leechers'])
    for idx in range(25 if len(title) == 25 else len(title)):
        rowTitle = format_title(title[idx])
        rowSeeder = format_seeders(seeders[idx])
        rowLeecher = format_leechers(leechers[idx])
        ageValue = age[idx]
        sizeValue = size[idx]
        id = str(idx+1)
        table.add_row([id, rowTitle, sizeValue, ageValue, rowSeeder, rowLeecher])
        #if idx < 15:
        #the creation
        torr = Torrent(id, title[idx] , sizeValue, ageValue, rowSeeder, rowLeecher)
        #into dict
        torrents_found[idx] = torr
    return table

def open_web_page():
    '''
    Open the webpage that shows the entire search
    Associated with the command "--webpage".
    '''
    if actual_link is None:
        print('Search for something first.')
    else:
        webbrowser.open(actual_link)

def turn_page(page_number):
    global actual_link
    if actual_link:
        #pattern = re.compile('\/\d+\/')
        #if pattern.search(actual_link):
        #    actual_link = actual_link.replace('\/\d+\/', '/' + page_number + '/?field');
        #else:
        actual_link = actual_link.replace("/?field", '/' + page_number + "/?field");
        print(actual_link)
        print(parse_search_results(make_http_request()))
    else:
        print('Search for something first.')

def list_all_cmds():
    '''
    Shows all options.
    Associated with the command "--list".
    '''
    print('--search {tags 1..+} -> New search with specified tags.')
    print('--download [id] -> Download the torrent file for the ID given.')
    print('--webpage       -> Open the webpage with the entire results.')
    print('--exit          -> Exit application.')
    print('--list          -> List all commands.')
    print('--id       [id] -> More info about a specific torrent.')
    print('--page     [n]  -> Turn the page in order to see more files')

def register_cmds():
    '''
    Register of all cmds
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', '-l', action ='store_true', help='List all supported commands.')
    parser.add_argument('--exit', '-e', action ='store_true', help='Asks to shut down the applications.')
    parser.add_argument('--search', '-s', nargs = '+', help='Starts a new search with given keywords.')
    parser.add_argument('--webpage','-webp', action = 'store_true', help = 'Open the webpage with the entire results.')
    parser.add_argument('--id', nargs = 1, help = 'More information about a given torrent ID.')
    parser.add_argument('--download', '-d', nargs = 1, help = 'Download the torrent file for the ID given.')
    parser.add_argument('--page', '-p', nargs = 1, help = 'Turn the page')
    return parser

def cmd(cmd_line, parser):
    '''
    Interpreter of all cmds.
    '''
    args = parser.parse_args(cmd_line.split())
    if args.list:
        list_all_cmds()
    elif args.exit:
        global wantsToExit
        wantsToExit = True
    elif args.search and len(args.search) > 0: 
        argss = ' '.join(args.search)
        print(parse_search_results(make_http_request((argss).split(' '))))
    elif args.webpage:
        open_web_page()
    elif args.id and len(args.id) == 1:
        print(torrents_found[num(args.id[0])-1])
    elif args.download and len(args.download) == 1:
        AsyncDownload(num(args.download[0])).start()
    elif args.page and len(args.page) == 1:
        turn_page(args.page[0])

#script
wantsToExit = False
parser = register_cmds()
while (wantsToExit is not True):
    cmd(input('>> '), parser)
print("bye bye! ")
