#!/usr/bin/python

import fileinput, string, GeoIP, sys, pprint, time, csv, pwd, ConfigParser

#
# script to create an xferlog extract named by ftp account and date range, 
# for transferring selectively elsewhere.
#
# this is so we can keep a list of ftp file transfers per project, if needed for that
# project.
#
# ONLY handles proftp logs, the script sftplog_report.py is for sftp, but uses the same config
#
# deployed in /etc/logrotate.d/proftpd-basic in postrotate script section, but can be run manually
# with any "xferlog" format log file as an input.
#
#
'''
# example config for /etc/logrotate.d/proftpd-basic
/var/log/proftpd/xferreport
{
        # monthly
        weekly
        missingok
        # rotate 24
        rotate 156
        compress
        delaycompress
        notifempty
        create 640 root adm
        sharedscripts
        prerotate
        endscript
        postrotate
                # reload could be not sufficient for all logs, a restart is safer
                invoke-rc.d proftpd restart 2>/dev/null >/dev/null || true
                # run ftpstats on past transfer log
                ftpstats -a -r -l 2 -d -h -f /var/log/proftpd/xferlog.1 2>/dev/null >/var/log/proftpd/xferreport || true
                # and custom ftp log extractor
                /usr/admin/xferlogreports/xferlog-extract.py /usr/admin/xferlogreports/ftpreport.ini /var/log/proftpd/xferlog.1 > /dev/null || true
        endscript
}
'''

# make the xferlog more readable with these definitions...
directions = { "o" : "outgoing",
               "i" : "incoming",
               "d" : "deleted" }

cstatusl = {"c" : "complete",
            "i" : "incomplete" }

gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

config = ConfigParser.ConfigParser()
try:
   config.read(sys.argv[1])
   logfilename = sys.argv[2]
except:
   print "Usage ",sys.argv[0]," config.ini logfilename"
   print "example config file:"
   print '''
[ftp]
reportdir = /tmp/xferlogtest
ignorefromip = 10.10.
ignorefromdomain = company.com.au
internalname = company_private_net
'''
   sys.exit(1)

reportdir = config.get('ftp','reportdir')

users = {}

for line in fileinput.input(sys.argv[2]):
   sline = line.split()
   dtime = string.join(sline[0:5])
   tdtime = time.strptime(dtime,'%a %b %d %H:%M:%S %Y')
   transfertime = sline[5]
   remotehost = sline[6]
   filesize = int(sline[7])
   filename = sline[8]
   direction = directions[sline[11]]
   username = sline[13]
   cstatus = cstatusl[sline[17]]

   country = gi.country_code_by_addr(remotehost)
   if country == None:
       country = gi.country_code_by_name(remotehost)
   if country == None:
       country = "NOT KNOWN"

   # flag internal network or company domain hosts 
   if remotehost.find(config.get('ftp','ignorefromip')) == 0 or remotehost.find(config.get('ftp','ignorefromdomain')) > 1:
      country = config.get('ftp','internalname')

   if users.has_key(username):
      users[username].append([tdtime,dtime,transfertime,remotehost,filesize,filename,direction,username,cstatus,country])
   else:
      users[username] = [[tdtime,dtime,transfertime,remotehost,filesize,filename,direction,username,cstatus,country]]

for user in users:
   print "user ",user
   users[user].sort()
   # remove users homedir from file, declutters the report - if the user is still there!
   try:
     homedir = pwd.getpwnam(user).pw_dir
     print "homedir is",homedir
   except:
     print "user not found"
     homedir = "" 
   print "first ",time.strftime("%Y-%m-%d-%H-%M",users[user][0][0])
   first = time.strftime("%Y-%m-%d-%H-%M",users[user][0][0])
   print "last ",time.strftime("%Y-%m-%d-%H-%M",users[user][-1][0])
   last = time.strftime("%Y-%m-%d-%H-%M",users[user][-1][0])
   csvfileptr = open(reportdir+'/'+user+" "+first+" to "+last+".csv",'wb')
   csvfile = csv.writer(csvfileptr,dialect='excel')
   # write heading
   csvfile.writerow(["time","transfertime","remotehost","filesize","filename","direction","username","status","country"])
   for line in users[user]:
      line[5] = line[5].replace(homedir,'')
      csvfile.writerow(line[1:])
   csvfileptr.close()
