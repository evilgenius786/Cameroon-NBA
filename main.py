import json
import math
import os.path
import time
import traceback
from datetime import datetime
from threading import Thread, Semaphore

import requests
from bs4 import BeautifulSoup
from pytz import timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# from webdrivermanager import ChromeDriverManager
from webdriver_manager.chrome import ChromeDriverManager


t = 1
timeout = 10

debug = False

headless = False
images = False
max = True
not_found = []
incognito = False
test = False
cover_semaphore = Semaphore(10)
projections = {}
if os.path.isfile('projections.json'):
    with open('projections.json') as ifile:
        projections = json.load(ifile)
players_translation = {}
if os.path.isfile('players_translation.json'):
    with open('players_translation.json') as ifile:
        players_translation = json.load(ifile)
else:
    with open('players_translation.json', 'w') as outfile:
        json.dump(players_translation, outfile)
stats = {
    "Points": {"bp": "156", "covers": "points-scored", 'rg': 'PTS'},
    "Rebounds": {"bp": "157", "covers": "total-rebounds", 'rg': 'REB'},
    "Assists": {"bp": "151", "covers": "total-assists", 'rg': 'AST'},
    "Pts+Rebs+Asts": {"bp": "338", "covers": "total-points,-rebounds,-and-assists", 'rg': 'P-R-A'},
    "Pts+Rebs": {"bp": "336", "covers": "points-and-rebounds", 'rg': 'P-R'},
    "Pts+Asts": {"bp": "335", "covers": "points-and-assists", 'rg': 'P-A'},
    "Rebs+Asts": {"bp": "337", "covers": "rebounds-and-assists", 'rg': 'R-A'},
}
ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

today = datetime.now(timezone('US/Central')).strftime('%Y-%m-%d')
if not os.path.isfile(f'history-{today}.json'):
    for file in os.listdir():
        if file.startswith('history-'):
            os.remove(file)
    with open(f'history-{today}.json', 'w') as outfile:
        json.dump({}, outfile)
if not os.path.isfile(f'rg-{today}.txt'):
    with open(f'rg-{today}.txt', 'w') as outfile:
        outfile.write('')

with open(f'rg-{today}.txt') as ifile:
    rg_list = ifile.read().splitlines()
with open(f'history-{today}.json') as infile:
    history = json.load(infile)


def getRotogrinders():
    if test:
        with open("rotogrinders.json") as ifile:
            return json.load(ifile)
    headers = {
        'authority': 'rotogrinders.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'cookie': 'remember_82e5d2c56bdd0811318f0cf078b78bfc=eyJpdiI6ImJKOW1kOW1UTWNJQTJldVVpbDJsWXc9PSIsInZhbHVlIjoiekIrRlI5QUdcL2F4RFo0ZGRCVUx4WCtSOUs5cXdvRkZhcG1rcVwveW1DTHVLQjJqYllFYVh5T0xZVkRIUlF3UW9UIiwibWFjIjoiMzg5NzhhMjJlNjBmNmIwNDc1MzE3ZjVhZjQzZWZlNDVjNzY4N2QwZTQ2OGZhMWVjMTNkNjU2MmU3ZmM0MDA5NCJ9; bc-cookie-consent=1; _vwo_uuid_v2=DDA7B76245EFD205288E1E7C552FB555E|c0cf04c5999aba98472b39cedf9ebb05; laravel_session=eyJpdiI6InJPeUNmQ1lEM3dWaWpadlh6TnhzbVE9PSIsInZhbHVlIjoiYVdHazlKUVwvZVR2ZmpZMXpVUkJTeFdKcGlHQ2VRNzhkTGN1U2Y1ejBtalMzOUp6enVZMzF0S2gzbXVVWmdEaFBiWkdWMHNBeG9ydWJOUG0yUjZvbkFBPT0iLCJtYWMiOiIxN2JjYTYxOGI4Y2QzNjBmYjMzMWZkYTVlZTlhMGYyMjQxMjY3YzUwZjI2ZDkzYzY0MzJlZjc2NzYxZWRkNDZlIn0%3D; logged_in=eyJpdiI6IlZWb3JONVg5SHNDaHd4RkhTVGZ5UkE9PSIsInZhbHVlIjoiTEpUMERndXRXdlRlMGJZcXB0Y2NhUT09IiwibWFjIjoiYzI1M2Y4MWY2MTA1NjNiZmJhNTkxMzc5NDAwODhhMGQyMmFkNzI5MmI0ZGE5MDJhYWUxYWE1NGJkZmQ4N2IyZSJ9',
        'dnt': '1',
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }

    params = (
        ('site', 'fanduel'),
    )
    url = 'https://rotogrinders.com/grids/nba-premium-projections-3350865'
    response = requests.get(url, headers=headers, params=params)
    data = []
    for line in response.text.split('\n'):
        if 'data =' in line:
            data = json.loads(line.split('data = ')[1][:-1].strip())
    rg_data = {}
    for player in data:
        name = player['PLAYER']
        tmp_data = {}
        for stat in stats:
            if stat == 'Rebs+Asts':
                tmp_data[stat] = player['REB'] + player['AST']
            else:
                tmp_data[stat] = player[stats[stat]['rg']]
        rg_data[name] = tmp_data
    with open('rotogrinders.json', 'w') as outfile:
        json.dump(rg_data, outfile, indent=4)
    return rg_data


