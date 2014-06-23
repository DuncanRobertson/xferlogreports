xferlogreports
==============

extract proftp xferlog and sftp log file info into per account, dated, readable CSV files viewable by spreadsheet.

for when you need to give some one legible reports on proftp and sftp account usage, instead of the unreadable stuff the default logging spits out.

intended to be added to the logrotate conf so they are run on the just renamed log file for both sftpd and proftpd.

very rudimentary config file parsing, ini file needs an [sftp] or [ftp] section for the appropriate scripts.

example logrotate conf and ini files in the source code.


