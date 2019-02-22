# Assembly Image Encoder FredHappyface
"""
Encodes a custom set of assembly style instructions into an image. Syntax has
been inspired by the Little Man Computer (LMC) created by Stuart Madnick in
1965. An online model of this can be found at https://peterhigginson.co.uk/LMC/
and the idea of executing a program from and image from
https://github.com/roo2319/Scritch. Note that this is not the best model of
assembly as it has a modest instruction set and lacks a stack. The main purpose
of this program is for those who find Steganography interesting to have a play
around.

"""

# Define application constants
HEADER_SIZE = 1024
FOOTER_SIZE = 1024
MAX_CODE_LEN = 1024

COMMAND0 = -128 #1000 0000
REGISTER0 = COMMAND0 + 16 #1001 0000
MAX_INT = 127 #0111 1111
MIN_INT = REGISTER0 + 16 #1010 0000

'''
See below for some basic documentation on the commands and registers. It is
recomended to read the README file for more information:

Commands

ADD : COMMAND0 : ADD out arg0 arg1 : out = arg0 + arg1
SUB : COMMAND0 + 1 : SUB out arg0 arg1 : out = arg0 - arg1
MULT : COMMAND0 + 2 : MULT out arg0 arg1 : out = arg0 * arg1
DIV : COMMAND0 + 3 : DIV out arg0 arg1 : out = arg0 / arg1 (int division)
INC : COMMAND0 + 4 : INC reg : reg ++
DECR : COMMAND0 + 5 : DECR reg : reg --
MOV : COMMAND0 + 6 : MOV out arg0 : out = arg0
OUT : COMMAND0 + 7 : OUT arg0 : print(arg0)
IN : COMMAND0 + 8 : IN reg : input(reg)
END : COMMAND0 + 9 : END : Terminate the program
BRA : COMMAND0 + 10 : BRA token : GOTO token
BRP : COMMAND0 + 11 : BRP token arg0 : GOTO token if arg0 > 0
BRZ : COMMAND0 + 12 : BRP token arg0 : GOTO token if arg0 = 0


Registers

r0 : REGISTER0
r1 : REGISTER0 + 1
r2 : REGISTER0 + 2
r3 : REGISTER0 + 3
r4 : REGISTER0 + 4
r5 : REGISTER0 + 5
r6 : REGISTER0 + 6
r7 : REGISTER0 + 7
'''


# Read text file and return content as a list of tokens  
def readFileContent(fileName):
    tokens = []
    file = open(fileName, "r")
    # Read line by line
    for line in file:
        # Remove start whitespace and lines starting with REM (remarks)
        if( line.lstrip()[:3] != "REM"):
            # Split remaining lines into tokens (add these to tokens list)
            tokens.extend(line.split())
    # Return tokens 
    return tokens

# Read image file in 
def readImg(imageName):
    image = open(imageName, "rb")
    return image

# Write image file out 
def writeImg(imageName):
    image = open(imageName, "wb")
    return image

# Get the size of the image in bytes to prevent overwriting footer
def getSize(imageName):
    import os
    return os.path.getsize(imageName)



# Write the assembly code to the image 
def writeEncodedImg(inputImgName, outputImgName, tokens):
    # Take the input image and get its size 
    inputImg = readImg(inputImgName)
    inputImgSize = getSize(inputImgName)
    
    # Create/ overwrite the output image 
    outputImg = writeImg(outputImgName)
    
    # Copy the header across 
    outputImg.write(inputImg.read(HEADER_SIZE))

    # Get the number of tokens
    numberTokens = len(tokens)

    # For the number of tokens
    for index in range(numberTokens):
        tokenAsByte = generateByteFromToken(tokens[index])
        outputImg.write(tokenAsByte)
          
    # Copy the footer and the remainder of the image across 
    outputImg.write(inputImg.read(FOOTER_SIZE + (inputImgSize - numberTokens)))
    return 0

def generateByteFromToken(token):
    # If any reg or command is used, needs to be an int
    integer = 0
    instructions = ["ADD", "SUB", "MULT", "DIV", "INC", "DECR", "MOV", "OUT", "IN",
                    "END", "BRA", "BRP", "BRZ"]
    registers = ["r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7"]
    isReserved = False

    # Convert an instruction to its reserved int 
    for instruction in range (len(instructions)):
        if token == instructions[instruction]:
            integer = COMMAND0 + instruction
            isReserved = True 

    # Convert a register to its reserved int
    for register in range (len(registers)):
        if token == registers[register]:
            integer = REGISTER0 + register
            isReserved = True 

    # Try and convert to an int if the token is not an instruction or register
    if not isReserved:
        try:
            integer = int(token)
        except:
            print("Error converting token to int: " + token)

    # Convert to a byte and return to the calling program 
    byte = integer.to_bytes(1, byteorder='big', signed=True)           
    return byte


