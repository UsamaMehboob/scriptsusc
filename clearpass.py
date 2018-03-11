'''
************************************************************************
*
* FILE NAME: clearpass.py
*
* DESCRIPTION
*    The script is responsible for editing the devices
*    parameters (Vlan, special vlan)
*    registered in clearpass.
*************************************************************************
'''


import requests
import re
import pdb
import csv
from requests.auth import HTTPDigestAuth
from requests.auth import HTTPBasicAuth
import ast
import json
import sys
import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ip_address = '68.181.191.92'
csvconfigfile = 'cp.csv'

proxiess = {
    'http': 'socks5://127.0.0.1:80',
    'https': 'socks5://127.0.0.1:80'
}



class ArgumentParser:
    '''
    Class responsible for parsing and storing
    commang line arguments for this script
    '''

    __mac_address = ""
    __vlan = ""


    def getmacAddress(self):
        return self.mac_address
    def getVlan(self):
        return self.vlan

    def read_args_clearpass(self, args):
        sys.argv = args
        parser = argparse.ArgumentParser(description='Change Vlan in clearpass')
        parser.add_argument("--mac_address", help="mac address for the device to be edited", required=True)
        parser.add_argument("--vlan", help="vlan that should be assigned ", required=True)
        args = parser.parse_args()
        self.mac_address = args.mac_address #you can verify the validity of mac by if args.mac_address and then go assign it
        self.vlan = args.vlan


class Config:
    '''
    This class would apply actual configuration to
    remote server
    '''
    def __init__(self, mac_address, vlan, flag_num):
        self.mac_address = mac_address
        self.vlan = vlan
        self.flag = flag_num

    def authenticate(self):
        r1 = requests.post('https://'+ip_address+'/api/oauth', data=self.creds,verify=False)
        self.token ="Bearer "+json.loads(r1.text)['access_token']
        self.headers={"Authorization":self.token, "Content-Type": "application/json"}
        print self.token
    
        
    def insertnewmac(self):
        self.newDevice={}
        self.newDevice["sponsor_name"]="usama"
        self.newDevice["visitor_name"]="usama"  
        self.newDevice["username"]=self.mac_address
        self.newDevice["mac"]=self.mac_address
        self.newDevice["role_id"]=2 #Quarantine for role_id = 2
        

        if (self.flag ==1):
            #applying special vlan
            self.newDevice['SpecialVLAN']=1
            #pdb.set_trace()
            self.newDevice['specialvlan_number']=int(self.vlan)
            self.newDevice['VLANID']=""
        elif (self.flag==0):
            self.newDevice['VLANID']=self.vlan
            self.newDevice['SpecialVLAN']=''
            self.newDevice['specialvlan_number']=''
            
        print self.newDevice
        print "***new device ****"
        
        r33 = requests.post('https://'+ip_address+'/api/device',data=json.dumps(self.newDevice),headers=self.headers,verify=False)
        print r33.text
        
            
            
            
        
    def getmactodevice(self):
        print "gonna make a call for "+self.mac_address
        r12 = requests.get('https://'+ip_address+'/api/device/mac/'+self.mac_address,headers=self.headers,verify=False)
        loadedjson = json.loads(r12.text)
        #mactoSearch = '00-14-4F-9B-70-33'

        #print "---"
        print json.dumps(loadedjson, separators=(',',':'))
        #print "---"
        self.device_id = None
        if loadedjson.has_key('id'):
            print "---"
            self.device_id = loadedjson['id']
            self.accessobjectfromid()
            self.patchDevice()
        else:
            print "mac::"+self.mac_address+" not found in the server"
            self.insertnewmac()
                

    def mactoid(self):
        r2 = requests.get('https://'+ip_address+'/api/device',headers=self.headers,verify=False)
        loadedjson = json.loads(r2.text)
        mactoSearch = '00-14-4F-9B-70-33'
        device_id = None
        print loadedjson
        cont =0
        for item in loadedjson["_embedded"]['items']:
            cont = cont +1
            if item['username'] == self.mac_address:
                self.device_id = item['id']
                print cont
                print "WTF"
                return
    
    def accessobjectfromid(self):
        if self.device_id!=None:
            r3 = requests.get('https://'+ip_address+'/api/device/'+self.device_id,headers=self.headers,verify=False)
            self.updateDevice = json.loads(r3.text)
            #print self.updateDevice
            #print "---"
            #pdb.set_trace()
            if (self.flag ==1):
                #applying special vlan
                self.updateDevice['SpecialVLAN']=1
                #pdb.set_trace()
                self.updateDevice['specialvlan_number']=int(self.vlan)
            elif (self.flag==0):
                self.updateDevice['VLANID']=self.vlan
                self.updateDevice['SpecialVLAN']=''
                self.updateDevice['specialvlan_number']=''
            #print "\n Updated Device \n"

    def patchDevice(self):
        r3 = requests.patch('https://'+ip_address+'/api/device/'+self.device_id,data=json.dumps(self.updateDevice),headers=self.headers,verify=False)
        #print r3.text
        print "verifying .... "
        r4 = requests.get('https://'+ip_address+'/api/device/'+self.device_id ,headers=self.headers,verify=False)
        print "special Vlan = "+json.loads(r4.text)["specialvlan_number"]
        print "Normal Vlan = "+json.loads(r4.text)["VLANID"]
        print "Vlan Flag = "+json.loads(r4.text)["SpecialVLAN"]
        #print r4.text



class ConfigFile:
    __paramlist=[]
    def __init__(self):
        self.paramlist = []
    def parseConfigFile(self):
        try:
            with open(csvconfigfile) as csvfile:
                linereader = csv.reader(csvfile, delimiter=',', quotechar='|')
                for row in linereader:
                    self.paramlist.append({'mac':row[0],'jack':row[2],'vlan':row[1]})
        except csv.Error as e:
            sys.exit('file {}, line {}: {}'.format(csvconfigfile, linereader.line_num, e))


        #print self.paramlist[1:]

    def applyConfig(self):
        for macparam in self.paramlist[1:]:
            splitedmac = re.split('[-:]',macparam['mac'])
            joinedmac = '-'.join(a for a in splitedmac )
            macparam['mac'] = joinedmac
            print "+++++++++++++++++++\nConfiguring this MAC ==> "+ macparam['mac']+" <== for vlan "+macparam['vlan']
            print "---"
            special = None
            if macparam['vlan'] not in ['devices','student','voip','guest','security_devices','usc','facilities','net_mgmt','pci','quarantine','staff']:
                print "vlan is not in the given vlan so applying specail vlan..."
                special = 1
            if special == 1:
                patchobj = Config(macparam['mac'],macparam['vlan'],1)
            else:
                patchobj = Config(macparam['mac'],macparam['vlan'],0)
            print "calling authentiacte"
            patchobj.authenticate()
            print "done authenticate"
            patchobj.getmactodevice()
            #patchobj.mactoid()



if __name__ == "__main__":
    csvobj = ConfigFile()
    csvobj.parseConfigFile()
    csvobj.applyConfig()
