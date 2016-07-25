'use strict';

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

var dom = skit.browser.dom;
var Controller = skit.platform.Controller;
var navigation = skit.platform.navigation;
var object = skit.platform.object;
var util = skit.platform.util;

var LKConfigAPIClient = library.api.LKConfigAPIClient;
var LKAnalyticsAPIClient = library.api.LKAnalyticsAPIClient;
var Dashboard = library.controllers.Dashboard;
var Select = library.react.components.Select;
var ConfigPreview = library.react.config.ConfigPreview;
var ConfigSettings = library.react.config.ConfigSettings;
var update = library.react.lib.update;
var ReactDOMServer = third_party.ReactDOMServer;


var DashboardContent = React.createClass({
  getInitialState: function() {
    return this.props.state;
  },

  setIsPublished: function(val) {
    return this.setState({isPublished:val});
  },

  setUpdatedKey: function(key, index) {
    var settings = update(this.state.settings, {$splice: [[index, 1, key]]});
    this.setState({settings: settings});
  },

  removeKey: function(index) {
    var settings = update(this.state.settings, {$splice: [[index, 1]]});
    this.setState({settings: settings});
  },

  togglePublishConfirm: function(){
    return this.setState({showPublish: !this.state.showPublish});
  },

  publishRules: function() {
    LKConfigAPIClient.publishRules(this.state.bundleId, {
      onSuccess: function(published) {
        this.setState({
          isPublished: published,
          publishedSettings: [].concat(this.state.settings)
        });
        this.togglePublishConfirm();
      },
      onError: function(error, msg) {
        this.handleError(error);
      },
      context: this
    });
  },

  addNewSetting: function(setting) {
    this.state.settings.push(setting);
    this.setState({settings: this.state.settings});
  },

  changeBundle: function(event) {
    var url;
    if (event.target.value == 'onboard') {
      url = '/config/onboard/';
    } else {
      url = '/config/dashboard/' + encodeURIComponent(event.target.value);
    }
    navigation.navigate(url);
  },

  previewLive: function() {
    this.setState({previewLive: !this.state.previewLive});
  },

  render: function() {
    return (
      <div>
        <div id="content-header" className="row">

          <div className="col-sm-4">
            <h1>
              <Select options={this.state.appOptions}
                onChange={this.changeBundle}
                selected={this.state.bundleId}/>
            </h1>

          </div>
          <div className="col-sm-8">

            <div className="pull-right">
              {(this.state.isPublished) ?
                <button type="button" className="btn btn-sm btn-success">
                  <span>Published</span>
                </button>
                :
                <span>
                  <button type="button" className="btn btn-sm btn-primary dropdown-toggle" onClick={this.togglePublishConfirm}>
                    <span>Publish</span> <span className="caret"></span>
                  </button>
                  <div className={(!this.state.showPublish) ? 'dropdown-menu dropdown-menu-animated' : 'dropdown-menu dropdown-menu-animated publish-confirm'}>
                    <strong>Really publish changes?</strong>
                    <p>This will have an immediate effect on your live app.</p>
                    <a className="btn btn-sm btn-block btn-primary" onClick={this.publishRules}>Publish Live</a>
                  </div>
                </span>
              }
              <a className="btn btn-sm btn-link pull-left" href={'/config/dashboard/' + encodeURIComponent(this.state.bundleId) + '/edit'}>
                <i className="fa fa-gear"></i> App Settings
              </a>
              <a className="btn btn-sm btn-link" href="/sdk/config/">
                Documentation
              </a>
            </div>
          </div>

        </div>

        <div id="content-editor" className="row">
          <div className="editor-preview">
            <h3>
              Preview
              {(this.state.publishedSettings.length) ?
                <button className="btn btn-xs btn-default pull-right" onClick={this.previewLive}>View Published</button>
                :
                null
              }
            </h3>
            <ConfigPreview settings={this.state.settings} />
          </div>
          {
            (this.state.previewLive) ?
              <div className="editor-preview published">
              <h3><span className="label label-success">Published Live</span></h3>
                <ConfigPreview settings={this.state.publishedSettings} />
              </div>
              :
              <ConfigSettings
                settings={this.state.settings}
                bundleId={this.state.bundleId}
                setIsPublished={this.setIsPublished}
                addNewSetting={this.addNewSetting}
                setUpdatedKey={this.setUpdatedKey}
                removeKey={this.removeKey} />
          }
        </div>
      </div>
    );
  }
})

