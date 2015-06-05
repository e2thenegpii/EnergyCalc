from config import *

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from time import sleep
from getpass import getpass

from os import remove

import zipfile
import pandas as pd
import numpy as np
from lxml import etree as et

def _parseBgeXml(f):
    timestamp = []
    consumed = []
    cost = []

    timezone = config.get('global','timezone')
    for e,elem in et.iterparse(f, tag='{http://naesb.org/espi}IntervalReading'):
        timestamp.append(elem.findall('.//{http://naesb.org/espi}start')[0].text)
        consumed.append( elem.findall('{http://naesb.org/espi}value')[0].text)
        cost.append(     elem.findall('{http://naesb.org/espi}cost')[0].text)
        nt = np.array(timestamp,dtype=int).astype('datetime64[s]')
        nc = np.array(consumed,dtype=float)
        no = np.array(cost,dtype=float)

    nc /= 1e5
    no /= 1e5

    consumed = pd.Series(nc,index=nt).tz_localize('UTC').tz_convert(timezone)
    cost     = pd.Series(no,index=nt).tz_localize('UTC').tz_convert(timezone)

    return (consumed,cost)

def getData(daterange):
    
    downloadDir = cache_directory

    customer_id = config.get('bge','customer_id')

    if config.has_option('bge','username') and config.has_option('bge','password'):
        username    = config.get('bge','username')
        password    = config.get('bge','password')
    else:
        username = raw_input('Username for bge.com:')
        password = getpass()

    begin = daterange[0].strftime('%Y-%m-%d')
    end   = daterange[-1].strftime('%Y-%m-%d')

    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList',2)
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir',downloadDir)
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/octet-stream')

    browser = webdriver.Firefox(profile)
    browser.implicitly_wait(60)

    browser.get('https://www.bge.com/')

    username_element = browser.find_element_by_id('USER')
    password_element = browser.find_element_by_id('PASSWORD')

    username_element.send_keys(username)
    password_element.send_keys(password)
    password_element.send_keys(Keys.RETURN)

    browser.find_element_by_link_text('My Energy Use').click()
    browser.find_element_by_link_text('My Usage Details').click()

    download_url = 'https://bgesmartenergymanager.com/ei/app/modules/customer/%s/energy/download?exportFormat=ESPI_AMI&xmlFrom=%s&xmlTo=%s'%(customer_id,begin,end)

    browser.get(download_url)

    sleep(5)

    browser.quit()

    zf = downloadDir + '/bgec_interval_data_%s_to_%s.zip'%(begin,end)

    with zipfile.ZipFile(zf,'r') as z:
        files = [ data_directory + '/' + fn for fn in z.namelist() ]
        z.extractall(data_directory)

    df = pd.DataFrame()

    for f in files:
        if 'gas' in f:
            consumed_name = 'gas_consumed'
            cost_name = 'gas_cost'
        if 'electric' in f:
            consumed_name = 'electric_consumed'
            cost_name = 'electric_cost'

        consumed,cost = _parseBgeXml(f)

        df.loc[:,consumed_name] = consumed
        df.loc[:,cost_name]     = cost

        
    remove(zf)
    for f in files:
        remove(f)

    return df