def executeFromImage(inputImgName):                    
    # Take the input image and get its size 
    inputImg = readImg(inputImgName)
    inputImgSize = getSize(inputImgName)
    inputImg.read(HEADER_SIZE)

    # Define variables
    end = False
    registers = [0,0,0,0,0,0,0,0]
    tokens = []
    tokenNumber = 0

    # Read the image and add each token to the tokens list
    for token in range(MAX_CODE_LEN):
        tokens.append(int.from_bytes(inputImg.read(1), byteorder='big',
                                     signed=True))
                    
    while (not end):
        # Get the instruction code 
        instruction = tokens[tokenNumber]
        tokenNumber += 1

        # ADD, SUB, MULT, DIV
        if (instruction >= COMMAND0 and (instruction < COMMAND0 + 4)): 
            outReg = tokens[tokenNumber] - REGISTER0
            tokenNumber += 1
            arg0 = tokens[tokenNumber]
            tokenNumber += 1
            # arg0 may be reg
            if arg0 < MIN_INT:
                arg0 = registers[arg0 - REGISTER0]
            arg1 = tokens[tokenNumber]
            tokenNumber += 1
            # arg1 may be reg
            if arg1 < MIN_INT:
                arg1 = registers[arg1 - REGISTER0]
            # ADD
            if (instruction == COMMAND0):
                registers[outReg] = arg0 + arg1
            # SUB
            if (instruction == COMMAND0 + 1):
                registers[outReg] = arg0 - arg1
            # MULT
            if (instruction == COMMAND0 + 2):
                registers[outReg] = arg0 * arg1
            # DIV
            if (instruction == COMMAND0 + 3):
                registers[outReg] = int(arg0 / arg1)

        # INC
        if (instruction == COMMAND0 + 4):
            reg = tokens[tokenNumber] - REGISTER0
            tokenNumber += 1
            registers[reg] += 1

        # DECR
        if (instruction == COMMAND0 + 5):
            reg = tokens[tokenNumber] - REGISTER0
            tokenNumber += 1
            registers[reg] -= 1

        # MOV
        if (instruction == COMMAND0 + 6):
            reg = tokens[tokenNumber] - REGISTER0
            tokenNumber += 1
            arg0 = tokens[tokenNumber]
            tokenNumber += 1
            # arg0 may be reg
            if arg0 < MIN_INT:
                arg0 = registers[arg0 - REGISTER0]
            registers[reg] = arg0

        # OUT
        if (instruction == COMMAND0 + 7):
            reg = tokens[tokenNumber] - REGISTER0
            tokenNumber += 1
            print(registers[reg])

        # IN
        if (instruction == COMMAND0 + 8):
            reg = tokens[tokenNumber] - REGISTER0
            tokenNumber += 1
            try:
                registers[reg] = int(input(">"))
            except:
                print("Input must be an integer")
                return 1

        # END
        if (instruction == COMMAND0 + 9):
            # Set the end flag to True and terminate 
            end = True

        # BRA
        if (instruction == COMMAND0 + 10):
            tokenNumber = tokens[tokenNumber]

        # BRP, BRZ
        if ((instruction == COMMAND0 + 11) or (instruction == COMMAND0 + 12)):
            newTokenNumber = tokens[tokenNumber]
            tokenNumber += 1
            arg0 = tokens[tokenNumber]
            tokenNumber += 1
            # arg0 may be reg
            if arg0 < MIN_INT:
                arg0 = registers[arg0 - REGISTER0]
            # BRP
            if (instruction == COMMAND0 + 11) and arg0 > 0:
                tokenNumber = newTokenNumber

            # BRZ
            if (instruction == COMMAND0 + 12) and arg0 == 0:
                tokenNumber = newTokenNumber
                
    return 0

def cli():
    print("Code to Image, Execute Image, Code to Image and Execute or Quit? " +
          "(C, e, a, q)" )
    choice = input(">")[0].lower()

    # Quit application 
    if choice == "q":
        return True 

    # All functions require the path to an image 
    print("Type in the path to the input image")
    inputImgName = input(">")

    # Code to Image 
    if choice != "e":
        print("Type in the path to the code file")
        codeFile = input(">")
        print("Type in the path to the output image")
        outputImgName = input(">")

    # Run the required function for each choice
    # EXECUTE IMAGE 
    if choice == "e":
        executeFromImage(inputImgName)
    # CODE TO IMAGE AND EXECUTE
    elif choice == "a":
        tokens = readFileContent(codeFile)
        writeEncodedImg(inputImgName, outputImgName, tokens)
        executeFromImage(outputImgName)
    # DEFAULT = CODE TO IMAGE  
    else:
        tokens = readFileContent(codeFile)
        writeEncodedImg(inputImgName, outputImgName, tokens)


# Run the CLI while the user has not finished 
finished = False 
while not finished:
    finished = cli()


