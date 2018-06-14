#!/usr/bin/env python
# WPE RDKV post-release bootstrapper
# Enables latest WPE on older versions of RDK

import sys, getopt, re, fileinput, urllib2, json, base64, os, subprocess

################################################################################
# Variables                                                                    #
################################################################################
manifest = {
	'17.2' : [
		'/meta-cmf-raspberrypi/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'/meta-cmf-raspberrypi/recipes-wpe/wpebackend-rdk/wpebackend-rdk_%.bbappend',
		'/meta-rdk-oem-tch-broadcom/meta-tch-spectrum-120i-uhd/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'/meta-rdk-charter-technicolor/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend',
		'/meta-rdk-video/recipes-multimedia/gstreamer/gstreamer1.0*',
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-multimedia/gstreamer/gstreamer1.0-plugins-good*'
	],
	'17.3' : [
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'/meta-cmf-raspberrypi/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend',
		'/meta-rdk-video/recipes-graphics/cairo/cairo_%.bbappend',
		'/meta-rdk-video/recipes-multimedia/gstreamer/gstreamer1.0_1.10.4.bbappend',
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend',
		'/meta-rdk-video/recipes-multimedia/gstreamer/gstreamer1.0*',
		'/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-multimedia/gstreamer/gstreamer1.0-plugins-good*'
	],
        '17.4' : [
                '/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
                '/meta-cmf-raspberrypi/recipes-wpe/wpewebkit/wpewebkit_%.bbappend',
                '/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend',
                '/meta-rdk-video/recipes-graphics/cairo/cairo_%.bbappend',
                '/meta-rdk-video/recipes-multimedia/gstreamer/gstreamer1.0_1.10.4.bbappend',
                '/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-wpe/wpebackend-rdk/wpebackend-rdk_0.1.bbappend',
                '/meta-rdk-video/recipes-multimedia/gstreamer/gstreamer1.0*',
                '/meta-rdk-broadcom-generic-rdk/meta-brcm-generic-rdk/recipes-multimedia/gstreamer/gstreamer1.0-plugins-good*'
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

def generateBBMask(mask):
	return 'BBMASK += "' + mask + '"\n'

def writeSiteConf(bbmasks, siteConfFile):
	with open(siteConfFile,'a+') as f:
		f.write(bbmasks)
	return

def silentExec(processAndParamsList):
	with open(os.devnull, 'wb') as devnull:
		subprocess.check_call(processAndParamsList, stdout=devnull, stderr=subprocess.STDOUT)
		return

################################################################################
# Main                                                                         #
################################################################################
def main(argv):
	bbMaskString 	= ""

	# Figure out which version of RDKV & Yocto were up against
	rdkvVersion     = findRdkvVersion()
	yoctoVersionName = rdkToYoctoMapping[ rdkvVersion ]
	print 'Found RDKV v' + rdkvVersion + ' and Yocto ' + yoctoVersionName

	# Disabled because aparently DISTRO VERSION isnt updated correctly for each RDK release :-(
	#yoctoVersion    = findYoctoVersion()
	#print 'Found Yocto v' + yoctoVersion
	#yoctoVersionName = yoctoMapping[ yoctoVersion ]

	# Sync meta-wpe to latest relevant meta-wpe Yocto branch if meta-wpe directory does not exist
	if os.path.isdir('./meta-wpe') == False:
		print 'Creating new clone of meta-wpe with the ' + yoctoVersionName + ' branch'
		silentExec(['git','clone','git@github.com:WebPlatformForEmbedded/meta-wpe.git','-b', yoctoVersionName])
	else:
		print 'Syncing latest meta-wpe to ' + yoctoVersionName + ' branch'

		os.chdir('./meta-wpe')
		silentExec(['git','checkout',yoctoVersionName])
		silentExec(['git','fetch'])
		silentExec(['git','rebase'])
		os.chdir('..')


	# generating bbmasks
	maskList = manifest[ rdkvVersion ]

	for e in maskList:
		bbMaskString += generateBBMask(e)


	#Trying to find your build directory
	dirList = os.listdir(os.getcwd())

	# check for existing build directory, which means yocto has been previously setup and we can write a site.conf if empty
	for d in dirList:
		if d[0:6] == 'build-':
			print 'Found build dir: ' + d
			siteConfFile = './' + d + '/conf/site.conf'

			if os.path.isfile(siteConfFile) == False:
				print 'No site.conf found in build dir, creating it'
				writeSiteConf(bbMaskString, siteConfFile)
			else:
				print 'Site conf is already present, did you run this script already?\n'
				print 'Please add the following to your local.conf or site.conf:'
				print bbMaskString



	print '\nDone! Please make sure to add meta-wpe to your bblayers when creating the build.'

if __name__ == '__main__':
	main(sys.argv[1:])
