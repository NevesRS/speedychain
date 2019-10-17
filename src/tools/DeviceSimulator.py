#import __builtin__

import sys
import os
import time
import socket
import random
import pickle

import Pyro4

import json
import requests
import traceback

from Crypto.PublicKey import RSA

# SpeedCHAIN modules
import Logger as Logger
import CryptoFunctions

logger = Logger.logging.getLogger("speedychain")
deviceName = ""
consensus = ""

fname = socket.gethostname()

server = "localhost"
serverAESEncKey = ""
serverAESKey = ""
privateKey = "-----BEGIN PRIVATE KEY-----\nMIIBVAIBADANBgkqhkiG9w0BAQEFAASCAT4wggE6AgEAAkEA7P6DKm54NjLE7ajy\nTks298FEJeHJNxGT+7DjbTQgJdZKjQ6X9lYW8ittiMnvds6qDL95eYFgZCvO22YT\nd1vU1QIDAQABAkBEzTajEOMRSPfmzw9ZL3jLwG3aWYwi0pWVkirUPze+A8MTp1Gj\njaGgR3sPinZ3EqtiTA+PveMQqBsCv0rKA8NZAiEA/swxaCp2TnJ4zDHyUTipvJH2\nqe+KTPBHMvOAX5zLNNcCIQDuHM/gISL2hF2FZHBBMT0kGFOCcWBW1FMbsUqtWcpi\nMwIhAM5s0a5JkHV3qkQMRvvkgydBvevpJEu28ofl3OAZYEwbAiBJHKmrfSE6Jlx8\n5+Eb8119psaFiAB3yMwX9bEjVy2wRwIgd5X3n2wD8tQXcq1T6S9nr1U1dmTz7407\n1UbKzu4J8GQ=\n-----END PRIVATE KEY-----\n"
publicKey = "-----BEGIN PUBLIC KEY-----\nMFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAOz+gypueDYyxO2o8k5LNvfBRCXhyTcR\nk/uw4200ICXWSo0Ol/ZWFvIrbYjJ73bOqgy/eXmBYGQrzttmE3db1NUCAwEAAQ==\n-----END PUBLIC KEY-----\n"

# input = getattr(__builtin__, 'raw_input', input)

def getMyIP():
     """ Return the IP from the gateway
     @return str 
     """
     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     s.connect(("8.8.8.8", 80))
     myIP = s.getsockname()[0]
     s.close()
     return myIP

def generateRSAKeyPair():
    """ Creates a pair of RSA key, one public and one private.\n
        @return pub - public key\n
        @return prv - private key
    """
    #randValue = Random.random.randrange(24)
    private = RSA.generate(1024)

    #private = RSA.generate(1024,randValue)
    pubKey = private.publickey()
    prv = private.exportKey()
    pub = pubKey.exportKey()
    return pub, prv

def setServer():
    """ Ask for the user to input the server URI and put it in the global var 'server' """
    global server
    #server = raw_input('Gateway IP:')
    uri = input("Enter the uri of the gateway: ").strip()
    server = Pyro4.Proxy(uri)

def addBlockOnChain():
    """ Take the value of 'publicKey' var, and add it to the chain as a block"""
    global serverAESEncKey
    # print("###addBlockonChain in devicesimulator, publicKey")
    # print(publicKey)
    serverAESEncKey = server.addBlock(publicKey)
    # print("###addBlockonChain in devicesimulator, serverAESEncKey")
    # print(serverAESEncKey)
    # while len(serverAESEncKey) < 10:
    #    serverAESEncKey = server.addBlock(publicKey)
    decryptAESKey(serverAESEncKey)
    # print("###after decrypt aes")

def sendDataTest():
    """ Send fake data to test the system """
    pub, priv = generateRSAKeyPair()
    temperature = readSensorTemperature()
    t = ((time.time() * 1000) * 1000)
    timeStr = "{:.0f}".format(t)
    data = timeStr + temperature
    signedData = CryptoFunctions.signInfo(priv, data)
    ver = CryptoFunctions.signVerify(data, signedData, pub)
    logger.debug("Sending data test " + str(ver) + "...")
    # print ("done: "+str(ver))

def sendData():
    """ Read the sensor data, encrypt it and send it as a transaction to be validated by the peers """
    temperature = readSensorTemperature()
    t = ((time.time() * 1000) * 1000)
    timeStr = "{:.0f}".format(t)
    data = timeStr + temperature
    logger.debug("data = "+data)
    signedData = CryptoFunctions.signInfo(privateKey, data)
    toSend = signedData + timeStr + temperature
    logger.debug("ServeAESKEY = " + serverAESKey)
    encobj = CryptoFunctions.encryptAES(toSend, serverAESKey)
    server.addTransaction(publicKey, encobj)

