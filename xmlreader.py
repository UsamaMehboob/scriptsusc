
'''
************************************************************************
*
* FILE NAME: xmlreader.py
*
* DESCRIPTION
*    The script is responsible for pushing the guest accounts
*    from exported xml files from production server
*
*************************************************************************
'''

from lxml import etree
import requests
import pprint
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
import logging
logging.basicConfig(filename='xmlreader.log',level=logging.DEBUG)

ip_address = '68.181.191.92'
xmlconfigfile = 'orginal.xml'

proxiess = {
    'http': 'socks5://127.0.0.1:80',
    'https': 'socks5://127.0.0.1:80'
}





class Config:
    '''
    This class would apply actual configuration to
    remote server
    '''
    def __init__(self):

    def authenticate(self):
        r1 = requests.post('https://'+ip_address+'/api/oauth', data=self.creds,verify=False)
        self.token ="Bearer "+json.loads(r1.text)['access_token']
        self.headers={"Authorization":self.token, "Content-Type": "application/json"}
        print self.token


    def insertnewmac(self, newDevice):
        r33 = requests.post('https://'+ip_address+'/api/device',data=json.dumps(newDevice),headers=self.headers,verify=False)
        print r33.text

    def getmactodevice(self):
        print "gonna make a call for "+self.mac_address
        r12 = requests.get('https://'+ip_address+'/api/device/mac/'+self.mac_address,headers=self.headers,verify=False)
        loadedjson = json.loads(r12.text)
        #mactoSearch = '00-14-4F-9B-70-33'

        #print "---"
        pprint.pprint(loadedjson)
        #print json.dumps(loadedjson, separators=(',',':'))
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

    def __init__(self):
        self.diclist=[]
        self.tree = None
        self.security_devices_begin_maclist=['000463','accc8e','000fe5','0cbf15','bcc3422c','000baa']
        self.security_devices_equals_maclist=['f8cab845751f','a08cfdd56075','b88a606bd668']
        ###########facilities
        self.facilities_begin_maclist=['0030af','00e091','00d0af07']
        self.facilities_equals_maclist=['204747aaec47','34e6d714cc10','00504e0306e8']
        self.facilities_contains_maclist=['002085f10','00e00c00']
        ############net_mgmt
        self.net_mgmt_begin_maclist=['002085']
        ###########pci
        self.pci_equals_maclist=['906cacfb4e13','085b0e14b224']
        ###########usc
        self.usc_begin_maclist=['4448c1c06','40b034f25','906cacd1','3c5282','0021CCC0','0021CCBF','00900B','B827EB','000BAB','C8D3FF','509A4C','14b31f']
        self.usc_equals_maclist=['14b31f10cc84','14B31F10D84C','14B31F10D8AF','14B31F10CD0D','14B31F10D8A9','14B31F10D855','14B31F10D895','14b31f0eab1b','509a4c44ad01',
        '509a4c449fdc','C8D3FFA6C220','906CACFB4E13','509a4c46a0a4','14B31F164493','7cf854015ab3','7cf8540163bb',
        '9c934e9670a0','3c5282bd440a','40b034247373','00206b8280cc','001f2928d3eb','60128bd1451e']
        self.usc_contains_maclist=['4048c1','14b31f12','7cf854015a']
        ##########devices
        self.devices_begin_maclist=['1C1B0D','408D5C','D8EB97','00405811','f430b926','4083ded7','5882a8']
        self.devices_equals_maclist=['1c1b0d7625fb','0080a3b3eaea','00204AE5BAB0','00204ad22473','0080A3B3E8CE','0080A3B3E80A','0080A3B3E90A']
        ##########student
        self.student_begin_maclist=['00900b']
        #########voip
        self.voip_contains_maclist=['a47886','a009ed0','707c6901']
        self.guest_maclist=[]
        self.quarantine_maclist=[]
        self.staff_maclist=[]

    def parseConfigFile(self):
        try:
            self.tree = etree.parse(xmlconfigfile)
            #print(tree.docinfo.xml_version)
        except:
            print "Error opening xml file"
            logging.info('Error opening xml file')
            exit()
        count = 0
        for kid in self.tree.getroot().iterchildren("{http://www.avendasys.com/tipsapiDefs/1.0}GuestUsers"):
            print "gonna do now"
            for subkid in kid.iterchildren("*"):
                count = count + 1
                dicWithParams={}
                for subsubkid in subkid.iterchildren("{http://www.avendasys.com/tipsapiDefs/1.0}GuestUserTags"):
                    dicWithParams['current_state']= 'active'
                    dicWithParams['enabled']= 'True'
                    if subsubkid.get('tagName')=='Role ID':
                        dicWithParams['role_id']= str(subsubkid.get('tagValue'))
                        #self.role = str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='mac':
                        dicWithParams['mac']= str(subsubkid.get('tagValue'))
                        #self.mac = str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_asset_tag':
                        dicWithParams['uscTag']= str(subsubkid.get('tagValue'))
                        #self.assettag = str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_room':
                        dicWithParams['room']= str(subsubkid.get('tagValue'))
                        #self.uscroom = str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_cpu':
                        dicWithParams['CPU']= str(subsubkid.get('tagValue'))
                        #self.usccpu = str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_building':
                        dicWithParams['building']= str(subsubkid.get('tagValue'))
                        #self.uscbuilding = str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_billing_contact':
                        dicWithParams['billcon']= str(subsubkid.get('tagValue'))
                        #self.billcon= str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_technical_contact':
                        dicWithParams['techcon']= str(subsubkid.get('tagValue'))
                        #self.techcon= str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_owner':
                        dicWithParams['owner']= str(subsubkid.get('tagValue'))
                        #self.uscowner= str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_actual_hostname':
                        dicWithParams['hostid']= str(subsubkid.get('tagValue'))
                        #self.hostname= str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_interface_name':
                        dicWithParams['Interface_name']= str(subsubkid.get('tagValue'))
                        #self.interfacename= str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_serial_number':
                        dicWithParams['serial']= str(subsubkid.get('tagValue'))
                        #self.serialnumber= str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='sponsor_profile_name':
                        dicWithParams['sponsor_profile_name']= str(subsubkid.get('tagValue'))
                        #self.sponsorprofilename=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_vendor':
                        dicWithParams['vendor']= str(subsubkid.get('tagValue'))
                        #self.uscvendor=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_shelf':
                        dicWithParams['Shelf']= str(subsubkid.get('tagValue'))
                        #self.uscshelf=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_operating_system':
                        dicWithParams['OS']= str(subsubkid.get('tagValue'))
                        #self.uscOS=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_rack':
                        dicWithParams['Rack']= str(subsubkid.get('tagValue'))
                        #self.uscRack=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_id':
                        dicWithParams['Usc_ID']= str(subsubkid.get('tagValue'))
                        #self.uscid=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_account':
                        dicWithParams['Usc_Account']= str(subsubkid.get('tagValue'))
                        #self.uscaccount=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_stolen':
                        dicWithParams['stolen']= str(subsubkid.get('tagValue')).lower()
                        #self.stolen=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='remote_addr':
                        dicWithParams['URL']= str(subsubkid.get('tagValue'))
                        #self.url=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='usc_static':
                        dicWithParams['static']= str(subsubkid.get('tagValue')).lower()
                        #self.static=str(subsubkid.get('tagValue'))
                    if subsubkid.get('tagName')=='Visitor Name':
                        dicWithParams['visitor_name']= str(subsubkid.get('tagValue'))

                self.diclist.append(dicWithParams)
        print "total obj inserted in dictionary = " + str(count) + "length = "+ str(len(self.diclist))
        #return self.diclist


        #print self.paramlist[1:]

    def applyConfig(self):
        patchobj = Config()
        patchobj.authenticate()
        facilitiesmac = 0
        securitymac=0;
        devicesmac=0;
        netmgmtmac=0
        pcimac=0;
        uscmac=0;
        studentmac=0;
        voipmac=0

        machitcount=0

        for dic in self.diclist:
            machit = 0;
            print "+++++++++++++++++++\nConfiguring this MAC ==> "+ dic['mac']+" <== for vlan "
            logging.info("+++++++++++++++++++\nConfiguring this MAC ==> "+ dic['mac']+" <== for vlan ")
            mac = dic['mac'].split('-')
            joinedmac = (''.join(map(str, mac))).lower()
            print mac
            print joinedmac
            logging.info("joinedmac = "+str(joinedmac))
            ##################security_devices
            #['devices','student','voip','guest','security_devices','usc','facilities','net_mgmt','pci','quarantine','staff']:

            for beginmac in self.security_devices_begin_maclist:#=['000463','accc8e','000fe5','0cbf15','bcc3422c','000baa']
                if beginmac == joinedmac[:len(beginmac)]:
                    dic['VLANID']='security_devices'
                    print "RULE::security_devices beginmac="+beginmac +",  mac="+joinedmac
                    logging.info("RULE::security_devices beginmac="+beginmac +",  mac="+joinedmac)
                    machit = 1
                    securitymac = securitymac+1
            for equalmac in self.security_devices_equals_maclist:#=['204747aaec47','34e6d714cc10','00504e0306e8']
                if equalmac == joinedmac:
                    dic['VLANID']='security_devices'
                    print "RULE::security_devices equalmac="+equalmac +",  mac="+joinedmac
                    logging.info("RULE::security_devices equalmac="+equalmac +",  mac="+joinedmac)
                    machit = 1
                    securitymac = securitymac+1


            ###########facilities

            for beginmac in self.facilities_begin_maclist:#=['0030af','00e091','00d0af07']
                if beginmac == joinedmac[:len(beginmac)]:
                    dic['VLANID']='facilities'
                    print "RULE::facilities beginmac="+beginmac +",  mac="+joinedmac
                    logging.info("RULE::facilities beginmac="+beginmac +",  mac="+joinedmac)
                    machit = 1
                    facilitiesmac = facilitiesmac+1

            for equalmac in self.facilities_equals_maclist:#=['204747aaec47','34e6d714cc10','00504e0306e8']
                if equalmac == joinedmac:
                    dic['VLANID']='facilities'
                    print "RULE::facilities equalmac="+equalmac +",  mac="+joinedmac
                    logging.info("RULE::facilities equalmac="+equalmac +",  mac="+joinedmac)
                    machit = 1
                    facilitiesmac = facilitiesmac +1
            for containmac in self.facilities_contains_maclist:#=['002085f10','00e00c00']!!!!!!!5elements TODO
                if containmac in joinedmac:
                    dic['VLANID']='facilities'
                    print "RULE::facilities containmac="+containmac +",  mac="+joinedmac
                    logging.info("RULE::facilities containmac="+containmac +",  mac="+joinedmac)
                    facilitiesmac = facilitiesmac + 1
                    machit = 1
            ############net_mgmt
            for beginmac in self.net_mgmt_begin_maclist:#=['002085']
                if beginmac == joinedmac[:len(beginmac)]:
                    dic['VLANID']='net_mgmt'
                    print "RULE::net_mgmt beginmac="+beginmac +",  mac="+joinedmac
                    logging.info("RULE::net_mgmt beginmac="+beginmac +",  mac="+joinedmac)
                    netmgmtmac = netmgmtmac + 1
            ###########pci
            for equalmac in self.pci_equals_maclist:#=['906cacfb4e13','085b0e14b224']
                if equalmac == joinedmac:
                    dic['VLANID']='net_mgmt'
                    print "RULE::pci containmac="+equalmac +",  mac="+joinedmac
                    logging.info("RULE::pci containmac="+equalmac +",  mac="+joinedmac)
                    pcimac = pcimac + 1
                    machit = 1
            ###########usc
            for beginmac in self.usc_begin_maclist:#=['4448c1c06','40b034f25','906cacd1','3c5282','0021CCC0','0021CCBF','00900B','B827EB','000BAB','C8D3FF','509A4C','14b31f']
                if beginmac == joinedmac[:len(beginmac)]:
                    dic['VLANID']='usc'
                    print "RULE::usc beginmac="+beginmac +",  mac="+joinedmac
                    logging.info("RULE::usc beginmac="+beginmac +",  mac="+joinedmac)
                    uscmac = uscmac + 1
                    machit = 1
            for equalmac in self.usc_equals_maclist:#=['14b31f10cc84','14B31F10D84C','14B31F10D8AF','14B31F10CD0D','14B31F10D8A9','14B31F10D855','14B31F10D895','14b31f0eab1b','509a4c44ad01',
                if equalmac == joinedmac:
                    dic['VLANID']='usc'
                    print "RULE::usc containmac="+equalmac +",  mac="+joinedmac
                    logging.info("RULE::usc containmac="+equalmac +",  mac="+joinedmac)
                    uscmac = uscmac + 1
                    machit = 1
            for containmac in self.usc_contains_maclist:#=['4048c1','14b31f12','7cf854015a']
                if containmac in joinedmac:
                    dic['VLANID']='usc'
                    print "RULE::usc containmac="+containmac +",  mac="+joinedmac
                    logging.info("RULE::usc containmac="+containmac +",  mac="+joinedmac)
                    uscmac = uscmac + 1
                    machit = 1
            ##########devices
            for beginmac in self.devices_begin_maclist:#=['1C1B0D','408D5C','D8EB97','00405811','f430b926','4083ded7','5882a8','']
                if beginmac == joinedmac[:len(beginmac)]:
                    dic['VLANID']='devices'
                    print "RULE::devices beginmac="+beginmac +",  mac="+joinedmac
                    logging.info("RULE::devices beginmac="+beginmac +",  mac="+joinedmac)
                    devicesmac = devicesmac+1
                    machit = 1
            for equalmac in self.devices_equals_maclist:#=['1c1b0d7625fb','0080a3b3eaea','00204AE5BAB0','00204ad22473','0080A3B3E8CE','0080A3B3E80A','0080A3B3E90A']
                if equalmac == joinedmac:
                    dic['VLANID']='devices'
                    print "RULE::devices containmac="+equalmac +",  mac="+joinedmac
                    logging.info("RULE::devices containmac="+equalmac +",  mac="+joinedmac)
                    devicesmac = devicesmac + 1
                    machit = 1
            ##########student
            for beginmac in self.student_begin_maclist:#=['00900b']:
                if beginmac == joinedmac[:len(beginmac)]:
                    dic['VLANID']='student'
                    print "RULE::student beginmac="+beginmac +",  mac="+joinedmac
                    logging.info("RULE::student beginmac="+beginmac +",  mac="+joinedmac)
                    studentmac = studentmac + 1
                    machit = 1
            #########voip
            for containmac in self.voip_contains_maclist:#=['a47886','a009ed0','707c6901']
                if containmac in joinedmac:
                    dic['VLANID']='voip'
                    print "RULE::voip containmac="+containmac +",  mac="+joinedmac
                    logging.info( "RULE::voip containmac="+containmac +",  mac="+joinedmac)
                    voipmac = voipmac + 1
                    machit = 1
            if machit == 0:
                logging.warning("THIS MAC IS NOT HIT "+str(joinedmac))
            else:
                machitcount = machitcount + 1
                patchobj.insertnewmac(dic)
            print "---"
        logging.info("facilitiesmac count= "+str(facilitiesmac))
        logging.info("securitymac count= "+str(securitymac))
        logging.info("devicesmac count= "+str(devicesmac))
        logging.info("netmgmtmaccount= "+str(netmgmtmac))
        logging.info("pcimac count= "+str(pcimac))
        logging.info("uscmac count= "+str(uscmac))
        logging.info("studentmaccount = "+str(studentmac))
        logging.info("voipmac count= "+str(voipmac))
        logging.info("hit count= "+str(machitcount))
        logging.info("unhitmac count= "+str(len(self.diclist) - machitcount))


            #if macparam['vlan'] not in ['devices','student','voip','guest','security_devices','usc','facilities','net_mgmt','pci','quarantine','staff']:
            #    print "vlan is not in the given vlan so applying specail vlan..."
            #    special = 1
            #if special == 1:
            #    patchobj = Config(macparam['mac'],macparam['vlan'],1)
            #else:
            #    patchobj = Config(macparam['mac'],macparam['vlan'],0)

            #patchobj.insertnewmac(dic)



if __name__ == "__main__":
    xmlobj = ConfigFile()
    xmlobj.parseConfigFile()
    xmlobj.applyConfig()
