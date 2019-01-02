import re, time, argparse
import collections, operator
from bisect import insort_left
import array, pickle
        
#==============================================================================
def arguments():
    # adapted from test-harness.py
    # returns: infile to be compressed, symbol scheme
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="input file to be compressed")
    parser.add_argument("-s", "--symbolmodel", help="specify character- or word-based Huffman encoding -- default is character",
                        choices=["char","word"])
    args= parser.parse_args()
    
    if not(args.symbolmodel):
        symbolmodel= 'char'
    else:
        symbolmodel = args.symbolmodel
    
    # Check that input file is there
    try:
        f = open(args.infile,'rb')
    except FileNotFoundError:   
        print("File",args.infile,"not found")
        exit(1)
    f.close()
    return(args.infile, symbolmodel)

def countSymbols(file,symbolType):
# countSymbols function
# counts symbols in a file according to the symbol type determing
# args: text file, symbol type (word | char)
# returns: dict {key=word, val=amount of 'word' in text}
    wordCount = collections.defaultdict(int)
    file_object = open(file)
    #choose regex accortdigly to symbol type
    if (symbolType == 'char'):
        fileRe = re.compile('.|[\n\t\0\r]+')  #any single char OR non printable chars
    else:
        fileRe = re.compile('[a-zA-z]+|.|[\n\t\0\r]+') # any word | any other char | non printable chars
    for line in file_object:
        for word in fileRe.findall(line):
            wordCount[word] += 1
    file_object.close()
    return (wordCount)

def zeroOrder(tfDict):
# zero_order function
# calculates zero order model of given text
# args: term and term freqeuncy dictionary {term: frequency}
# returns: dict{term: probability}
    total_symbols = sum(tfDict.values())
    for k,v in tfDict.items():
        tfDict[k]= v / total_symbols
    return (tfDict)

def createNodes(zom):
# createNodes function
# calculates zero order model of given text
# args: term and term freqeuncy dictionary {term: frequency}
# returns: dict{term: probability}
    nodesList =[]
    for symbol in zom:
        node = Node(symbol[0],symbol[1])
        nodesList.append(node)
    return(nodesList)

def binaryTree(nodeslist):
# binaryTree function
# given a list of nodes, will create a binary tree
# args: list of nodes
# returns: root node of binary tree
    while len(nodeslist) != 1:
        # get the last two elements of sorted list
        right= nodeslist.pop(-1)
        left = nodeslist.pop(-1)
        # create and store new node
        newProb = right.probability + left.probability        
        newNode = Node(None, newProb, left, right)
        insort_left(nodeslist,newNode) # insert new node in a sorted manner
    return (nodeslist)

def getBinaryCodes(node,bit, newbit):
# getBinaryCodes function
# given root node of tree, will assign binary codes by traversing the binary tree, storing them in a dictionary
# args: binary tree node, bit code until this tree node, newbit depending branch of origin
    # preorder tree traversal
    bit += newbit #create a string of bit values (0/1)
    if (node.leftSub == None and node.rightSub == None):
        binaryCodes[node.symbol] = bit #store to dictionary of symbol:bit representation
        bit=''
        return()
    getBinaryCodes(node.leftSub, bit, '0')
    getBinaryCodes(node.rightSub, bit, '1')
    
def encode(binaryCodes, file, symbol):
# encode function
# given a model, a file and an encoding method (char/word) will create a binary form string representation of the file
# args: model, file, symbol type
# returns: binary form string
    file_object = open(file)
    binStr = ''
    #choose regex accortdigly to symbol type
    if (symbol == 'char'):
        fileRe = re.compile('.|[\n\t\0\r]+')  #any single char OR non printable chars
    else:
        fileRe = re.compile('[a-zA-z]+|.|[\n\t\0\r]+') # any word | any other char | non printable chars
    for line in file_object:
        for word in fileRe.findall(line):
            binStr += binaryCodes[word]
    file_object.close()
    return (binStr)

def pad(string):
# pad function 
# given a string will pad with a number of 0 so string % 8 = 0
# args: binary form string
# return: padded string, pseudo-EOF character 
    eof =''
    while (len(string)%8 !=0):
        eof += '0'
        string += '0'
    return (string,eof)

def compress(encoded):
# compress function
# given a byte form string to bytes and store them into an array
# args: byte form string
# return: array of  bytes
    codearray = array.array('B')
    lowerLim = 0
    lim = int(len(encoded)/8)
    for n in range (0,lim):
        byte = encoded[lowerLim:lowerLim+8]
        lowerLim += 8
        codearray.append(int(byte,2))
    return (codearray)

#==============================================================================
class Node(object):
# class Node
# attributes: symbol, probability, left subtree, right subtree
# function __lt__
    def __init__(self, symbol, probability, left = None, right = None):
        self.symbol = symbol
        self.probability = probability
        self.leftSub = left
        self.rightSub = right
        
    # function __lt__ of bisect module
    # used by insort_left for comparison
    # should be self.probability < other.probability but is opposite because nodes list sorted on reverse
    def __lt__(self, other):
        return self.probability > other.probability
    
#==============================================================================
if __name__ == '__main__':
    start_time = time.time() #timer 
    infile, symbolType = arguments() #get arguments
    wordCount = countSymbols(infile,symbolType) #get word count
    zeroOrderModel = zeroOrder(wordCount) #calculate zero order model
    sortedZOM = sorted(zeroOrderModel.items(), key=operator.itemgetter(1), reverse = True) #sorted list of zero order model dictionary
    nodes = createNodes(sortedZOM) #create list of nodes based on sorted list of zero order model
    nodes = binaryTree(nodes) #create code tree    

    # create binary codes dictionary {symbol:binaryCodes}    
    binaryCodes = {}
    getBinaryCodes(nodes[0],'','')
    # print time needed for model creation, restart counter
    elapsed_time = time.time() - start_time
    print('model time: {0:.3f} sec'.format(elapsed_time))
    start_time = time.time()
    
    encoded = encode(binaryCodes, infile, symbolType) #encode text to binary form string
    encoded,eof = pad(encoded) #pad binary form string so it can be divisible to bytes and create pseudo-EOF character
    binaryCodes['eof']= eof #store pseudoeof character to symbol model
    codearray = compress(encoded) #get array of bytes
    
    #store compressed text to infile.bin file
    #store symbol dictionary to infile-symbol-model.pkl file
    pickle.dump(codearray, open(infile.split('.')[0] + ".bin", "wb"))
    pickle.dump(binaryCodes, open(infile.split('.')[0] + "-symbol-model.pkl","wb"))
    elapsed_time = time.time() - start_time
    print('compression time: {0:.3f} sec'.format(elapsed_time))