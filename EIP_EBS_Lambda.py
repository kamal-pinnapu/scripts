import json
import boto3
import os
import argparse
import inspect

functions = { 'ec2' : [
    {'name' : 'get_ec2_instances', 'title' : 'Running EC2 Instances' },
    {'name' : 'get_ebs_volumes', 'title' : 'Un-attached EBS Volumes' },
    {'name' : 'get_eip', 'title' : 'Un-attached EIPs' }
]
}

def html_header_2(title):
    return "<h2>" + title + "</h2>\n"
def html_header_3(title):
    return "<h3>" + title + "</h3>\n"
def html_para(para):
    return "<p>" + para + "</p>\n"
def html_table(columns, data):
    c=1
    #Add header row
    table="<table border=1 CELLPADDING=1 CELLSPACING=0 width=\"86%\">"
    table += "<tr bgcolor=\"#0099cc\">"
    for column in columns:
        table += "<th><font color=\"#fff\">" + column + "</font></th>"
    table += "</tr>"
    #Add data rows
    for row in data:
        table += "<tr>"
        for item in row:
            table += "<td>" + str(item) + "</td>"
        table += "</tr>"
    table += "</table>"
    return table

#TODO Add paginations for all functions
def price_cache_update(itype, region, cost):
    if itype in price_cache:
        if region in price_cache[itype]:
            return
        else:
            price_cache[itype][region] = cost
    else:
        price_cache[itype] = { region : cost }

def saving_update(type, cost):
    if type in savings:
        savings[type] += cost
    else:
        savings[type] = cost

def clear_cache():
    price_cache = {}
    #Lambda execution caching global data
    savings['ec2'] = 0
    savings['ebs'] = 0
    savings['eip'] = 0

def get_ebs_price(pricing, region, vtype, vsize):
    #check if price is there in cache
    if vtype in price_cache and region in price_cache[vtype]:
        return price_cache[vtype][region]

    #print "VolumeType=%s location=%s" %(vtype, RegionMapping[region])
    price_detail = pricing.get_products(ServiceCode='AmazonEC2',
                                        Filters=[
                                            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage'},
                                            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': RegionMapping[region]}
                                        ])
    #print json.dumps(price_detail, indent=2)
    UsageData = {}
    for item in price_detail['PriceList']:
        data = json.loads(item)
        if 'EBS:VolumeUsage.' + vtype not in data['product']['attributes']['usagetype']:
            continue
        else:
            UsageData = data
    if not UsageData:
        return ''
    #print json.dumps(UsageData, indent=2)
    sku_code = UsageData['product']['sku']
    sku_offer_term = sku_code + '.' + OfferTermCode
    values = UsageData['terms']['OnDemand'][sku_offer_term]['priceDimensions']
    for key in values:
        if 'rateCode' in values[key]:
            ratecode = ['rateCode']
            cost = float(values[key]['pricePerUnit']['USD'])
            volume_cost = round((cost * vsize), 2)
            price_cache_update(vtype, region, volume_cost)
    return volume_cost


def get_ec2_price(pricing, region, itype):
    #check if price is there in cache
    if itype in price_cache and region in price_cache[itype]:
        return price_cache[itype][region]

    #print "InstanceType=%s location=%s" %(itype, RegionMapping[region])
    price_detail = pricing.get_products(ServiceCode='AmazonEC2',
                                        Filters=[
                                            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': itype},
                                            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                                            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                                            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                                            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': RegionMapping[region]}
                                        ])
    #print json.dumps(price_detail, indent=2)
    UsageData = {}
    for item in price_detail['PriceList']:
        data = json.loads(item)
        if 'BoxUsage' not in data['product']['attributes']['usagetype']:
            continue
        else:
            UsageData = data
    if not UsageData:
        return ''
    #print json.dumps(UsageData, indent=2)
    sku_code = UsageData['product']['sku']
    sku_offer_term = sku_code + '.' + OfferTermCode
    values = UsageData['terms']['OnDemand'][sku_offer_term]['priceDimensions']
    for key in values:
        if 'rateCode' in values[key]:
            ratecode = ['rateCode']
            cost = float(values[key]['pricePerUnit']['USD'])
            instance_cost = round((cost * 24 * 30.5), 2)
            price_cache_update(itype, region, instance_cost)
    return instance_cost

