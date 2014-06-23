xferlogreports
==============

extract proftp xferlog and sftp log file info into per account, dated, readable CSV files viewable by spreadsheet

intended to be added to the logrotate conf so they are run on the just renamed log file for both sftpd and proftpd.

very rudimentary config file parsing, ini file needs an [sftp] or [ftp] section for the appropriate scripts.

example logrotate conf and ini files in the source code.



