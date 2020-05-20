import os
import zipfile

def unzip_file(zipfilename, dirname):      # zipfilename is the compressed file，dirname is the directory to be compressed
    with zipfile.ZipFile(zipfilename, 'r') as z:
        z.extractall(dirname)

DataDir = './environment_classification_dataset'
targetPath = './environment_classification_dataset_upzip'

for i in range(1, 9):
    source = '%s/subject_%03d' % (DataDir, i)
    print(source)
    subfiles = [o for o in os.listdir(source) if o.endswith('.zip')]
    for sub in subfiles:
        zipPath = '%s/%s' % (source, sub)
        print(zipPath)
        unzip_file(zipPath, targetPath)