def get_eip_price(pricing, region, etype):
    #check if price is there in cache
    if etype in price_cache and region in price_cache[etype]:
        return price_cache[etype][region]

    #print "IPType=%s location=%s" %(etype, RegionMapping[region])
    price_detail = pricing.get_products(ServiceCode='AmazonEC2',
                                        Filters=[
                                            {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'IP Address'},
                                            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': RegionMapping[region]}
                                        ])
    #print json.dumps(price_detail, indent=2)
    UsageData = {}
    for item in price_detail['PriceList']:
        data = json.loads(item)
        if 'ElasticIP:AdditionalAddress' not in data['product']['attributes']['usagetype']:
            continue
        else:
            UsageData = data
    if not UsageData:
        return ''
    #print json.dumps(UsageData, indent=2)
    sku_code = UsageData['product']['sku']
    sku_offer_term = sku_code + '.' + OfferTermCode
    values = UsageData['terms']['OnDemand'][sku_offer_term]['priceDimensions']
    for key in values:
        if 'rateCode' in values[key]:
            ratecode = ['rateCode']
            cost = float(values[key]['pricePerUnit']['USD'])
            eip_cost = round((cost * 24 * 30.5), 2)
            price_cache_update(etype, region, eip_cost)
    return eip_cost

def get_ec2_instances(service, pricing, regions, body):
    header = ['Sr.','Region','InstanceId','Name', 'State','InstanceType','LaunchTime', 'Monthly cost']
    table = []
    c=1
    found = False
    for region in regions:
        ec2client = boto3.client('ec2', region_name=region)
        data = ec2client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        if not data or not data['Reservations'] or not data['Reservations'][0]['Instances']:
            continue

        for i in data['Reservations'][0]['Instances']:
            iname = ''
            if 'Tags' in i:
                tag = [x for x in i['Tags'] if x['Key'] == 'Name']
                iname = tag[0]['Value'] if tag[0] else ''
            try:
                instance_cost = get_ec2_price(pricing, region, i['InstanceType'])
                #print "Calling saving_update for %s %s %s" %(region, i['InstanceId'], i['InstanceType'])
                saving_update('ec2', instance_cost)
                instance_cost_dollar = '$ ' + str(instance_cost) if instance_cost else ''
            except Exception,e:
                print "Could not determine cost: %s" %(str(e))
                instance_cost_dollar=''
            table.append([c, region, i['InstanceId'], iname, i['State']['Name'],
                          i['InstanceType'], str(i['LaunchTime']), instance_cost_dollar])
            c += 1
            found = True

    if found:
        fdetails = [ f for f in functions[service] if f['name'] == inspect.stack()[0][3]]
        body += html_header_2(fdetails[0]['title'])
        body += html_header_3('Total EC2 spending approx <font color="red">$' + str(savings['ec2']) + '</font>. Save cost by identifying and stopping unused EC2 instances (if any)')
        body += html_table(header, table)
    return body

def get_ebs_volumes(service, pricing, regions, body):
    header = ['Sr.','Region', 'Volume Id', 'Name', 'Type', 'State', 'IOPS', 'Size', 'Creation Time', 'Monthly Cost']
    table = []
    c=1
    found = False
    for region in regions:
        ec2client = boto3.client('ec2', region_name=region)
        data = ec2client.describe_volumes()
        if not data or not data['Volumes']:
            continue
        for v in data['Volumes']:
            if v['State'] != 'available':
                continue
            vname = ''
            if 'Tags' in v:
                tag = [x for x in v['Tags'] if x['Key'] == 'Name']
                vname = tag[0]['Value'] if tag[0] else ''
            try:
                volume_cost = get_ebs_price(pricing, region, v['VolumeType'], v['Size'])
                saving_update('ebs', volume_cost)
                volume_cost_dollar = '$ ' + str(volume_cost) if volume_cost else ''
            except Exception,e:
                print "Could not determine cost. %s" %(str(e))
                volume_cost_dollar = ''
            table.append([c, region, v['VolumeId'], vname, v['VolumeType'], v['State'], v['Iops'], v['Size'], v['CreateTime'], volume_cost_dollar])
            c += 1
            found = True
    if found:
        fdetails = [ f for f in functions[service] if f['name'] == inspect.stack()[0][3]]
        body += html_header_2(fdetails[0]['title'])
        body += html_header_3('*save monthly <font color="red">$' + str(savings['ebs']) + '</font> by deleting following EBS volumes')
        body += html_table(header, table)
    return body

def get_eip(service, pricing, regions, body):
    header = ['Sr.','Region', 'EIP', 'InstanceId', 'InstanceState', 'Monthly Cost']
    table = []
    c=1
    found = False
    for region in regions:
        ec2client = boto3.client('ec2', region_name=region)
        data = ec2client.describe_addresses()
        if not data or not data['Addresses']:
            continue
        for e in data['Addresses']:
            iid=''
            istate=''
            if 'AssociationId' in e:
                if 'InstanceId' in e:
                    idata = ec2client.describe_instances(InstanceIds=[e['InstanceId']],
                                                         Filters=[{'Name':'instance-state-name', 'Values': ['stopped']}]
                                                         )
                    if not idata['Reservations']:
                        continue
                    else:
                        iid =  idata['Reservations'][0]['Instances'][0]['InstanceId']
                        istate = idata['Reservations'][0]['Instances'][0]['State']['Name']
                else:#If EIP is not attached to instance e.g NAT
                    continue
            try:
                eip_cost = get_eip_price(pricing, region, 'eip')
                saving_update('eip', eip_cost)
                eip_cost_dollar = '$ ' + str(eip_cost) if eip_cost else ''
            except Exception,e:
                print "Could not determine cost. %s" %(str(e))
                eip_cost_dollar = ''
            table.append([c, region, e['PublicIp'], iid, istate, eip_cost_dollar])
            c += 1
            found = True
    if found:
        fdetails = [ f for f in functions[service] if f['name'] == inspect.stack()[0][3]]
        body += html_header_2(fdetails[0]['title'])
        body += html_header_3('*save monthly <font color="red">$' + str(savings['eip']) + '</font> by releasing following EIP addresses')
        body += html_table(header, table)
    return body

