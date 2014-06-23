#!/usr/bin/python
#
import fileinput, sys, string, GeoIP, pprint, csv, ConfigParser

#
#  parses SFTP log files (with the newer precision timestamp from rsyslog)
#  to produce a csv spreadsheet of uploads, downloads and deletions.
#
#
# needs rsyslog set to have RSYSLOG_TraditionalFileFormat DISABLED so it
# works with the "high precision" timestamps that also log the YEAR.
#
# i.e. syslog has to timestamp in the format 2012-06-10T06:25:53.584812+10:00
#
# can be run manually, or 
# deployed as a postrotate action in /etc/logrotate.d/ssh-sftp

# i.e.
'''
/var/log/sftp.log {
        weekly
        missingok
        rotate 52
        compress
        delaycompress
        postrotate
                invoke-rc.d rsyslog reload > /dev/null
                /usr/admin/xferlogreports/sftplog_report.py /usr/admin/xferlogreports/ftpreport.in /var/log/sftp.log.1 > /dev/null
        endscript
}
'''


gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

config = ConfigParser.ConfigParser()
try:
   config.read(sys.argv[1])
   logfilename = sys.argv[2]
except:
   print "Usage ",sys.argv[0]," config.ini logfilename"
   print "example config file:"
   print '''
[sftp]
reportdir = /tmp/xferlogtest
ignorefromip = 10.10.
ignorefromdomain = company.com.au
internalname = company_private_net
'''
   sys.exit(1)

reportdir = config.get('sftp','reportdir')


pidlines = {}

# first extract out all the lines for each pid

for line in fileinput.input(logfilename):
   sline = line.split()
   date = sline[0]
   pid = sline[2].strip("internal-sftp[").strip("]:")

   if pidlines.has_key(pid):
      pidlines[pid].append([date,sline[3:],line])
   else:
      pidlines[pid] = [[date,sline[3:],line]]

userentries = {}

# process each pid, getting fromip and username,
# then any files uploaded/downloaded/deleted.

for pid in pidlines:
   user = ''
   fromip = ''
   country = ''
   for line in pidlines[pid]:
      # set for line
      date = line[0]
      # below set for whole connection, but should be at first entry..
      if line[1][0:5] == ['session', 'opened', 'for', 'local', 'user']:
         user = line[1][5]
         if not userentries.has_key(user):
            userentries[user] = []
         fromip = line[1][7].strip("]").strip("[")
         country = gi.country_code_by_addr(fromip)
         if country == None:
            country = gi.country_code_by_name(fromip)
         if country == None:
            country = "NOT KNOWN"

         # flag internal network or company domain hosts 
         if fromip.find(config.get('sftp','ignorefromip')) == 0 or fromip.find(config.get('sftp','ignorefromdomain')) > 1:
            country = config.get('sftp','internalname')
         # print "ip found ", fromip, "country determined as: ",country

      #
      filesplit = line[2].split('"')
      # print filesplit
      if filesplit[0].split(":")[-1] == ' remove name ':
         file = filesplit[1]
         # print date,fromip,user
         # print "delete occurred on file: ",file
         userentries[user].append([date,"",fromip,"",file,"delete",user,"",country])
      if len(filesplit) > 2:
         file = filesplit[1]
         fileinfo = filesplit[2].split()
         if len(fileinfo) == 5:
            if int(fileinfo[4]) > 0:
               # print date,fromip,user
               # print "upload occurred of file:",file
               userentries[user].append([date,"",fromip,int(fileinfo[4]),file,"upload",user,"",country])
            if int(fileinfo[2]) > 0:
               # print date,fromip,user
               # print "download occurred of file:",file
               userentries[user].append([date,"",fromip,int(fileinfo[2]),file,"download",user,"",country])

# format we want to write the csv file in         
# ["time","transfertime","remotehost","filesize","filename","direction","username","status","country"])

for user in userentries.iterkeys():
   userentries[user].sort()
   if len(userentries[user]) < 1:
      continue
   first = userentries[user][0][0]
   last = userentries[user][-1][0]
   csvfileptr = open(reportdir+'/'+user+" "+first+" to "+last+".csv",'wb')
   csvfile = csv.writer(csvfileptr,dialect='excel')
   csvfile.writerow(["time","transfertime","remotehost","filesize","filename","direction","username","status","country"])
   for entry in userentries[user]:
      csvfile.writerow(entry)
   csvfileptr.close()