def sendDataSC(stringSC):
    t = ((time.time() * 1000) * 1000)
    timeStr = "{:.0f}".format(t)
    data = timeStr + stringSC
    signedData = CryptoFunctions.signInfo(privateKey, data)
    logger.debug("###Printing Signing Data before sending: "+signedData)
    # print ("###Signature lenght: " + str(len(signedData)))
    toSend = signedData + timeStr + stringSC
    encobj = CryptoFunctions.encryptAES(toSend, serverAESKey)
    server.addTransactionSC(publicKey, encobj)
    # server.addTransaction(toSend)

def decryptAESKey(data):
    """ Receive a encrypted data, decrypt it and put it in the global var 'serverAESKey' """
    global serverAESKey
    serverAESKey = CryptoFunctions.decryptRSA2(privateKey, data)

def readSensorTemperature():
    """ Generates random data like '23 C' """
    temp = str(random.randint(10, 40)) + " C"
    return temp

def addPeer():
    """ Ask for the user to inform a peer URI and add it to the server """
    # if sys.version_info < (3, 0):
    #     input = raw_input
    uri = input("Enter the PEER uri: ").strip()
    server.addPeer(uri, True)

def listBlockHeader():
    """ Log all blocks """
    server.showIoTLedger()

def listTransactions():
    """ Ask for the user to input an index and show all transaction of the block with that index """
    index = input("Which IoT Block do you want to print?")
    server.showBlockLedger(int(index))


def listPeers():
    """ List all peers in the network """
    logger.debug("calling server...")
    server.listPeer()

def newKeyPair():
    """ Generates a new pair of keys and put is on global vars 'privateKey' and 'publicKey' """
    global privateKey
    global publicKey
    publicKey, privateKey = generateRSAKeyPair()
    while len(publicKey) < 10 or len(privateKey) < 10:
        publicKey, privateKey = generateRSAKeyPair()

def brutePairAuth(retry):
    """ Add a block on the chain with brute force until it's add"""
    isOk = True
    while isOk:
        try:
            newKeyPair()
            addBlockOnChain()
            isOk = False
        except KeyboardInterrupt:
            sys.exit()
        except:
            logger.error("failed to execute:"+str(retry))
            isOk = True

def bruteSend(retry):
    """ Try to send a random data with brute force until it's sended """
    isOk = True
    while isOk:
        try:
            sendData()
            isOk = False
        except KeyboardInterrupt:
            sys.exit()
        except:
            logger.error("failed to execute:"+str(retry))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error("*** print_exception:\n" + str(traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)))
            #global serverAESKey
            # print("the size of the serverAESKey is: "+str(len(serverAESKey)))
            return  # addBlockConsensusCandiate

def defineAutomaNumbers():
    """ Ask for the user to input how many blocks and transaction he wants and calls the function automa()"""
    blocks = int(input('How many Blocks:'))
    trans = int(input('How many Transactions:'))
    automa(blocks, trans)

def automa(blocks, trans):
    """ Adds a specifc number of blocks and transaction to the chain\n
        @param blocks - int number of blocks\n
        @param trans - int number of transactions
    """
    for blk in range(0, blocks):
        logger.info("Adding block #" + str(blk) + "...")
        newKeyPair()
        addBlockOnChain()
        # brutePairAuth(blk)
        for tr in range(0, trans):
            logger.info("Sending transaction #" + str(tr) + "...")
            # sendData()
            while (not (server.isBlockInTheChain(publicKey))):
                continue
                # time.sleep(1)
            bruteSend(tr)

def merkle():
    """ Calculates the hash markle tree of the block """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blk = int(input("Which block you want to create the merkle tree:"))
    server.calcMerkleTree(blk)  # addBlockConsensusCandiate
    # print ("done")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def newElection():
    server.electNewOrchestrator()
    return True
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) ###WHAT???###

def defineInteractiveConsensus():
    receivedConsensus = str(input('Set a consensus (None, PBFT, PoW, dBFT or Witness3) (None is default) : '))
    print("after receiving consensus string: "+receivedConsensus)
    server.setConsensus(receivedConsensus)
    return True

