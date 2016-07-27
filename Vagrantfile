# -*- mode: ruby -*-
# vi: set ft=ruby :

#
# Copyright 2016 Cluster Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  # LaunchKit services
  config.vm.network "forwarded_port", guest: 9100, host: 9100 # skit web app
  config.vm.network "forwarded_port", guest: 9101, host: 9101 # backend api
  config.vm.network "forwarded_port", guest: 9102, host: 9102 # dev proxy
  config.vm.network "forwarded_port", guest: 9103, host: 9103 # un-proxied app engine
  config.vm.network "forwarded_port", guest: 9104, host: 9104 # (intentionally left blank)
  config.vm.network "forwarded_port", guest: 9105, host: 9105 # hosted websites

  config.vm.network "private_network", ip: "192.168.42.10"

  config.vm.provider "libvirt" do |vb|
    vb.memory = "1024"
  end
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "1024"
  end

  config.vm.provision :ansible do |ansible|
    ansible.playbook = "ansible/vagrant.yml"
  end
end
