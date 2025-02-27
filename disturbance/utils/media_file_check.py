import os
import argparse
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_MEDIA_PATH = os.path.normpath(BASE_DIR + "/media/")
ROOT_PRIVATE_MEDIA_PATH = os.path.normpath(BASE_DIR + "/private-media/")

def validate_paths(src_path, dst_path):
    #validate src_path
    if not src_path.startswith(ROOT_MEDIA_PATH):
        raise Exception("Source file path provided not within root media path:",ROOT_MEDIA_PATH)
    #validate dst_path
    if not dst_path.startswith(ROOT_PRIVATE_MEDIA_PATH):
        raise Exception("Destination file path provided not within root private media path:",ROOT_PRIVATE_MEDIA_PATH)

def normalise_paths(src_path, dst_path):
    try:
        src_path = os.path.normpath(src_path)
    except:
        raise Exception("Invalid source file path provided")

    try:
        dst_path = os.path.normpath(dst_path)
    except:
        raise Exception("Invalid destination file path provided")

    return src_path, dst_path

def remove_base_path(base_path,path):
    return path.replace(base_path,"")

def get_dir_files(directory):
    
    found_files = []

    #iterate through files
    for path, folders, files in os.walk(directory):
        #run func recursively for sub-directories
        for file in files:
            found_files.append(os.path.join(path,file))
        
    return found_files

def check_missing_files(src_path, dst_path):
    #normalise paths
    src_path, dst_path = normalise_paths(src_path, dst_path)
    #validate paths
    validate_paths(src_path, dst_path)

    src_files = get_dir_files(src_path)
    dst_files = get_dir_files(dst_path)
    
    temp = []
    for file in src_files:
        temp.append(remove_base_path(ROOT_MEDIA_PATH,file))
    src_files = temp

    temp = []
    for file in dst_files:
        temp.append(remove_base_path(ROOT_PRIVATE_MEDIA_PATH,file))
    dst_files = temp

    missing_files = []
    found_files = []

    for file in src_files:
        if file in dst_files:
            found_files.append(file)
        else:
            missing_files.append(file)

    return missing_files, found_files

def copy_missing_files(src_path, dst_path, overwrite=False, copy=False):

    missing_files, found_files = check_missing_files(src_path, dst_path)

    if missing_files:
        print("\n\nFiles missing from destination directory:\n")
        for i in missing_files:
            print(i,"\n")
    else:
        print("\n\nNo files missing")
    
    if found_files:
        print("\n\nFiles found in destination directory:\n")
        for i in found_files:
            print(i,"\n")

    if copy:
        print("\n\ncopying files to destination directory\n\n")
        for i in missing_files:
            copy_src_path = ROOT_MEDIA_PATH + i
            copy_dst_path = ROOT_PRIVATE_MEDIA_PATH + i
            os.makedirs(os.path.dirname(copy_dst_path), exist_ok=True)
            shutil.copy(copy_src_path, copy_dst_path)
            print(copy_src_path, "copied to", copy_dst_path, "\n")

        #if overwrite is True then we also overwrite files that are not missing
        if overwrite:
            print("\n\noverwrite option active - overwriting all files in destination directory")
            for i in found_files:
                copy_src_path = ROOT_MEDIA_PATH + i
                copy_dst_path = ROOT_PRIVATE_MEDIA_PATH + i
                print(copy_src_path, "overwrites", copy_dst_path, "\n")
                shutil.copy(copy_src_path, copy_dst_path)

def __main__():

    parser = argparse.ArgumentParser()
    parser.add_argument("src_path", help="file path of media directory or sub-directory, source path for checking/replacing missing files")
    parser.add_argument("dst_path", help="file path of private media directory or sub-directory, destination path for checking/replacing missing files")
    parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite all files in specified destination path with those found in specified source path")
    parser.add_argument("-c", "--copy", action="store_true", help="copy the files to the destination directory, otherwise missing and found files are just listed in a printout")
    args = parser.parse_args()
    
    print("\nRunning media_file_check.py...")

    if not args.copy:
        print("\n\nOnly listing files, files will not be copied...\n\n")

    print("Source Directory:",args.src_path)
    print("Destination Directory:", args.dst_path)
    copy_missing_files(args.src_path, args.dst_path, args.overwrite)

__main__()