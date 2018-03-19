#!/usr/bin/env python
# WPE RDKV post-release bootstrapper
# Enables latest WPE on older versions of RDK

import sys, getopt, re, fileinput, urllib2, json, base64, os

################################################################################
# Variables                                                                    #
################################################################################
manifest = {
	'17.2' : [
		'./meta-cmf-raspberrypi/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'./meta-rdk-oem-tch-broadcom/meta-tch-spectrum-120i-uhd/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'./meta-rdk-charter-technicolor/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'./meta-cmf-raspberrypi/recipes-wpe/wpebackend-rdk/wpebackend-rdk_%.bbappend',
		'./meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend',
		'./meta-rdk-oem-tch-broadcom/meta-tch-spectrum-120i-uhd/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend'
	],
	'17.3' : [
		'./meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'./meta-cmf-raspberrypi/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'./meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend'
	]
}

rdkToYoctoMapping = {
	'17.2' : 'krogoth',
	'17.3' : 'krogoth',
	'17.4' : 'morty'
}

yoctoMapping = {
	'2.0' : 'jethro',
	'2.1' : 'krogoth',
	'2.2' : 'morty',
	'2.3' : 'pyro',
	'2.4' : 'rocko'
}

bcmRefswDirectory = './meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-bsp/broadcom-refsw/'
yoctoDistroConf   = './meta-cmf/conf/distro/rdk.conf'

################################################################################
# Utility                                                                      #
################################################################################

# Reads all files in the bcmRefwDirectory and tries to find the correct bcm refsw version in the .bb filename
def findRdkvVersion():
	filelist = os.listdir(bcmRefswDirectory)
	version = None

	# Parse & find right refsw version (this should match the RDKV version, usually)
	for item in filelist:
		bbFile = re.search(r'(.bb)(?!append)', item)
		if bbFile:
			version = re.search(r'([0-9]{1,2})([.][0-9]{1,3})', item)
			if version:
				version = version.group(0)
			else:
				continue
		else:
			continue


	return version

# Opens the RDK distro configuration file and reads the DISTRO_VERSION number
def findYoctoVersion():
	version = None

	with open(yoctoDistroConf, 'r') as f:
		for line_terminated in f:
			line = line_terminated.rstrip('\n')  

			# skip garbage
			if line[0:1] == ' ' or line == '' or line[0:1] == '#':
				continue

			# find distro version, break it down and exit loop
			if line[0:14] == 'DISTRO_VERSION':
				version = line.split('=')[1].replace(' ', '').replace('"', '')
				break

	return version

# Renames a .bbappend to .off
def disableBbappend(file):
	if os.path.isfile(file):
		os.rename(file, file[:-8] + '.off')

################################################################################
# Main                                                                         #
################################################################################
def main(argv):
	# Figure out which version of RDKV & Yocto were up against
	rdkvVersion     = findRdkvVersion()
	print 'Found RDKV v' + rdkvVersion

	# Disabled because aparently DISTRO VERSION isnt updated correctly for each RDK release :-(
	#yoctoVersion    = findYoctoVersion()
	#print 'Found Yocto v' + yoctoVersion
	#yoctoVersionName = yoctoMapping[ yoctoVersion ]

	fileList = manifest[ rdkvVersion ]

	for file in fileList:
		disableBbappend(file)
		print "Disabled " + file

	
	yoctoVersionName = rdkToYoctoMapping[ rdkvVersion ]
	print 'Syncing meta-wpe to ' + yoctoVersionName + ' branch'

	# Sync meta-wpe to latest relevant meta-wpe Yocto branch if meta-wpe directory does not exist
	if os.path.isdir('./meta-wpe') == False:
		os.system('git clone git@github.com:WebPlatformForEmbedded/meta-wpe.git -b ' + yoctoVersionName)

	os.chdir('./meta-wpe')
	os.system('git checkout ' + yoctoVersionName)
	os.system('git fetch')
	os.system('git rebase')
	os.chdir('..')

	print '\nDone! Please make sure to add meta-wpe to your bblayers when creating the build.'

if __name__ == '__main__':
	main(sys.argv[1:])
