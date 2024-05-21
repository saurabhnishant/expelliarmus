# Expelliarmus

## Paper Citation (Please cite the two papers below):

(1) N. Saurabh, J. Remmers, D. Kimovski, R. Prodan and J. G. Barbosa, "Semantics-Aware Virtual Machine Image 
    Management in IaaS Clouds," 2019 IEEE International Parallel and Distributed Processing Symposium (IPDPS), 
    Rio de Janeiro, Brazil, 2019, pp. 418-427, doi: 10.1109/IPDPS.2019.00052.
	
(2) Nishant Saurabh, Shajulin Benedict, Jorge G. Barbosa, Radu Prodan, Expelliarmus: Semantic-centric virtual 
    machine image management in IaaS Clouds, Journal of Parallel and Distributed Computing, Volume 146, 2020, 
    Pages 107-121, ISSN 0743-7315,https://doi.org/10.1016/j.jpdc.2020.08.001.
	

## Design and Contribution credits:
        1. Nishant Saurabh (PhD Researcher,University of Innsbruck, Alpen-Adria Universitat Klagenfurt, Austria)
        2. Julian Remmers, (MSc., University of Innsbruck, Austria)
        3. Contact: nishant(at)itec.aau.at

## Goal and definition:
	Semantic management of Virtual machine images (VMIs). The current implementation of Expelliarmus is tested on Ubuntu 16.04 LTS, however there is no such arbitrary requirement and can be deployed on any Linux based environment with manual build for libguestfs.

## Checklist
 	1. Expelliarmus Requirements
  	2. Expelliarmus Installation
  	3. Dataset (VMIs) preparation for Expelliarmus
  	4. Experimental workflow of Expelliarmus
	5. Evaluation steps for Expelliarmus


## Requirements
  	1. Python (>=2.7)
  	2. Python module newtorkx
  	3. libguestfs-tools (>=1.36.x)
  	4. python-guestfs
 
## Installation
  	1.  $ mkdir Expelliarmus
  	2.  $ cd Expelliarmus
  	3.  $ git clone https://github.com/ExpelliarmusSuperComp/Expelliarmus
  	4.  $ cd ../../
  	5.  $ apt install libguestfs-tools
  	6.  $ apt install libguestfs-dev
  	7.  $ apt install python-guestfs
  	8.  $ wget “download.libguestfs.org/1.36-stable/libguestfs-1.36.13.tar.gz”
  	9.  $ tar -xf libguestfs-1.36.13.tar.gz
  	10. $ cd libguestfs-1.36.13
  	11. $ apt-get build-dep libguestfs
  	12. $ apt install autoconf automake libtool-bin gettext
  	13. $ ./configure
  	14. $ make
  	15. $ cd../Expelliarmus/Expelliarmus/
  	16. $ python main.py
  	17. $ Please provide path to libguestfs: ../../libguestfs-1.36.13
  	18. $ Expelliarmus ready to use : Type “help” to get more details.

## Troubleshooting
     
   	1. Error "libguestfs: error: tar_in: write error on directory: ..."	
      		$ Echo dash >/user/lib/x86_64-linux-gnu/guestfs/supermin.d/zz-dash-packages
     
   	2. Error "suprmin exited with status 1"	
      		$ chmod 0644 /boot/vmlinuz*
    
### Remark
	Check http://libguestfs.org/guestfs-building.1.html for more details on building libguestfs

## Dataset
	Expelliarmus is tested over synthetic VMIs created using virt-builder. Minimal script to create VMIs for local and Cloud use:
	```
	#!/bin/bash
	# path to libuguestfs
	../../libguestfs-1.36.13/run virt-builder ubuntu-16.04 \
	-o Image.qcow2 \
	--size 4G \
	--format qcow2 \
	--root-password password:123 \
	--edit '/etc/default/grub:s/ ^GRUB_CMDLINE_LINUX_DEFAULT= .*/GRUB_CMDLINE_LINUX_DEFAULT= "console=tty0 		console=ttyS0,115200n8"/' \
	--run-command update-grub \
	--install "dpkg-repack,fakeroot,dpkg-dev" \
	--update \
	--write /etc/default/locale: $"LANG=\"en_US.UTF-8\"" \
	--append /etc/default/locale: $"LANGUAGE=\"en_US\"" \
	--firstboot-command 'userdel -r builder && useradd -m -p "" builder ; chage -d 0 builder' 
	```
