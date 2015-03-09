#!/usr/bin/env python


import os, sys, time, httplib, urllib

PLUGIN_NAME = "EDPluginControlInterfaceToMXCuBEv1_3"
BES_HOST = "mxhpc2-1601.esrf.fr"
BES_PORT = 8080


if __name__ == '__main__':

	if len(sys.argv) < 4:
		print("Usage: {0} inputFile outputFile workingDirectory".format(os.path.basename(sys.argv[0])))
		sys.exit(1)
		
	pluginName = "EDPluginControlInterfaceToMXCuBEv1_3"
	inputFile = sys.argv[1]
	outputFile = sys.argv[2]
	workingDirectory = sys.argv[3]

	print("Running BES Characterisation workflow with:")
	print("pluginName = " + pluginName)
	print("inputFile = " + inputFile)
	print("outputFile = " + outputFile)
	print("workingDirectory = " + workingDirectory)

	# Create EDNA script file, just for re-processing
	timeString = time.strftime("%Y%m%d-%H%M%S", time.localtime(time.time()))
	ednaStartScriptFileName = "edna_start_{0}.sh".format(timeString)
	print("Name of EDNA startup script: " + ednaStartScriptFileName)

	ednaStartScriptFilePath = os.path.join(workingDirectory, ednaStartScriptFileName)
	
	try:
		ednaStartFile = open(ednaStartScriptFilePath, "w")
		ednaStartFile.write("export EDNA_SITE=ESRF\n")
		ednaStartFile.write("/opt/pxsoft/bin/edna-plugin-launcher  --execute EDPluginControlInterfaceToMXCuBEv1_3")
		ednaStartFile.write(" --inputFile {0} --outputFile {1} --basedir {2} 2>&1\n".format(inputFile, outputFile, workingDirectory))
		ednaStartFile.close()		
		os.chmod(ednaStartScriptFilePath, 0755)
		
		directories = workingDirectory.split(os.path.sep)
		try:
			if directories[2]=='visitor':
				beamline = directories[4]
				proposal = directories[3]
			else:
				beamline = directories[2]
				proposal = directories[4]
		except:
			beamline = "unknown"
			proposal = "unknown" 

		conn = httplib.HTTPConnection(BES_HOST, BES_PORT)
		params = urllib.urlencode({"inputFile":inputFile,
								   "outputFile":outputFile,
								   "workingDirectory":workingDirectory,
								   "pluginName": PLUGIN_NAME,
								   "beamline": beamline,
								   "proposal": proposal,
								   "initiator": beamline,
                                   "externalRef": proposal,
                                   "reuseCase": "true" })
		conn.request("POST", 
					 "/BES/bridge/rest/processes/Characterisation/RUN?%s" % params, 
					 headers={"Accept":"text/plain"})
		response = conn.getresponse()
		if response.status != 200:
			print("ERROR! RUN response status = {0}".format(response.status))
		else:
			requestId=response.read()
			print("Workflow started, request id: %r" % requestId)
			
			# What till finished
			bContinue = True
			while bContinue:
				time.sleep(1)
				statusWorkflowURL = os.path.join("/BES", "bridge", "rest", "processes", requestId, "STATUS")
				conn = httplib.HTTPConnection(BES_HOST, BES_PORT)
				conn.request("GET", statusWorkflowURL)
				response = conn.getresponse()
				if response.status == 200:
					workflowStatus=response.read()
					print(workflowStatus)
					if workflowStatus != "STARTED":
						bContinue = False
				else:
					print("ERROR! STATUS response status = {0}".format(response.status))
					bContinue = False
				



	except:
		raise