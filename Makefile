status:
	supervisorctl status

start:
	supervisorctl start all

stop:
	supervisorctl stop all

debug_corp:
	mosh corp.judge.vita500.ml --ssh="ssh -L 15673:127.0.0.1:15672" sudo su - onlinejudge


install reinstall update: .python-version
	make stop
	git pull
	pip install --upgrade -r requirements.txt
	make update-symbolic-link
	supervisorctl reload  # start

pyenv:  sudo-install-pyenv-dependency
	# https://minhoryang.github.io/en/posts/aws-ec2-instance-creation-for-python-dev/
	curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
	pyenv install 3.5.1
	pyenv virtualenv 3.5.1 3.5.1-onlinejudge
	pyenv local 3.5.1-onlinejudge


PLATFORM := $(shell uname)
ifeq ($(PLATFORM),Linux)
sudo-install:
	# Add user for OnlineJudge (without password)
	sudo adduser onlinejudge
	sudo passwd -d onlinejudge 
	# Install Packages
	sudo apt-get install rabbitmq-server supervisor
	# Set rabbitmq
	sudo rabbitmq-plugins enable rabbitmq_management
	# Set supervisor
	sudo addgroup supervisor
	-sudo addgroup minhoryang supervisor
	-sudo addgroup juice500 supervisor
	sudo addgroup onlinejudge supervisor
	sudo chown root:supervisor /etc/supervisor/conf.d
	sudo chmod 775 /etc/supervisor/conf.d
	@awk '/chmod=0700/{print "chmod=0770" RS "chown=root:supervisor";next}1' /etc/supervisor/supervisord.conf | sudo tee /etc/supervisor/supervisord.conf

sudo-install-pyenv-dependency:
	# https://github.com/yyuu/pyenv/wiki/Common-build-problems
	sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
	    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev

update-symbolic-link:
	@ln -s -f ~/online-judge/supervisor.onlinejudge.conf /etc/supervisor/conf.d/

else

install-mac install-darwin:
	brew install rabbitmq supervisor
	brew cask install launchrocket
	# XXX: Uncomment those 2 lines @ /usr/local/etc/supervisord.ini
	# [inet_http_server]
	# port=127.0.0.1:9001

pyenv-dependency  sudo-install-pyenv-dependency:
	# https://github.com/yyuu/pyenv/wiki/Common-build-problems
	brew install readline

update-symbolic-link:
	@sed 's/home/Users/' supervisor.onlinejudge.conf > supervisor.onlinejudge.ini.1
	@sed 's/onlinejudge/$(USER)/' supervisor.onlinejudge.ini.1 > supervisor.onlinejudge.ini.2
	@sed 's/-$(USER)/-onlinejudge/' supervisor.onlinejudge.ini.2 > supervisor.onlinejudge.ini
	@rm supervisor.onlinejudge.ini.*
	@mkdir -p /usr/local/etc/supervisor.d/
	ln -s -f $(PWD)/supervisor.onlinejudge.ini /usr/local/etc/supervisor.d/
endif