def defineConsensus(receivedConsensus):
    #receivedConsensus = str(input('Set a consensus (None, PBFT, PoW, dBFT or Witness3) (None is default) : '))
    # server will set its consensus and send it to all peers
    server.setConsensus(receivedConsensus)
    # print("Consensus " + receivedConsensus + " was defined")
    return True

def createBlockForSC():
    newKeyPair()
    addBlockOnChain()
    while (not (server.isBlockInTheChain(publicKey))):
        continue
        # time.sleep(1)
    firstTransactionSC = '{ "Tipo" : "", "Data": "", "From": "", "To" : "", "Root" : "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421" }'
    sendDataSC(firstTransactionSC)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def showLastTransactionData():
    blockIndex = int(input('Type the index to show the last transaction data: '))
    lastDataTransactionData = server.showLastTransactionData(blockIndex)
    return lastDataTransactionData

def callEVMInterface():
    # Create a TCP
    # IP socket
    global privateKey
    global publicKey
    # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #
    # # Coleta o data da ultima transacao um json
    # ultimaTrans = showLastTransactionData()
    # ultimaTransJSON = json.loads(ultimaTrans)

    # print("###Please, insert data to call the Smart Contract###")
    callType = str(input("Type (Exec,Criar,Cham): "))
    data = str(input("Data (binary in hexa): "))
    origin = str(input("From account: "))
    dest = str(input("Destination account: "))
    scInfo = callType+data+origin+dest
    signedData = CryptoFunctions.signInfo(privateKey,scInfo)

    scType = pickle.dumps(callType)
    scData = pickle.dumps(data)
    scFrom = pickle.dumps(origin)
    scDest = pickle.dumps(dest)
    scSignedData = pickle.dumps(signedData)
    scPublicKey = pickle.dumps(publicKey)

    logger.debug("###Printing Signing Sc before sending: "+signedData)

    server.callEVM(scType,scData,scFrom,scDest,scSignedData,scPublicKey)
    # transAtual = json.loads(
    #     '{"Tipo":"%s","Data":"%s","From":"%s","To":"%s"}' % (tipo, data, origin, dest))
    #
    # chamada = '{"Tipo":"%s","Data":"%s","From":"%s","To":"%s","Root":"%s"}' % (
    #     transAtual['Tipo'], transAtual['Data'], transAtual['From'], transAtual['To'], ultimaTransJSON['Root'])
    # #chamada =  '{"Tipo":"%s","Data":"%s","From":null,"To":null,"Root":"%s"}' % (transAtual['Tipo'], transAtual['Data'], ultimaTransJSON['Root'])
    # chamadaJSON = json.loads(chamada)
    #
    # # chamada = '{"Tipo":"Exec","Data":"YAFgQFNgAWBA8w==","From":null,"To":null,"Root":null}'  # Comentar
    # # chamadaJSON = json.loads(chamada)  # Comentar
    #
    # try:
    #     # Tamanho maximo do JSON 6 caracteres
    #     s.connect(('localhost', 6666))
    #     tamanhoSmartContract = str(len(chamada))
    #     for i in range(6 - len(tamanhoSmartContract)):
    #         tamanhoSmartContract = '0' + tamanhoSmartContract
    #     # print("Enviando tamanho " + tamanhoSmartContract + "\n")
    #     # Envia o SC
    #     s.send(tamanhoSmartContract)
    #     time.sleep(1)
    #     # print(json.dumps(chamadaJSON))
    #     s.send(chamada)
    #
    #     # Recebe tamanho da resposta
    #     tamanhoResposta = s.recv(6)
    #     # print("Tamanho da resposta: " + tamanhoResposta)
    #     # Recebe resposta
    #     resposta = s.recv(int(tamanhoResposta))
    #     # print(resposta + "\n")
    #
    #     # Decodifica resposta
    #     respostaJSON = json.loads(resposta)
    #     # print(respsotaJSON['Ret'])
    #
    #     if respostaJSON['Erro'] != "":
    #         logger.Exception("Transacao nao inserida")
    #     elif chamadaJSON['Tipo'] == "Exec":
    #         logger.info("Execucao, sem insercao de dados na blockchain")
    #     else:
    #         transacao = '{ "Tipo" : "%s", "Data": "%s", "From": "%s", "To" : "%s", "Root" : "%s" }' % (
    #             chamadaJSON['Tipo'], chamadaJSON['Data'], chamadaJSON['From'], chamadaJSON['To'], respostaJSON['Root'])
    #         logger.info("Transacao sendo inserida: %s \n" % transacao)
    #         sendDataSC(transacao)
    #         # pass
    #
    # finally:
    #     # print("fim\n")
    #     s.close()
    return True


