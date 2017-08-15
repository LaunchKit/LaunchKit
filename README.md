LaunchKit
=========

This repo contains an unbranded version of all the code that once powered [LaunchKit](https://techcrunch.com/2015/03/11/for-those-about-to-launch-their-apps/). This notably includes **Screenshot Builder**, a web UI for creating App Store screenshots, and **Review Monitor**, which monitors Apple App Store review RSS feeds for new reviews and optionally notifies you about them.

**DISCLAIMER** This code was originally a subscription-supported consumer product, serving millions of web requests across many servers. If you are not technical, it will probably be difficult to make this work.

There's a bunch of other code in here for supporting the old [LaunchKit SDK](https://github.com/launchkit/launchkit-ios), in case you want to, for example, host a whitelabel in-app analytics platform or build a hosted server-configurable feature flags offering.

## Overview

We have packaged things up to run easily with [Vagrant](https://www.vagrantup.com) and [Ansible](https://www.ansible.com), so getting started running LaunchKit's services locally should be fairly straightforward in theory.

* [Getting Started](#getting-started) → HOWTO install & run your own instance of LK.
* [System Configuration](#system-configuration) → Easily editable settings to enable LK to work with third-party providers.
* [Architecture Overview](#architecture-overview) → Overview of how LK works.
* [Code Organization](#code-organization) → Overview of how code is organized in this repository.

If anything in this guide is not accurate or if you run into any issues installing & running LaunchKit, please send us a pull request. No one is actively addressing bug reports, but we will happily review and integrate pull requests.

## Getting Started

Getting your LK instance up and running is fairly simple. This process has been tested thoroughly on **Mac OS 10.11**, but should also work on other systems compatible with Vagrant, VirtualBox and Ansible.

### STEP 1

(OS X only -- on Linux & other systems you might need various other build tools in order to install Vagrant/Ansible.)

Install **Xcode dev tools** if you don’t have them yet. Running `cc` from the command line on OS X Terminal should prompt you to install them.

    $ cc

If the command complains about clang input, you're all set.

### STEP 2

Install **Vagrant**. You can find the installer here: https://www.vagrantup.com/downloads.html

Once the installer finishes, you don't need to do anything else.

### STEP 3

Install **VirtualBox** 5.0. You can find 5.0.x here: https://www.virtualbox.org/wiki/Download_Old_Builds_5_0 (The latest 5.1.x versions are not yet compatible for some reason, so use 5.0.x.)

Once the installer finishes, you don't need to open the VirtualBox app. (You can close it if it opens.)

### STEP 4

Install **ansible**:

    # You need pip and a newer version of setuptools to use ansible
    $ sudo easy_install pip
    $ pip install --upgrade setuptools --user python

    # Install ansible globally
    $ sudo pip install ansible

`ansible` should now work as a command:

    $ ansible

(Output should be an error message about missing targets, that's fine.)

### STEP 5

Get the LaunchKit code and configure your LK settings.

    $ git clone https://github.com/LaunchKit/LaunchKit.git
    $ cd LaunchKit

Edit your [System Configuration](#system-configuration) according to the various configuration detailed in the next section. (If you do this after the server is started, you will have to reboot.)

### STEP 6

Start LaunchKit (this might take awhile):

    $ vagrant up --provision

After that command finishes, your LK instance should be up and running at `http://localhost:9100/` &mdash; woohoo! (The instance might not be ready right away, check 30 seconds after provision is done.)

If you're **all done** using LaunchKit, you can stop the machine by running:

    $ vagrant halt

If you're never going to use LaunchKit again, you can destroy the machine altogether:

    $ vagrant destroy

## System Configuration

LaunchKit will work largely out of the box, but each service has some **external dependencies** that you will need to configure if you wish the service to work properly.

We have moved the most common configuration bits for LaunchKit into `LaunchKit/backend/settings.py` so you can easily find and reconfigure your local instance. After changes are made to this file, you should restart your local instance using `vagrant reload` &mdash; changes will not be reflected immediately on a running system.


### Global

If you want your LK instance to send emails, you will need to update the following settings:

* **EMAIL_SMTP_HOST** → You can set up an account with a service like Sendgrid, and enter their SMTP endpoint here, eg. `smtp.sendgrid.com`. By default TLS on port 587 is used, this is editable further down in the file.
* **EMAIL_SMTP_USER** and **EMAIL_SMTP_PASSWORD** → Your SMTP account credentials.
* **EMAIL_FROM_DOMAIN** → This should be the email address you with to send email _from_, eg. `yourdomain.com`.


### Screenshot Builder

Screenshot Builder runs locally and in your browser, but has one key dependency: in production environments, .zip files should be uploaded and hosted from Amazon S3, rather than the default local configuration.

In `LaunchKit/backend/settings.py`, update:

* **BUNDLES_S3_BUCKET_NAME** → Set this to the name of your S3 bucket, eg. `my-screenshot-bundles`
* **READWRITE_S3_ACCESS_KEY_ID** → Create an IAM role for a user with write access to your S3 bucket, and set the ID here.
* **READWRITE_S3_SECRET_ACCESS_KEY** → ... and set the SECRET here.
* **READONLY_S3_ACCESS_KEY_ID** → When serving bundles for download, you may wish to use a different IAM role if this server is public. Set this key to an IAM role with read access to your S3 bucket.
* **READONLY_S3_SECRET_ACCESS_KEY** → ... and set the SECRET for that user here.


### Review Monitor & Sales Monitor

If you would like Slack or Twitter integrations to work in your local instance, you must create a [Slack App](https://api.slack.com/slack-apps) or [Twitter App](https://apps.twitter.com/) and enter the key pairs in `backend/settings.py`. The relevant keys are:

* **SLACK_CLIENT_ID** and **SLACK_CLIENT_SECRET** → Credentials for your Slack App
* **TWITTER_APP_KEY** and **TWITTER_APP_SECRET** → Credentials for your Twitter App

If you would like Twitter preview images to work properly, you will need to configure a [URL2PNG](https://www.url2png.com/) account and set **URL2PNG_URL_KEY** and **URL2PNG_SECRET_KEY**.

### App Websites

If you want to use App Websites to host an actual website, you will need to expose the hosted frontend webserver externally. This webserver is accessible locally on `http://localhost:9105/` and works by loading the website configured for the current domain ("localhost" in this case) in order to render it.

To test it locally, you can create an App Website and set your domain to "localhost" &mdash; then your website should show up on `http://localhost:9105/` just like how you made it. If you configure a domain for it, eg. `hosted.yourdomain.com`, you can use that domain as a CNAME endpoint to host many App Websites.

### Super Users & Cloud Config

These products use our [LaunchKit iOS SDK](https://github.com/launchkit/launchkit-ios) to send events to the backend. In order to use them, our API webserver &mdash; located at `http://localhost:9101/` &mdash; must be accessible to the network your phone client is on. You can then update the iOS SDK to communicate with your instance of the API webserver, at whichever address you end up hosting it on.


## Architecture Overview

LaunchKit spawns several different *processes* in order to work:

* Skit frontend &mdash; `http://localhost:9100/` → Renders all of our frontend HTML, JavaScript and CSS. This server communicates with our backend API over HTTP in order to load content, and does not access the database itself. Daemon: `ansible/roles/lk-skit`, code: `LaunchKit/skit/...`
* API backend &mdash; `http://localhost:9101/` → Authenticates users, loads content, renders JSON over a REST API for all services. Daemon: `ansible/roles/lk-django/files/init.lk-django.conf`, code: `LaunchKit/backend/...`
* Celery task worker → Executes async tasks, spread throughout python codebase. Sends emails, fetches data from iTunes, creates Screenshot Bundles, etc. `ansible/roles/lk-django/files/init.celery.conf`, code: `LaunchKit/backend/...`
* Review ingester → Loads reviews from iTunes periodically. `ansible/roles/lk-review-ingester`, code: `LaunchKit/backend/review_ingester.py`
* Skit hosted frontend &mdash; `http://localhost:9105/` → Loads and renders custom App Websites according to the current domain (provided in the Host: HTTP header) and is not used by the other products. Daemon: `ansible/roles/lk-skit`, code: `LaunchKit/skit/lk/public_hosted/...`
* App Engine images host &mdash; `http://localhost:9103/` → Our GAE server handles all image hosting, image uploading and image resizing for LaunchKit products. Daemon: `ansible/roles/lk-google-app-engine`, code: `LaunchKit/gae/...`
* Dev proxy &mdash; `http://localhost:9102/` → A hack to enable App Engine to work with CORS locally. Daemon: `ansible/roles/lk-go-devproxy`, code: `LaunchKit/devproxy.go`


## Code Organization

LaunchKit is largely two codebases: a large python app called `backend`, and a large JavaScript app called `skit`. There are other parts that are less important, but those are the two primary codebases.

* `ansible` → All configuration for this local runtime environment, which spawns all services and loads all dependencies.
* `backend` → All python code, which is organized in a vaguely Django-like way, for our backend API and async task queues. This Django project has only one "app", called `lk`, which can be found in `backend/lk/`. Settings are in `backend/settings.py`.
* `backend/lk/views` → Backend API HTTP handlers.
* `backend/lk/logic` → Backend business logic for creating and managing various LK products.
* `backend/lk/models` → Backend database models for storing everything in LaunchKit.
* `gae` → A simple App Engine python application which handles all LaunchKit images. In production, Google App Engine's image service is simply incredible.
* `skit` → Our frontend web app and hosted App Websites webservers, based on [Skit](https://skitjs.com/).
* `skit/lk/library` → Library code used throughout the LK frontend & hosted frontend.
* `skit/lk/public` → Code for the public website, located at https://launchkit.io/
* `skit/lk/public_hosted` → Code for the hosted App Website endpoint, located at http://domains.launchkit.io/
