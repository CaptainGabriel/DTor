class Torrent:
    def __init__(self, id, name, size, age, seeds, leechers):
        self.id = id
        self.name = name
        self.size = size
        self.age = age
        self.seeds = seeds
        self.leechers = leechers

    def __str__(self):
        return self.id + " - " + self.name + " - " + self.size + " - " + self.age + " - " + self.seeds + " - " + self.leechers




import requests, sys, bs4
import webbrowser, argparse, collections
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

#dict of objects
torrents_found = {}

#support link
link = 'https://kickass.to/usearch/'
#main link
actual_link = None
#query to get them in descending order
query = '/?field=seeders&sorder=desc'



def entry_point(args):
    '''
    Make the request
    '''
    if len(args) > 0:
        global actual_link
        actual_link = link + '%20'.join(args) + query
        print(actual_link)
    else:
        sys.exit('invalid number of arguments -> usage: dtor <tags>')
    result = requests.get(actual_link)
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
    return text[0:25]+'...' if len(text) > 25 else text

def format_seeders(text):
    return green(text) if num(text) > 50 else red(text)

def format_leechers(text):
    return green(text) if num(text) > 20 else red(text)

def new_search(content):
    #We need to get data in the following format:
    #   TorrentName - Size - Age - Seed - Leech
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
    for idx in range(15 if len(title) > 15 else len(title)):
        rowTitle = format_title(title[idx])
        rowSeeder = format_seeders(seeders[idx])
        rowLeecher = format_leechers(leechers[idx])
        age = age[idx]
        size = size[idx]
        id = str(idx+1)
        table.add_row([id, rowTitle, size, age, rowSeeder, rowLeecher])
        #the creation
        torr = Torrent(id, title[idx] , size, age, rowSeeder, rowLeecher)
        #into dict
        torrents_found[idx] = torr
    return table

def download_torr(cmdParts):
    torrFile = requests.get(href[int(cmdParts[1])])
    try:
        torrFile.raise_for_status()
    except Exception:
        print('Download was not completed..')
    actualTorrentFile = open(title[int(cmdParts[1])] + '.torrent', 'wb')
    for chunk in torrFile.iter_content(100000):
        actualTorrentFile.write(chunk)

def open_web_page():
    '''
    Open the webpage that shows the entire search
    Associated with the command "--webpage".
    '''
    if actual_link is None:
        print('Search for something first.')
    else:
        webbrowser.open(actual_link)

def list_all_cmds():
    '''
    Shows all options.
    '''
    print('--search {tags 1..+} -> New search with specified tags.')
    print('--download [id] -> List all commands.')
    print('--webpage       -> Open the webpage with the entire results.')
    print('--exit          -> Exit application.')
    print('--list          -> List all commands.')
    print('--id [id]       -> More info about a specific torrent.')
    

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
    return parser
    
def cmd(cmd_line, parser):
    '''
    Interpreter of all cmds
    '''
    args = parser.parse_args(cmd_line.split())
    if args.list:
        list_all_cmds()
    elif args.exit:
        global wantsToExit
        wantsToExit = True
    elif args.search and len(args.search) > 0:
        argss = ' '.join(args.search)
        print(new_search(entry_point((argss).split(' '))))
    elif args.webpage:
        open_web_page()
    elif args.id and len(args.id) == 1:
        print(torrents_found[num(args.id[0])-1])
        
    
#script part
wantsToExit = False
parser = register_cmds()
while (wantsToExit is not True):
    cmd(input('>> '), parser)
print("bye bye! ")