def getCoverPlayer(url, covers_data):
    with cover_semaphore:
        try:
            print(f"[*] Fetching data for player {url.split('/')[-1]}...")
            soup = BeautifulSoup(requests.get(url).text, 'html.parser')
            player = soup.find('img', {"class": "covers-CoversMatchups-playerImage", "alt": True})['alt']
            for key, value in stats.items():
                section = soup.find('section', {"id": value["covers"]})
                if not section:
                    continue
                game = section.find('div', {"class": "other-odds-label u-nowrap"}).text.split()[0]
                total = section.find('tfoot').find_all('td')[1].text
                if player not in covers_data:
                    covers_data[player] = {}
                if key not in covers_data[player]:
                    covers_data[player][key] = {}
                covers_data[player][key] = round((float(game) + float(total)) / 2, 2)
                stats_table = section.find('table', {"id": "stats-table"}).find('tbody')
                covers_data[player][f"{key} Last 10"] = [int(tr.find_all("td")[2].text.split("(")[0]) for tr in
                                                         stats_table.find_all("tr") if
                                                         tr.find_all("td")[2].text != 'DNP']
                covers_data[player][f"{key} Close"] = [float(tr.find_all("td")[3].text) for tr in
                                                       stats_table.find_all("tr") if tr.find_all("td")[3].text != '-']
                # print(json.dumps(covers_data, indent=4))
            # return covers_data
        except:
            traceback.print_exc()
            # input(f"[-] Failed to fetch data for player {url}...")


def getCovers():
    if test:
        with open("covers.json") as ifile:
            return json.load(ifile)
    print("[+] Fetching data from Covers...")
    soup = BeautifulSoup(requests.get('https://www.covers.com/sport/basketball/nba/player-props').text, 'html.parser')
    teams = [a['href'] for a in soup.find_all('a', {'class': 'matchup-cta'})]
    covers_data = {}
    threads = []
    for team in teams:
        print(f"[*] Fetching data for team {team.split('/')[-1]}...")
        soup = BeautifulSoup(requests.get(f'https://www.covers.com{team}').text, 'html.parser')
        players = [a['href'] for a in soup.find_all('a', {'data-event-name': 'points-scored'})]
        for player in players:
            t = Thread(target=getCoverPlayer, args=(f'{player}', covers_data,))
            threads.append(t)
            t.start()
    for thread in threads:
        thread.join()
    with open('covers.json', 'w') as outfile:
        json.dump(covers_data, outfile)
    # print(json.dumps(covers_data, indent=4))
    return covers_data


