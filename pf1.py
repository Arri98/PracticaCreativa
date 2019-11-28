#!/usr/bin/python
import logging
import sys
from subprocess import *
import os
from lxml import etree


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
		maquina="s"+str(y)
		logger.info("Creando Maquina"+maquina)
		call(["qemu-img", "create", "-f", "qcow2","-b", "cdps-vm-base-pf1.qcow2",maquina+".qcow2"])
		call(["cp","plantilla-vm-pf1.xml",maquina+".xml"])
		#modificar ficheros de la maquina:
		s = etree.parse('s'+str(y)+'.xml')
		root= s.getroot()
		name = root.find("name")
		name.text = 's'+str(y)
		x=root.find("./devices/disk/source")		
		x.set("file", "/mnt/tmp/Pcreativa/s"+str(y)+".qcow2")
		w=root.find("./devices/interface/source")
		w.set("bridge", "LAN2")
		s.write('s'+str(y)+'.xml')
		#Crear y cambiar los ficheros
		f= open("interfaces","w+")
		f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.2.1"+y+" \n   netmask 255.255.255.0 \n   gateway 10.0.2.1\n   dns-nameservers 192.168.122.1\n")
		f.close()
		call(["sudo","virsh","define",machine+".xml"])
		call(["sudo","virt-copy-in","-a",maquina+".qcow2","interfaces","/etc/network"])
		
	#Crear balanceador
	logger.info("Creando Balanceador")
	call(["qemu-img", "create", "-f", "qcow2","-b", "cdps-vm-base-pf1.qcow2","lb.qcow2"])
	call(["cp","plantilla-vm-pf1.xml","lb.xml"])
	#modificar ficheros lb:
	f= open("interfaces","w+")
	f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.1.1.1 \n   netmask 255.255.255.0 \n   gateway 10.0.1.1\n   dns-nameservers 192.168.122.1\nauto eth1  \niface eth1 inet static \n   address 10.0.1.2.1 \n   netmask 255.255.255.0 \n   gateway 10.0.2.1\n   dns-nameservers 192.168.122.1\n")
	f.close()
	lb = etree.parse('lb.xml')
	root= lb.getroot()
	name = root.find("name")
	name.text = 'lb'
	x=root.find("./devices/disk/source")
	x.set("file", "/mnt/tmp/Pcreativa/lb.qcow2")
	w=root.find("./devices/interface/source")
	w.set("bridge", "LAN1")
	u=root.find(".devices")
	i=etree.Element("interface")
	i.attrib['type']= 'bridge'
	u.append(i)
	h=root.findall("./devices/interface")
	x=1
	for u  in h:
		jj=etree.Element("model")
		jj.attrib['type'] = 'virtio'
		ja= etree.Element("source")
		ja.attrib["bridge"]="LAN"+str(x)
		x=x+1
		u.append(jj)
		u.append(ja)
	lb.write('lb.xml')
	call(["sudo","virsh","define","lb.xml"])
	call(["sudo","virt-copy-in","-a","lb.qcow2","interfaces","/etc/network"])

	#Crear C1
	logger.info("Creando C1")
	call(["qemu-img", "create", "-f", "qcow2","-b", "cdps-vm-base-pf1.qcow2","c1.qcow2"])
	call(["cp","plantilla-vm-pf1.xml","c1.xml"])
	f= open("interfaces","w+")
	f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.1.3"+y+" \n   netmask 255.255.255.0 \n   gateway 10.0.1.1\n   dns-nameservers 192.168.122.1\n")
	f.close()
	f= open("interfaces","w+")
	f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.1.1.1 \n   netmask 255.255.255.0 \n   gateway 10.0.1.1\n   dns-nameservers 192.168.122.1\nauto eth1  \niface eth1 inet static \n   address 10.0.1.2.1 \n   netmask 255.255.255.0 \n   gateway 10.0.2.1\n   dns-nameservers 192.168.122.1\n")
	f.close()
	#modificar ficheros c1:
	c1 = etree.parse('c1.xml')
	root= c1.getroot()
	name = root.find("name")
	name.text = 'c1'
	x=root.find("./devices/disk/source")
	x.set("file", "/mnt/tmp/Pcreativa/c1.qcow2")
	w=root.find("./devices/interface/source")
	w.set("bridge", "LAN1")
	c1.write('c1.xml')
	call(["sudo","virsh","define","c1.xml"])
	call(["sudo","virt-copy-in","-a c1.qcow2","hostname","/etc"])
	call(["sudo","virt-copy-in","-a","c1.qcow2","interfaces","/etc/network"])
	

	#Crear bridges
    logger.info("Creando Brideges")
	call(["sudo","brctl","addbr","LAN1"])
	call(["sudo","brctl","addbr","LAN2"])
	call(["sudo","ifconfig","LAN1","up"])
	call(["sudo","ifconfig","LAN2","up"])

else:
    #Recuperamos el numero de maquinas
    f=open("pf1.cfg", "r")
    for line in f:
        option = line.split("=")[1]
        logger.debug("Numero de maquinas"+option)
        option = int(option)
    
    #Ejecutamos la nueva orden
    if order == "arrancar":
        logger.info("Arrancando")
        #call(["HOME=/mnt/tmp", "sudo","virt-manager"])
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Arrancando maquina "+machine)
            call(["sudo","virsh","start",machine])
            Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", machine, "-e","sudo virsh console "+machine])
        logger.info("Arrancando C1")
        call(["sudo","virsh","start","c1"])
        Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "c1", "-e","sudo virsh console c1"])

        logger.info("Arrancando Lb")
        call(["sudo","virsh","start","lb"])
        Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "lb", "-e","sudo virsh console lb"])
		call(["sudo","virt-edit","-a","lb.qcow2","/etc/sysctl.conf", "\", "-e", "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/"])

    
    elif order == "parar":
        logger.info("Parando")
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Parando maquina "+machine)
            call(["sudo","virsh","shutdown",machine])
        logger.info("Parando maquina lb")    
        call(["sudo","virsh","shutdown","c1"])
        logger.info("Parando maquina c1")   
        call(["sudo","virsh","shutdown","lb"])

    elif order == "destruir":
        logger.info("Borrando Ficheros")
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Borrando maquina "+machine)
	    call(["sudo","virsh","destroy",machine])
            call(["sudo","virsh","undefine",machine])
            call(["rm","-f","s"+str(y)+".qcow2"])
            call(["rm","-f","s"+str(y)+".xml"])
            
        logger.info("Borrando c1")
		call(["sudo","virsh","destroy","c1"])
        call(["sudo","virsh","undefine","c1"])    
        call(["rm","-f","c1.qcow2"])
        call(["rm","-f","c1.xml"])   
        logger.info("Borrando lb")    
		call(["sudo","virsh","destroy","lb"])
        call(["sudo","virsh","undefine","lb"])    
        call(["rm","-f","lb.xml"])      
        call(["rm","-f","lb.qcow2"])   
        logger.info("Borrando plantilla de configuracion") 
        call(["rm","-f","pf1.cfg"])   
        logger.info("Borrando hostname e interfaces") 
		call(["rm","-f","hostname"])   
		call(["rm","-f","interfaces"])   


#copia en remoto maquinas virtuales
#root = scp root@compute1:/root/nombrefichero.pcapng.
