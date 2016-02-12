"""
Photogrammetry toolkit
"""
import argparse
import os
import subprocess
import sys
import cv2

bundleFileName  = "bundle.nvm"
makesceneAppUrl = "/mve/apps/makescene/makescene"
makesceneResultFolderSufix = "SCENE/"
sfmreconAppUrl = "/mve/apps/sfmrecon/sfmrecon"
dmreconAppUrl = "/mve/apps/dmrecon/dmrecon"
scene2psetAppUrl = "/mve/apps/scene2pset/scene2pset"
psetFileName = "pset-L2.ply"
fssreconAppUrl = "/mve/apps/fssrecon/fssrecon"
surfaceFileName = "surface-L2.ply"
meshcleanAppUrl = "/mve/apps/meshclean/meshclean"
cleanedSurfacePrefix = "clean"
frameAmountToBeGeneratedFromVideo = 500
blurLaplacianThreshold = 110

def runInteractiveSystemCommand(command):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    while True:
        data = proc.stdout.readline()   # Alternatively proc.stdout.read(1024)
        if len(data) == 0:
            break
        sys.stdout.write(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Reconstruct a Poisson surface from photos using photogrammetry.')
    parser.add_argument('url', help='URL of a folder with photos or video file')
    args = parser.parse_args()
    url = None
    #sample a video into files
    splitedArgument = args.url.split(".")
    if splitedArgument[-1] in ['avi', 'mp4', 'mpg']:
        cap = cv2.VideoCapture(args.url)
        frameNumber = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
        print "Video contains ", frameNumber, " frames"
        if frameNumber < 2:
            print "The video contains to little frames"
            cap.release()
            exit()
        else: #make a folder with the same name like the video
            url = args.url[:-(len(splitedArgument[-1]) + 1)]
            runInteractiveSystemCommand("mkdir "+url)
            takeEveryN_Frame = int(frameNumber) / frameAmountToBeGeneratedFromVideo
            print "Only ", frameAmountToBeGeneratedFromVideo, " frames needed, will skip every ", takeEveryN_Frame, " frames."
            for imageIndex in xrange(frameNumber):
                ret, frame = cap.read()
                # compute the Laplacian of the image and then return the focus
	            # measure, which is simply the variance of the Laplacian
                if imageIndex % takeEveryN_Frame == 0 and \
                                cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var() > blurLaplacianThreshold:
                    imageName = url + "/" + str(imageIndex) + ".jpg"
                    print "Saved ", imageName
                    cv2.imwrite(imageName, frame)
            cap.release()
    else:
        url = args.url
    #prepare a bundle for feature extraction
    listOfFilesInFolder = os.listdir(url)
    if len(listOfFilesInFolder)<2:
        print("Not enough files for photogrammetry processing")
    with open(url + '/'+ bundleFileName,'w') as bundleFile:
        for fileName in listOfFilesInFolder:
            splitedName= fileName.split('.')
            if len(splitedName) >= 2:
                extension = splitedName[-1]
                if extension in ['jpg', 'jpeg', 'png']:
                    bundleFile.write(fileName+'\n')

    #creates a separate folder with the views
    sceneResultFolderUrl = url + makesceneResultFolderSufix

    #makescene: makescene -i <image-dir> <scene-dir>
    makesceneCommand ='.' + makesceneAppUrl + ' -i ' + url + ' ' + sceneResultFolderUrl
    runInteractiveSystemCommand(makesceneCommand)

    #sfmrecon: sfmrecon <scene-dir>
    sfmreconCommand = '.' + sfmreconAppUrl + ' ' + sceneResultFolderUrl
    runInteractiveSystemCommand(sfmreconCommand)

    #dmrecon: dmrecon -s2 <scene-dir>
    dmreconCommand = '.' + dmreconAppUrl + ' -s2 ' + sceneResultFolderUrl
    runInteractiveSystemCommand(dmreconCommand)

    #scene2pset: scene2pset -F2 <scene-dir> <scene-dir>/pset-L2.ply
    scene2psetCommand = '.' + scene2psetAppUrl + ' -F2 ' + sceneResultFolderUrl + ' ' + sceneResultFolderUrl \
                        + psetFileName
    runInteractiveSystemCommand(scene2psetCommand)

    #fssrecon: fssrecon <scene-dir>/pset-L2.ply <scene-dir>/surface-L2.ply
    fssreconCommand = '.' + fssreconAppUrl + ' ' + sceneResultFolderUrl + psetFileName + ' ' + sceneResultFolderUrl \
                      + surfaceFileName
    runInteractiveSystemCommand(fssreconCommand)

    #meshclean: meshclean -p10 <scene-dir>/surface-L2.ply <scene-dir>/surface-L2-clean.ply
    cleanedSurfaceUrl = sceneResultFolderUrl + cleanedSurfacePrefix + surfaceFileName
    meshcleanCommand = '.' + meshcleanAppUrl + ' -p10 ' + sceneResultFolderUrl + surfaceFileName + ' ' + \
                       cleanedSurfaceUrl
    runInteractiveSystemCommand(meshcleanCommand)

    #vizualize the output mesh
    #meshlab: meshlab <scene-dir>/surface-L2-clean.ply
    meshlabCommand =  'meshlab' + ' ' + cleanedSurfaceUrl
    runInteractiveSystemCommand(meshlabCommand)