def getEventId():
    headers = {
        'authority': 'api.bettingpros.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'dnt': '1',
        'origin': 'https://www.bettingpros.com',
        'referer': 'https://www.bettingpros.com/nba/odds/player-props/points/',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'x-api-key': 'CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh',
    }
    params = (
        ('sport', 'NBA'),
        # ('date', '2023-01-02'),
        ('date', datetime.now(timezone('US/Central')).strftime("%Y-%m-%d")),
    )
    response = requests.get('https://api.bettingpros.com/v3/events', headers=headers, params=params)
    return ":".join([f"{event['id']}" for event in response.json()['events']])


def getBettingPros():
    headers = {
        'authority': 'api.bettingpros.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'dnt': '1',
        'origin': 'https://www.bettingpros.com',
        'referer': 'https://www.bettingpros.com/nba/odds/player-props/points-rebounds/',
        'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': ua,
        'x-api-key': 'CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh',
    }
    bettingpros = {}
    if test:
        with open("bettingpros.json", "r") as f:
            bettingpros = json.load(f)
    else:
        for stat in stats:
            print(f"[+] Getting {stat} from bettingpros.com")
            params = (
                ('sport', 'NBA'),
                ('market_id', stats[stat]['bp']),
                ('event_id', getEventId()),
                ('location', 'ALL'),
                ('live', 'true'),
            )
            response = requests.get('https://api.bettingpros.com/v3/offers', headers=headers, params=params)
            # print(json.dumps(response.json(), indent=4))
            bettingpros[stat] = response.json()
        with open("bettingpros.json", "w") as f:
            json.dump(bettingpros, f, indent=4)
    bp_data = {}
    for stat in stats:
        if "offers" not in bettingpros[stat]:
            continue
        for offer in bettingpros[stat]['offers']:
            for selection in offer['selections']:
                found = False
                for book in selection['books']:
                    if book['id'] == 12:
                        odd = ""
                        for line in book['lines']:
                            if not line['is_off']:
                                odd = f"{line['line']} ({line['cost']})"
                                found = True
                        name = offer['participants'][0]['name'].strip()
                        if name not in bp_data:
                            bp_data[name] = {}
                        if stat not in bp_data[name]:
                            bp_data[name][stat] = {}
                        bp_data[name][stat][selection['selection']] = odd
                if not found:
                    for book in selection['books']:
                        if book['id'] == 13:
                            odd = ""
                            for line in book['lines']:
                                odd = f"{line['line']} ({line['cost']})"
                                found = True
                                print(f"[+] {offer['participants'][0]['name']} {stat} found from consensus line")
                            name = offer['participants'][0]['name'].strip()
                            if name not in bp_data:
                                bp_data[name] = {}
                            if stat not in bp_data[name]:
                                bp_data[name][stat] = {}
                            bp_data[name][stat][selection['selection']] = odd
                    # try:
                    #     name = offer['participants'][0]['name'].strip()
                    #     ol = selection['opening_line']
                    #     if name not in bp_data:
                    #         bp_data[name] = {}
                    #     if stat not in bp_data[name]:
                    #         bp_data[name][stat] = {}
                    #     bp_data[name][stat][selection['selection']] = f"{ol['line']} ({ol['cost']})"
                    #     print(f"[+] {offer['participants'][0]['name']} {stat} found from Open Line")
                    #     found = True
                    # except:
                    #     traceback.print_exc()
                if not found:
                    print(
                        f"[+] {offer['participants'][0]['name']} {selection['selection']} {stat} not found on bettingpros.com")
    # print(json.dumps(bp_data, indent=4))
    return bp_data


