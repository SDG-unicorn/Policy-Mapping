import os, sys
import pathlib as ptlb

#print(ptlb.Path.cwd())
sys.stdout.write(str(os.system('git status')))

def test_execution():
    #pass
    #os.system('./python3 keyword_count_polmaplib.py -i test/data/goalandtarget.txt -k keywords/keywords.xlsx -o output/exectution_test')
    #print(os.system('git status'))
    return os.system('git status')
    
