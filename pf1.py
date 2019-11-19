#!/usr/bin/python
import logging
import sys
from subprocess import call
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pf1')

#Comprobacion de parametros
if len(sys.argv)<2:
    order = "Order Empty"
    logger.info(order)
    sys.exit(1)
else: 
    order=sys.argv[1]

#Cada script

if (order != "crear" and order != "destruir" and order != "parar" and order != "arrancar"):
    logger.error("Orden incorrecta")
    sys.exit(1)


if order == "crear":
    #Comprobacion de parametros
    if len(sys.argv)<3:
        option = 2
        logger.info("Option Empty: Using 2 as value")   
    else: 
        try:
            option = int(sys.argv[2])
        except ValueError, e:
            logger.error("Unable to parse option as an integer")
            sys.exit(1)

    #Solo 5 maquinas
    if option < 6:
        logger.debug("Numero de maquinas: " +str(option))
    else: 
        option= 5
        logger.info("Cant create more than 5 machines")
    logger.info("Creando Ficheros")
    #Guardamos numero de maquinas 
    f= open("pf1.cfg","w+")
    f.write("num_serv="+str(option))
    f.close() 

    #Bucle para cada maquina
    for x in range(option):
        y = x+1
        logger.info("Creando Maquina"+str(y))
        call(["qemu-img", "create", "-f", "qcow","-b", "cdps-vm-base-p3.qcow2","s"+str(y)+".qcow2"])
    #Crear balanceador
    logger.info("Creando Balanceador")
    call(["qemu-img", "create", "-f", "qcow","-b", "cdps-vm-base-p3.qcow2","lb.qcow2"])
    #Crear C1
    logger.info("Creando C1")
    call(["qemu-img", "create", "-f", "qcow","-b", "cdps-vm-base-p3.qcow2","c1.qcow2"])

else:
    #Recuperamos el numero de maquinas
    f=open("pf1.cfg", "r")
    for line in f:
        option = line.split("=")[1]
        logger.debug("Numero de maquinas"+option)
        option = int(option)
    #Ejecutamos la nueva orden
    if order == "arrancar":
        #Leer option antes
        logger.info("Arrancando")
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Arrancando maquina "+machine)
            call(["sudo","virsh","define",machine+".xml"])
            call(["sudo","virsh","start",machine])

    elif order == "parar":
        #Leer option antes
        logger.info("Parando")
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Parando maquina "+machine)
            call(["sudo","virsh","shutdown",machine])

    elif order == "destruir":
        #Leer option antes
        logger.info("Borrando Ficheros")
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Borrando maquina "+machine)
            call(["sudo","virsh","destroy",machine])
            call(["sudo","rm","s"+str(y)+".qcow2"])
        logger.info("Borrando c1")    
        call(["sudo","rm","c1.qcow2"])
        logger.info("Borrando lb")    
        call(["sudo","rm","lb.qcow2"])       