def getPrizePicks():
    print("Fetching data...")
    if test:
        with open('prizepicks.json', 'r') as dfile:
            data = json.load(dfile)
    else:
        driver = getChromeDriver()
        url = 'https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true'
        driver.get(url)
        res = driver.find_element(By.XPATH, '//*').text
        data = json.loads(res)
        with open('prizepicks.json', 'w') as f:
            json.dump(data, f, indent=4)
    players = {}
    for player in data["included"]:
        players[player["id"]] = player["attributes"]
    player_data = []
    for data in data['data']:
        pid = data["relationships"]["new_player"]["data"]["id"]
        if data['attributes']['stat_type'] not in stats.keys():
            continue
        player = {
            "Name": players[pid]["name"].strip(),
            "Position": players[pid]["position"],
            "Team": players[pid]["team"],
            "Stat": data['attributes']['stat_type'],
            "Score": data['attributes']['line_score'],
            "Opp": data['attributes']['description'],
            "Over": "",
            "Under": "",
            "Proj": "coming soon",
            "Diff": 0.0,
        }
        player_data.append(player)
    return player_data


def compileOdds():
    prizepicks = getPrizePicks()
    bettingpros = getBettingPros()
    covers = getCovers()
    rg = getRotogrinders()
    if len(rg_list) > 0:
        rg = getRotogrinders()
    # print(json.dumps(bettingpros,indent=4))
    rows = []
    for player in prizepicks:
        try:
            row = player.copy()
            if player["Name"] not in history:
                history[player["Name"]] = {}
            if player["Stat"] not in history[player["Name"]]:
                history[player["Name"]][player["Stat"]] = []
            rname = player['Name']
            bname = player['Name']
            # if player['Name'] not in bettingpros:
            #     found = False
            #     if "I" in player['Name']:
            #         player['Name'] = player['Name'].replace("I", "").strip()
            #     lname = player['Name'].split(" ")[-1].strip()
            #     for name in bettingpros:
            #         # print(json.dumps(name, indent=4))
            #         if lname in name and name.startswith(player['Name'][0]):
            #             bname = name
            #             print(f"[+] {player['Name']} found as {name} on bettingpros")
            #             found = True
            #             break
            #     if not found:
            #         print(f"[-] {player['Name']} not found in bettingpros.com")
            #         continue
            # if player['Name'] not in covers:
            #     # print(f"[-] {player['Name']} not found in {covers.keys()}")
            #     if "I" in player['Name']:
            #         player['Name'] = player['Name'].replace("I", "").strip()
            #     if "Jr." in player['Name']:
            #         rname = player['Name'].replace("Jr.", "").strip()
            #     else:
            #         found = False
            #         lname = player['Name'].split(" ")[-1]
            #         for name in covers:
            #             # print(json.dumps(name, indent=4))
            #             if lname in name and name.startswith(player['Name'][0]):
            #                 rname = name
            #                 print(f"[+] {player['Name']} found as {name} on covers")
            #                 found = True
            #                 break
            #         if not found:
            #             print(f"[-] {player['Name']} not found in covers.com")
            #             continue
            if player['Name'] in str(not_found):
                continue
            if player['Name'] not in covers:
                if player['Name'] not in players_translation:
                    print(f"[-] {player['Name']} not found in covers.com")
                    not_found.append(f"{player['Name']} - covers")
                    continue
                else:
                    rname = players_translation[player['Name']]
                    print(f"[+] {player['Name']} found as {rname} on covers")
            if player['Name'] not in bettingpros:
                if player['Name'] not in players_translation:
                    print(f"[-] {player['Name']} not found in bettingpros.com")
                    not_found.append(f"{player['Name']} - bettingpros")
                    continue
                else:
                    bname = players_translation[player['Name']]
                    print(f"[+] {player['Name']} found as {bname} on bettingpros")
            if player['Stat'] not in bettingpros[bname]:
                print(f"[-] {player['Name']} ({player['Stat']}) not found in bettingpros.com")
                continue
            # print(json.dumps(bettingpros[player['Name']],indent=4))
            if 'over' not in bettingpros[bname][player['Stat']] or bettingpros[bname][player['Stat']]['over'] == '':
                print(f"[-] {player['Name']} ({player['Stat']}) over not found in bettingpros.com")
                continue
            if 'under' not in bettingpros[bname][player['Stat']] or bettingpros[bname][player['Stat']]['under'] == '':
                print(f"[-] {player['Name']} ({player['Stat']}) under not found in bettingpros.com")
                continue
            row['Over'] = bettingpros[bname][player['Stat']]['over']
            row['Under'] = bettingpros[bname][player['Stat']]['under']
            if rname not in covers:
                print(f"[-] {player['Name']} ({player['Stat']}) not found in covers.com")
                continue
            consensus = 0
            row['Proj'] = ''
            try:
                consensus = float(row['Over'].split('(')[0])
                if consensus not in history[player['Name']][player['Stat']]:
                    history[player['Name']][player['Stat']].append(consensus)
                    with open(f'history-{today}.json', 'w') as f:
                        json.dump(history, f, indent=4)
                over = float(row['Over'].split('(')[1].replace(")", "").replace('-', ''))
                under = float(row['Under'].split('(')[1].replace(")", "").replace('-', ''))
                print(player['Name'], player['Stat'], consensus, min(history[player['Name']][player['Stat']]))
                if len(rg_list) > 0 and f"{player['Name']}-{player['Stat']}" in rg_list:
                    print(f"[+] {player['Name']} ({player['Stat']}) found in RotoGrinders list")
                    rg_c_proj = float(rg[player['Name']][player['Stat']])
                    row['Proj'] = round((rg_c_proj + consensus) / 2, 2)
                elif len(history[player['Name']][player['Stat']]) > 0 and consensus - min(
                        history[player['Name']][player['Stat']]) >= 2:
                    if rg == {}:
                        rg = getRotogrinders()
                    rg_c_proj = float(rg[player['Name']][player['Stat']])
                    print(f"[+] {player['Name']} ({player['Stat']}) has difference > 2")
                    with open(f'rg-{today}.txt', 'a') as f:
                        f.write(f"{player['Name']}-{player['Stat']}\n")
                    row['Proj'] = round((rg_c_proj + consensus) / 2, 2)
                if over > under:
                    print(
                        f"[+] {player['Name']} ({player['Stat']}) over ({row['Over']}) is favored on under ({row['Under']}) so {math.ceil(consensus)}")
                    consensus = math.ceil(consensus)
                elif over < under:
                    print(
                        f"[+] {player['Name']} ({player['Stat']}) under ({row['Under']}) is favored on over ({row['Over']}) so {math.floor(consensus)}")
                    consensus = math.floor(consensus)
                else:
                    print(
                        f"[+] {player['Name']} ({player['Stat']}) over ({row['Over']}) is equal to under ({row['Under']}) so {consensus}")
            except:
                traceback.print_exc()
                print(row['Over'])
                time.sleep(1)
            if row['Proj'] == '':
                row['Proj'] = round((float(covers[rname][player['Stat']]) + consensus) / 2, 2)
            if player['Name'] in projections and player['Stat'] in projections[player['Name']] and "Date" in \
                    projections[
                        player['Name']]:
                x = datetime.strptime(projections[player['Name']]["Date"], "%Y-%m-%d").strftime("%Y-%m-%d")
                y = datetime.now(timezone('US/Central')).strftime("%Y-%m-%d")
                if x == y:
                    proj = projections[player['Name']][player['Stat']]
                    print(f"[+] {player['Name']} ({player['Stat']}) found in projections {proj}")
                    row['Proj'] = float(proj)
            row['Diff'] = round(row['Proj'] - row['Score'], 2)
            if row['Diff'] > 2 or row['Diff'] < -2:
                rg_stat = rg[player['Name']][player['Stat']]
                if rg_stat.count('.') > 1:
                    rg_c_proj = float(rg_stat)
                else:
                    rg_c_proj = float(rg_stat.split('.')[0])
                if row['Diff'] < -2:
                    print(f"[+] {player['Name']} ({player['Stat']}) has difference ({row['Diff']}) < 2")
                elif row['Diff'] > 2:
                    print(f"[+] {player['Name']} ({player['Stat']}) has difference ({row['Diff']}) > 2")
                with open(f'rg-{today}.txt', 'a') as f:
                    f.write(f"{player['Name']}-{player['Stat']}\n")
                row['Proj'] = round((rg_c_proj + consensus) / 2, 2)
                row['Diff'] = round(row['Proj'] - row['Score'], 2)
            last_10 = covers[rname][f"{player['Stat']} Last 10"]
            close = covers[rname][f"{player['Stat']} Close"]
            if row['Diff'] < 0:
                s_count = 0
                c_count = 0
                for l10 in last_10:
                    if l10 < float(row['Score']):
                        s_count += 1
                for c in close:
                    if c < float(row['Score']):
                        c_count += 1
                row["Last 10"] = f"{s_count}/{len(last_10)}"
                row["Close"] = f"{c_count}/{len(close)}"
            else:
                s_count = 0
                c_count = 0
                for l10 in last_10:
                    if l10 >= float(row['Score']):
                        s_count += 1
                for c in close:
                    if c > float(row['Score']):
                        c_count += 1
                row["Last 10"] = f"{s_count}/{len(last_10)}"
                row["Close"] = f"{c_count}/{len(close)}"
            rows.append(row)
        except:
            traceback.print_exc()
            print(f"Error on player {player}")
            # time.sleep(1)
    # rows = sorted(rows, key=lambda k: k['Diff'], reverse=True)
    # print(json.dumps(rows, indent=4))
    with open('odds.json', 'w') as ofile:
        json.dump(rows, ofile, indent=4)
    convertOddsToManualProjection(rows)
    return rows