def evmConnector():
    return True


def executeEVM():
    return True


def loadConnection(nameServerIP, nameServerPort, gatewayName):
    global deviceName
    """ Load the URI of the connection  """
    # ----> Adicionado por Arruda
    ns = Pyro4.locateNS(host=nameServerIP, port=nameServerPort)
    gatewayURI = ns.lookup(gatewayName)
    # print(gatewayURI)
    global server
    # fname = socket.gethostname()
    # text_file = open("localhost", "r")
    # uri = text_file.read()
    # print(uri)
    server = Pyro4.Proxy(gatewayURI)
    # text_file.close()
    # os.remove(fname)
    # ---->
    defineConsensus(consensus)
    return gatewayURI

#############################################################################
#############################################################################
######################          Main         ################################
#############################################################################
#############################################################################
def InteractiveMain():
    """ Creates an interactive screen for the user with all option of a device"""
    global server
    options = {
        1: setServer,
        2: addPeer,
        3: addBlockOnChain,
        4: sendData,
        5: listBlockHeader,
        6: listTransactions,
        7: listPeers,
        8: newKeyPair,
        9: defineAutomaNumbers,
        10: merkle,
        11: newElection,
        12: defineInteractiveConsensus,
        13: createBlockForSC,
        14: showLastTransactionData,
        15: callEVMInterface,
        16: evmConnector,
        17: executeEVM
    }

    mode = -1
    while True:
        print("Choose your option [" + str(server) + "]")
        print("#############################################################")
        print("0 - Exit")
        print("1 - Set Server Address[ex:PYRO:chain.server@blablabala:00000]")
        print("2 - Add Peer")
        print(
            "3 - Authentication Request [a)Gw Generate AES Key;b)Enc key with RSA;c)Dec AES Key]")
        print(
            "4 - Produce Data [a)sign data;b)encrypt with AES key;c)Send to Gateway;d)GW update ledger and peers")
        print("5 - List Block Headers from connected Gateway")
        print("6 - List Transactions for a given Block Header")
        print("7 - List PEERS")
        print("8 - Recreate Device KeyPair")
        print("9 - Run a batch operation...")
        print("10 - Create Merkle Tree for a given block")
        print(
            "11 - Elect a new node as Orchestator (used for voting based consensus")
        print("12 - Set a consensus algorithm")
        print("13 - Create a block for Smart Contract")
        print("14 - Show data from last transaction from block Index")
        print("15 - Call Smart Contract")
        # print("16 - EVM connector")
        # print("17 - execute EVM code")
        print("#############################################################")

        try:
            mode = int(input('Input:'))
        except ValueError:
            print ("Not a number")
        if (mode == 0):
            break
        options[mode]()

if __name__ == '__main__':

    # if len(sys.argv[1:]) > 1:
        # ----> Adicionado por Arruda
        # print ("Command Line usage:")
        # print (
        #     "    python deviceSimulator.py <name server IP> <gateway name> <blocks> <transactions>")
        # ---->
        # os.system("clear")
        # print("running automatically")
    if len(sys.argv[1:])<4:
        print("Command line syntax:")
        print("  python DeviceSimulator.py <name server IP> <name server port> <gateway name> <device name>")
    else:
        nameServerIP = sys.argv[1]
        nameServerPort = int(sys.argv[2])
        gatewayName = sys.argv[3]
        deviceName = sys.argv[4]
        logger = Logger.configure(deviceName + ".log")
        logger.info("Running device " + deviceName + " in " + getMyIP())



        if (len(sys.argv) < 6): #when it is not called with number of blocks/transactions and consensus, it is called interactive mode
            consensus = "None"
            gatewayURI = loadConnection(nameServerIP, nameServerPort, gatewayName)

            logger.info("Connected to gateway: " + gatewayURI.asString())
            InteractiveMain()
        else:
            blocks = sys.argv[5]
            transactions = sys.argv[6]
            consensus = sys.argv[7]

            gatewayURI = loadConnection(nameServerIP, nameServerPort, gatewayName)

            logger.info("Connected to gateway: " + gatewayURI.asString())

            logger.info("Processing " + blocks + " blocks and " + transactions + " transactions...")
            automa(int(blocks), int(transactions))

        # else:
        # os.system("clear")
        # loadConnection()
        # main()