####### START ###########

parser = argparse.ArgumentParser()
parser.add_argument('--service', '-s', help='service', required=False)
parser.add_argument('--region', '-r', help='Region', required=False)
args = parser.parse_args()

RegionMapping = {
    'us-east-1': 'US East (N. Virginia)',
    'us-east-2': 'US East (Ohio)',
    'us-west-1': 'US West (N. California)',
    'us-west-2': 'US West (Oregon)',
    'ap-south-1': 'Asia Pacific (Mumbai)',
    'ap-northeast-2': 'Asia Pacific (Seoul)',
    'ap-southeast-1': 'Asia Pacific (Singapore)',
    'ap-southeast-2': 'Asia Pacific (Sydney)',
    'ap-northeast-1': 'Asia Pacific (Tokyo)',
    'ca-central-1': 'Canada (Central)',
    'eu-central-1': 'EU (Frankfurt)',
    'eu-west-1': 'EU (Ireland)',
    'eu-west-2': 'EU (London)',
    'eu-west-3': 'EU (Paris)',
    'sa-east-1': 'South America (Sao Paulo)',
}
OfferTermCode = 'JRTCKXETXF'
price_cache = {}
savings = {}

def lambda_handler(event, context):
    #all_regions = [ {'RegionName' : 'ap-south-1'},{'RegionName' : 'us-east-1'}]
    pricing = boto3.client('pricing', region_name='us-east-1') #Always N.Virginia
    regions = []
    body = "<!DOCTYPE html><html><body>"
    all_regions = get_supported_regions('ec2')
    clear_cache()
    for service in functions.keys():
        if args.service and args.service != service:
            continue
        if args.region:
            regions = [args.region]
        else:
            for region in all_regions:
                regions.append(region['RegionName'])
        for f in functions[service]:
            body = globals()[f['name']](service, pricing, regions, body)

    if not savings:
        body += html_para('Looks like there are no AWS resources (EC2, EBS, EIP) in your AWS account')
    else:
        body += html_para('Note: The EC2 monthly cost is calculated considering on-demand pricing for Linux instances in given AWS Region.')
    body += "</html></body>"
    send_email(body)
    return 0

def send_email(body):
    #print body
    ses = boto3.client('ses', region_name='us-east-1')
    #Check if Sender and Receiver emails are already registered
    vemails = ses.list_verified_email_addresses(IdentityType='EmailAddress')
    reqemails = ses.list_identities(IdentityType='EmailAddress')
    sender = os.environ['SENDER_EMAIL']
    sender_verified = False
    if sender not in vemails['VerifiedEmailAddresses']:
        if sender in reqemails['Identities']:
            print "Sender Email %s verification is pending .." %(sender)
        else:
            print "Sending the verification for sender %s.." %(sender)
            ses.verify_email_address(EmailAddress=sender)
    else:
        sender_verified = True

    emailids = os.environ['RECV_EMAIL'].strip().replace("\t","").replace(" ","").split(",")
    verified = []
    for email in emailids:
        if email in vemails['VerifiedEmailAddresses']:
            verified.append(email)
        else:
            if email in reqemails['Identities'] and email not in vemails['VerifiedEmailAddresses']:
                print "%s is requested to verify the email" %(email)
            else:
                print "Sending the verification for receiver %s" %(email)
                ses.verify_email_address(EmailAddress=email)
    try:
        #Send email to only verified email addresses
        if verified and sender_verified:
            print "Sending emails to: ", verified
            ses.send_raw_email(
                Source=sender,
                Destinations=verified,
                RawMessage= {'Data': 'Subject: AWS Usage Daily Report\nMIME-Version: 1.0 \nContent-Type: text/html;\n\n' + body }
            )
        clear_cache()
    except Exception as e:
        print "Error sending email: %s" %(str(e))

def get_supported_regions(service):
    response = []
    if service == 'ec2':
        ec2_c = boto3.client('ec2')
        response = ec2_c.describe_regions()
    return response['Regions'] if response['Regions'] else []

#lambda_handler(None, None)