def convertOddsToManualProjection(rows):
    for row in rows:
        name = row['Name']
        if name not in projections.keys():
            projections[name] = {"Date": datetime.now(timezone('US/Central')).strftime("%Y-%m-%d")}
            for stat in stats.keys():
                projections[name][f"-{stat}"] = 0
    with open('projections.json', 'w') as pfile:
        json.dump(projections, pfile, indent=4)


def generateHtml(player_data):
    with open('index.html') as tfile:
        total = tfile.read()

    row_data = ""
    for player in player_data:
        try:
            trs = ""
            trs += f"""<tr><td>{player['Name']}</td><td>{player['Position']}</td><td>{player['Team']}</td>
            <td>{player['Opp']}</td><td>{player['Stat']}</td><td>{player['Score']}</td>"""
            # <td>{player['Over']}</td><td>{player['Under']}</td>
            # <td>{player['Proj']}</td><td>{player['Diff']}</td></tr>"""
            over = player['Over'].split("(")[1].split(")")[0]
            under = player['Under'].split("(")[1].split(")")[0]
            # print("over",over,abs(float(over))," under",under,abs(float(under)))
            if abs(float(over)) > abs(float(under)):
                # print("over")
                trs += f"<td style='background-color: green;'>{player['Over']}</td><td>{player['Under']}</td>"
            else:
                trs += f"<td>{player['Over']}</td><td style='background-color: green;'>{player['Under']}</td>"
            trs += f"<td>{player['Last 10']}</td><td>{player['Close']}</td><td>{player['Proj']}</td>"
            if -1 < float(player['Diff']) < 1:
                trs += f"<td style='background-color: yellow;'>{player['Diff']}</td></tr>"
            else:
                trs += f"<td style='background-color: green;'>{player['Diff']}</td></tr>"
            row_data += trs
        except:
            traceback.print_exc()
            print(player)
            time.sleep(1)
    btn = f"<button onclick='myFunction()'>All</button>"
    for stat_type in stats:
        btn += f"<button onclick='myFunction()'>{stat_type}</button>"
    now = datetime.now(timezone('US/Central')).strftime('%B %d %Y %H:%M %p')
    with open('index-out.html', 'w') as ifile:
        ifile.write(total.replace('{btn}', btn).replace('{trs}', row_data).replace("LastRefreshed", now).
                    replace('NotFoundPlayers', ", ".join(not_found)))


