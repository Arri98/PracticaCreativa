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

if (order != "crear" and order != "destruir" and order != "parar" and order != "arrancar" and order != "pararsolo" and order !="arrancarsolo" and order !="monitorizar"):
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

	call(["mkdir","-p","/mnt/tmp/Pcreativa"])
	#Guardamos numero de maquinas 
	f= open("/mnt/tmp/Pcreativa/pf1.cfg","w+")
	f.write("num_serv="+str(option))
	f.close() 
	#Copiamos plantilla
	call(["cp","cdps-vm-base-pf1.qcow2","/mnt/tmp/Pcreativa/base.qcow2"])
	#Crear bridges
	logger.info("Creando Bridges")
	call(["sudo","brctl","addbr","LAN1"])
	call(["sudo","brctl","addbr","LAN2"])
	call(["sudo","ifconfig","LAN1","up"])
	call(["sudo","ifconfig","LAN2","up"])


	#Bucle para cada maquina
	for x in range(option):
		y = x+1
		maquina="s"+str(y)
		logger.info("Creando Maquina"+maquina)
		call(["qemu-img", "create", "-f", "qcow2","-b", "/mnt/tmp/Pcreativa/base.qcow2","/mnt/tmp/Pcreativa/"+maquina+".qcow2"])
		call(["cp","plantilla-vm-pf1.xml","/mnt/tmp/Pcreativa/"+maquina+".xml"])	
		#modificar ficheros de la maquina:
		f= open("/mnt/tmp/Pcreativa/hostname","w+")
		f.write("127.0.1."+str(y)+" "+maquina)
		f.close()
		s = etree.parse('/mnt/tmp/Pcreativa/s'+str(y)+'.xml')
		root= s.getroot()
		name = root.find("name")
		name.text = 's'+str(y)
		x=root.find("./devices/disk/source")		
		x.set("file", "/mnt/tmp/Pcreativa/s"+str(y)+".qcow2")
		w=root.find("./devices/interface/source")
		w.set("bridge", "LAN2")
		s.write('/mnt/tmp/Pcreativa/s'+str(y)+'.xml')
		#Crear y cambiar los ficheros
		f= open("/mnt/tmp/Pcreativa/interfaces","w+")
		f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.2.1"+str(y)+" \n   netmask 255.255.255.0 \n   gateway 10.0.2.1\n   dns-nameservers 192.168.122.1\n")
		f.close()
		call(["sudo","virsh","define","/mnt/tmp/Pcreativa/"+maquina+".xml"])
		call(["sudo","virt-copy-in","-a","/mnt/tmp/Pcreativa/"+maquina+".qcow2","/mnt/tmp/Pcreativa/interfaces","/etc/network"])
		call(["sudo","virt-copy-in","-a" ,"/mnt/tmp/Pcreativa/"+maquina+".qcow2","/mnt/tmp/Pcreativa/hostname","/etc"])
		
	#Crear balanceador
	logger.info("Creando Balanceador")
	call(["qemu-img", "create", "-f", "qcow2","-b", "/mnt/tmp/Pcreativa/base.qcow2","/mnt/tmp/Pcreativa/lb.qcow2"])
	call(["cp","plantilla-vm-pf1.xml","/mnt/tmp/Pcreativa/lb.xml"])
	#modificar ficheros lb:
	f= open("/mnt/tmp/Pcreativa/interfaces","w+")
	f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.1.1 \n   netmask 255.255.255.0 \n   gateway 10.0.1.1\n   dns-nameservers 192.168.122.1\nauto eth1  \niface eth1 inet static \n   address 10.0.2.1 \n   netmask 255.255.255.0 \n   gateway 10.0.2.1\n   dns-nameservers 192.168.122.1\n")
	f.close()
	f= open("/mnt/tmp/Pcreativa/hostname","w+")
	f.write("127.0.1.6 lb")
	f.close()
	lb = etree.parse('/mnt/tmp/Pcreativa/lb.xml')
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
	lb.write('/mnt/tmp/Pcreativa/lb.xml')
	call(["sudo","virsh","define","lb.xml"])
	call(["sudo","virt-copy-in","-a","/mnt/tmp/Pcreativa/lb.qcow2","/mnt/tmp/Pcreativa/interfaces","/etc/network"])
	call(["sudo","virt-copy-in","-a", "/mnt/tmp/Pcreativa/lb.qcow2","/mnt/tmp/Pcreativa/hostname","/etc"])
	call(["sudo","virt-edit","-a","/mnt/tmp/Pcreativa/lb.qcow2","/etc/sysctl.conf","-e", "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/"])

	#Crear C1
	logger.info("Creando C1")
	call(["qemu-img", "create", "-f", "qcow2","-b", "/mnt/tmp/Pcreativa/base.qcow2","/mnt/tmp/Pcreativa/c1.qcow2"])
	call(["cp","plantilla-vm-pf1.xml","/mnt/tmp/Pcreativa/c1.xml"])
	f= open("/mnt/tmp/Pcreativa/hostname","w+")
	f.write("127.0.1.6 c1")
	f.close()
	f= open("/mnt/tmp/Pcreativa/interfaces","w+")
	f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.1.2 \n   netmask 255.255.255.0 \n   gateway 10.0.1.1\n   dns-nameservers 192.168.122.1")
	f.close()
	#modificar ficheros c1:
	c1 = etree.parse('/mnt/tmp/Pcreativa/c1.xml')
	root= c1.getroot()
	name = root.find("name")
	name.text = 'c1'
	x=root.find("./devices/disk/source")
	x.set("file", "/mnt/tmp/Pcreativa/c1.qcow2")
	w=root.find("./devices/interface/source")
	w.set("bridge", "LAN1")
	c1.write('/mnt/tmp/Pcreativa/c1.xml')
	call(["sudo","virsh","define","c1.xml"])
	call(["sudo","virt-copy-in","-a", "/mnt/tmp/Pcreativa/c1.qcow2","/mnt/tmp/Pcreativa/hostname","/etc"])
	call(["sudo","virt-copy-in","-a","/mnt/tmp/Pcreativa/c1.qcow2","/mnt/tmp/Pcreativa/interfaces","/etc/network"])

	#Crear HOST
	logger.info("Creando Host")
	call(["qemu-img", "create", "-f", "qcow2","-b", "/mnt/tmp/Pcreativa/base.qcow2","/mnt/tmp/Pcreativa/host.qcow2"])
	call(["cp","plantilla-vm-pf1.xml","/mnt/tmp/Pcreativa/host.xml"])
	f= open("/mnt/tmp/Pcreativa/hostname","w+")
	f.write("127.0.1.7 host")
	f.close()
	f= open("/mnt/tmp/Pcreativa/interfaces","w+")
	f.write("auto lo\niface lo inet loopback \nauto eth0  \niface eth0 inet static \n   address 10.0.1.3 \n   netmask 255.255.255.0 \n   gateway 10.0.1.1\n   dns-nameservers 192.168.122.1")
	f.close()
	#modificar ficheros HOST:
	host = etree.parse('/mnt/tmp/Pcreativa/host.xml')
	root= host.getroot()
	name = root.find("name")
	name.text = 'host'
	x=root.find("./devices/disk/source")
	x.set("file", "/mnt/tmp/Pcreativa/host.qcow2")
	w=root.find("./devices/interface/source")
	w.set("bridge", "LAN1")
	host.write('/mnt/tmp/Pcreativa/host.xml')
	call(["sudo","virsh","define","host.xml"])
	call(["sudo","virt-copy-in","-a", "/mnt/tmp/Pcreativa/host.qcow2","/mnt/tmp/Pcreativa/hostname","/etc"])
	call(["sudo","virt-copy-in","-a","/mnt/tmp/Pcreativa/host.qcow2","/mnt/tmp/Pcreativa/interfaces","/etc/network"])


