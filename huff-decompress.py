import time, argparse, pickle

#==============================================================================
def arguments():
    # adapted from test-harness.py
    # returns: infile to be compressed, symbol scheme
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="file to be decompressed")
    args= parser.parse_args()
    model = args.infile.split('.')[0] + "-symbol-model.pkl"
    
    # Check that input file is there
    try:
        f = open(args.infile,'rb')
    except FileNotFoundError:   
        print("File",args.infile,"not found")
        exit(1)
    f.close()
    
    try:
        f = open(model,'rb')
    except FileNotFoundError:   
        print("File",model,"not found")
        exit(1)
    f.close()
    return(args.infile,model)
    
#==============================================================================
def reByte(bit):
# reByte function
# given a binary code of arbitrary number of bits will create a byte by adding 0 to the beginning
# args: strings of bits
# return: string of byte
    bits = bin(bit).split('b')[1]
    if len(bits) < 8:
        bits =  '0' * (8 - len(bits)) + bits
    return(bits)

def reText(infile):
# reText function
# given the infile will return a binary for string
# args: infile
# return: binary text
    binText = ''
    for i in range (len(infile)):
        byte = infile[i]
        byte = reByte(int(byte))
        binText += byte
    return(binText)

def decompress(inverse_model,text):
# decompress function
# given compressed text in binary form, and a model, will return plaintext
# args: binary text, model
# return: plain text
    plaintext = ''
    lowerlim = 0
    minCodeLen = min(len(l) for l in inverse_model.keys()) #get possible binary code lengths
    maxCodeLen = max(len(l) for l in inverse_model.keys()) #to make iterations more efficient
    while (len(text)!=lowerlim):
        for n in range (minCodeLen,maxCodeLen+1):
            code = text[lowerlim:lowerlim + n]
            if code in inverse_model:
                plaintext += inverse_model[code]
                lowerlim += n
                break
    return(plaintext)
 

#==============================================================================
if __name__ == '__main__':
    #load file and model
    start_time = time.time()
    file_obj,model_obj = arguments()
    infile = pickle.load(open(file_obj,"rb")) #infile array of bits
    model = pickle.load(open(model_obj,"rb"))
    
    binText = reText(infile) #recreate the binary form string
    #remove the pseudo-eof character from the text, and then remove it from the model
    eof = model['eof']
    binText = binText[:-len(eof)]
    model.pop('eof')

    inverseModel = {v: k for k, v in model.items()} #create an inverse dictionary of {code:symbol}
    decompressedText = decompress(inverseModel, binText) #decompress text

    #write to file 
    f= open(file_obj.split('.')[0] + "-decompressed.txt","w+")
    f.write(decompressedText)
    f.close
    elapsed_time = time.time() - start_time
    print('decompression time: {0:.3f} sec'.format(elapsed_time))