def upload():
    print("Uploading...")
    with open(f'index-out.html') as ifile:
        res = requests.post('https://gldprops.com/upload.php', data={"nba-data": ifile.read()})
        print(res.content)


def main():
    logo()
    generateHtml(compileOdds())
    if not test:
        upload()
    print("Done!")


def pprint(msg):
    try:
        print(f"{datetime.now()}".split(".")[0], msg)
    except:
        traceback.print_exc()


def logo():
    print(r"""
__________        .__             __________.__        __            
\______   \_______|__|_______ ____\______   \__| ____ |  | __  ______
 |     ___/\_  __ \  \___   // __ \|     ___/  |/ ___\|  |/ / /  ___/
 |    |     |  | \/  |/    /\  ___/|    |   |  \  \___|    <  \___ \ 
 |____|     |__|  |__/_____ \\___  >____|   |__|\___  >__|_ \/____  >
                           \/    \/                 \/     \/     \/ 
=======================================================================
            prizepicks.com (NBA) scraper by @evilgenius786
=======================================================================
[+] Scraping data from prizepicks.com
[+] Scraping data from bettingpros.com
[+] Scraping data from Covers.com
[+] Generating HTML
[+] JSON Output
[+] Works via API!
_______________________________________________________________________
""")


def click(driver, xpath, js=False):
    if js:
        driver.execute_script("arguments[0].click();", getElement(driver, xpath))
    else:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def getElement(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))


