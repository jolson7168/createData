python-pip:
    pkg.installed
pika:
    pip.installed:
    - name: pika
    - require:
      - pkg: python-pip
    cmd.script:
    - source: /srv/salt/configDataSubscriber.sh