// This is the normal "controller" for this URL in skit, which renders HTML
// and then takes over in the client.
module.exports = Controller.create(Dashboard, {
  fullWidthContent: true,

  __preload__: function(done) {
    this.bundleId = this.params['__bundle__'];

    var i = 2;
    function maybeFinish() {
      if (--i == 0) {
        done();
      }
    }

    function maybeHasLive() {
      if (this.publishStatus && this.publishStatus.live) {
        LKConfigAPIClient.rules({bundleId: this.bundleId, namespace: 'live'}, {
          onSuccess: function(rules, status) {
            this.publishedRules = rules;
            this.publishStatus = status;
          },
          onError: function(code, e) {
            throw new Error(JSON.stringify(e));
          },
          onComplete: maybeFinish,
          context: this
        });
      } else {
        maybeFinish()
      }
    }

    LKConfigAPIClient.rules({bundleId: this.bundleId}, {
      onSuccess: function(rules, status) {
        this.rules = rules;
        this.publishStatus = status;
      },
      onError: function(code, e) {
        throw new Error(JSON.stringify(e));
      },
      onComplete: maybeHasLive,
      context: this
    });

    var options = {
      product: LKAnalyticsAPIClient.Products.CONFIG,
      onlyConfigParents: true
    };
    LKAnalyticsAPIClient.apps(options, {
      onSuccess: function(apps) {
        this.apps = apps;
      },
      onError: function(code, e) {
        throw new Error('Error: ' + JSON.stringify(e));
      },
      onComplete: maybeFinish,
      context: this
    });

  },

  __title__: function() {
    return 'Edit Cloud Config: ' + this.bundleId;
  },

  reactBody: function(body) {
    var bundleId = this.bundleId;
    var settingsByKey = {};
    var settings = [];
    var publishedSettingsByKey = {};
    var publishedSettings = [];

    var isPublished = (
        this.publishStatus &&
        this.publishStatus['live'] &&
        this.publishStatus['draft'] &&
        this.publishStatus['live'] >= this.publishStatus['draft']);

    this.rules.forEach(function(rule, i) {
      var setting = settingsByKey[rule['key']];

      if (!setting) {
        if (rule['version'] || rule['build'] || rule['iosVersion']) {
          console.log('WARNING: Top-level setting somehow has qualifiers:', rule);
        }

        // First rule with this key: Make it the top-level setting, add rules list.
        setting = object.copy(rule);
        setting.rules = [];

        settingsByKey[setting.key] = setting;
        settings.push(setting);

      } else {
        setting.rules.push(rule);

      }
    });

    if (this.publishedRules) {
      this.publishedRules.forEach(function(rule, i) {
        var setting = publishedSettingsByKey[rule['key']];

        if (!setting) {
          // First rule with this key: Make it the top-level setting, add rules list.
          setting = object.copy(rule);
          setting.rules = [];

          publishedSettingsByKey[setting.key] = setting;
          publishedSettings.push(setting);
        } else {
          setting.rules.push(rule);
        }
      });
    }

    var appOptions = this.apps.map(function(app) {
      return {
        label: app['names']['short'],
        value: app['bundleId']
      };
    });
    appOptions.push({value: 'onboard', label: 'Add new app'})

    var state = this.state;
    if (!state) {
      state = {
        appOptions: appOptions,
        bundleId: this.bundleId || '',
        filterVersion: this.filterVersion || '',
        filterBuild: this.filterBuild || '',
        settings: settings,
        isPublished: isPublished,
        publishedSettings: publishedSettings
      };

      this.state = state;
    }

    return (
      <DashboardContent state={state} />
    );
  },

  __body__: function() {
    return ReactDOMServer.renderToString(this.reactBody());
  },

  __ready__: function() {
    ReactDOM.render(this.reactBody(), document.getElementById('dashboard-container'));

  }
});