def getElements(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))


def sendkeys(driver, xpath, keys, js=False):
    if js:
        driver.execute_script(f"arguments[0].value='{keys}';", getElement(driver, xpath))
    else:
        getElement(driver, xpath).send_keys(keys)


def getChromeDriver(proxy=None):
    options = webdriver.ChromeOptions()
    if debug:
        # print("Connecting existing Chrome for debugging...")
        options.debugger_address = "127.0.0.1:9222"
    else:
        options.add_argument('--user-data-dir=C:/Selenium2/ChromeProfile')

    #     options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #     options.add_experimental_option("excludeSwitches", ["enable-logging"])
    #     options.add_experimental_option('useAutomationExtension', False)
    #     options.add_argument("--disable-blink-features")
    #     options.add_argument("--disable-blink-features=AutomationControlled")
    #
    # if not images:
    #     # print("Turning off images to save bandwidth")
    #     options.add_argument("--blink-settings=imagesEnabled=false")
    # if headless:
    #     # print("Going headless")
    #     options.add_argument("--headless")
    #     options.add_argument("--window-size=1920x1080")
    # if max:
    #     # print("Maximizing Chrome ")
    #     options.add_argument("--start-maximized")
    # if proxy:
    #     # print(f"Adding proxy: {proxy}")
    #     options.add_argument(f"--proxy-server={proxy}")
    # if incognito:
    #     # print("Going incognito")
    #     options.add_argument("--incognito")
    # return webdriver.Chrome(service=Service(ChromeDriverManager().download_and_install()[0]), options=options)
    # return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return webdriver.Chrome(options=options)


def getFirefoxDriver():
    options = webdriver.FirefoxOptions()
    if not images:
        # print("Turning off images to save bandwidth")
        options.set_preference("permissions.default.image", 2)
    if incognito:
        # print("Enabling incognito mode")
        options.set_preference("browser.privatebrowsing.autostart", True)
    if headless:
        # print("Hiding Firefox")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    return webdriver.Firefox(options)


if __name__ == '__main__':
    main()
    # print("Done!")
    # getCovers()