### Preparing VMIs for experiments
    	1. Save the above script as “vmBuilder.sh”. 
    	2. $ chmod +x vmBuilder.sh
    	3. source vmBuilder.sh
    	4. Output: Image.qcow2

### To Shrink the image, following commands are used:
    	On guest OS:
    	1. $ dd if=/dev/zero of=/mytempfile
    	2. $ rm -f /mytempfile
    
    	To shrink the VMI disk file without compression:
    	1. $ mv Image.qcow2 Image.qcow2_backup
    	2. $ qemu-img convert -O qcow2 Image.qcow2_backup Image.qcow2
  
### To Shrink the image, following commands are used:
    	Copy Image.qcow2 /Expelliarmus/Input/

## Experimental Workflow

    	$ python main.py 
    	Please provide path to libguestfs: /libguestfs-1.36.13 
    
    	(Expelliarmus): Command line interface 
    	Type "help" to see a list of available commands. 
    	Type "help name" to get a summary about the command "name" and how to use it. 
    	Any path given by the user to specify files or folders has to be relative to the working directory of this program.
    
    	(Expelliarmus): help
    	The following Commands are available. Type "help name" to get a summary about the command "name" and how to use it.
    	Any path given by the user to specify files or folders has to be relative to the working directory of this program:
		list-show information about VMI components currently stored
		inspect- inspect VMIs and define main services
		decompose- decompose VMIs
		reassemble- reassemble VMIs
		evaluate- tool to evaluate this program
		reset- reset local repository of VMI components
        	exit- exit program
    
     	Step 1: Enter primary software packages name
     	(Expelliarmus) inspect Input/Image.qcow2
      	Enter Main Services in format "MS1,MS2,..."
      	tomcat7,python3
	      
     	Step 2: Decompose a VMI
     	(Expelliarmus) decompose Input/
     
     	Step 3: Reassemble a VMI
     	(Expelliarmus) reassemble Image.qcow2
     
     
 ## Evaluation
 
    	(Expelliarmus) help evaluate
    	Usage: evaluate [options] { decomposition1 | decomposition2 | reassembly | similarity }
    	Evaluates the given functionality and saves results in folder "Evaluations".
    	Functionalities:
    	decomposition1:
    	Evaluates the decomposition process exploiting semantic redundancy (i.e. using a local repository).
    	Option "--path" has to be set to specify a source folder for VMIs (These will only be copied, not manipulated).
    
    	decomposition2:
    	Evaluates the decomposition process without exploiting semantic redundancy (i.e. not using a local     repository).
    	Option "--path" has to be set to specify a source folder for VMIs (These will only be copied, not manipulated).

    	reassembly:
    	Evaluates the reassembly process using any VMI present in the local repository.
    	Option "--path" is ignored.
	
    	similarity:
    	Evaluates the similarity between each VMI in source folder.
    	Option "--path" has to be set to specify a source folder for VMIs (These will not be manipulated).

    	Options:
		--repetitions=x:
        		Specify number of repetitions for evaluation (default is 5), not applicable for similarity.

		--path=x:
     		Specify source folder with VMIs for evaluation (ignored for evaluation of reassembly).
			Meta Files for all VMIs have to exist. Files in this folder are not manipulated.
	
    	Examples for Evaluation:
    
    	(Expelliarmus) evaluate --repetitions=5 --path=/Input/ decomposition1
    	(Expelliarmus) evaluate --repetitions=5 --path=/Input/ decomposition2
    	(Expelliarmus) evaluate --repetitions=5 reassembly
    	(Expelliarmus) evaluate --path=/Input/ similarity
    
    




