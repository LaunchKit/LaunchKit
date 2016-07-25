/**
 * @license
 * Copyright 2016 Cluster Labs, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var ElementWrapper = skit.browser.ElementWrapper;
var dom = skit.browser.dom;
var Controller = skit.platform.Controller;
var iter = skit.platform.iter;
var navigation = skit.platform.navigation;
var string = skit.platform.string;
var urls = skit.platform.urls;
var util = skit.platform.util;

var LKAPIClient = library.api.LKAPIClient;
var Dashboard = library.controllers.Dashboard;
var inlineeditable = library.misc.inlineeditable;
var placeholderlabels = library.misc.placeholderlabels;
var AmbiguousProgressOverlay = library.overlays.AmbiguousProgressOverlay;
var ButtonOverlay = library.overlays.ButtonOverlay;
var Overlay = library.overlays.Overlay;
var TitledOverlay = library.overlays.TitledOverlay;
var products = library.products.products;

var html = __module__.html;
var addEmailForm = __module__.add_email.html;


module.exports = Controller.create(Dashboard, {
  __preload__: function(loaded) {
    LKAPIClient.userDetails({
      onSuccess: function(user, settings, emails) {
        this.user = user;
        this.settings = settings;
        this.emails = emails;
      },
      onComplete: function() {
        loaded();
      },
      context: this
    });
  },

  __load__: function() {
    this.products = products.publicProducts();
  },

  __body__: function() {
    this.emails.sort(function(a, b) {
      return a['email'].localeCompare(b['email']);
    });

    return html({
      'user': this.user,
      'emails': this.emails,
      'products': this.products
    });
  },

  __title__: function() {
    return 'Your Account';
  },

  renderFromDetails_: function(user, settings, emails) {
    this.user = user;
    this.emails = emails;

    this.rerender();
  },

  __ready__: function() {
    inlineeditable.init();

    this.subscribe(inlineeditable.EDITABLE_WILL_COMMIT, this.onEditableWillCommit_, this);
    this.subscribe(inlineeditable.EDITABLE_DID_COMMIT, this.onEditableDidCommit_, this);
  },

  onKeyPressInvoiceTextarea: function(evt) {
    // jquery much?
    evt.target.up('form').get('button').enable();
  },

  onSubmitInvoiceForm: function(evt) {
    evt.preventDefault();

    evt.target.get('button').disable();
    var params = evt.target.serializeForm();
    LKAPIClient.updateUserDetails(params, {
      onError: function() {
        evt.target.get('button').enable();
      }
    });
  },

  //
  // EVENT HANDLERS
  //

  onEditableWillCommit_: function(el, text, cancel) {
    var $el = new ElementWrapper(el);
    if (!$el.up('.name')) {
      return;
    }

    text = string.trim(text);
    if (!text || text.split(/\s+/).length < 2) {
      cancel();

      var overlay = new ButtonOverlay('First and Last Name Required', 'Please add a first and last name.');
      overlay.addButton('Okay');
      overlay.show();
    }
  },

  onEditableDidCommit_: function(el, text) {
    var $el = new ElementWrapper(el);
    if (!$el.up('.name')) {
      return;
    }

    var names = text.split(/\s+/);
    var firstName = names[0];
    var lastName = names.slice(1, names.length).join(' ');

    var fields = {
      'first_name': firstName,
      'last_name': lastName
    };
    LKAPIClient.updateUserDetails(fields, {
      onSuccess: this.renderFromDetails_,
      context: this
    });
  },

  handleAction: function(name, $target) {
    Dashboard.prototype.handleAction.apply(this, arguments);

    switch(name) {
      case 'edit-email':
        var email = $target.getData('email');
        var primary = $target.getData('primary');
        var unverified = $target.getData('unverified');
        this.editEmail_(email, primary, unverified);
        break;

      case 'add-email':
        this.addEmail_();
        break;
    }
  },

  // EDIT EXISTING EMAIL / PHONE

  editEmail_: function(email, primary, unverified) {
    if (this.emails.length == 1 && !unverified) {
      var overlay = new ButtonOverlay(email,
          'This is your only email address. If you want to change it, add another address first.');
      overlay.show();
      return;
    }

    var overlay = new ButtonOverlay('Change Email', email);
    if (!primary) {
      overlay.addButton('Make Primary', function() {
        this.maybeMakeEmailPrimary_(email);
      }, this);
    }
    if (this.emails.length > 1) {
      overlay.addButton('Remove', function() {
        this.maybeRemoveEmail_(email);
      }, this);
    }
    if (unverified) {
      overlay.addButton('Re-send Confirmation Email', function() {
        this.resendVerificationEmail_(email);
      }, this);
    }
    overlay.addButton('Cancel');
    overlay.show();
  },

  maybeMakeEmailPrimary_: function(email) {
    var message = 'Make this address primary?';
    var subtext = 'Any email notifications will be sent to this address.';
    var overlay = new ButtonOverlay(message, subtext);
    overlay.addButton('Make Primary', function() {
      var progress = new AmbiguousProgressOverlay('Saving...');
      progress.show();

      LKAPIClient.setEmailAddressPrimary(email, {
        onSuccess: function(emails) {
          this.emails = emails;
          this.rerender();
        },
        onComplete: function() {
          progress.done();
        },
        context: this
      });
    }, this);
    overlay.addButton('Cancel');
    overlay.show();
  },

  maybeRemoveEmail_: function(email) {
    var message = 'Remove this address?';
    var overlay = new ButtonOverlay(message);
    overlay.addButton('Remove', function() {
      var progress = new AmbiguousProgressOverlay('Removing...');
      progress.show();

      LKAPIClient.removeEmailAddress(email, {
        onSuccess: function(emails) {
          this.emails = emails;
          this.rerender();
        },
        onComplete: function() {
          progress.done();
        },
        context: this
      });
    }, this);
    overlay.addButton('Cancel');
    overlay.show();
  },

  resendVerificationEmail_: function(email) {
    var progress = new AmbiguousProgressOverlay('Sending...');
    progress.show();

    LKAPIClient.requestVerificationEmail(email, {
      onSuccess: function() {
        var overlay = new ButtonOverlay('Email Sent!',
            'Check your email for verification instructions.');
        overlay.show();
      },
      onComplete: function() {
        progress.done();
      },
      context: this
    });
  },

  // ADD NEW EMAIL

  addEmail_: function() {
    var $addForm = ElementWrapper.fromHtml(addEmailForm());
    this.addEmailOverlay_ = new TitledOverlay('Add Email', {
      content: $addForm,
      className: 'add-email-overlay',
      closeButtonTitle: 'Cancel'
    });

    placeholderlabels.init($addForm);
    this.bind($addForm, 'submit', this.onSubmitEmail_, this);

    this.addEmailOverlay_.addDidDismissListener(function() {
      delete this.addEmailOverlay_;
    }, this);
    this.addEmailOverlay_.show();
  },

  onSubmitEmail_: function(evt) {
    evt.preventDefault();

    var progress = new AmbiguousProgressOverlay('Adding email...');
    progress.show();

    var $form = evt.target.up('form');
    var email = $form.get('input').value();

    LKAPIClient.addEmailAddress(email, {
      onSuccess: function(email) {
        var success = new ButtonOverlay('Success!',
            'We have added the email address to your account.');
        success.addButton('Okay');
        success.show();

        this.emails.push(email);
        this.rerender();

        this.addEmailOverlay_.hide();
      },
      onError: function() {
        var ohnoes = new ButtonOverlay('Oh noes!',
            'Looks like we could not add this email address to your account.');
        ohnoes.addButton('Okay');
        ohnoes.show();
      },
      onComplete: function() {
        progress.done();
      },
      context: this
    });
  }

});