elif order == "pararsolo":
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
	
	machine="s"+str(option)
        logger.info("Parando maquina "+machine)
        call(["sudo","virsh","shutdown",machine])

elif order == "arrancarsolo":
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
	
	machine="s"+str(option)
        logger.info("Arrancando maquina "+machine)
        call(["sudo","virsh","start",machine])
        Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", machine, "-e","sudo virsh console "+machine])


else:
    #Recuperamos el numero de maquinas
    try:	
    	f=open("/mnt/tmp/Pcreativa/pf1.cfg", "r")
    except (OSError, IOError) as e:
	logger.error("Pf1.cfg not found. Most likely machines where not created")
 	sys.exit(1)
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
	logger.info("Arrancando Host")
        call(["sudo","virsh","start","host"])
        Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", 	"host", "-e","sudo virsh console host"])

    
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
	logger.info("Parando maquina host")   
        call(["sudo","virsh","shutdown","host"])


    elif order == "destruir":
        logger.info("Borrando Ficheros")
        for x in range(option):
            y=x+1;
            machine="s"+str(y)
            logger.info("Borrando maquina "+machine)
	    call(["sudo","virsh","destroy",machine])
            call(["sudo","virsh","undefine",machine])
            call(["rm","-f","/mnt/tmp/Pcreativa/s"+str(y)+".qcow2"])
            call(["rm","-f","/mnt/tmp/Pcreativa/s"+str(y)+".xml"])
            
        logger.info("Borrando c1")
	call(["sudo","virsh","destroy","c1"])
        call(["sudo","virsh","undefine","c1"])    
        call(["rm","-f","/mnt/tmp/Pcreativa/c1.qcow2"])
        call(["rm","-f","/mnt/tmp/Pcreativa/c1.xml"])   
	logger.info("Borrando host")
	call(["sudo","virsh","destroy","host"])
        call(["sudo","virsh","undefine","host"])    
        call(["rm","-f","/mnt/tmp/Pcreativa/host.qcow2"])
        call(["rm","-f","/mnt/tmp/Pcreativa/host.xml"])   
        logger.info("Borrando lb")    
	call(["sudo","virsh","destroy","lb"])
        call(["sudo","virsh","undefine","lb"])    
        call(["rm","-f","/mnt/tmp/Pcreativa/lb.xml"])      
        call(["rm","-f","/mnt/tmp/Pcreativa/lb.qcow2"])   
        logger.info("Borrando plantilla de configuracion") 
        call(["rm","-f","/mnt/tmp/Pcreativa/pf1.cfg"])   
        logger.info("Borrando hostname e interfaces") 
	call(["rm","-f","/mnt/tmp/Pcreativa/hostname"])   
	call(["rm","-f","/mnt/tmp/Pcreativa/interfaces"])   
	logger.info("Borrando bridges")
	call(["sudo","ifconfig","LAN1","down"])
	call(["sudo","ifconfig","LAN2","down"])
	call(["sudo","brctl","delbr","LAN1"])
	call(["sudo","brctl","delbr","LAN2"])
	call(["rm","--force","/mnt/tmp/Pcreativa/base.qcow2"])
	
    elif order == "monitorizar":
	Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "Estado","-e","watch -n 5 sudo virsh list --all"])
	Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "Monitor lb","-e","watch -n 5 sudo virsh cpu-stats host"])
	Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "Monitor c1","-e","watch -n 5 sudo virsh cpu-stats c1"])
	Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "Monitor host","-e","watch -n 5 sudo virsh cpu-stats host"])
	for x in range(option):
            y=x+1;
            machine="s"+str(y)
	    Popen(["xterm","-rv","-sb","-rightbar","-fa","monospace","-fs", "10", "-title", "Monitor "+machine,"-e","watch -n 5 sudo virsh cpu-stats "+machine])


